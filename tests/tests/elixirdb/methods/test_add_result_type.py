import pytest
from sqlalchemy import Result


def test_add_result_type(parameter_db):
    """
    Test the add_result_type method of the ElixirDB class.
    """
    parameter_db.result_types = []
    parameter_db.add_result_type(Result)

    assert Result in parameter_db.result_types

    # For coverage, test warning for duplicate result.
    parameter_db.add_result_type(Result)


def test_add_invalid_result_type(parameter_db):
    """
    Test the add_result_type method of the ElixirDB class.
    """
    with pytest.raises(TypeError):
        parameter_db.add_result_type("invalid_type")
