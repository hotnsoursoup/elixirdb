from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch
import pytest
from elixirdb.utils.files import load_config
from elixirdb.utils.files import scan_files


@pytest.fixture
def mock_find_root():
    """Fixture to mock the `find_root` function."""
    with patch(
        "elixirdb.utils.files.find_root", return_value=Path("/mock/root")
    ) as mock:
        yield mock


@pytest.fixture
def mock_rglob():
    """Fixture to mock the `Path.rglob` method."""
    with patch("pathlib.Path.rglob") as mock_rglob:
        yield mock_rglob


def test_scan_files(mock_find_root, mock_rglob):
    """Test the `scan_files` function."""
    mock_rglob.return_value = [
        Path("/mock/root/file1.yaml"),
        Path("/mock/root/file2.yaml"),
    ]

    result = scan_files("file", "yaml")

    assert len(result) == 2  # noqa: PLR2004
    assert all(isinstance(p, Path) for p in result)
    mock_find_root.assert_called_once()
    mock_rglob.assert_called_once_with("*file*yaml")


def test_load_config_yaml(mock_find_root, mock_rglob):
    """Test loading a YAML configuration file."""
    mock_rglob.return_value = [Path("/mock/root/config.yaml")]

    with (
        patch("builtins.open", MagicMock()) as mock_open,
        patch("yaml.load", return_value={"key": "value"}) as mock_yaml_load,
    ):
        result = load_config(partial="config", file_type="yaml")

        assert result == {"key": "value"}
        mock_open.assert_called_once_with(
            Path("/mock/root/config.yaml"), "r", encoding="utf-8"
        )
        mock_yaml_load.assert_called_once()


def test_load_config_json(mock_find_root, mock_rglob):
    """Test loading a JSON configuration file."""
    mock_rglob.return_value = [Path("/mock/root/config.json")]

    with (
        patch("builtins.open", MagicMock()) as mock_open,
        patch("json.load", return_value={"key": "value"}) as mock_json_load,
    ):
        result = load_config(partial="config", file_type="json")

        assert result == {"key": "value"}
        mock_open.assert_called_once_with(
            Path("/mock/root/config.json"), "r", encoding="utf-8"
        )
        mock_json_load.assert_called_once()


def test_load_config_unsupported_file_type(mock_find_root, mock_rglob):
    """Test loading an unsupported file type."""
    mock_rglob.return_value = [Path("/mock/root/config.txt")]

    with pytest.raises(ValueError, match=r"Unsupported file type: .txt"):
        load_config(partial="config", file_type=".txt")  # pyright: ignore[reportArgumentType]


def test_load_config_multiple_files(mock_find_root, mock_rglob):
    """Test raising an error when multiple files are found."""
    mock_rglob.return_value = [
        Path("/mock/root/config1.yaml"),
        Path("/mock/root/config2.yaml"),
    ]

    with pytest.raises(
        ValueError,
        match="elixir-db only supports one configuration file at the moment",
    ):
        load_config(partial="config", file_type="yaml")


def test_load_config_no_files_found(mock_find_root, mock_rglob):
    """Test when no files are found."""
    mock_rglob.return_value = []

    result = load_config(partial="config", file_type="yaml")

    assert result is None
