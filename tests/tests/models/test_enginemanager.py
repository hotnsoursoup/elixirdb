# pyright: reportArgumentType=false, reportOptionalMemberAccess=false
from __future__ import annotations

import pytest
from pydantic import ValidationError
from elixirdb import EngineManager
from elixirdb.enums import Dialect


pytestmark = pytest.mark.models


class TestEngineManager:
    """Tests for the EngineManager model."""

    @property
    def config(self):
        return {
            "defaults": {
                "engine_options": {"pool_size": 5},
                "session_options": {"autocommit": False},
            },
            "engines": {
                "engine1": {
                    "name": "DB1",
                    "dialect": "postgres",
                    "url": "postgresql+psycopg2://user:pass@localhost:5432/db1",
                    "default": True,
                },
                "engine2": {
                    "name": "DB2",
                    "dialect": "mysql",
                    "url": "mysql://user:pass@localhost:3306/db2",
                    "engine_options": {"pool_size": 10},
                },
            },
        }

    def test_defaults_merging(self) -> None:
        """Test merging defaults with engine configs."""

        manager = EngineManager(**self.config)
        engine1 = manager.engines["engine1"]

        assert engine1.engine_options.pool_size == 5  # noqa: PLR2004

    def test_multiple_defaults(self, engine_url) -> None:
        """Test error when multiple engines are default."""

        config = self.config.copy()

        config["engines"]["engine3"] = {
            "name": "DB3",
            "dialect": Dialect.POSTGRESQL,
            "url": engine_url,
            "default": True,
        }

        with pytest.raises(ValidationError):
            EngineManager(**config)

    def test_default_engine_key_set(self) -> None:
        """Test that default engine key is set correctly."""

        manager = EngineManager(**self.config)
        assert manager.default_engine_key == "engine1"

    def test_driver_mapping(self) -> None:
        """Test driver mapping."""

        manager = EngineManager(**self.config)

        assert manager.driver_mapping["postgres"] == "postgresql+psycopg2"
