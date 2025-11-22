"""Tests for configuration error handling."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest

from src.infrastructure.config.base import ConfigLoader, ConfigurationError


class TestConfigurationError:
    """Test ConfigurationError is raised instead of sys.exit."""

    def test_missing_config_file_raises_configuration_error(self):
        """Test that missing config file raises ConfigurationError instead of sys.exit."""
        with TemporaryDirectory() as tmpdir:
            # Patch the config path to point to non-existent directory
            with patch("src.infrastructure.config.base.Path") as mock_path:
                # Make Path(__file__).parent.parent.parent.parent point to tmpdir
                mock_path.return_value.parent.parent.parent.parent = Path(tmpdir)

                with pytest.raises(ConfigurationError) as exc_info:
                    ConfigLoader.load_json("nonexistent")

                # Verify error message contains helpful instructions
                error_msg = str(exc_info.value)
                assert "nonexistent.json not found" in error_msg
                assert "Setup instructions" in error_msg
                assert "cp -r backend/config.example backend/config" in error_msg

    def test_invalid_json_raises_configuration_error(self):
        """Test that invalid JSON raises ConfigurationError instead of sys.exit."""
        with TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "config"
            config_dir.mkdir()

            # Create invalid JSON file
            invalid_json_file = config_dir / "invalid.json"
            invalid_json_file.write_text("{invalid json content")

            with patch("src.infrastructure.config.base.Path") as mock_path:
                mock_path.return_value.parent.parent.parent.parent = Path(tmpdir)

                with pytest.raises(ConfigurationError) as exc_info:
                    ConfigLoader.load_json("invalid")

                error_msg = str(exc_info.value)
                assert "invalid.json has invalid JSON" in error_msg

    def test_missing_required_fields_raises_configuration_error(self):
        """Test that missing required fields raises ConfigurationError."""
        config_data = {"field1": "value1"}
        required_fields = ["field1", "field2", "field3"]

        with pytest.raises(ConfigurationError) as exc_info:
            ConfigLoader.validate_required_fields(config_data, required_fields, "test")

        error_msg = str(exc_info.value)
        assert "test.json is missing required fields" in error_msg
        assert "field2" in error_msg
        assert "field3" in error_msg
        assert "field1" not in error_msg  # field1 exists, shouldn't be in error

    def test_valid_config_loads_successfully(self):
        """Test that valid config file loads without errors."""
        with TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "config"
            config_dir.mkdir()

            # Create valid JSON file
            valid_json_file = config_dir / "valid.json"
            config_data = {"key1": "value1", "key2": "value2"}
            valid_json_file.write_text(json.dumps(config_data))

            with patch("src.infrastructure.config.base.Path") as mock_path:
                mock_path.return_value.parent.parent.parent.parent = Path(tmpdir)

                result = ConfigLoader.load_json("valid")
                assert result == config_data

    def test_validate_required_fields_succeeds_with_all_fields(self):
        """Test that validation succeeds when all required fields are present."""
        config_data = {"field1": "value1", "field2": "value2", "field3": "value3"}
        required_fields = ["field1", "field2"]

        # Should not raise any exception
        ConfigLoader.validate_required_fields(config_data, required_fields, "test")
