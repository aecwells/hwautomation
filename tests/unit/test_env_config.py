"""
Unit tests for environment-based configuration system.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from hwautomation.utils.env_config import Config, ConfigError, load_config


class TestConfig:
    """Test the new Config class."""

    def test_init_without_env_file(self):
        """Test Config initialization without .env file."""
        config = Config()
        assert isinstance(config.to_dict(), dict)
        assert "project" in config.to_dict()
        assert "database" in config.to_dict()

    def test_get_env_defaults(self):
        """Test environment variable defaults."""
        config = Config()
        assert config.get("project.name") == "hwautomation"
        assert config.get("database.table_name") == "servers"
        assert config.get("maas.timeout") == 30

    def test_get_env_with_custom_values(self):
        """Test environment variables with custom values."""
        with patch.dict(
            os.environ,
            {
                "PROJECT_NAME": "custom_project",
                "DATABASE_TABLE_NAME": "custom_table",
                "MAAS_TIMEOUT": "60",
            },
        ):
            config = Config()
            assert config.get("project.name") == "custom_project"
            assert config.get("database.table_name") == "custom_table"
            assert config.get("maas.timeout") == 60

    def test_boolean_conversion(self):
        """Test boolean environment variable conversion."""
        test_cases = [
            ("true", True),
            ("True", True),
            ("1", True),
            ("yes", True),
            ("false", False),
            ("False", False),
            ("0", False),
            ("no", False),
        ]

        for env_value, expected in test_cases:
            with patch.dict(os.environ, {"DEBUG": env_value}):
                config = Config()
                assert config.get("project.debug") == expected

    def test_numeric_conversion(self):
        """Test numeric environment variable conversion."""
        with patch.dict(
            os.environ,
            {
                "DB_PORT": "3306",
                "MAAS_TIMEOUT": "45",
            },
        ):
            config = Config()
            assert config.get("database.port") == 3306
            assert config.get("maas.timeout") == 45

    def test_invalid_numeric_conversion(self):
        """Test handling of invalid numeric values."""
        with patch.dict(os.environ, {"DB_PORT": "invalid"}):
            config = Config()
            # Should fall back to default
            assert config.get("database.port") == 5432

    def test_get_section(self):
        """Test getting entire configuration sections."""
        config = Config()

        database_section = config.get_section("database")
        assert isinstance(database_section, dict)
        assert "path" in database_section
        assert "table_name" in database_section

        maas_section = config.get_section("maas")
        assert isinstance(maas_section, dict)
        assert "timeout" in maas_section

    def test_get_nonexistent_key(self):
        """Test getting nonexistent configuration key."""
        config = Config()
        assert config.get("nonexistent.key") is None
        assert config.get("nonexistent.key", "default") == "default"

    def test_dictionary_access(self):
        """Test dictionary-style access to configuration."""
        config = Config()
        assert config["project.name"] == config.get("project.name")
        assert config["database.path"] == config.get("database.path")


class TestConfigWithEnvFile:
    """Test Config class with .env file support."""

    def test_load_env_file(self, tmp_path):
        """Test loading configuration from .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            """
# Test configuration
PROJECT_NAME=test_project
DEBUG=true
DATABASE_PATH=/tmp/test.db
MAAS_TIMEOUT=120
"""
        )

        # Clear any existing environment variables that might interfere
        env_vars_to_clear = ["PROJECT_NAME", "DEBUG", "DATABASE_PATH", "MAAS_TIMEOUT"]
        with patch.dict(os.environ, {}, clear=False):
            # Remove the environment variables for this test
            for var in env_vars_to_clear:
                os.environ.pop(var, None)

            config = Config(str(env_file))
            assert config.get("project.name") == "test_project"
            assert config.get("project.debug") is True
            assert config.get("database.path") == "/tmp/test.db"
            assert config.get("maas.timeout") == 120

    def test_load_nonexistent_env_file(self):
        """Test handling of nonexistent .env file."""
        # Should not raise an exception
        config = Config("/nonexistent/.env")
        assert isinstance(config.to_dict(), dict)


class TestLoadConfigFunction:
    """Test the load_config compatibility function."""

    def test_load_config_returns_dict(self):
        """Test that load_config returns a dictionary."""
        from hwautomation.utils.env_config import reload_config

        config = reload_config()  # Use reload to avoid global state
        assert isinstance(config, dict)
        assert "project" in config
        assert "database" in config
        assert "maas" in config

    def test_load_config_with_env_file(self, tmp_path):
        """Test load_config with custom .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("PROJECT_NAME=custom_load_test\n")

        # Clear any existing PROJECT_NAME env var to test .env file loading
        with patch.dict(os.environ, {}, clear=False):
            if "PROJECT_NAME" in os.environ:
                del os.environ["PROJECT_NAME"]

            from hwautomation.utils.env_config import reload_config

            config = reload_config(env_file=str(env_file))
            assert config["project"]["name"] == "custom_load_test"

    def test_load_config_finds_env_file(self):
        """Test that load_config works without explicit env file."""
        from hwautomation.utils.env_config import reload_config

        config = reload_config()
        assert isinstance(config, dict)


class TestConfigValidation:
    """Test configuration validation."""

    def test_invalid_log_level_warning(self, caplog):
        """Test warning for invalid log level."""
        with patch.dict(os.environ, {"LOG_LEVEL": "INVALID"}, clear=False):
            config = Config()
            assert "Invalid log level" in caplog.text
            assert config.get("logging.level") == "INFO"

    def test_missing_maas_credentials_warning(self, caplog):
        """Test warning for incomplete MaaS configuration."""
        # Clear environment first to avoid interference
        env_backup = os.environ.copy()
        try:
            # Clear MaaS-related variables
            for key in list(os.environ.keys()):
                if key.startswith("MAAS_"):
                    del os.environ[key]

            # Set only host without credentials
            os.environ["MAAS_HOST"] = "http://test.local"

            config = Config()
            assert (
                "MaaS configuration provided but missing authentication" in caplog.text
            )
        finally:
            # Restore environment
            os.environ.clear()
            os.environ.update(env_backup)


class TestBackwardCompatibility:
    """Test backward compatibility functions."""

    def test_load_config_file_deprecated(self, caplog):
        """Test that load_config_file shows deprecation warning."""
        from hwautomation.utils.env_config import load_config_file

        result = load_config_file("dummy.yaml")
        assert isinstance(result, dict)
        assert "deprecated" in caplog.text

    def test_load_config_from_env_compatibility(self):
        """Test backward compatibility of load_config_from_env."""
        from hwautomation.utils.env_config import load_config_from_env

        result = load_config_from_env()
        assert isinstance(result, dict)
        assert "project" in result


class TestConfigIntegration:
    """Integration tests for configuration system."""

    def test_full_configuration_workflow(self, tmp_path):
        """Test complete configuration loading workflow."""
        # Create test .env file
        env_file = tmp_path / ".env"
        env_file.write_text(
            """
PROJECT_NAME=integration_test
DEBUG=true
DATABASE_PATH=/tmp/integration.db
DATABASE_TABLE_NAME=test_servers
MAAS_HOST=http://test-maas.local:5240/MAAS
MAAS_CONSUMER_KEY=test_key
MAAS_TOKEN_KEY=test_token
MAAS_TOKEN_SECRET=test_secret
MAAS_VERIFY_SSL=false
IPMI_USERNAME=test_admin
IPMI_PASSWORD=test_password
SSH_USERNAME=test_user
LOG_LEVEL=DEBUG
"""
        )

        # Clear environment variables to test .env file loading
        env_vars_to_clear = [
            "PROJECT_NAME",
            "DEBUG",
            "DATABASE_PATH",
            "DATABASE_TABLE_NAME",
            "MAAS_HOST",
            "MAAS_CONSUMER_KEY",
            "MAAS_TOKEN_KEY",
            "MAAS_TOKEN_SECRET",
            "MAAS_VERIFY_SSL",
            "IPMI_USERNAME",
            "IPMI_PASSWORD",
            "SSH_USERNAME",
            "LOG_LEVEL",
        ]

        # Backup existing environment
        env_backup = {key: os.environ.get(key) for key in env_vars_to_clear}

        try:
            # Clear the environment variables
            for key in env_vars_to_clear:
                if key in os.environ:
                    del os.environ[key]

            # Load configuration with explicit env file
            config = Config(str(env_file))

            # Verify all sections are properly loaded
            assert config.get("project.name") == "integration_test"
            assert config.get("project.debug") is True
            assert config.get("database.path") == "/tmp/integration.db"
            assert config.get("database.table_name") == "test_servers"
            assert config.get("maas.host") == "http://test-maas.local:5240/MAAS"
            assert config.get("maas.consumer_key") == "test_key"
            assert config.get("maas.verify_ssl") is False
            assert config.get("ipmi.username") == "test_admin"
            assert config.get("ssh.username") == "test_user"
            assert config.get("logging.level") == "DEBUG"
        finally:
            # Restore environment variables
            for key, value in env_backup.items():
                if value is not None:
                    os.environ[key] = value
                elif key in os.environ:
                    del os.environ[key]

    def test_environment_variable_precedence(self, tmp_path):
        """Test that environment variables take precedence over .env file."""
        # Create .env file with one value
        env_file = tmp_path / ".env"
        env_file.write_text("PROJECT_NAME=env_file_value\n")

        # Set environment variable with different value
        with patch.dict(os.environ, {"PROJECT_NAME": "env_var_value"}):
            config = Config(str(env_file))
            # Environment variable should take precedence
            assert config.get("project.name") == "env_var_value"


# Test fixtures for integration with the existing test suite
@pytest.fixture
def test_config():
    """Fixture providing test configuration."""
    with patch.dict(
        os.environ,
        {
            "PROJECT_NAME": "test_project",
            "DATABASE_PATH": ":memory:",
            "DATABASE_TABLE_NAME": "test_servers",
            "TESTING": "true",
            "DEVELOPMENT_MOCK_SERVICES": "true",
        },
    ):
        yield Config()


@pytest.fixture
def test_config_dict():
    """Fixture providing test configuration as dictionary."""
    with patch.dict(
        os.environ,
        {
            "PROJECT_NAME": "test_project",
            "DATABASE_PATH": ":memory:",
            "TESTING": "true",
        },
    ):
        yield load_config()
