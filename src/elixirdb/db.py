"""
Database connection and configuration management.

"""

# ruff: noqa: D102, PLR0916
# flake8: noqa: E501,
# pylint: disable=C0103,C0301,R0912,W0212
# pyright: reportUnknownVariableType=false, reportAttributeAccessIssue=false
from __future__ import annotations

import warnings
from functools import wraps
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import Literal
from typing import Sequence
from sqlalchemy import CursorResult
from sqlalchemy import Executable
from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from typing_extensions import Self
from elixirdb.base import ConnectionBase
from elixirdb.base import CursorResultMetadata
from elixirdb.enums import ConnectionState
from elixirdb.enums import ExecutionState
from elixirdb.exc import CursorResultError
from elixirdb.exc import EngineKeyNotFoundError
from elixirdb.exc import InvalidElixirConfigError
from elixirdb.exc import InvalidEngineTypeError
from elixirdb.exc import NoSessionFactoryError
from elixirdb.handlers import handler as h_
from elixirdb.models.manager import EngineModel
from elixirdb.utils.db_utils import apply_schema_to_statement


if TYPE_CHECKING:
    from sqlalchemy.engine import Engine
    from sqlalchemy.engine.interfaces import _CoreAnyExecuteParams
    from sqlalchemy.engine.row import RowMapping
    from sqlalchemy.orm.session import Session
    from elixirdb.types import DatabaseEngineConfig
    from elixirdb.types import EngineType
    from elixirdb.types import QueryResult
    from elixirdb.types import RowData


class ElixirDB(ConnectionBase):
    """Create a SqlAlchemyDatabase object from a configuration file."""

    # Provide a scopefunc for the session factory.
    scopefunc: Callable[[], Any] | None = None

    def __init__(
        self,
        config: DatabaseEngineConfig | None = None,
        engine_key: str | None = None,
        engine_type: EngineType = "direct",
        session_factory: scoped_session[Session]
        | sessionmaker[Session]
        | None = None,
        **kwargs,
    ):
        """
        Create a connection manager for SqlAlchemy Connections using a mapping
        such as a configuration file. This library provides support automatically
        for yaml files if the configuration has the prefix `elixir` within it.

        e.g. `elixir_db_config.yaml`
        e.g. `myelixir_config.yaml`

        A typed dict has been provided as well as the model to which it validates.

        For typedDict see :class:`elixirdb.models.manager.DatabaseEngineConfig`
        For model see :class:`elixirdb.models.manager.DatabaseEngineConfig`

        Args:
            config (DatabaseEngineConfig | None): The configuration used to initialize

            engine_key (str | None): Identifier for multi-db setups.
            engine_type (EngineType): Mode for session management:
                direct: Raw connection.
                scoped: Thread-local sessions.
                session: Standard session.
            session_factory (SessionType | None): Pre-configured session factory.
            **kwargs: Additional connection parameters.

        Raises:
            ModelValidationError: If configuration validation fails.
            InvalidConfigModel: If engine_key conflicts with single config.
            InvalidEngineTypeError: If engine_type is invalid.
        """
        super().__init__(config=config, engine_key=engine_key, **kwargs)

        self.debug = self.db.debug

        self.engine_type = engine_type
        self.session_factory = session_factory

        if engine_type != "direct":
            if not self.session_factory:
                self.session_factory = self.create_session_factory(
                    engine=self.engine, engine_type=engine_type
                )
            if engine_type == "scoped":
                self.session = self.session_factory
        if self.db.auto_connect and engine_type != "scoped":
            self.connect()

    def __repr__(self) -> str:
        if isinstance(self.db, EngineModel):
            config = self.db.model_dump(exclude_unset=True) if self.db else ""
        else:
            config = self.db
        # dialect = self.db.dialect if self.db else ""
        return f"Model={self.__class__.__name__}, config={config}>"

    def __enter__(self) -> Self:
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Exit context"""
        if exc_type is not None and self.connection is not None:
            self.connection.rollback()
        self.close()

    def __getattr__(self, name: str) -> Any:
        """
        Wrap attribute access with parameter and result handling.

        Returns:
            Any: Attribute value or wrapped callable managing state.
        """
        attribute = None
        # Check if it's in slots
        if name in getattr(type(self), "__slots__", []):
            return object.__getattribute__(self, name)

        # Check if it's a class-level attribute
        if hasattr(type(self), name):
            return getattr(type(self), name)
        # Set the execution state to active for state tracking
        self.statevars.exc_state = ExecutionState.BEGIN

        # Fetch methods retrieve from the Result object.
        if self.result and hasattr(self.result, name):
            attribute = getattr(self.result, name)
        else:
            if not self.session and not self.connection:
                self.connect()
            # Get attribute from the connection or session
            if self.engine_type == "direct":
                if hasattr(self.connection, name):
                    attribute = getattr(self.connection, name)
            elif hasattr(self.session, name):
                attribute = getattr(self.session, name)

        if not attribute:
            raise AttributeError(f"Attribute {name} not found")
        if callable(attribute):

            @wraps(attribute)
            def wrapper(*args, **kwargs):
                # Update state variables
                try:
                    # Process the args/kwargs and update any based on pre-processors
                    # (e.g. applying textclause to statement strings)
                    if name == "execute":
                        # Process any param handlers and convert str statements to textclause
                        new_args, new_kwargs = self._process_execute_args_kwargs(
                            *args, **kwargs
                        )
                        self.result = result = attribute(*new_args, **new_kwargs)
                    else:
                        self.result = result = attribute(*args, **kwargs)
                    # Add debugging information to the result
                    if isinstance(result, CursorResult) and self.debug:
                        self.update_cursor_meta(result)
                    # Process results if there are result handlers and result is
                    # a valid result type to be processed. Result types can be
                    # added to the result_types list using cls.add_result_type()
                    if (
                        result
                        and self.result_handlers
                        and (
                            isinstance(result, tuple(self.result_types))
                            or (
                                isinstance(result, list)
                                and all(
                                    isinstance(item, tuple(self.result_types))
                                    for item in result
                                )
                            )
                        )
                    ):
                        result = h_(handlers=self.result_handlers, data=result)
                    # Return the result
                    self.statevars.exc_state = ExecutionState.IDLE
                    return result

                except Exception as e:  # pylint: disable=broad-except
                    self.statevars.exc_state = ExecutionState.ERROR
                    # An error handler to capture different errors and apply
                    # handling globally.
                    if self.error_handlers:
                        if isinstance(self.error_handlers, list):
                            for handler in self.error_handlers:
                                handler(e)
                        else:
                            self.error_handlers(e)
                    else:
                        raise e from e

            return wrapper
        self.statevars.exc_state = ExecutionState.IDLE
        return attribute

    def _process_execute_args_kwargs(self, *args, **kwargs):
        """ """
        param_key = "parameters" if self.engine_type == "direct" else "params"

        if args:
            statement = args[0]
            if len(args) > 1:
                params = args[1]
            else:
                params = kwargs.get(param_key, {})
        else:
            statement = kwargs.pop("statement", None)
            params = kwargs.pop(param_key, {})
        # Return the args and let sqlalchemy handle the execution error
        if not statement:
            return args, kwargs

        if isinstance(statement, str) and self.db.apply_textclause:
            statement = text(statement)

        # Process any parameter handlers. This is useful to cleanse or validate
        # any parameters.
        if params and self.parameter_handlers:
            for handler in self.parameter_handlers:
                statement, params = handler(params)

        kwargs["statement"] = statement
        kwargs[param_key] = params

        return (), kwargs

    @property
    def engine(self) -> Engine:
        """
        Create a SQLAlchemy engine. See sqlalchemy.create_engine for more details.

        Renamed from engine to potentially provide some integration with
        flask_sqlalchemy
        """
        if not self.current_engine:
            engine_options = (
                self.db.engine_options.model_dump(
                    exclude_unset=True, exclude_none=True
                )
                if self.db.engine_options
                else {}
            )
            self.current_engine = create_engine(self.url_string, **engine_options)
        return self.current_engine

    def has_connection(self) -> bool:
        """
        Check if there is a connection/session to the database based on engine type.
        """
        if self.engine_type == "direct":
            return True if self.connection else False
        else:
            return True if self.session else False

    def new_session(self) -> ElixirDB:
        """
        Return a new session with the current configuration.

        If there is no session_factory, it means that there is isn't an active
        session either and using this method  will raise an exception.

        In this scenario, just use connect() to create a new session on the current
        instance.

        Returns:
            ElixirDB: New instance with active session.

        Raises:
            InvalidEngineTypeError: If connection mode is DIRECT or no session factory.
            NoSessionFactoryError: If session factory is not set.
        """

        if self.engine_type != "session":
            raise InvalidEngineTypeError(
                "new_session only works with `session` engine_type."
            )
        if not self.session_factory:
            raise NoSessionFactoryError(
                "A session was never created. Use connect() first."
            )

        self.session_factory = self.create_session_factory(
            engine=self.engine, engine_type=self.engine_type
        )
        config = self.config or self.db

        return ElixirDB(
            config=config,
            engine_key=self.engine_key,
            engine_type=self.engine_type,
            session_factory=self.session_factory,
            result_types=self.result_types,
        )

    def connect(self) -> Self:
        """Open, set, and return the connection."""
        if (self.engine_type == "direct" and self.connection) or (
            self.engine_type in ("scoped", "session") and self.session
        ):
            return self

        if self.engine_type == "direct":
            self.connection = self.engine.connect()
        else:
            # Ensure there is a factory
            if self.session_factory is None:
                self.session_factory = self.create_session_factory(
                    engine=self.engine, engine_type=self.engine_type
                )

            if self.engine_type == "session":
                self.session = self.session_factory()
            else:
                # Scoped sessions use factory directly.
                self.session = self.session_factory

        self.statevars.state = ConnectionState.CONNECTED
        return self

    def create_session_factory(
        self,
        engine: Engine | None = None,
        engine_type: EngineType | None = None,
        scopefunc: Any | None = None,
    ) -> sessionmaker[Session] | scoped_session[Session]:
        """
        Helper method to create a session factory.

        See :class:`sqlalchemy.orm.session.sessionmaker` for more details.

        Args:
            engine: SQLAlchemy engine. Default behavior is to check the
                property `engine` and use that.
            engine_type: The engine type to use. `direct` will yield a
                `connection` assigned to self, whereas `session` and `scoped`
                will yield a `session` assigned to self.
            scopefunc: Scope function for scoped sessions.
        Raises:
            InvalidEngineTypeError: If the connection mode is set to `direct`,
            this will raise an error.
        """
        engine = engine or self.engine
        engine_type = engine_type or self.engine_type
        if engine_type == "direct":
            raise InvalidEngineTypeError(
                "Cannot create a session factory for direct connection mode."
            )
        # Extract and prepare session options
        options = (
            self.db.session_options.model_dump(
                exclude_none=True, exclude_unset=True
            )
            if self.db.session_options
            else {}
        )

        if engine_type == "session":
            return sessionmaker(bind=engine, **options)

        # Reference to flask_sqlalchemy implementation. A scopefunc callable
        # can be assigned to the class as well. Used with scoped sessions.
        scopefunc = scopefunc or options.pop("scopefunc", None) or self.scopefunc

        return scoped_session(
            sessionmaker(bind=engine, **options), scopefunc=scopefunc
        )

    def set_engine(self, engine_key: str) -> None:
        """
        Set or change the configuration of the instance in a multi-database
        configuration by key engine_key.

        Args:
            engine_key: The engine_key of the database configuration to use.

        Raises:
            InvalidConfigModel: If attempting to call the method when the
                configuration is not a MultiEngineModel.
            KeyError: If the database configuration with the given engine_key
                does not exist.
        """
        if not self.config:
            raise InvalidElixirConfigError(
                "Cannot set engine when there is not configuration for "
                "multiple engines found. Review the docs for setting up "
                "multiple engines."
            )

        if engine_key not in list(self.config.engines.keys()):
            raise EngineKeyNotFoundError(engine_key=engine_key)

        if self.has_connection():
            self.close()

        self.engine_key = engine_key
        self.db = self.config.engines[engine_key]
        # Automatically connect new engine
        if self.db.auto_connect and hasattr(self, "connect"):
            self.connect()

    def close(self) -> None:
        """Close the connection to the database and cleanup resources."""
        if not self.connection:
            return
        try:
            if self.engine_type == "scoped" and self.session_factory:
                self.session_factory.remove()
            else:
                self.connection.close()
            self.connection = None
        except Exception as e:
            raise ConnectionError(f"Failed to close connection: {e!s}") from e

    def fetch_results(self, fetch: int | None = None) -> Sequence[RowData]:
        """Fetch results from the result object as mappings."""
        result = self.result
        if not result or not isinstance(self.result, CursorResult):
            raise CursorResultError(
                "The result object does not exist or is not a CursorResult."
            )

        if self.db.result_to_dict:
            if fetch == 0:
                return result.mappings().all()
            return result.mappings().fetchmany(fetch)

        if fetch == 0:
            return result.all()

        return result.fetchmany(fetch)

    def update_cursor_meta(self, result: CursorResult) -> None:
        """Update self.statevars.cursor_meta with metadata from CursorResult."""
        self.statevars.cursor_meta = CursorResultMetadata(
            columns=list(result.keys()),
            rows_affected=result.rowcount,
            last_insert_id=result.lastrowid,
            last_insert_rowid=result.lastrowid,
            last_insert_rowid_str=str(result.lastrowid),
            parameters=getattr(result.context, "compiled_parameters", None),
            sql_query=str(getattr(result.context, "compiled_statement", None)),
            column_descriptions=[
                {"name": col, "type": type_}
                for col, type_ in getattr(result.cursor, "description", []) or []
            ],
            generated_keys=getattr(result, "inserted_primary_key", None),
            is_closed=result.closed,
            execution_context=str(getattr(result, "context", None)),
        )

    def update_orm_meta(self, result: Any) -> None:
        """Update self.statevars.orm_meta with metadata from CursorResult."""

    @classmethod
    def set_scopefunc(cls, scopefunc: Any) -> None:
        """
        Add a scopefunc.

        This adds a scopefunc that the session_factory will use to identify
        the current session.
        """
        cls._scopefunc = scopefunc


class StatementsMixin:
    """
    Mixin class to add support for stored procedures. Will override execute
    method of the base class.
    """

    def procedure(
        self, procedure_name: str, parameters: _CoreAnyExecuteParams | None = None
    ) -> QueryResult:
        """
               Execute a stored procedure with given parameters.

               Args:
                   procedure_name (str): Name of the procedure.
                   parameters (_CoreAnyExecuteParams
        | None): Optional procedure
                       parameters.

               Returns:
                   QueryResult: Dict of affected rows or procedure results.

               Raises:
                   ValueError: If executed on SQLite.
        """

        dialect = self.db.dialect

        if dialect == "sqlite":
            raise ValueError(
                "SQLite does not support stored procedures or functions."
            )

        # Apply a schema prefix if enabled
        if (
            not self.statevars.schema_applied
            and self.db.statements.prefix_procedures
        ):
            procedure_name = self.add_schema_prefix(procedure_name, "procedure")
            self.statevars.schema_applied = True

        # Build the parameter string
        proc_parameters = self._build_parameters(parameters) if parameters else ""
        # Build the statement
        sql_statement = self._build_proc_stmt(
            procedure_name=procedure_name,
            parameters_str=proc_parameters,
            dialect=self.db.dialect,
        )

        return self.execute(sql_statement, parameters)

    def _execute_query(
        self,
        statement: Executable | str,
        parameters: _CoreAnyExecuteParams | None = None,
        fetch: int | None = None,
    ) -> Sequence[RowMapping] | Sequence[Any]:
        """Execute the actual statement and handle result fetching"""
        if parameters:
            result = self.result = self.connection.execute(statement, parameters)
        else:
            result = self.result = self.connection.execute(statement)
        if not result.returns_rows:
            return result

        self.statevars.columns = result.keys()

        if fetch is not None:
            result = self.fetch_results(result, fetch)

        return result

    def _build_proc_stmt(
        self,
        procedure_name: str,
        parameters_str: str,
        dialect: str,
    ) -> str:
        """Build SQL template for stored procedure based on dialect"""
        match self.db.dialect:
            case "postgres" | "mysql":
                return f"CALL {procedure_name}{parameters_str}"
            case "mssql":
                return f"EXEC {procedure_name} {parameters_str}"
            case "oracle":
                return f"BEGIN {procedure_name}{parameters_str}; END;"
            case _:
                raise ValueError(f"Unsupported dialect: {dialect}")

    def _build_parameters(self, parameters: _CoreAnyExecuteParams) -> str:
        """Build SQL template for stored procedure based on dialect"""

        match self.db.dialect:
            case "mssql" if parameters:
                return ", ".join(f"@{key} = :{key}" for key in parameters)
            case _:
                return (
                    f"({', '.join(f':{key}' for key in parameters)})"
                    if parameters
                    else ""
                )

    def add_schema_prefix(
        self,
        statement: str,
        operation_type: Literal["statement", "procedure"] = "procedure",
    ) -> str:
        """Add the schema to stored procedure/function names."""
        if not self.db.statements.schema_name:
            return statement
        if operation_type == "procedure":
            if "." in statement:
                warnings.warn(
                    "Prefix requires a query, stored procedure, or function name.",
                    stacklevel=2,
                )
            return f"{self.db.statements.schema_name}.{statement}"

        return apply_schema_to_statement(
            statement, self.db.config.schema_name, self.db.dialect
        )


class ElixirDBStatements(StatementsMixin, ElixirDB):
    """Statement enabled connection class."""


def create_db(
    config: DatabaseEngineConfig | None,
    engine_key: str | None = None,
    enable_statements: bool = False,
    engine_type: EngineType = "direct",
    **kwargs: Any,
) -> ElixirDB:
    """
    Create a db connection instance.

    Args:
        config (DbConfigDict | Config | None): Database configuration.
        engine_key (str | None): Connection engine_key.
        enable_statements (bool): If True, enable statement mixin.
        **kwargs: Additional keyword arguments for connection initialization.
            These can be a handler_dict, or other attributes for the base
            connection config class.

    Returns:
        ElixirDB: An instance of ElixirDB or a subclass
        with statement execution capabilities.
    """
    if enable_statements:
        return ElixirDBStatements(
            config=config,
            engine_key=engine_key,
            engine_type=engine_type,
            **kwargs,
        )

    return ElixirDB(
        config=config, engine_key=engine_key, engine_type=engine_type, **kwargs
    )
