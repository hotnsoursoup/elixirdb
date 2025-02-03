from __future__ import annotations

from elixirdb import EngineOptions
from elixirdb import ExecutionOptions
from elixirdb.models.options import SessionOptions


execution_options_dict = {
    "compiled_cache": {},
    "logging_token": "test_token",
    "isolation_level": "READ COMMITTED",
    "no_parameters": True,
    "stream_results": True,
    "max_row_buffer": 500,
    "yield_per": 200,
    "insertmanyvalues_page_size": 500,
    "schema_translate_map": {"old_schema": "new_schema"},
    "preserve_rowcount": True,
}


class TestOptions:
    """Test the options model."""

    def test_session_options(self) -> None:
        """Test complete model."""

        session_options = SessionOptions(
            autocommit=False,
            autoflush=True,
            expire_on_commit=True,
            twophase=False,
            bind=None,
            binds=None,
        )

        assert isinstance(session_options, SessionOptions)

    def test_execution_options(self) -> None:
        execution_options = ExecutionOptions(**execution_options_dict)

        assert isinstance(execution_options, ExecutionOptions)

    def test_engine_options(self) -> None:
        engine_options = EngineOptions(
            connect_args={"sslmode": "require"},
            creator=None,
            echo=True,
            echo_pool="debug",
            enable_from_linting=False,
            execution_options=ExecutionOptions(**execution_options_dict),
            future=True,
            hide_parameters=True,
            insertmanyvalues_page_size=500,
            isolation_level="SERIALIZABLE",
            json_deserializer=None,
            json_serializer=None,
            label_length=64,
            logging_name="test_engine",
            max_identifier_length=128,
            max_overflow=15,
            paramstyle="named",
            pool=None,
            poolclass=None,
            pool_logging_name="test_pool",
            pool_pre_ping=True,
            pool_size=10,
            pool_recycle=300,
            pool_reset_on_return="rollback",
            pool_timeout=20.0,
            pool_use_lifo=True,
            plugins=["test_plugin"],
            query_cache_size=100,
            use_insertmanyvalues=True,
        )
        assert isinstance(engine_options, EngineOptions)
