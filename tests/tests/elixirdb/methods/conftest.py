import pytest


@pytest.fixture
def handlers():
    """
    Handlers for testing.
    """

    def myhandler1(x):
        return x

    def myhandler2(x):
        return [x]

    handlers = {
        "result_handlers": [
            myhandler1,
            myhandler2,
        ],
        "parameter_handlers": [
            myhandler1,
            myhandler2,
        ],
        "error_handlers": myhandler1,
    }
    return handlers
