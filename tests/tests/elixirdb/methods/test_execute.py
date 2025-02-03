from tests.utils import assert_case_result


def test_execute_with_results(enginemodel_db, test_user, test_table):
    """
    Test executing a simple SELECT statement to retrieve a user.

    Args:
        enginemodel_db: A database enginemodel_db using
            elixirdb or statementss mixin.

    Asserts:
        - The result contains the expected user with id = 1.
    """
    select_sql = f"SELECT name FROM {test_table} WHERE id = {test_user['id']}"

    result = enginemodel_db.execute(select_sql)
    fetched_result = result.fetchone()

    assert_case_result(fetched_result, expected_value=test_user["name"])


def test_execute_with_params(enginemodel_db, test_user, test_table):
    """
    Test executing a SELECT statement with parameters to retrieve a user.

    Args:
        enginemodel_db: A database enginemodel_db using elixirdb
            or statementss mixin.

    Asserts:
        - The result contains the expected user with the specified name.
    """

    select_sql = f"SELECT name FROM {test_table} WHERE id = :id"
    params = {"id": test_user["id"]}
    name = test_user["name"]

    result = enginemodel_db.execute(select_sql, params)
    fetched_result = result.fetchone()

    assert_case_result(fetched_result, expected_value=name)
