"""Database and test configurations."""

from itertools import product


# Load base database configurations
appconfig = {
    "debug": True,
    "defaults": {
        "engine_options": {
            "pool_size": 20,
            "pool_recycle": 3600,
            "echo": False,
        },
    },
    "engines": {
        "mysql": {
            "dialect": "mysql",
            "url": "mysql+pymysql://test_user:StrongPassword!123@localhost:3306/elixirdb",
            "engine_options": {
                "connect_args": {
                    "connect_timeout": 5,
                },
            },
        },
        "postgres": {
            "dialect": "postgres",
            "url": "postgresql+psycopg2://test_user:StrongPassword!123@localhost:5432/elixirdb",
            "engine_options": {
                "connect_args": {
                    "connect_timeout": 5,
                },
            },
        },
        "mssql": {
            "dialect": "mssql",
            "url": "mssql+pymssql://test_user:StrongPassword!123@localhost:1433/elixirdb",
            "schema_name": "dbo",
            "query_settings": {
                "schema_name": "elixirdb.dbo",
            },
            "engine_options": {
                "connect_args": {
                    "timeout": 5,
                },
            },
        },
        "oracle": {
            "dialect": "oracle",
            "url": "oracle+oracledb://test_user:StrongPassword!123@localhost:1521/?service_name=FREEPDB1",
        },
    },
}


databases = appconfig["engines"]

db_ids = list(databases.keys())

# Define the 3 types of engines to test.
engine_types = ("direct", "session", "scoped")

# dialect.engine_type
database_values = list(product(db_ids, engine_types))

# Generate readable IDs for the tests
database_ids = [f"{db}.{engine}" for db, engine in database_values]
