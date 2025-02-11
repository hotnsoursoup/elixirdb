"""
Application Configuration
"""

# ruff: noqa: TC001
from __future__ import annotations

from typing import Any
from typing import ClassVar
from typing import Mapping
from typing import Self
from pydantic import Field
from pydantic import model_validator

# from elixirdb.dictionaries.resources import drivers
from elixirdb.models.engine import EngineModel
from elixirdb.models.engine import driver_map
from elixirdb.models.model import StrictModel
from elixirdb.types import DriverMapping
from elixirdb.types import EngineKey


class EngineManager(StrictModel):
    """
    Configuration Manager for SqlAlchemy Engines.

    Sample Engine dictionary.

    engine = {
        "dialect": "postgres",
        "url": "postgresql+psycopg2://test_user:StrongPassword!123@localhost:5432/ellixirdb"
        "engine_options": {
            "pool_size": 10,
            "pool_recycle": 3600,
            "pool_pre_ping": True,
        },
        "session_options": {
            "autocommit": True,
            "autoflush":
        },
        "execution_options": {},
        "default": True
    }

    """

    default_engine_key: ClassVar[EngineKey | None] = None

    defaults: Mapping[str, Any] | None = Field(
        None,
        description=(
            """
            A mapping of EngineModel values. All fields become optional
            and these values are inherited by all engines. Values within
            each engine will take precedence over the defaults.
            """
        ),
    )

    engines: Mapping[EngineKey, EngineModel] = Field(
        description=(
            """
            A dictionary of engine configurations. The EngineKey is a str value
            that is used to identify the engine.
            """
        )
    )

    driver_mapping: DriverMapping = Field(
        driver_map,
        description=(
            "A dictionary that maps a database dialect to a "
            "'driver' or 'dialect+driver'. "
        ),  # pyright: ignore[reportAssignmentType]
    )
    global_override: bool = Field(
        False,
        description=(
            """
            Controls whether settings here override all other settings.
            Default behavior is for settings in specific databases to override
            the defaults set in defaults.
            """
        ),
    )

    debug: bool = Field(
        False,
        description=("Controls debug mode for all engines"),
    )

    @model_validator(mode="before")
    @classmethod
    def update_configs_with_default_values(
        cls,
        values: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Set the default values that all engines will use as a base. Configurations
        in the engines dictionary will override the defaults.
        """
        engines = values.get("engines", None)
        defaults = values.get("defaults", None)
        msg = "The `%s` key must be a dictionary or mapping."
        if engines and not isinstance(engines, dict):
            raise ValueError(msg % "engines")
        if defaults and not isinstance(defaults, dict):
            raise ValueError(msg % "defaults")

        if engines and defaults:
            if defaults:
                for engine_name, engine in values["engines"].items():
                    # Merge defaults and engine, with engine overriding defaults
                    merged_engine = defaults.copy()
                    merged_engine.update(engine)
                    values["engines"][engine_name] = merged_engine
        return values

    @model_validator(mode="after")
    def ensure_only_one_default(self) -> Self:
        """Ensure only only one database is marked as default"""
        if len(self.engines) < 1:
            return self

        defaults = sum(1 for db in self.engines.values() if db.default)

        if defaults > 1:
            raise ValueError(
                "Only one database can be set as the default. "
                "Please remove extra 'default' flags and ensure only one is set."
            )
        return self

    @model_validator(mode="after")
    def get_and_set_default_engine_key(self) -> Self:
        """
        Set the default engine key if one is set.
        """
        if not self.engines:
            return self
        for engine_key, engine in self.engines.items():
            if engine.default:
                self.set_default_engine_key(engine_key)
        return self

    @classmethod
    def set_default_engine_key(cls, engine_key: EngineKey) -> None:
        """
        Set the default engine key for the class.
        """
        cls.default_engine_key = engine_key
