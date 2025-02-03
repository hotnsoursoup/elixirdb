"Configuration Model Tests"

# pyright: reportArgumentType=false, reportOptionalMemberAccess=false, reportCallIssue=false
from __future__ import annotations

import pytest
from pydantic import ValidationError
from elixirdb import EngineModel
from elixirdb.enums import Dialect
from elixirdb.models.engine import Statements
from elixirdb.models.engine import UrlParams


pytestmark = pytest.mark.models


class TestUrlParams:
    """Tests for the UrlParams model."""

    @pytest.mark.parametrize(
        ("host", "port", "username", "expected_port"),
        [
            ("localhost", 5432, "user", "5432"),
            ("127.0.0.1", 3306, "", "3306"),
        ],
    )
    def test_url_params_port_validation(self, host, port, username, expected_port):
        """
        Tests the port validation in UrlParams.

        Ensures that the port is correctly coerced to a string, regardless of
        whether it's initially an integer or a string.
        """
        params_int = UrlParams(
            host=host, username=username, port=port, database="test"
        )
        assert params_int.port == expected_port
        params_str = UrlParams(
            host=host, username=username, port=str(port), database="test"
        )
        assert params_str.port == expected_port

    def test_missing_host(self):
        """
        Test UrlParams raises ValidationError when host is missing.
        """
        with pytest.raises(ValidationError):
            UrlParams(username="user")


class TestEngineModel:
    """Tests for EngineModel."""

    def test_valid_url(self, engine_url):
        """
        Test EngineModel accepts a valid SQLAlchemy URL and assigns it
        correctly.
        """
        model = EngineModel(
            name="TestDB",
            dialect=Dialect.POSTGRESQL,
            url=engine_url,
        )
        assert model.url == engine_url

    def test_valid_url_params(self):
        """
        Test EngineModel accepts valid connection parameters and assigns
        them correctly.
        """
        params = UrlParams(host="localhost", database="testdb")
        model = EngineModel(
            name="TestDB", dialect=Dialect.SQLITE, url_params=params
        )
        assert model.url_params.host == "localhost"
        assert model.url_params.database == "testdb"

    def test_both_url_and_url_params(self, engine_url):
        """
        Test EngineModel raises ValidationError when both URL and
        url_params are provided.
        """
        params = UrlParams(host="localhost", database="testdb")
        with pytest.raises(ValidationError):
            EngineModel(
                name="TestDB",
                dialect=Dialect.SQLITE,
                url=engine_url,
                url_params=params,
            )

    def test_missing_url_and_url_params(self):
        """
        Test EngineModel raises ValidationError when neither URL nor
        url_params are provided.
        """
        with pytest.raises(ValidationError):
            EngineModel(name="TestDB", dialect=Dialect.POSTGRESQL)

    def test_extra_fields(self, engine_url):
        """
        Test EngineModel when extra fields are provided.
        """

        EngineModel(
            name="TestDB",
            dialect=Dialect.POSTGRESQL,
            url=engine_url,
            extra_field="extra",
        )

        # Does not raise ValidationError
        assert True


class TestStatements:
    """Tests for the Statements model."""

    def test_default_prefix(self) -> None:
        """Tests default prefix setting logic."""
        settings = Statements(schema_name="public")
        assert settings.prefix_raw_statements is True
        assert settings.prefix_procedures is True

        # Test if a schema_name is defined, but both prefix_raw_statements
        # and prefix_procedures are False
        with pytest.raises(ValidationError):
            Statements(
                schema_name="public",
                prefix_raw_statements=False,
                prefix_procedures=False,
            )
        # Test if a schema_name is not defined, but prefixing is enabled.
        with pytest.raises(ValidationError):
            Statements(prefix_raw_statements=True)
        with pytest.raises(ValidationError):
            Statements(prefix_procedures=True)
