"""
Module for parsing YAML/JSON configuration files. Support is present only for
one file, but future iterations may parse entire directories and merge them
as well as support for specific loading configurations in pyproject.toml.
"""

import json
from pathlib import Path
from typing import Any
from typing import Literal
import yaml
from pyrootutils import find_root


def scan_files(partial: str, type: str | None = None) -> list[Path]:
    """
    Recursively find files matching the given partial name.

    Args:
        partial (str): The partial string to search for in filenames.

    Returns:
        list[Path]: A list of Path objects that match the criteria.
    """
    base_dir = find_root()
    if type:
        return list(base_dir.rglob(f"*{partial}*{type}"))
    return list(base_dir.rglob(f"*{partial}*"))


def load_config(
    partial: str = "elixir", file_type: Literal["json", "yaml", "yml"] = "yaml"
) -> dict[str, Any] | None:
    """
    Load a configuration file by searching the project for JSON/YAML files
    matching the given partial name.

    Args:
        partial (str): The partial string to search for in filenames.
        file_type (Literal["json", "yaml", "yml"] | None): The file type to load.
            If not specified, all matching files are considered.

    Returns:
        dict[str, Any] | None: A dictionary of configurations if a file is found,
        otherwise None.

    Raises:
        ValueError: If more than one matching configuration file is found or if the
        file type is unsupported.
    """
    files = scan_files(partial, file_type)

    if len(files) > 1:
        raise ValueError(
            "elixir-db only supports one configuration file at the moment. "
            "Please aggregate configurations into one file."
        )
    if files:
        file = files[0]
        if file.suffix in [".yaml", ".yml"]:
            with open(file, "r", encoding="utf-8") as f:
                data = yaml.load(f, Loader=yaml.SafeLoader)
                if isinstance(data, dict):
                    return data
                else:
                    raise ValueError("YAML content not parsed to dictionary.")
        elif file.suffix == ".json":
            with open(file, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            raise ValueError(f"Unsupported file type: {file.suffix}")
    return None
