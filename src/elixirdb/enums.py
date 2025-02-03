"""This module contains enums for various database operations and states."""

from enum import Enum
from enum import auto


class SQLOperation(str, Enum):
    """
    Enum for SQL operation types.

    Specifies the types of SQL operations that can be performed.
    """

    PROCEDURE = "procedure"  # A stored procedure operation.
    FUNCTION = "function"  # A function call operation.
    QUERY = "query"  # A standard SQL query operation.


class Dialect(str, Enum):
    """
    Enum for supported database dialects.

    Defines the database dialects supported by the application.
    """

    MYSQL = "mysql"  # MySQL database dialect.
    MARIADB = "mariadb"  # MariaDB database dialect.
    MSSQL = "mssql"  # Microsoft SQL Server dialect.
    POSTGRESQL = "postgres"  # postgres database dialect.
    ORACLE = "oracle"  # Oracle database dialect.
    SQLITE = "sqlite"  # SQLite database dialect.


class Handlers(str, Enum):
    """
    Enum for handler types.
    """

    ERROR_HANDLER = "error_handler"
    EXECUTION_HANDLER = "execution_handler"
    parameter_handlers = "parameter_handlers"
    STATEMENT_HANDLERS = "statement_handlers"
    RESULT_HANDLERS = "result_handlers"


class ExecutionState(str, Enum):
    """
    Enum for execution states.

    Represents the current state of database execution operations.
    """

    IDLE = "idle"  # Execution is idle.
    BEGIN = "begin"  # Execution is active.
    PROCESS_PARAMS = "process_params"  # Processing parameters.
    ADD_PAGING = "add_paging"  # Paging is being added to the query.
    FETCH = "fetch"  # Fetching results from the database.
    EXECUTE = "execute"  # Execution is in progress.
    PROCESS_RESULTS = "process_results"  # Processing results.
    COMMIT = "commit"  # Commiting changes.
    ERROR = "error"  # Execution encountered an error.


class ConnectionState(Enum):
    """
    Enum for connection states.

    Tracks the status of the database connection.
    """

    CONNECTED = auto()  # Connection is active.
    DISCONNECTED = auto()  # Connection is not active.
    ERROR = auto()  # Connection encountered an error.B


class ResultKeys(str, Enum):
    """
    Enum for result keys.
    """

    FETCHALL = "fetchall"
    FETCHONE = "fetchone"
    FETCHMANY = "fetchmany"
    ALL = "all"
    SCALARS = "scalars"
    COLUMNS = "columns"
    MAPPINGS = "mappings"
    RETURN_ROWS = "return_rows"
    ROWCOUNT = "rowcount"
    KEYS = "keys"
