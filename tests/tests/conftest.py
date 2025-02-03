import pytest


@pytest.fixture(scope="session")
def engine_url():
    return (
        "postgresql+psycopg2://test_user:StrongPassword!123@localhost:5432/elixirdb"
    )
