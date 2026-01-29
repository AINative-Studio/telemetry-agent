"""
Tests for Configuration Management

Tests cover:
- Default configuration values
- Environment variable loading
- JSON file loading
- YAML file loading (if available)
- Configuration validation
- Configuration merging
- Error handling
"""

import os
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch

from src.config import AgentConfig, ConfigurationError


class TestDefaultConfiguration:
    """Test default configuration values"""

    def test_default_values(self):
        """Default configuration should have expected values"""
        config = AgentConfig()

        assert config.polling_interval == 5.0
        assert config.context_threshold == 80
        assert config.sensor_timeout == 5.0
        assert config.enable_zerodb is False
        assert config.zerodb_api_key is None
        assert config.zerodb_project_id is None
        assert config.zerodb_enable_logging is True
        assert config.log_level == "INFO"
        assert config.log_format == "json"

    def test_default_config_is_valid(self):
        """Default configuration should pass validation"""
        config = AgentConfig()
        config.validate()  # Should not raise


class TestEnvironmentVariableLoading:
    """Test loading configuration from environment variables"""

    def test_load_all_env_vars(self):
        """Should load all configuration from environment variables"""
        env_vars = {
            "CONTEXT_AGENT_POLLING_INTERVAL": "10.0",
            "CONTEXT_AGENT_CONTEXT_THRESHOLD": "90",
            "CONTEXT_AGENT_SENSOR_TIMEOUT": "3.0",
            "CONTEXT_AGENT_ENABLE_ZERODB": "true",
            "CONTEXT_AGENT_ZERODB_API_KEY": "test_key",
            "CONTEXT_AGENT_ZERODB_PROJECT_ID": "test_project",
            "CONTEXT_AGENT_ZERODB_ENABLE_LOGGING": "false",
            "CONTEXT_AGENT_LOG_LEVEL": "DEBUG",
            "CONTEXT_AGENT_LOG_FORMAT": "text",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = AgentConfig.from_env()

        assert config.polling_interval == 10.0
        assert config.context_threshold == 90
        assert config.sensor_timeout == 3.0
        assert config.enable_zerodb is True
        assert config.zerodb_api_key == "test_key"
        assert config.zerodb_project_id == "test_project"
        assert config.zerodb_enable_logging is False
        assert config.log_level == "DEBUG"
        assert config.log_format == "text"

    def test_boolean_parsing(self):
        """Should correctly parse boolean values"""
        test_cases = [
            ("true", True),
            ("True", True),
            ("1", True),
            ("yes", True),
            ("on", True),
            ("false", False),
            ("False", False),
            ("0", False),
            ("no", False),
            ("off", False),
        ]

        for value, expected in test_cases:
            env_vars = {"CONTEXT_AGENT_ENABLE_ZERODB": value}
            with patch.dict(os.environ, env_vars, clear=True):
                config = AgentConfig.from_env()
                assert config.enable_zerodb == expected, f"Failed for value: {value}"

    def test_partial_env_vars(self):
        """Should use defaults for missing env vars"""
        env_vars = {
            "CONTEXT_AGENT_POLLING_INTERVAL": "10.0",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = AgentConfig.from_env()

        assert config.polling_interval == 10.0
        assert config.context_threshold == 80  # Default
        assert config.sensor_timeout == 5.0  # Default


class TestFileLoading:
    """Test loading configuration from files"""

    def test_load_from_json(self):
        """Should load configuration from JSON file"""
        config_data = {
            "polling_interval": 10.0,
            "context_threshold": 90,
            "sensor_timeout": 3.0,
            "enable_zerodb": True,
            "log_level": "DEBUG",
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            config = AgentConfig.from_file(temp_path)

            assert config.polling_interval == 10.0
            assert config.context_threshold == 90
            assert config.sensor_timeout == 3.0
            assert config.enable_zerodb is True
            assert config.log_level == "DEBUG"
        finally:
            os.unlink(temp_path)

    def test_load_from_yaml(self):
        """Should load configuration from YAML file (if pyyaml available)"""
        try:
            import yaml
        except ImportError:
            pytest.skip("PyYAML not installed")

        config_yaml = """
polling_interval: 10.0
context_threshold: 90
sensor_timeout: 3.0
enable_zerodb: true
log_level: DEBUG
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_yaml)
            temp_path = f.name

        try:
            config = AgentConfig.from_file(temp_path)

            assert config.polling_interval == 10.0
            assert config.context_threshold == 90
            assert config.sensor_timeout == 3.0
            assert config.enable_zerodb is True
            assert config.log_level == "DEBUG"
        finally:
            os.unlink(temp_path)

    def test_file_not_found(self):
        """Should raise ConfigurationError if file not found"""
        with pytest.raises(ConfigurationError, match="not found"):
            AgentConfig.from_file("/nonexistent/config.json")

    def test_invalid_json(self):
        """Should raise ConfigurationError for invalid JSON"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            temp_path = f.name

        try:
            with pytest.raises(ConfigurationError, match="Invalid JSON"):
                AgentConfig.from_file(temp_path)
        finally:
            os.unlink(temp_path)

    def test_unsupported_format(self):
        """Should raise ConfigurationError for unsupported file format"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("config")
            temp_path = f.name

        try:
            with pytest.raises(ConfigurationError, match="Unsupported file format"):
                AgentConfig.from_file(temp_path)
        finally:
            os.unlink(temp_path)


class TestConfigurationValidation:
    """Test configuration validation"""

    def test_invalid_polling_interval(self):
        """Should reject polling_interval <= 0"""
        with pytest.raises(ConfigurationError, match="polling_interval must be > 0"):
            AgentConfig(polling_interval=0)

        with pytest.raises(ConfigurationError, match="polling_interval must be > 0"):
            AgentConfig(polling_interval=-1)

    def test_invalid_context_threshold(self):
        """Should reject context_threshold outside 0-100 range"""
        with pytest.raises(ConfigurationError, match="context_threshold must be between 0-100"):
            AgentConfig(context_threshold=-1)

        with pytest.raises(ConfigurationError, match="context_threshold must be between 0-100"):
            AgentConfig(context_threshold=101)

    def test_valid_context_threshold_boundaries(self):
        """Should accept context_threshold at boundaries"""
        config1 = AgentConfig(context_threshold=0)
        assert config1.context_threshold == 0

        config2 = AgentConfig(context_threshold=100)
        assert config2.context_threshold == 100

    def test_invalid_sensor_timeout(self):
        """Should reject sensor_timeout <= 0"""
        with pytest.raises(ConfigurationError, match="sensor_timeout must be > 0"):
            AgentConfig(sensor_timeout=0)

        with pytest.raises(ConfigurationError, match="sensor_timeout must be > 0"):
            AgentConfig(sensor_timeout=-1)

    def test_invalid_log_level(self):
        """Should reject invalid log levels"""
        with pytest.raises(ConfigurationError, match="log_level must be one of"):
            AgentConfig(log_level="INVALID")

    def test_valid_log_levels(self):
        """Should accept valid log levels"""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            config = AgentConfig(log_level=level)
            assert config.log_level == level

    def test_invalid_log_format(self):
        """Should reject invalid log formats"""
        with pytest.raises(ConfigurationError, match="log_format must be one of"):
            AgentConfig(log_format="invalid")

    def test_valid_log_formats(self):
        """Should accept valid log formats"""
        for fmt in ["json", "text"]:
            config = AgentConfig(log_format=fmt)
            assert config.log_format == fmt

    def test_zerodb_enabled_without_credentials(self, caplog):
        """Should warn if ZeroDB is enabled but credentials are missing"""
        import logging
        caplog.set_level(logging.WARNING)

        config = AgentConfig(enable_zerodb=True)

        assert "ZeroDB is enabled but configuration is incomplete" in caplog.text
        assert "ZERODB_API_KEY is not set" in caplog.text
        assert "ZERODB_PROJECT_ID is not set" in caplog.text

    def test_zerodb_enabled_with_partial_credentials(self, caplog):
        """Should warn if only some ZeroDB credentials are provided"""
        import logging
        caplog.set_level(logging.WARNING)

        config = AgentConfig(enable_zerodb=True, zerodb_api_key="test_key")

        assert "ZERODB_PROJECT_ID is not set" in caplog.text


class TestConfigurationMerging:
    """Test configuration merging from multiple sources"""

    def test_merge_configs(self):
        """Should merge configurations correctly"""
        base = AgentConfig(polling_interval=5.0, context_threshold=80)
        override = AgentConfig(context_threshold=90, log_level="DEBUG")

        merged = AgentConfig._merge_configs(base, override)

        assert merged.polling_interval == 5.0  # From base
        assert merged.context_threshold == 90  # From override
        assert merged.log_level == "DEBUG"  # From override

    def test_load_priority(self):
        """Should respect configuration priority order"""
        # Create a temporary config file
        config_data = {
            "polling_interval": 10.0,
            "context_threshold": 90,
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            # Set environment variable (should override file)
            env_vars = {
                "CONTEXT_AGENT_CONTEXT_THRESHOLD": "95",
            }

            with patch.dict(os.environ, env_vars):
                config = AgentConfig.load(config_file=temp_path)

                # polling_interval from file
                assert config.polling_interval == 10.0
                # context_threshold from env (higher priority)
                assert config.context_threshold == 95
        finally:
            os.unlink(temp_path)


class TestConfigurationSerialization:
    """Test configuration serialization"""

    def test_to_dict(self):
        """Should convert configuration to dictionary"""
        config = AgentConfig(
            polling_interval=10.0,
            context_threshold=90,
            log_level="DEBUG",
        )

        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict["polling_interval"] == 10.0
        assert config_dict["context_threshold"] == 90
        assert config_dict["log_level"] == "DEBUG"

    def test_to_json(self):
        """Should convert configuration to JSON string"""
        config = AgentConfig(
            polling_interval=10.0,
            context_threshold=90,
        )

        config_json = config.to_json()

        assert isinstance(config_json, str)
        parsed = json.loads(config_json)
        assert parsed["polling_interval"] == 10.0
        assert parsed["context_threshold"] == 90

    def test_repr_masks_secrets(self):
        """Should mask sensitive data in string representation"""
        config = AgentConfig(
            zerodb_api_key="secret_key_12345",
        )

        repr_str = repr(config)

        assert "secret_key_12345" not in repr_str
        assert "REDACTED" in repr_str


class TestConfigurationIntegration:
    """Integration tests for complete configuration loading"""

    def test_default_config_file_loading(self):
        """Should load default config file if it exists"""
        # This test verifies the actual default.json file exists and is valid
        config_file = Path(__file__).parent.parent / "config" / "default.json"

        if config_file.exists():
            config = AgentConfig.from_file(str(config_file))
            config.validate()  # Should not raise

    def test_load_without_any_config(self):
        """Should work with only default values"""
        with patch.dict(os.environ, {}, clear=True):
            config = AgentConfig.load()
            assert config.polling_interval == 5.0
            assert config.context_threshold == 80
