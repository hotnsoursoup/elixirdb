# pyright: reportOptionalMemberAccess=false,  reportAttributeAccessIssue=false
import uuid
import pytest
from elixirdb.enums import Dialect
from tests.tests.elixirdb.conftest import ElixirDBStatements
from tests.utils import assert_case_result


def test_stored_procedures(elixirdb_statements, test_user, test_table):
    """
    Test executing stored procedures using the statements mixin
    and verifying the results.

    - For MySQL and SQL Server, the 'GetUser' procedure is executed to
        retrieve a user.
    - For Oracle and postgres, the 'UpdateUserUUID' procedure updates
        a user's uuid.

    Args:
        elixirdb_statements: A database ElixirDB elixirdb_statements with a
        statements mixin.

    Asserts:
        - For 'GetUser', the result contains the expected user named
            'Emma Thompson'.
        - For 'UpdateUserUUID', the user's uuid is successfully updated.
    """
    if not isinstance(elixirdb_statements, ElixirDBStatements):
        pytest.skip(
            "Engine elixirdb_statements does not have raq statement support / "
            "stored procedures."
        )
    dialect = elixirdb_statements.db.dialect

    if dialect not in (Dialect.ORACLE, Dialect.POSTGRESQL):
        procedure_name = "GetUserName"
        params = {"id": test_user["id"]}
        name = test_user["name"]

        result = elixirdb_statements.procedure(procedure_name, params)
        fetched_result = result.fetchone()
        assert_case_result(fetched_result, expected_value=name)
    else:
        procedure_name = "UpdateUserUUID"

        new_uuid = uuid.uuid4()
        uuid_str = str(new_uuid)
        params = {"id": test_user["id"], "uuid": uuid_str}
        select_sql = f"SELECT uuid FROM {test_table} WHERE id = :id"

        # Execute the change
        elixirdb_statements.procedure(procedure_name, params)
        # Retrieve the result
        result = elixirdb_statements.execute(select_sql, {"id": test_user["id"]})
        fetched_result = result.fetchone()
        # Oracle returns the UUID as a string
        if dialect == Dialect.ORACLE:
            assert_case_result(fetched_result, expected_value=uuid_str)
        else:
            assert_case_result(fetched_result, expected_value=new_uuid)


def test_prefix_schema(engine_url):
    """
    Test the prefix_schema method to ensure it correctly prefixes a schema
    name with the appropriate dialect-specific prefix.
    """
    config = {
        "dialect": Dialect.POSTGRESQL,
        "url": engine_url,
        "statements": {"schema_name": "my_schema", "prefix_procedures": True},
    }

    db = ElixirDBStatements(config)

    procedure_name = "GetUserName"

    new_procedure = db.add_schema_prefix(procedure_name)

    assert new_procedure == "my_schema.GetUserName"
