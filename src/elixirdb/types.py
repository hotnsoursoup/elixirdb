"Type definitions"

# isort: off
# ruff: noqa: E266, E501
# flake8: noqa: E266, E501
from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Literal, Mapping, Union
from typing import Callable
from typing import NotRequired
from typing import Protocol
from typing import Required
from typing import TypeAlias
from typing import TypedDict
from typing import TypeVar
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import RowMapping, Row

from elixirdb.models.engine import EngineModel
from elixirdb.enums import Dialect

if TYPE_CHECKING:
    from elixirdb.models.manager import EngineManager
    from sqlalchemy.sql.base import Executable
    from sqlalchemy.engine import Engine
    from sqlalchemy.engine.interfaces import _CoreAnyExecuteParams

M = TypeVar("M", bound=BaseModel)
_S = TypeVar("_S", bound=Session)

# Handler related types
# Dialect = Literal["mysql", "postgres", "sqlite", "oracle", "mssql", "mariadb"]

HandlerCallable = Callable[..., Any]
HandlerNames: TypeAlias = Literal[
    "parameter_handlers", "result_handlers", "error_handlers"
]

ProcessorFunc: TypeAlias = Callable[..., Any]
HandlerSequence: TypeAlias = Sequence[ProcessorFunc]
HandlerMapping: TypeAlias = Mapping[str, HandlerSequence]
# Query related types
SingleParam = Mapping[str, Any]
MultiParam = Sequence[SingleParam]
QueryResult: TypeAlias = (
    list[dict[str, Any]]  # List of dictionaries (e.g., rows with column names)
    | dict[str, Any]  # A single dictionary (e.g., a single row result)
    | list[tuple[Any, ...]]  # List of tuples (e.g., rows without column names)
    | None  # No result or empty result
)

# Database related types
SQLStatement: TypeAlias = str
TableName: TypeAlias = str
SchemaName: TypeAlias = str
DialectName: TypeAlias = str
DatabaseKey: TypeAlias = str
DriverName: TypeAlias = str  # e.g. "postgresql+psycopg2"
DriverMapping: TypeAlias = Mapping[Dialect, DriverName]


EngineType: TypeAlias = Literal["direct", "session", "scoped"]
SessionType: TypeAlias = Session | Callable[[], Session]
RowData: TypeAlias = Row[Any] | RowMapping | list[Row] | Any


# Typed Dicts
class BaseEngineDict(TypedDict, total=False):
    """
    Base TypedDict for shared optional fields in database configurations.
    """

    cursor_result_to_dict: bool
    apply_textclause: bool
    description: str
    default: bool
    engine_options: EngineOptionsDict | Mapping[str, Any]
    session_options: SessionOptionsDict | Mapping[str, Any]


class SessionOptionsDict(TypedDict, total=False):
    """
    SqlAlchemy-specific options for sessionmaker.

    See :class:`sqlalchemy.orm.session.sessionmaker` for more information.

    """

    # Whether to automatically flush pending changes to the database.
    autoflush: bool
    # Whether to expire all ORM objects after commit so that their state
    # is refreshed on next access.
    expire_on_commit: bool
    # Whether to use two-phase commit (requires backend support).
    twophase: bool
    # A default Engine used for this session (if any).
    bind: Engine | None
    # A mapping of bind keys to Engine objects for per-entity or multi-engine setups.
    binds: dict[str, Engine] | None


class EngineOptionsDict(TypedDict):
    """
    SqlAlchemy-specific options for database configurations.

    See :class:`sqlalchemy.engine.Engine` for more information.
    """

    # Database URL and connection
    url: str | None

    # Number of connections in the connection pool
    pool_size: int | None

    # Maximum number of connections to allow beyond the pool size
    max_overflow: int | None

    # Timeout in seconds for getting a connection from the pool
    pool_timeout: int | None

    # Number of seconds before recycling a connection
    pool_recycle: int | None

    # Test connections for liveness before using
    pool_pre_ping: bool | None

    # Log all SQL statements
    echo: bool | None

    # Enable SQLAlchemy 2.0-style behavior (for forward compatibility)
    future: bool | None

    # Connection Arguments
    # Pass arguments to the DBAPI
    connect_args: dict[str, str | int | bool] | None

    # Options for statement execution
    execution_options: dict[str, str | int | bool] | None

    # Thread/Process Management
    # Custom connection pool class
    poolclass: Callable | None

    # Custom connection function
    creator: Callable | None

    # Transaction isolation level (e.g., "READ_COMMITTED")
    isolation_level: str | None

    # Statement Cache
    # Enable/disable native Unicode handling
    use_native_unicode: bool | None

    # Number of prepared statements to cache
    statement_cache_size: int | None

    # Dialect-specific options (common examples)
    # Parameter style, e.g., "qmark", "numeric"
    paramstyle: str | None

    # Case sensitivity in column lookups
    case_sensitive: bool | None

    # Others
    # Log connection pool checkouts/checkins
    echo_pool: bool | None

    # Disable server-side cursors for certain DBs
    disable_server_side_cursors: bool | None


class UrlParams(TypedDict):
    """
    Connection parameters for database connections.

    See :class:`sqlalchemy.engine.URL` for more information.
    """

    drivername: NotRequired[str]
    host: Required[str]
    port: NotRequired[str | int]
    username: NotRequired[str]
    password: NotRequired[str]
    database: NotRequired[str]
    query: NotRequired[Mapping[str, Any]]


class EngineParams(TypedDict):
    """
    TypedDict for configurations requiring url_params and dialect.
    """

    url_params: Required[UrlParams]
    dialect: Required[Dialect]


class EngineUrl(TypedDict):
    """
    TypedDict for configurations requiring url_params and dialect.
    """

    url: Required[str]  # Database connection url string
    dialect: Required[Dialect]


class OptUrl(EngineUrl, BaseEngineDict, total=False):
    """
    TypedDict for default config that uses UrlConfig where the attributes
    are not required.
    """


class OptParam(EngineParams, BaseEngineDict, total=False):
    """
    TypedDict for default config that uses UrlParams where the
    attributes are not required.

    """


# The default configuration applied to all database connections.
DefaultEngineConfig: TypeAlias = OptUrl | OptParam
# Engine Configurations
EngineConfig: TypeAlias = EngineUrl | EngineParams
EngineConfigDict: TypeAlias = Mapping[str, EngineConfig | Mapping[str, Any]]


class ConfigDict(TypedDict, total=False):
    """
    Set the configuration for the application. You can provide a default
    """

    # A database driver mapping dictionary
    driver_mapping: DriverMapping

    # Controls whether settings here override all other settings.
    # Default behavior is for settings in specific databases to override
    # the defaults set in defaults.
    global_override: bool

    # Defaults that are used by all database connections. Any setting
    # in the database config itself will override the defaults set here.
    # The default configuration does not have to validate to a EngineModel.
    # It can be a partial that is inherited by other configs to be a complete
    # configuration.
    defaults: DefaultEngineConfig | Mapping[str, Any] | None


class AppConfigDict(TypedDict):
    """Database configuration dictionary"""

    app: NotRequired[ConfigDict]
    # A dictionary of database configurations, with keys as database names
    # Added dict[str, Any] to allow for more lax type checking
    engines: EngineConfigDict | dict[str, Any]


ConfigModel: TypeAlias = Union["EngineManager", EngineModel]

# The configuration passed into the connection classes
DatabaseEngineConfig: TypeAlias = (
    EngineConfig | AppConfigDict | ConfigModel | Mapping[str, Any]
)


# Protocol definitions
class ExecutionProtocol(Protocol):
    """
        This protocol specifies the methods that must be implemented by any
        class that wants to serve as a database executor.


        Example:
            >>> class CustomExecutionHandler(ExecutionProtocol):
            ...     def __call__(
            ...         self,
            ...         statement: str,
            ...         params: _CoreAnyExecuteParams
    ,
            ...         fetch: int | None
            ...     ) -> QueryResult:
            ...         # Your custom execution logic here
            ...         return result
    """

    def __call__(
        self, statement: str | Executable, params: _CoreAnyExecuteParams
    ) -> QueryResult: ...


class ErrorHandlerProtocol(Protocol):
    """
    Defines the interface for an error handler that can intercept and
    process exceptions. Classes implementing this protocol may also
    intercept attribute access with __getattr__ if desired.

    Example:
        >>> class CustomErrorHandler(ErrorHandlerProtocol):
        ...     def __init__(self, logger: logging.Logger):
        ...         self.logger = logger
        ...
        ...     def __call__(self, error: Exception) -> Any:
        ...         self.logger.error(f"An error occurred: {error}")
        ...         return "Handled result"

    """

    def __call__(self, error: Exception, config: EngineConfig | None = None) -> Any:
        """
        Handle an exception and return an appropriate response or action.

        Args:
            error (Exception): The exception to handle.

        Returns:
            Any: The result of handling the exception. Could be a default
                 value, a re-raised or wrapped exception, or any other
                 custom outcome.
        """

    def __getattr__(self, attr: str) -> Any:
        """
        Optionally intercept attribute/method access for additional error
        handling behavior, if needed.

        This is left open-ended to allow dynamic behavior. For example,
        you might dynamically generate methods that always handle errors
        internally.

        Args:
            attr (str): The attribute name being accessed.

        Returns:
            Any: The attribute or a callable that handles errors.
        """


class ResultHandlerCallable(Protocol):
    """
    Protocol for a result handler function. This function is responsible
    for processing the output of a database operation and returning the
    result for any result_types in ElixirDB.result_types.

    Example:
        >>> def filter_results(result: Any) -> Any:
        ...     # Your custom result processing logic here
        ...     return result
    """

    def __call__(
        self,
        result: Any,
        **kwargs: Any,
    ) -> Any: ...


class ParamHandlerCallable(Protocol):
    """
    Protocol to do parameter pre-processing before a query is executed
    (e.g. for logging, cleansing,)
    """

    def __call__(
        self,
        parameters: _CoreAnyExecuteParams,
        config: DatabaseEngineConfig | None = None,
        **kwargs: Any,
    ) -> Any: ...
