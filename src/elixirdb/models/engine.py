"""
EngineModel provides pydantic validation for SQLAlchemy Engine
configurations.
"""

# pyright: reportArgumentType=false
# pylint: disable=broad-except, W0707
# ruff: noqa: TC001
from __future__ import annotations

from typing import Any
from typing import Literal
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator
from pydantic_core import PydanticCustomError
from sqlalchemy.engine.url import make_url
from typing_extensions import Self
from elixirdb.enums import Dialect
from elixirdb.models.model import StrictModel
from elixirdb.models.options import EngineOptions
from elixirdb.models.options import SessionOptions
from elixirdb.models.urls import engines_url


driver_map = {
    Dialect.MYSQL: "mysql+pymysql",
    Dialect.MARIADB: "mariadb+pymysql",
    Dialect.MSSQL: "mssql+pymssql",
    Dialect.POSTGRESQL: "postgresql+psycopg2",
    Dialect.ORACLE: "oracle+oracledb",
    Dialect.SQLITE: "sqlite",
}


class UrlParams(StrictModel):
    """
    Url Connection parameters for the database.

    This model is used to store the necessary information to connect to
    a database.The driver is optional only if odbc is not utilized. If
    url is present in the model, it will override connection parameters.
    Review the model_validator in EngineModel for more information.

    """

    drivername: str = Field(
        "",
        description=(
            "SQLAlchemy database driver identifier. It may be a single dialect "
            "or a dialect and driver combination separated by '+'. "
        ),
        examples=["mysql+pymysql", "postgresql+psycopg2", "oracle+cx_oracle"],
    )
    host: str
    port: str = ""
    username: str = ""
    password: str = ""
    database: str = ""
    query: dict = Field(
        default_factory=dict,
        description="Query parameters for the URL string. (e.g. url/?key=value)",
    )

    @field_validator("port", mode="before")
    @classmethod
    def validate_port(cls, value: Any) -> str:
        """
        Will coerce a port to string.
        """
        return str(value)


class Statements(StrictModel):
    """
    Query model for database operations. This is experimental at the moment
    and the uses aren't fully flushed out.

    """

    schema_name: str | None = None
    prefix_raw_statements: bool = Field(
        False,
        description="Prefix tables defined in raw sql statements. Not in use",
    )
    prefix_procedures: bool = Field(
        default=False,
        description=(
            "When executing stored procedures, automatically prefix the "
            "procedure name with the schema defined in 'schema'."
        ),
    )

    def __init__(self, **data):
        """Sets the default values when enabling schema."""

        super().__init__(**data)
        p_queries = data.get("prefix_raw_statements", None)
        p_procedures = data.get("prefix_procedures", None)

        # Set the defaults to be True if not defined
        if self.schema_name and (p_queries is None and p_procedures is None):
            self.prefix_raw_statements = True
            self.prefix_procedures = True

    @model_validator(mode="before")
    @classmethod
    def validate_statements(cls, values: dict) -> dict:
        """
        Ensure correct values required by schema is set.

        Check before to ensure the user isn't passing the False value themselves.

        """

        schema_prefix = values.get("schema_name")
        prefix_raw_statements = values.get("prefix_raw_statements", None)
        prefix_procedures = values.get("prefix_procedures", None)

        if (
            schema_prefix
            and prefix_raw_statements is False
            and prefix_procedures is False
        ):
            raise ValueError(
                "Schema_prefix is provided, but both prefix_raw_statements and "
                "prefix_procedures are disabled."
            )

        if not schema_prefix and (prefix_raw_statements or prefix_procedures):
            raise ValueError(
                "schema_prefix is not provided, but prefix_raw_statements "
                "or prefix_procedures is set to 'True'"
            )

        return values


class EngineModel(StrictModel):
    """
    Single sqlalchemy database engine configuration model.

    The model forces a configuration to align with the expected schema
    to ensure that the database connection has the necessary parameters
    to create a connection.

    """

    debug: bool = False

    name: str = Field("", description="Name of the engine. Not in use.")
    dialect: Literal["mysql", "postgres", "mariadb", "sqlite", "mssql", "oracle"]
    default: bool = Field(
        False,
        description=(
            "Set the current engine as the default engine "
            "in a EnginerManager Model. (Multiple engines defined)"
        ),
    )
    auto_connect: bool = True
    apply_textclause: bool = Field(
        True,
        description=(
            "Apply textclause to any query sent to execute as a raw string."
        ),
        examples=["'SELECT 1' -> textclause('SELECT 1')"],
    )
    url: str | None = Field(
        None,
        description=("SQLAlchemy database connection url string."),
    )
    url_params: UrlParams | None = Field(
        None,
        description="URL parameters. Can be used instead of url. Useful when "
        "there are characters in the password that need escaping",
    )

    result_to_dict: bool = Field(
        True,
        description="Return results as dict. Only used in fetch_results method.",
    )

    session_options: SessionOptions | None = Field(
        None,
        description="See :class:`SessionOptions` for more information",
    )

    engine_options: EngineOptions | None = Field(
        None,
        description="Options passed into create_engine. See :class:`EngineOptions`",
    )
    statements: Statements = Field(default_factory=Statements)
    meta: dict[str, Any] = Field(
        default_factory=dict, description="Unused dictionary field. "
    )

    model_config = ConfigDict(extra="ignore", use_enum_values=True)

    @field_validator("url", mode="before")
    @classmethod
    def validate_sqlalchemy_url(cls, value: str | None) -> str | None:
        """
        Validates the provided url attribute.
        """
        if value is None:
            return value
        try:
            # Use SQLAlchemy's make_url to validate the URL
            make_url(value)
        except Exception:
            # raise ValueError("Url must match SqlAlchemy's engine url construct.")
            raise PydanticCustomError(  # noqa: B904
                "value_error",
                f"Invalid url format. Value provided: {value}",
                {"url": f"{engines_url}#sqlalchemy.engine.make_url"},
            )
        return value

    @model_validator(mode="after")
    def check_if_both_url_and_params(self) -> Self:
        """
        Checks if both `url` and `url_params` are provided. Both
        are mutually exclusive. (For this version)
        """
        if self.url and self.url_params:
            raise PydanticCustomError(
                "user_error",
                "Config should have either url or connection params, not both.",
            )
        return self

    @model_validator(mode="after")
    def check_if_not_url_and_not_params(self) -> Self:
        """
        Checks if both `url` and `url_params` are provided.
        """

        if not self.url and not self.url_params:
            raise PydanticCustomError(
                "user_error",
                "Each config requires a url or url_params.",
            )
        return self

    @model_validator(mode="after")
    def assign_driver(self) -> Self:
        """
        Assigns a default driver if not provided.
        """

        if self.url_params and not self.url_params.drivername:
            self.url_params.drivername = driver_map[self.dialect]
        return self
