"""Various formatting functions"""

from __future__ import annotations

import re


def capitalize(string: str) -> str:
    "Capitalizes the first character within a group"
    return re.sub(
        r"(^|[/!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), string
    )


def lowercase_nested_data(data: str | dict | list) -> str | dict | list:
    """
    Lowercases all keys in nested dictionaries and lists.

    :param data: data to be lowercased
    :type data: str, dict, list
    :return: data
    :rtype: str, dict, list
    """
    if isinstance(data, dict):
        return {k.lower(): lowercase_nested_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [lowercase_nested_data(item) for item in data]
    elif isinstance(data, str):
        return data.lower()
    else:
        return data


def flatten_str(message: str) -> str:
    """Removes line breaks and excess spaces from the string"""
    return " ".join(message.split())


def flatten_dict(message: dict) -> dict:
    """Flattens strings in a dictionary"""
    for key, value in message.items():
        if isinstance(value, dict):
            message[key] = flatten_dict(value)
        elif isinstance(value, list):
            message[key] = [
                (
                    flatten_dict(item)
                    if isinstance(item, dict)
                    else flatten_str(item)
                )
                for item in value
            ]
        elif isinstance(value, str):
            message[key] = flatten_str(value)
    return message


def fix_format_args(query: str) -> bool:
    """
    Checks if the SQL query string contains incorrectly formatted
    arguments, such as {arg}, %s, %d, f-strings, or string
    concatenation.

    Args:
        query (str): The SQL query string.

    Returns:
        str: Fixed query string compatible with the text() construct
    """
    # Define patterns for incorrect formatting
    incorrect_patterns = [
        r"\{.*?\}",  # Curly braces for format() or f-strings
        r"%s",
        r"%d",
        r"%\w",  # Old-style % formatting
        r'f".*?"',  # f-strings (Python 3.6+)
        r"f\'.*?\'",  # f-strings with single quotes
    ]

    # Check for each incorrect pattern
    for pattern in incorrect_patterns:
        if re.search(pattern, query):
            return True  # Return True if any incorrect format is found

    # If none of the incorrect formats are found, return False
    return False
