"Configure connection fixture for connection tests"

# pyright: reportArgumentType=false, reportOptionalMemberAccess=false
import uuid
from datetime import datetime
from itertools import product
from typing import Any
from typing import Generator
import pytest
from elixirdb import ElixirDB
from elixirdb.db import ElixirDBStatements
from tests.definitions import appconfig as appconfig_


databases = appconfig_.get("engines", {}) if appconfig_ else {}
dialects = list(databases.keys())  # mysql, postgres etc

# The three engines to use for every test that will use a live connection to db
engine_types = ("direct", "session", "scoped")

# Generate a unique combination of dialect and engine type
dbclass_dialect_enginetypes = list(
    product((ElixirDB, ElixirDBStatements), dialects, engine_types)
)

# Generate readable IDs for the combinations
database_ids = [
    f"{cls}.{db}.{engine}" for db, engine, cls in dbclass_dialect_enginetypes
]


@pytest.fixture(scope="session")
def appconfig() -> dict[str, Any]:
    return appconfig_


@pytest.fixture
def multiengine_db(request) -> Generator[ElixirDB, None, None]:
    """
    Create and yield a database connection instance, parameterized by
    the provided configurations. Closes the connection after tests.
    """
    db = None
    try:
        db = ElixirDB(config=appconfig_)
        db.connect()
        yield db
    finally:
        if db is not None and db.has_connection():
            db.rollback()
            db.close()


@pytest.fixture(params=dbclass_dialect_enginetypes)
def enginemodel_db(
    request,
) -> Generator[ElixirDB | ElixirDBStatements, None, None]:
    """
    Create and yield a database connection instance, parameterized by
    the provided configurations. Closes the connection after tests.

    Args:
        request: Pytest request object to access indirect parameters.

    Yields:
        ElixirDB: Instance of ElixirDB.
    """
    dbclass, dialect, engine_type = request.param
    config = databases[dialect]
    db = None
    try:
        db = dbclass(config=config, engine_type=engine_type)
        db.connect()
        yield db
    finally:
        if db is not None and db.has_connection():
            db.rollback()
            db.close()


dbclass_enginetypes = list(product((ElixirDB, ElixirDBStatements), engine_types))


@pytest.fixture(params=dbclass_enginetypes)
def enginemanager_db(
    request,
) -> Generator[ElixirDB | ElixirDBStatements, None, None]:
    """
    Create and yield an ElixirDB instance using an app with multiple engine
    configurations. Mysql is seleted as the initial engine configuration.
    """
    dbclass, engine_type = request.param
    engine_key = "mysql"
    db = None
    try:
        db = dbclass(
            config=appconfig_, engine_key=engine_key, engine_type=engine_type
        )
        db.connect()
        yield db
    finally:
        if db is not None and db.has_connection():
            db.rollback()
            db.close()


dialect_enginetypes = list(product(dialects, engine_types))


@pytest.fixture(params=dialect_enginetypes)
def elixirdb_statements(
    request,
) -> Generator[ElixirDBStatements, None, None]:
    """
    Create and yield a ElixirDBStatements instance for isolated, specific
    test cases for the ElixirDBStatements. (StatementsMixin +  ElixirDB))

    (e,g. test stored procedures)
    """
    dialect, engine_type = request.param
    config = databases[dialect]
    db = None
    try:
        db = ElixirDBStatements(config=config, engine_type=engine_type)
        db.connect()
        yield db
    finally:
        if db is not None and db.has_connection():
            db.rollback()
            db.close()


@pytest.fixture(scope="session")
def test_user() -> dict:
    """
    Fixture to return test user details.

    Returns test data that is populated into each database for testing

    Returns:
        dict: A dictionary containing test user details.
    """

    return {
        "id": 1,
        "name": "Emma Thompson",
        "dob": datetime.strptime("1985-07-23", "%Y-%m-%d").date(),
        "uuid": uuid.UUID("8a6f1d9e-53a9-4f8c-bb07-1d18a3e4b9b9"),
    }


@pytest.fixture
def test_table() -> str:
    """Return the test table. Can return direct string or a lookup"""
    return "test_data"


@pytest.fixture
def parameter_db():
    """
    Fixture to ensure some of the various base tests work with a db config built
    with a connection mapping configuration and single method tests.
    """
    config = {
        "dialect": "postgres",
        "url_params": {
            "username": "test_user",
            "password": "StrongPassword!123",
            "host": "localhost",
            "port": 5432,
            "database": "elixirdb",
        },
        "options": {
            "pool_size": 20,
            "max_overflow": 10,
            "pool_timeout": 30,
            "pool_recycle": 600,
            "pool_pre_ping": True,
            "connect_args": {"connect_timeout": 5},
        },
    }
    db = None
    try:
        db = ElixirDB(config=config)
        db.connect()
        yield db
    finally:
        if db is not None and db.has_connection():
            db.rollback()
            db.close()
