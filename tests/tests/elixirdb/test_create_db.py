from elixirdb import ElixirDB
from elixirdb import ElixirDBStatements
from elixirdb import create_db


def test_create_db(appconfig):
    db = create_db(appconfig, engine_key="mysql")

    assert isinstance(db, ElixirDB)


def test_create_db_with_statements(appconfig):
    db = create_db(appconfig, engine_key="mysql", enable_statements=True)

    assert isinstance(db, ElixirDBStatements)
