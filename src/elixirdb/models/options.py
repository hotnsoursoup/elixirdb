"""Options for configuring SQLAlchemy connections."""

# ruff:: noqa: E501
# flake8: noqa: E501
# pylint: disable=C0301
from __future__ import annotations

from typing import Any
from typing import Callable
from pydantic import Field
from sqlalchemy.engine import Engine
from typing_extensions import Annotated
from elixirdb.models.model import StrictModel
from elixirdb.models.schemas import CallableSchema
from elixirdb.models.schemas import EngineSchema


Engine_ = Annotated[Engine, EngineSchema]
Callable_ = Annotated[Callable, CallableSchema]


class SessionOptions(StrictModel):
    """
    Options for configuring SQLAlchemy sessions.
    See :class:`sqlalchemy.orm.session.Session` for more details.
    """

    autocommit: bool = Field(
        False,
        description=(
            "When enabled, the session will automatically commit changes after "
            "each operation. This can be useful for simple operations but may not be "
            "appropriate for complex scenarios."
        ),
    )
    autoflush: bool = Field(
        True,
        description=(
            "When enabled, ensures that the session automatically calls "
            "`Session.flush()` before executing any query. This eliminates the "
            "need to manually flush changes, ensuring queries always operate on "
            "the latest state."
        ),
    )
    expire_on_commit: bool = Field(
        True,
        description=(
            "When set to True, all objects in the session are automatically expired "
            "after `commit()`, ensuring their state is reloaded from the database upon "
            "next access. This guarantees consistency with the database's current state."
        ),
    )
    twophase: bool = Field(
        False,
        description=(
            "When enabled, transactions use a two-phase commit protocol, allowing "
            "preparation of transactions across multiple databases before a final commit. "
            "This is useful for distributed or multi-database transactions."
        ),
    )
    bind: Engine_ | None = Field(
        None,
        description=(
            "The `bind` parameter associates a specific `Engine` or `Connection` "
            "with the session, ensuring all SQL operations are executed via this connection."
        ),
    )

    binds: dict[str, Engine_] | None = Field(
        None,
        description=(
            "A dictionary mapping specific entities (e.g., tables, mapped classes) "
            "to individual `Engine` objects for per-entity or multi-engine setups."
        ),
    )


class EngineOptions(StrictModel):
    """
    SqlAlchemy-specific options for database configurations.

    See :class:`sqlalchemy.engine.Engine` for more information or visit
    https://docs.sqlalchemy.org/en/20/core/engines.html#sqlalchemy.create_engine
    """

    connect_args: dict[str, Any] | None = Field(
        None,
        description=(
            "Dictionary of keyword arguments passed directly to the DBAPI's "
            "connect() method. Allows customization of the database "
            "connection process. See SQLAlchemy docs on 'Custom DBAPI "
            "connect() arguments / on-connect routines'."
        ),
    )

    creator: Callable_ | None = Field(
        None,
        description=(
            "Callable that returns a DBAPI connection. Used by the connection "
            "pool to create new connections. This bypasses connection "
            "parameters specified in the URL. DialectEvents.do_connect() "
            "offers more flexibility for customization."
        ),
    )

    echo: bool | str = Field(
        False,
        description=(
            "If True, logs all SQL statements and their parameters. If set "
            "to 'debug', result rows are also printed. Uses Python logging."
        ),
    )

    echo_pool: bool | str = Field(
        False,
        description=(
            "If True, logs pool activity like invalidation and recycling. If "
            "set to 'debug', checkouts and checkins are logged. Uses Python "
            "logging for more control."
        ),
    )

    enable_from_linting: bool = Field(
        True,
        description=(
            "If True, emits warnings for SELECTs with unlinked FROM elements "
            "that may cause Cartesian products."
        ),
    )

    execution_options: ExecutionOptions | None = Field(
        None,
        description=(
            "Dict of execution options applied to all connections. See "
            "Connection.execution_options() for details."
        ),
    )

    future: bool = Field(
        True,
        description=(
            "Use the 2.0-style Engine and Connection API. Default and only "
            "supported mode in SQLAlchemy 2.x."
        ),
    )

    hide_parameters: bool | None = Field(
        None,
        description=(
            "If True, hides SQL parameters in INFO logs and StatementError "
            "strings. Useful for logging sensitive data."
        ),
    )

    insertmanyvalues_page_size: int | None = Field(
        None,
        description=(
            "Rows per INSERT statement in 'insertmanyvalues' mode. Defaults "
            "to 1000 but varies by dialect."
        ),
    )

    isolation_level: str | None = Field(
        None,
        description=(
            "Transaction isolation level for new connections. Overrides URL "
            "defaults. See SQLAlchemy docs on 'Setting Transaction "
            "Isolation Levels'."
        ),
    )

    json_deserializer: Callable_ | None = Field(
        None,
        description=(
            "Callable to deserialize JSON strings into Python objects. "
            "Defaults to json.loads."
        ),
    )

    json_serializer: Callable_ | None = Field(
        None,
        description=(
            "Callable to serialize Python objects into JSON strings. Defaults "
            "to json.dumps."
        ),
    )

    label_length: int | None = Field(
        None,
        description=(
            "Max length of generated column labels. Defaults to the "
            "dialect's max identifier length."
        ),
        gt=0,
    )

    logging_name: str | None = Field(
        None,
        description=(
            "Identifier used in SQLAlchemy engine log messages. Defaults to "
            "a hexstring of the object's id."
        ),
    )

    max_identifier_length: int | None = Field(
        None,
        description=(
            "Overrides dialect max identifier length. Defaults to dialect settings."
        ),
    )

    max_overflow: int = Field(
        10,
        description=(
            "Max connections allowed in pool overflow. Only for QueuePool."
        ),
    )

    paramstyle: str | None = Field(
        None,
        description=(
            "DBAPI parameter style (e.g., 'named', 'qmark'). Defaults to the "
            "DBAPI's default."
        ),
    )

    pool: Any | None = Field(
        None,
        description=(
            "Pre-constructed Pool instance for connection pooling. Overrides "
            "URL parameters."
        ),
    )

    poolclass: Any | None = Field(
        None,
        description=(
            "Pool subclass used for connection pooling. Specifies type but "
            "does not instantiate it."
        ),
    )

    pool_logging_name: str | None = Field(
        None,
        description=(
            "Identifier for pool log messages. Defaults to object's id hexstring."
        ),
    )

    pool_pre_ping: bool | None = Field(
        None,
        description=(
            "If True, enables connection liveness checks before checkout "
            "from the pool."
        ),
    )

    pool_size: int = Field(
        5,
        description=(
            "Number of connections in the pool. 0 disables pooling "
            "(use NullPool instead)."
        ),
    )

    pool_recycle: int = Field(
        -1,
        description=(
            "Seconds before a connection is recycled. -1 disables timeout."
        ),
    )

    pool_reset_on_return: str | None = Field(
        "rollback",
        description=(
            "Reset strategy on connection return: 'rollback', 'commit', or "
            "None. See SQLAlchemy docs on 'Reset On Return'."
        ),
    )

    pool_timeout: float = Field(
        30,
        description=(
            "Seconds to wait for a connection from the pool before timing out."
        ),
    )

    pool_use_lifo: bool = Field(
        False,
        description=(
            "If True, uses LIFO for connection retrieval in QueuePool "
            "(default is FIFO)."
        ),
    )

    plugins: list[str] | None = Field(
        None,
        description=("List of plugin names to load. See CreateEnginePlugin docs."),
    )

    query_cache_size: int = Field(
        500,
        description=(
            "Size of SQL string cache. 0 disables caching. Cache pruned "
            "when 1.5x size."
        ),
    )

    use_insertmanyvalues: bool = Field(
        True,
        description=(
            "If True, enables 'insertmanyvalues' mode for bulk inserts with "
            "RETURNING clauses."
        ),
    )


class ExecutionOptions(StrictModel):
    """
    Execution options for SQLAlchemy connections.

    See :class:`sqlalchemy.engine.Connection.execution_options` or visit
    https://docs.sqlalchemy.org/en/20/core/connections.html# for more details.

    """

    compiled_cache: dict[Any, Any] | None = Field(
        None,
        description=(
            "Dictionary for caching compiled SQL statements. This can "
            "improve performance by reusing parsed query plans instead of "
            "recompiling them each time a query is executed."
        ),
    )
    logging_token: str | None = Field(
        None,
        description=(
            "A token included in log messages for debugging concurrent "
            "connection scenarios. Useful for tracking specific database "
            "connections in a multi-threaded or multi-process environment."
        ),
    )

    isolation_level: str | None = Field(
        None,
        description=(
            "Specifies the transaction isolation level for this connection. "
            "Controls how transactions interact with each other. Common "
            "values include 'SERIALIZABLE', 'REPEATABLE READ', "
            "'READ COMMITTED', 'READ UNCOMMITTED', and 'AUTOCOMMIT'."
        ),
    )
    no_parameters: bool | None = Field(
        None,
        description=(
            "If True, skips parameter substitution when no parameters are "
            "provided. Helps prevent errors with certain database drivers "
            "that treat statements differently based on parameter presence."
        ),
    )
    stream_results: bool | None = Field(
        None,
        description=(
            "Enables streaming of result sets instead of pre-buffering "
            "them in memory. Useful for handling large query results "
            "efficiently by fetching rows in batches."
        ),
    )
    max_row_buffer: int | None = Field(
        None,
        description=(
            "Defines the maximum buffer size for streaming results. "
            "Larger values reduce query round-trips but consume more memory. "
            "Defaults to 1000 rows."
        ),
    )
    yield_per: int | None = Field(
        None,
        description=(
            "Specifies the number of rows to fetch per batch when streaming "
            "results. Optimizes memory usage and improves performance "
            "for large result sets."
        ),
    )
    insertmanyvalues_page_size: int | None = Field(
        None,
        description=(
            "Determines how many rows are batched into an INSERT statement "
            "when using 'insertmanyvalues' mode. Defaults to 1000 but "
            "varies based on database support."
        ),
    )
    schema_translate_map: dict[str, str] | None = Field(
        None,
        description=(
            "A mapping of schema names for automatic translation during "
            "query compilation. Useful for working across multiple schemas "
            "or database environments."
        ),
    )
    preserve_rowcount: bool | None = Field(
        None,
        description=(
            "If True, preserves row count for all statement types, "
            "including SELECT and INSERT, in addition to the default "
            "behavior of tracking row counts for UPDATE and DELETE."
        ),
    )
