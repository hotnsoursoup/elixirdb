"Model Validation Errors"

from __future__ import annotations


REF_URL = "https://github.com/hotnsoursoup/quik-db/blob/master/README.md%s"


class ModelConfigError(Exception):
    """
    Custom exception class for handling validation errors.
    """


def print_and_raise_validation_errors(validation_errors, raise_error=True):
    """
    Prints validation errors extracted from a ValidationError object
    with linked information.

    """

    errors = validation_errors.errors()  # Extract errors from ValidationError
    config_errors = []
    engine_errors = {}
    msg = ""

    for error in errors:
        # Extract location and separate root config errors and engine model errors.
        loc = error.get("loc", [])
        if loc and loc[0] == "engines" and len(loc) > 1:
            name = loc[1]
            if name not in engine_errors:
                engine_errors[name] = [error]
            else:
                engine_errors[name].append(error)
        else:
            config_errors.append(error)

    if config_errors:
        msg = "Configuration Errors:\n"

        for e in config_errors:
            msg += add_model_error_to_msg(e)

    if engine_errors:
        for k, v in engine_errors.items():
            msg += f"Engine Errors: {k}\n"
            for engine_error in v:
                msg += add_model_error_to_msg(engine_error)
    if raise_error:
        msg = "\n" + msg
        raise ModelConfigError(msg) from None
    else:
        print(msg)
        return msg


def add_model_error_to_msg(error: dict) -> str:
    """
    Add an error message to a given error dictionary.
    """
    msg = ""
    location = None
    loc = error.get("loc", [])
    error_type = error.get("type", None)
    input = error.get("input", None)

    if loc and loc[0] == "engines":
        location = ".".join(str(loc) for loc in loc[2:])
    else:
        location = ".".join(str(loc) for loc in loc)

    msg += f"   - Type: {error_type} \n" if error_type else ""
    msg += f"     Location: {location}\n" if location else ""
    msg += f"     Message: {error.get('msg', 'Unknown error message')}\n"
    if error_type and error_type != "missing":
        msg += f"     Input: {input}\n" if input else ""

    # Add additional context if present
    for key, value in error.get("ctx", {}).items():
        if key != "error":
            msg += f"     {key.capitalize()}: {value}\n"
    return msg


def get_error_msg(error: dict) -> str:
    """
    Extract and return an error message from a given error dictionary.

    Args:
        error (dict): A dictionary containing error information.

    Returns:
        str: The extracted error message. If the "ctx" dictionary
            contains an "error" key, its value is returned. Otherwise,
            the value of the "msg" key in the error dictionary is
            returned. If neither is present, an empty string is returned.

    """
    ctx = error.get("ctx", {})
    if ctx and ctx.get("error"):
        return ctx.pop("error")
    return error.get("msg", "")


class ElixirConfigError(Exception):
    """
    Base exception class for ElixirDB configuration errors.
    """


class InvalidElixirConfigError(ElixirConfigError):
    """Exception raised when an invalid configuration is provided."""


class ElixirFileNotFoundError(ElixirConfigError):
    """Exception raised when a specified configuration name is not found."""


class EngineKeyNotFoundError(ElixirConfigError):
    """Exception raised when a specified configuration name is not found."""

    def __init__(self, engine_key: str, message: str | None = None):
        if not message:
            message = f"Engine key '{engine_key}' not found in the configuration."
        message = message.format(engine_key=engine_key)

        super().__init__(message)


class InsufficientEnginesError(ElixirConfigError):
    """Exception raised when a specified configuration name is not found."""


class EngineKeyNotDefinedError(ElixirConfigError):
    """
    Exception raised when a configuration could not be identified because
    an 'engine_key' was not provided or a 'default' configuration could not
    be found.

    :class:'elixirdb.models.manager.Config'
    """


class InvalidEngineTypeError(Exception):
    """
    Exception raised when attempting to create a session factory in
    direct connection mode.
    """


class CursorResultError(Exception):
    """
    Exception when attempting to access a cursor result.
    """


class NoSessionFactoryError(Exception):
    """
    Exception raised when attempting to access a session factory.
    """


class FlaskNotInstalledError(Exception):
    """
    Error raised when using flask related features without flask installed.
    """
