"""
This module provides utility functions for working with SQL queries and
database configurations.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING
from typing import Any
import sqlglot
from sqlglot import exp


if TYPE_CHECKING:
    from elixirdb.types import DialectName
    from elixirdb.types import HandlerSequence
    from elixirdb.types import SchemaName
    from elixirdb.types import SQLStatement
    from elixirdb.types import TableName
    from elixirdb.types import _CoreAnyExecuteParams


def is_stored_procedure(query: SQLStatement) -> bool:
    """
    Determine if a given SQL query string is a stored procedure call.

    Args:
        query: The SQL query string to be checked.

    Returns:
        True if the query is identified as a stored procedure call.

    Examples:
        >>> is_stored_procedure("EXEC my_stored_procedure")
        True
        >>> is_stored_procedure("SELECT * FROM my_table")
        False
    """
    query = query.strip().lower()

    patterns = [
        r"^exec\s",  # SQL Server, Sybase
        r"^execute\s",  # SQL Server, Sybase (alternative)
        r"^call\s",  # MySQL, postgres, Oracle
        r"^begin\s",  # PL/SQL block in Oracle
        r"^declare\s",  # PL/SQL anonymous block
    ]

    return any(re.match(pattern, query) for pattern in patterns)


TEMP_TABLE_PREFIXES = {
    "mssql": ["#", "tempdb..#"],
    "mysql": ["tmp_", "temp_"],
    "mariadb": ["tmp_", "temp_"],
    "sqlite": ["temp.", "temp_"],
    "postgres": ["pg_temp."],
    "oracle": ["temp_", "ora$ptt_", "sess$", "sys_temp_"],
}


def is_temp_table(table_name: TableName, dialect: DialectName) -> bool:
    """
    Checks if a table name represents a temporary table based on the dialect.

    Args:
        table_name: The name of the table to check.
        dialect: The SQL dialect to consider.

    Returns:
        True if the table name suggests a temporary table, False otherwise.
    """
    table_name = table_name.lower()
    prefixes = TEMP_TABLE_PREFIXES.get(dialect, [])
    return any(table_name.startswith(prefix) for prefix in prefixes)


def has_sorting(sql: SQLStatement) -> bool:
    """
    Check if an SQL query contains an "ORDER BY" clause outside subqueries.

    Args:
        sql: The SQL query string to be checked.

    Returns:
        True if the SQL query contains an "ORDER BY" clause.
    """
    sql = re.sub(r"\([^()]*\)", "", sql)
    order_by_pattern = re.compile(r"\bORDER\s+BY\b", re.IGNORECASE)
    return bool(order_by_pattern.search(sql))


def has_paging(sql: SQLStatement) -> bool:
    """
    Detect paging with limits and offsets in an SQL query.

    Args:
        sql: The SQL query to analyze.

    Returns:
        True if paging is detected.
    """
    paging_patterns = [
        r"\bLIMIT\s+(\d+)\s*(?:OFFSET\s+(\d+))?\b",
        r"\bLIMIT\s+(\d+)\b(?:\s+OFFSET\s+(\d+)\b)?",
        r"\bTOP\s+(\d+)\b(?:\s+OFFSET\s+(\d+)\b)?",
        r"\bROWNUM\s*\b(?:\s*\bBETWEEN\s*\d+\s*AND\s*\d+\b|\s*\b<=?\s*\d+\b)",
        r"\bLIMIT\s+(\d+)\s*(?:OFFSET\s+(\d+))?\b",
    ]

    return any(
        re.search(pattern, sql, re.IGNORECASE) for pattern in paging_patterns
    )


def build_sql_proc_params(params: _CoreAnyExecuteParams) -> str:
    """Formats parameters for SQL stored procedure query."""
    return f"({', '.join(f':{key}' for key in params)})" if params else ""


def process_params(
    params: dict[str, str] | tuple[tuple[str, str], ...], handlers: HandlerSequence
) -> dict[str, str] | tuple[tuple[str, str], ...]:
    """
    Preprocess parameters before passing them to the database query.

    Args:
        params: Parameters to process (dict or tuple of key-value pairs)
        handlers: List of processor functions to apply to parameter values

    Returns:
        Processed parameters as dictionary or tuple
    """
    if isinstance(params, dict):
        return {key: h(value) for key, value in params.items() for h in handlers}

    return tuple((key, h(value)) for key, value in params for h in handlers)


def return_mapped_dialect(dialect: DialectName) -> str:
    """Return mapped dialect for sqlglot"""
    dialect_map = {
        "mysql": "mysql",
        "mariadb": "mysql",
        "postgres": "postgres",
        "sqlite": "sqlite",
        "oracle": "oracle",
        "msql": "sqlserver",
    }
    return dialect_map.get(dialect, "")


def apply_schema_prefix(
    node: exp.Expression,
    schema_prefix: SchemaName,
    cte_names: set[str],
    dialect: DialectName,
) -> None:
    """
    Apply schema prefix to table nodes within SQL AST.

    Args:
        node: Current node in SQL AST
        schema_prefix: Schema prefix to apply
        cte_names: Set of CTE names to exclude from prefixing
        dialect: SQL dialect in use
    """
    match node:
        case exp.Table():
            table_name = node.this.name.lower()
            if table_name not in cte_names and not is_temp_table(
                table_name, dialect
            ):
                node.set("db", exp.Identifier(this=schema_prefix))

    for child in node.args.values():
        match child:
            case exp.Expression():
                apply_schema_prefix(child, schema_prefix, cte_names, dialect)
            case list():
                for item in child:
                    if isinstance(item, exp.Expression):
                        apply_schema_prefix(item, schema_prefix, cte_names, dialect)


def apply_schema_to_statement(
    query: SQLStatement, schema_prefix: SchemaName, dialect: DialectName = "mysql"
) -> SQLStatement:
    """
    Modify SQL query by applying schema prefix to table references.

    Args:
        query: Original SQL query to modify
        schema_prefix: Schema prefix to apply
        dialect: SQL dialect in use

    Returns:
        Modified SQL query with schema prefixes applied
    """
    dialect = return_mapped_dialect(dialect)
    ast = sqlglot.parse_one(query, read=dialect)
    cte_names = {cte.alias_or_name.lower() for cte in ast.find_all(exp.CTE)}
    apply_schema_prefix(ast, schema_prefix, cte_names, dialect)
    return ast.sql(dialect=dialect)


def get_default_db_count(config: dict) -> int:
    """
    Calculate the number of default databases in the given configuration.

    Args:
        config (dict): The database configuration dictionary that matches the
        MultiEngineModel schema.

    Returns:
        int: The count of databases marked as default in the configuration.

    """
    return sum(
        1 for db in config.values() if isinstance(db, dict) and db.get("default")
    )


def is_dml_query(statement: SQLStatement) -> bool:
    """Checks if a SQL statement is a DML query (INSERT, UPDATE, DELETE)."""
    try:
        parsed = sqlglot.parse_one(statement)
        return isinstance(parsed, (exp.Insert, exp.Update, exp.Delete))
    except Exception:  # pylint: disable=broad-except
        return False


def is_list_of_type(obj: Any, type_: type, subclass: bool = False) -> bool:
    """
    Check if an object is a list where all elements are of a specific type.

    Args:
        obj (Any): The object to check.
        type_ (type): The type to check the elements against.

    Returns:
        bool: True if obj is a list of type_, otherwise False.
    """
    if not subclass:
        return isinstance(obj, list) and all(
            isinstance(item, type_) for item in obj
        )
    return isinstance(obj, list) and all(issubclass(item, type_) for item in obj)
