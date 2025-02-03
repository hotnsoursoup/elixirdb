# pyright: reportOptionalMemberAccess=false
from __future__ import annotations

import pytest
from sqlalchemy import URL
from sqlalchemy.exc import SQLAlchemyError
from elixirdb import ElixirDB
from elixirdb.enums import ConnectionState
from elixirdb.exc import EngineKeyNotDefinedError
from tests.utils import assert_case_result


pytestmark = pytest.mark.core


@pytest.mark.parametrize("engine", ["direct", "session", "scoped"])
def test_valid_parameter_dbconfig(parameter_db, engine, test_table):
    """ """

    connection = parameter_db

    try:
        # Ensure the object is made properly
        assert isinstance(connection, ElixirDB)

        # Retrieve a sqlalchemy.engine.url.URL and validate type
        url = connection.param_url
        assert isinstance(url, URL)

        connection.connect()
        assert connection.has_connection()

        # Test a basic execute here. The rest of the methods once this is validated
        # should be the same as a connection built with a url.
        result = connection.execute(f"SELECT * from {test_table}")
        fetched_result = result.fetchall()

        assert len(fetched_result) > 0
    finally:
        connection.close()


def test_valid_elixirdb_base(enginemodel_db):
    """
    Test the connectivity to the database using the defined
    configurations.
    """
    connection = enginemodel_db
    try:
        assert isinstance(connection, ElixirDB)
        connection.connect()
        assert connection.has_connection()

        result = connection.execute("SELECT 1")
        fetched_result = result.fetchone()
        assert_case_result(fetched_result, expected_value=1)

    except SQLAlchemyError:
        dialect = connection.db.dialect
        connection.statevars.state = ConnectionState.ERROR

        pytest.fail(
            f"Connect could not be established for {dialect}."
            "Skipping the remaining tests for dialect."
        )
    except Exception as e:
        pytest.fail(f"Unexpected error: {e}")


def test_valid_multiengine_base(enginemanager_db):
    """
    Test to see if a multidatabase engine instance of ElixirDB / StatementsEnabledDB
    has been created and functions the same as a single engine instance.
    """
    connection = enginemanager_db

    assert isinstance(connection, ElixirDB)
    connection.connect()
    assert connection.has_connection()
    # Check to see if the engine_key is properly set
    assert connection.engine_key == "mysql"
    # Check if the specific dialect is set for the ElixirClass.db.dialect.
    # This confirms that the correct configuration was loaded into the EngineModel
    assert connection.db.dialect == "mysql"


def test_missing_default_and_engine_key(appconfig):
    """
    Raise a EngineKeyNotDefinedError error if a configuration with multiple engines
    is missing a default engine key or an engine_key is not defined.
    """
    with pytest.raises(EngineKeyNotDefinedError):
        ElixirDB(config=appconfig)
