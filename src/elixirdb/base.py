"""
Database base configuration classes.

"""

# ruff: noqa: D102
# flake8: noqa: E501
# pylint: disable=C0301
# pyright: reportAttributeAccessIssue=false, reportArgumentType=false, reportUnknownVariableType=false
from __future__ import annotations

import warnings
from dataclasses import dataclass
from dataclasses import field
from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar
from pydantic import ValidationError
from sqlalchemy import URL
from sqlalchemy import Connection
from sqlalchemy import CursorResult
from sqlalchemy import Engine
from sqlalchemy import Result
from sqlalchemy import ScalarResult
from sqlalchemy.orm.decl_api import declarative_base
from elixirdb.enums import ConnectionState
from elixirdb.enums import ExecutionState
from elixirdb.exc import ElixirFileNotFoundError
from elixirdb.exc import EngineKeyNotDefinedError
from elixirdb.exc import EngineKeyNotFoundError
from elixirdb.exc import print_and_raise_validation_errors
from elixirdb.models.engine import EngineModel
from elixirdb.models.manager import EngineManager
from elixirdb.utils.files import load_config


if TYPE_CHECKING:
    from sqlalchemy.orm import scoped_session
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.orm.session import Session
    from elixirdb.types import DatabaseEngineConfig
    from elixirdb.types import EngineType
    from elixirdb.types import ErrorHandlerProtocol
    from elixirdb.types import ExecutionProtocol
    from elixirdb.types import HandlerMapping
    from elixirdb.types import ParamHandlerCallable
    from elixirdb.types import ResultHandlerCallable
    from elixirdb.types import T


@dataclass(slots=True)
class ORMResultMetadata:
    """Metadata for ORM result objects."""

    model_name: str | None = None
    total_rows: int | None = None
    query_time: float | None = None
    fields: list[str] = field(default_factory=list)
    relationships: list[str] = field(default_factory=list)
    rows: list[Any] = field(default_factory=list)


@dataclass(slots=True)
class CursorResultMetadata:
    """ "Metadata for CursorResult objects"""

    columns: list[str] | None = None
    rows_affected: int | None = None
    last_insert_id: Any | None = None
    last_insert_rowid: Any | None = None
    last_insert_rowid_str: str | None = None
    pre_format_parameters: dict[str, Any] | list[Any] | None = None
    parameters: dict[str, Any] | list[Any] | None = None
    pre_format_sql_query: str | None = None
    sql_query: str | None = None
    column_descriptions: list[dict[str, Any]] = field(default_factory=list)
    generated_keys: list[Any] | None = None
    is_closed: bool | None = None
    execution_context: str | None = None


@dataclass(slots=True)
class StateVars(CursorResultMetadata):
    """State variables for tracking database execution state"""

    state: ConnectionState = ConnectionState.DISCONNECTED
    exc_state: ExecutionState = ExecutionState.IDLE
    connection_type: str = ""
    schema_applied: bool = False
    fetch_size: int | None = None
    page: int = 0
    limit: int = 0
    offset: int = 0
    rowcount: int = 0
    results: list = field(default_factory=list)
    cursor_meta: CursorResultMetadata = field(default_factory=CursorResultMetadata)
    orm_meta: ORMResultMetadata = field(default_factory=ORMResultMetadata)


@dataclass(slots=True)
class ConnectionConfig:
    """Boilerplate database configuration for SqlAlchemy"""

    # The model representation of the database configuration. This
    # will be generated based on the db_config.
    db: EngineModel

    # The global app or database settings.
    config: ClassVar[EngineManager | None] = None

    # Enable debug mode for more verbose state variable tracking
    debug: bool = False

    # Bypass validation. For internal use.
    _bypass: bool = False

    # The key used to identify the database configuration that is loaded.
    engine_key: str = ""

    # Result object returned from the database execution. This can be a
    # SqlAlchemy Result object, a declarative base class, SQLModel, etc.
    result: CursorResult | T | list[T] | None = field(default=None)

    # The current sqlalchemy engine being used by the subclass. Created
    # with :class:`sqlalchemy.create_engine`
    current_engine: Engine | None = None

    # The result types that result_handlers will process.
    # e.g. [Result, SqlAlchemyResult, SqlAlchemyRow, SqlAlchemyRowProxy]
    # All handlers in result_handlers will process the output of any
    # type defined in the result_types in addition to the SqlAlchemy
    # declarative base class.

    # Some types that may be useful for result_types:
    # Result, Row, RowMapping, ScarlarResult, MappingResult, ChunkedIteratorResult

    # This is not comprehensive as it does not include all ORM type results such
    # as Query, QueryResult, etc.
    result_types: list[Any] = field(default_factory=list)

    # The database connection created using a `direct` engine_type.
    connection: Connection | None = field(default=None)

    # The session created using a `session` or `scoiped_session` engine_type.
    session: Session | scoped_session[Session] | None = field(default=None)

    # The connection mode - direct, session, or scoped_session.
    engine_type: EngineType = "direct"

    session_options: dict[str, Any] | None = None
    # A session factory if the connection mode is session or scoped_session.
    session_factory: sessionmaker[Session] | scoped_session[Session] | None = field(
        default=None
    )

    # State tracking variables. Mainly used for debugging
    statevars: StateVars = field(default_factory=StateVars)

    # A custom handler to control the execution process for statements
    # such as raw SQL, Stored Procedures, etc.
    execution_handler: ExecutionProtocol | None = field(default=None)

    # An error handler you can assign to manage different types of errors
    # globally or create rules within the error handler to manage how
    # errors are handled depending on database type.
    error_handlers: ErrorHandlerProtocol | list[ErrorHandlerProtocol] | None = (
        field(default=None)
    )

    # A list of handlers to process the parameters of a database execution.
    # Use cases include converting data types, validating data, cleansing
    # data, etc.
    parameter_handlers: list[ParamHandlerCallable] = field(default_factory=list)

    # A list of handlers to process the result of a database execution.
    # These handlers can process results such as filtering data from
    # certain sources, serializing data, or performing other
    # operations on the result.
    # Future version may convert this to a dictionary mapping of :type:, Callable | list[Callable]
    result_handlers: list[ResultHandlerCallable] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Add in result types"""

        if not self.result_types:
            self.result_types = [
                Result,
                CursorResult[Any],
                declarative_base(),
                ScalarResult,
            ]

    @property
    def url_string(self) -> str | URL:
        """Return the URL if assigned, otherwise return the param URL"""
        return self.db.url if self.db.url else self.param_url

    @property
    def param_url(self) -> URL | str:
        """Return the connection URL built from connection parameters."""
        if self.db.url_params:
            return URL.create(**self.db.url_params.model_dump())
        return ""

    @property
    def url_base(self) -> str:
        """The base string for the connection uri"""
        return "{drivername}://{username}:{password}@{host}:{port}/{database}"

    @property
    def schema(self) -> str:
        """Get the schema name from the configuration"""
        s = self.db.statements
        if s and s.schema_name:
            return f"{s.schema_name}."
        return ""


class ConnectionBase(ConnectionConfig):
    """
    A base class that provides the base database attributes and initializes
    the configuration.
    """  # A mapping of handlers passed in as a dictionary.

    def __init__(
        self,
        config: DatabaseEngineConfig | None = None,
        engine_key: str | None = None,
        handlers: HandlerMapping | None = None,
        **kwargs,
    ) -> None:
        """
        Initialize the configuration object.

        Validate the type of configuration model being used. If no
        db_config is provided. Attempt to find a *elixir*.yaml/yml file
        within the project. Assign handlers and select the active engine
        configuration to be used if the configuration has multiple engines.

        Raises:
            ConfigNotFoundError: If no configuration is found, or a 'engine_key'
                key was provided, but no configuration matched that key.
        """

        # If a configuration is not provided, attempt to find it. The yaml
        # file must be prefixed with elixir. (e.g. myelixirdb.yaml, myelixirdb.yml)
        config = config or load_config()
        if not config:
            raise ElixirFileNotFoundError(
                "There were no configurations found "
                "in the project that matched `*elixir*.yaml`. "
            )

        # If the provided configuration is a dictionary, then validate it.
        if isinstance(config, dict):
            # Coerce it to a regular dict if it is a TypedDict
            config = dict(config)
            try:
                if config.get("engines"):
                    config = EngineManager(**config)
                else:
                    # If the config does not have `engines` as a key,
                    # assume it is a single Engine configuration. If it is not
                    # an EngineModel, it will fail validation.
                    config = EngineModel(**config)
            except ValidationError as e:
                print_and_raise_validation_errors(e)

        # The config should be a pydantic model at this point.
        if isinstance(config, EngineManager):
            # Set self.config, but only if it is not already set.
            self.config = config if not self.config else self.config
            engine_key = engine_key or config.default_engine_key or None
            if engine_key:
                db_config = config.engines.get(engine_key)
                if not db_config:
                    raise EngineKeyNotFoundError(engine_key=engine_key)
            # If there is only one configuration, then load it.
            elif len(config.engines) == 1:
                engine_key = engine_key or next(iter(config.engines.keys()))
                db_config = config.engines.get(engine_key)
            else:
                msg = (
                    "An engine_key was not provided and no default configurations "
                    "were found. Please see the quick start guide in the readme "
                    "for information on setting up your engines. "
                )
                keys = list(config.engines.keys())
                if keys:
                    msg += f"Available configurations: {keys}"
                raise EngineKeyNotDefinedError(msg)

        elif isinstance(config, EngineModel):
            # The config must be a EngineModel if validation has passed and
            # it is not a EngineManager model.
            db_config = config
        else:
            raise TypeError("Invalid configuration type. ")

        super().__init__(db=db_config, engine_key=engine_key, **kwargs)

        # Assign to class attribute
        if not self.config:  # Ensure it doesn't overwrite the class config
            self.config = config

        if not self.result_types:
            self.result_types = [Result, CursorResult[Any]]

        # Set the processing handlers.
        if handlers:
            self.set_handlers(handlers)

    @property
    def handler_names(self):
        """
        Return the names of the handlers available to be set.

        result_handlers:
            Process the results of a raw/orm query based on self.result_types
            that are set. Use cases could include converting ORM result objects or
            CursorResults to a list.

            See :class:'ConnectionnBase.result_types'
        parameter_handlers:
            Processes the parameters of a raw statement. This can be for
            cleansing the parameters or ensuring the params are compatible
            with the database charset, etc.

        error_handlers:
            Manage different error types within the instance instead of
            deploying handling for each function/method that may use the instance.
            Reduces redundancy in handling and can also be used for logging
            to a different source/engine.

        """
        return ["result_handlers", "parameter_handlers", "error_handlers"]

    def set_handlers(self, handlers: HandlerMapping) -> None:
        """Sets the handlers for the database operations."""

        for handler_name, _handler in handlers.items():
            # Check if the attribute exists in __slots__
            current_handler = getattr(self, handler_name)

            if handler_name not in self.handler_names:
                raise AttributeError(
                    f"Invalid handler name: {handler_name}. "
                    f"Valid handlers are: {self.handler_names}"
                )

            if isinstance(current_handler, list):
                # Append to the list if it's already a list
                if isinstance(_handler, list):
                    current_handler.extend(_handler)
                else:
                    current_handler.append(_handler)
            else:
                # If the dataclass did not set the default factory, it
                # should be set directly and not as a list.
                setattr(self, handler_name, _handler)

    def add_result_type(self, result_type: Any) -> None:
        """
        Add a new result type to the result types that are checked when
        determining if result_handlers should process the specified result
        type.
        >> db.add_result_type(SQLModel)

        if self.result_handlers and (
            isinstance(result.__class__, DeclarativeMeta)
            or isinstance(result, (self.result_types))
        ):
            return self._process_handler("result_handler", result)

        Args:
            result_type: The type to add for result validation

        Raises:
            TypeError: If validate=True and result_type is not a valid type

        Warns:
            UserWarning: If result_type already exists in result_types list
        """
        if not isinstance(result_type, type):
            raise TypeError(f"Expected a type, got {type(result_type)}")

        if result_type in self.result_types:
            warnings.warn(
                f"Result type {result_type.__name__} already exists.",
                UserWarning,
                stacklevel=2,
            )
            return

        self.result_types.append(result_type)
