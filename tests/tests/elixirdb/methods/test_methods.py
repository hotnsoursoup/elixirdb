import sys
import pytest
from elixirdb import ElixirDB
from elixirdb.exc import InvalidEngineTypeError
from elixirdb.exc import NoSessionFactoryError
from elixirdb.models.engine import EngineModel


def test_set_engine(appconfig):
    """
    Change the engine when using multiple engines.
    """
    if not len(appconfig["engines"]) > 1:
        raise ValueError("No multiple engines found in appconfig.")
    engines = list(appconfig["engines"].keys())

    dialect1 = engines[0]
    dialect2 = engines[1]
    conn = ElixirDB(config=appconfig, engine_key=dialect1)

    # Ensure the config is correct before comparison
    db_config_model1 = EngineModel(**appconfig["engines"][dialect1])
    assert conn.engine_key == dialect1
    assert conn.db == db_config_model1
    sys.stdout.write(str(type(conn.db)))
    conn.set_engine(dialect2)

    db_config_model2 = EngineModel(**appconfig["engines"][dialect2])
    sys.stdout.write(str(type(conn.db)))
    # Ensure the new engine_key is dialect2
    assert conn.engine_key == dialect2
    # Ensure it's the correct model for dialect2
    assert conn.db == db_config_model2


def test_connect(parameter_db):
    """Test using connect and return value"""
    with parameter_db.connect() as conn:
        assert isinstance(conn, ElixirDB)


def test_new_session(parameter_db):
    """Test creating new session"""
    parameter_db.engine_type = "session"
    parameter_db.connect()
    new_session = parameter_db.new_session()

    assert isinstance(new_session, ElixirDB)


def test_invalid_new_session(parameter_db):
    """Test creating new session"""
    parameter_db.engine_type = "direct"
    with pytest.raises(InvalidEngineTypeError):
        new_session = parameter_db.new_session()


def test_invalid_new_session_without_session(parameter_db):
    """Test creating new session"""
    parameter_db.engine_type = "session"
    parameter_db.session_factory = None
    with pytest.raises(NoSessionFactoryError):
        new_session = parameter_db.new_session()
