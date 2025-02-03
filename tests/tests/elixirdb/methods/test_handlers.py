import pytest
from elixirdb import ElixirDB


def test_config_with_handlers(appconfig, handlers):
    """
    Test setting handlers during instantiation.
    """
    db = ElixirDB(config=appconfig, engine_key="mysql", handlers=handlers)

    assert db.parameter_handlers[0] == handlers["parameter_handlers"][0]
    assert db.parameter_handlers[1] == handlers["parameter_handlers"][1]
    assert db.result_handlers[0] == handlers["result_handlers"][0]
    assert db.result_handlers[1] == handlers["result_handlers"][1]


def test_set_handlers_after_instantiation(parameter_db, handlers):
    """
    Test setting handlers after instantiation.
    """
    parameter_db.set_handlers(handlers)

    assert parameter_db.parameter_handlers[0] == handlers["parameter_handlers"][0]
    assert parameter_db.parameter_handlers[1] == handlers["parameter_handlers"][1]
    assert parameter_db.result_handlers[0] == handlers["result_handlers"][0]
    assert parameter_db.result_handlers[1] == handlers["result_handlers"][1]


def test_set_single_handler(parameter_db):
    def test_func(data):
        return data

    handlers = {"result_handlers": test_func}

    parameter_db.set_handlers(handlers)

    assert test_func in parameter_db.result_handlers


def test_invalid_handler_name(parameter_db):
    """
    Raises an attribute error when an unexpected handler key is passed into
    the set_engine dictionary.
    """

    def test_func(x):
        return x

    with pytest.raises(AttributeError):
        parameter_db.set_handlers({"invalid_handler": [test_func]})
