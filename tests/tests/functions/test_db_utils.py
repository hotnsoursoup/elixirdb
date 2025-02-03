# ruff: noqa: PT006
import pytest
from elixirdb.utils.db_utils import apply_schema_to_statement
from elixirdb.utils.db_utils import build_sql_proc_params
from elixirdb.utils.db_utils import has_paging
from elixirdb.utils.db_utils import has_sorting
from elixirdb.utils.db_utils import is_dml_query
from elixirdb.utils.db_utils import is_list_of_type
from elixirdb.utils.db_utils import is_stored_procedure
from elixirdb.utils.db_utils import is_temp_table
from elixirdb.utils.db_utils import process_params
from elixirdb.utils.db_utils import return_mapped_dialect


@pytest.mark.parametrize(
    "query, expected",
    [
        ("EXEC my_stored_procedure", True),
        ("SELECT * FROM my_table", False),
        ("CALL my_procedure", True),
        ("BEGIN my_block", True),
        ("DECLARE my_var", True),
    ],
)
def test_is_stored_procedure(query, expected):
    assert is_stored_procedure(query) == expected


@pytest.mark.parametrize(
    "table_name, dialect, expected",
    [
        ("#temp_table", "mssql", True),
        ("tempdb..#temp_table", "mssql", True),
        ("tmp_table", "mysql", True),
        ("my_table", "mysql", False),
    ],
)
def test_is_temp_table(table_name, dialect, expected):
    assert is_temp_table(table_name, dialect) == expected


@pytest.mark.parametrize(
    "sql, expected",
    [
        ("SELECT * FROM my_table ORDER BY id", True),
        ("SELECT * FROM (SELECT * FROM my_table) ORDER BY id", True),
        ("SELECT * FROM my_table", False),
    ],
)
def test_has_sorting(sql, expected):
    assert has_sorting(sql) == expected


@pytest.mark.parametrize(
    "sql, expected",
    [
        ("SELECT * FROM my_table LIMIT 10", True),
        ("SELECT * FROM my_table LIMIT 10 OFFSET 5", True),
        ("SELECT * FROM my_table", False),
    ],
)
def test_has_paging(sql, expected):
    assert has_paging(sql) == expected


@pytest.mark.parametrize(
    "params, expected",
    [
        ({"param1": "value1", "param2": "value2"}, "(:param1, :param2)"),
        ({}, ""),
    ],
)
def test_build_sql_proc_params(params, expected):
    assert build_sql_proc_params(params) == expected


@pytest.mark.parametrize(
    "params, handlers, expected",
    [
        ({"param1": "value1"}, [str.upper], {"param1": "VALUE1"}),
        ((("param1", "value1"),), [str.upper], (("param1", "VALUE1"),)),
    ],
)
def test_process_params(params, handlers, expected):
    assert process_params(params, handlers) == expected


@pytest.mark.parametrize(
    "dialect, expected",
    [
        ("mysql", "mysql"),
        ("mariadb", "mysql"),
        ("postgres", "postgres"),
        ("unknown", ""),
    ],
)
def test_return_mapped_dialect(dialect, expected):
    assert return_mapped_dialect(dialect) == expected


def test_apply_schema_to_statement():
    query = "SELECT * FROM my_table"
    schema_prefix = "my_schema"
    expected = "SELECT * FROM my_schema.my_table"
    assert apply_schema_to_statement(query, schema_prefix) == expected


@pytest.mark.parametrize(
    "statement, expected",
    [
        ("INSERT INTO my_table (id) VALUES (1)", True),
        ("UPDATE my_table SET id = 1", True),
        ("DELETE FROM my_table", True),
        ("SELECT * FROM my_table", False),
    ],
)
def test_is_dml_query(statement, expected):
    assert is_dml_query(statement) == expected


@pytest.mark.parametrize(
    "obj, type_, subclass, expected",
    [
        ([1, 2, 3], int, False, True),
        ([1, "2", 3], int, False, False),
        ([int, bool], object, True, True),
    ],
)
def test_is_list_of_type(obj, type_, subclass, expected):
    assert is_list_of_type(obj, type_, subclass) == expected
