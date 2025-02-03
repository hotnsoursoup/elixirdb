"Test utility functions"

# ruff: noqa: B904, PLR0912

from __future__ import annotations

from copy import deepcopy
from datetime import date
from datetime import datetime
from pathlib import Path
from random import choice
from typing import TYPE_CHECKING
from typing import Any
import pytest


if TYPE_CHECKING:
    from elixirdb import ElixirDB


def has_any_marker(item: pytest.Item, markers: str | list[str]) -> bool:
    """
    Check if a test item has any marker from a specified list or string.

    Args:
        item: The test item to check for markers.
        markers: A single marker name or a list of marker names to
            check for.

    Returns:
        True if any marker from the input is present on the test item.
    """

    markers = [markers] if isinstance(markers, str) else markers

    return any(item.get_closest_marker(marker) for marker in markers)


def assert_case_result(
    result, expected_value, key=None, expected_type=None, msg=None
):
    """
    Helper function to handle different result types and compare
    against anexpected value.

    Args:
        result: The result returned from a database query.
        expected_value: The value expected to be found in the result.
        key (optional): The key to use when extracting value from
            mappings or objects.
        expected_type (optional): The expected type of the extracted
            value.

    Raises:
        AssertionError: If the actual value does not match the expected
            value or type.
        KeyError: If the specified key is not found in the result.
        TypeError: If the result type is unexpected or cannot be
            handled.
    """

    actual = extract_value(result, key)

    if isinstance(actual, datetime):
        actual = actual.date()
    if isinstance(expected_value, datetime):
        expected_value = expected_value.date()

    # Convert to string representations
    if isinstance(actual, date):
        actual_str = actual.isoformat()
    else:
        actual_str = str(actual)

    if isinstance(expected_value, date):
        expected_str = expected_value.isoformat()
    else:
        expected_str = str(expected_value)

    actual_str = actual_str.strip()
    expected_str = expected_str.strip()

    if expected_type is not None:
        assert isinstance(actual, expected_type), (
            f"Expected type {expected_type}, got {type(actual)}."
        )

    msg_ = (
        f"Expected value: {expected_str!r} (type {type(expected_value)}) \n"
        f"Actual value: {actual_str!r} (type {type(actual)})"
    )

    msg = msg if msg else msg_

    assert actual == expected_value, msg


def extract_value(item: Any, key: str | None = None) -> Any:
    """
    Extracts a value from an item, which can be a scalar, list, tuple,
    dict, or an object with __getitem__.

    Args:
        item: The item from which to extract the value.
        key (optional): The key to use when extracting value from
            mappings or objects.

    Returns:
        The extracted value.

    Raises:
        KeyError: If the specified key is not found in the item.
        TypeError: If the item type is unexpected or cannot be handled.
        AssertionError: If the item is an empty list or tuple.
    """
    # Handle scalar values directly
    if isinstance(item, (int, float, str)):
        return item

    # Handle lists or tuples
    elif isinstance(item, (list, tuple)):
        if not item:
            raise AssertionError("Result list or tuple is empty.")
        # Recursively extract from the first element
        return extract_value(item[0], key)

    # Handle dictionaries or mappings
    elif isinstance(item, dict):
        if key is not None:
            if key in item:
                return item[key]
            else:
                m = f"Key '{key!r}' not found in the result dictionary."
                raise KeyError(m)
        else:
            # Return the first value if no key is specified
            return next(iter(item.values()))

    # Handle objects with __getitem__
    elif hasattr(item, "__getitem__"):
        if key is not None:
            try:
                return item[key]
            except (KeyError, IndexError, TypeError) as exc:
                raise KeyError(
                    f"Key or index '{key!r}' not found in the result object."
                ) from exc
        else:
            # Return the first item if no key is specified
            try:
                return item[0]
            except (IndexError, TypeError) as exc:
                raise TypeError(
                    "Cannot extract value from object of type "
                    f"{type(item)} without a key or index."
                ) from exc

    else:
        raise TypeError(f"Unexpected result type: {type(item)}")


def assert_error_message(exception, message):
    """
    Asserts that an exception message contains the expected string.

    Args:
        exception: The exception object.
        message: The expected message string.

    Raises:
        AssertionError: If the message is not found in the exception.
    """
    assert message in str(exception), (
        f"Expected message '{message!r}' not found in exception."
    )


def pytest_addoption(parser):
    """Add option to select databases to _c."""
    parser.addoption(
        "--dbs",
        action="store",
        default=None,
        help="List of databases to test, e.g., --dbs postgres,mysql",
    )


def connection_failed_msg(connection: ElixirDB) -> str:
    """
    Generate a connection failure message based on the connection details.

    Args:
        connection (ElixirDB): The database connection object.

    Returns:
        str: A formatted error message indicating the failure reason.
    """

    conn_type = connection.conn_type
    dialect = connection.db.dialect

    message = (
        f"Connection failed for {dialect} using {conn_type}. "
        "Disabling further tests using this connection."
    )
    return message


def get_configs(namespace, string: str) -> list[dict[str, Any]]:
    """Returns a list of all dictionaries starting `string`"""
    return [
        obj
        for name, obj in namespace.items()
        if isinstance(obj, dict) and name.startswith(string)
    ]


def find_by_partial(d: dict, substring: str) -> dict:
    """Return the first value where the key contains the substring."""
    return next((value for key, value in d.items() if substring in key), {})


def deep_merge(base: dict, update: dict) -> dict:
    """
    Recursively merges update into base. Only updates keys in base with
    values from update that are not present in base, allowing base to
    retain any existing structure.

    Args:
        base (dict): The base dictionary to update.
        update (dict): The dictionary with updates to merge into base.

    Returns:
        dict: The base dictionary with merged updates.
    """
    for key, value in update.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            deep_merge(base[key], value)  # Recursive call for nested dictionaries
        else:
            base[key] = value  # Set value if key is not present or not a dict
    return base


def update_test_configs(
    test_config: list[dict], base_configs: dict[str, Any]
) -> list[dict]:
    """
    Update test configurations with base database configs.

    This function takes a list of test configurations and a
    dictionary of base configurations. It updates each test
    configuration by merging it with a selected base configuration
    based on the dialect and the connection type.

    Args:
        test_config (list[dict]): A list of dictionaries, where
            each dictionary represents a test configuration.
        base_configs (dict): A dictionary containing database
            configurations. The keys are formed by concatenating
            the connection dialect and type (e.g mysql.args)
    Returns:
        list[dict]: The updated list of test configurations.
    """
    base_configs = deepcopy(base_configs)
    param_cfgs = {k: v for k, v in base_configs.items() if "params" in k}
    url_cfgs = {k: v for k, v in base_configs.items() if "url" in k}

    for c in test_config:
        sel_cfg = {}
        cfg = c["config"] or {}

        # Select a base configuration for "any" dialect
        if "any" in c["dialect"]:
            sel_cfg = choice(
                list(
                    param_cfgs.values()
                    if "url_params" in cfg
                    else list(url_cfgs.values())
                )
            )
        else:
            sel_cfg = (
                find_by_partial(url_cfgs, c["dialect"])
                if "url" in cfg
                else find_by_partial(param_cfgs, c["dialect"])
            )

        # Make a copy of sel_cfg to preserve base structure, then merge cfg
        merged_config = deep_merge(sel_cfg.copy(), cfg)
        c["config"] = merged_config

    return test_config


def map_test_schema(map_keys: list[str], test_schema: str) -> dict:
    """
    Builds a nested dictionary from a map of keys and the
    test_schema value.

    Args:
        map_keys (list[str]): A list of keys to structure the dictionary.
        test_schema (str): The final value to place in the
        nested dictionary.

    Returns:
        dict: A nested dictionary following the structure defined by
            map_keys.
    """
    nested_dict = current_level = {}

    for key in map_keys:
        current_level[key] = {}
        current_level = current_level[key]  # Move down a level

    # Set the final value
    current_level = test_schema
    return nested_dict


def pytest_config_value(config: pytest.Config, key: str) -> str:
    """
    Retrieve a configuration value from pytest.ini.

    Args:
        config (pytest.Config): The pytest config object.
        key (str): The configuration key to retrieve.

    Returns:
        str: The corresponding configuration value.
    """
    return str(config.getini(key))


def pytest_collection_modifyitems(config, items):
    # Define the folder where tests should be marked
    target_folder = Path("tests/specific_folder").resolve()

    for item in items:
        # Check if the test is in the target folder
        if target_folder in Path(item.fspath).resolve().parents:
            # Add the "order(2)" marker
            item.add_marker(pytest.mark.order(2))
