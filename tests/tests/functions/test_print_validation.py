from pydantic import ValidationError
from elixirdb import EngineManager
from elixirdb.exc import print_and_raise_validation_errors


def test_print_validation_errors(engine_url):
    invalid_config = {
        "something": 1,  # extra attribute, forbidden
        "engines": {
            "engine1": {
                "url": "randomurl://",  # Invalid URL
                "default": True,
            },
            "engine2": {
                "name": "DB2",
                "default": True,
                "dialect": "mysql0",  # literal_error
                "url": "wrong_url",
                "engine_options": {"pool_size": 10},
            },
        },
    }
    expected_extra_input_error = "extra_forbidden"
    expected_literal_error = "literal_error"
    expected_invalid_url_error = "Invalid url format. Value provided: wrong_url"

    try:
        EngineManager(**invalid_config)
    except ValidationError as e:
        error_msg = print_and_raise_validation_errors(e, raise_error=False)
        assert expected_extra_input_error in error_msg
        assert expected_literal_error in error_msg
        assert expected_invalid_url_error in error_msg
