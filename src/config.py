"""
Configuration Management for Context Agent

Handles loading and validation of configuration from multiple sources:
1. Environment variables (CONTEXT_AGENT_*)
2. config.json (if exists)
3. config.yaml (if exists)
4. Default values
"""

import os
import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any
from pathlib import Path

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration is invalid"""
    pass


@dataclass
class AgentConfig:
    """
    Context Agent Configuration

    Configuration priority (highest to lowest):
    1. Environment variables (CONTEXT_AGENT_*)
    2. config.json (if exists)
    3. config.yaml (if exists)
    4. Default values
    """

    # Agent Settings
    polling_interval: float = 5.0
    context_threshold: int = 80
    sensor_timeout: float = 5.0
    enable_zerodb: bool = False

    # ZeroDB Settings (optional)
    zerodb_api_key: Optional[str] = None
    zerodb_project_id: Optional[str] = None
    zerodb_enable_logging: bool = True

    # Logging Settings
    log_level: str = "INFO"
    log_format: str = "json"  # or "text"

    def __post_init__(self):
        """Validate configuration after initialization"""
        self.validate()

    @classmethod
    def from_env(cls) -> "AgentConfig":
        """
        Load configuration from environment variables

        Environment variables are prefixed with CONTEXT_AGENT_
        Example: CONTEXT_AGENT_POLLING_INTERVAL=10

        Returns:
            AgentConfig instance
        """
        config_data = {}

        # Map environment variables to config fields
        env_mapping = {
            "CONTEXT_AGENT_POLLING_INTERVAL": ("polling_interval", float),
            "CONTEXT_AGENT_CONTEXT_THRESHOLD": ("context_threshold", int),
            "CONTEXT_AGENT_SENSOR_TIMEOUT": ("sensor_timeout", float),
            "CONTEXT_AGENT_ENABLE_ZERODB": ("enable_zerodb", cls._parse_bool),
            "CONTEXT_AGENT_ZERODB_API_KEY": ("zerodb_api_key", str),
            "CONTEXT_AGENT_ZERODB_PROJECT_ID": ("zerodb_project_id", str),
            "CONTEXT_AGENT_ZERODB_ENABLE_LOGGING": ("zerodb_enable_logging", cls._parse_bool),
            "CONTEXT_AGENT_LOG_LEVEL": ("log_level", str),
            "CONTEXT_AGENT_LOG_FORMAT": ("log_format", str),
        }

        for env_var, (field_name, type_converter) in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    config_data[field_name] = type_converter(value)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid value for {env_var}: {value}. Error: {e}")

        return cls(**config_data)

    @classmethod
    def from_file(cls, path: str, as_dict: bool = False) -> "AgentConfig":
        """
        Load configuration from JSON or YAML file

        Args:
            path: Path to configuration file (.json or .yaml/.yml)
            as_dict: If True, return raw dict instead of AgentConfig instance

        Returns:
            AgentConfig instance or dict if as_dict=True

        Raises:
            ConfigurationError: If file cannot be read or parsed
        """
        file_path = Path(path)

        if not file_path.exists():
            raise ConfigurationError(f"Configuration file not found: {path}")

        try:
            with open(file_path, 'r') as f:
                if file_path.suffix == '.json':
                    config_data = json.load(f)
                elif file_path.suffix in ['.yaml', '.yml']:
                    if not YAML_AVAILABLE:
                        raise ConfigurationError(
                            "PyYAML not installed. Install with: pip install pyyaml"
                        )
                    config_data = yaml.safe_load(f)
                else:
                    raise ConfigurationError(
                        f"Unsupported file format: {file_path.suffix}. "
                        "Use .json or .yaml/.yml"
                    )

            if as_dict:
                return config_data

            return cls(**config_data)

        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in {path}: {e}")
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in {path}: {e}")
        except TypeError as e:
            raise ConfigurationError(f"Invalid configuration fields in {path}: {e}")

    @classmethod
    def load(cls, config_file: Optional[str] = None) -> "AgentConfig":
        """
        Load configuration with priority order

        Priority (highest to lowest):
        1. Environment variables
        2. Specified config file (if provided)
        3. config.json (if exists)
        4. config.yaml (if exists)
        5. Default values

        Args:
            config_file: Optional path to specific config file

        Returns:
            AgentConfig instance with merged configuration
        """
        # Start with defaults
        config_data = asdict(cls())

        # Try to load from standard config files
        config_dir = Path(__file__).parent.parent / "config"

        # Try config.yaml first
        yaml_path = config_dir / "default.yaml"
        if yaml_path.exists():
            try:
                file_data = cls.from_file(str(yaml_path), as_dict=True)
                config_data.update(file_data)
                logger.info(f"Loaded configuration from {yaml_path}")
            except ConfigurationError as e:
                logger.warning(f"Failed to load {yaml_path}: {e}")

        # Try config.json (overrides yaml)
        json_path = config_dir / "default.json"
        if json_path.exists():
            try:
                file_data = cls.from_file(str(json_path), as_dict=True)
                config_data.update(file_data)
                logger.info(f"Loaded configuration from {json_path}")
            except ConfigurationError as e:
                logger.warning(f"Failed to load {json_path}: {e}")

        # Load from specified config file (overrides defaults)
        if config_file:
            try:
                file_data = cls.from_file(config_file, as_dict=True)
                config_data.update(file_data)
                logger.info(f"Loaded configuration from {config_file}")
            except ConfigurationError as e:
                logger.error(f"Failed to load config file {config_file}: {e}")
                raise

        # Load from environment variables (highest priority)
        env_config = cls.from_env()
        for key, value in asdict(env_config).items():
            if value is not None and value != asdict(cls())[key]:
                # Only override if env var was explicitly set (differs from default)
                config_data[key] = value

        # Create final config and validate
        config = cls(**config_data)

        return config

    @staticmethod
    def _merge_configs(base: "AgentConfig", override: "AgentConfig") -> "AgentConfig":
        """
        Merge two configurations, with override taking precedence

        Args:
            base: Base configuration
            override: Override configuration

        Returns:
            Merged configuration
        """
        base_dict = asdict(base)
        override_dict = asdict(override)

        # Only override non-None values
        for key, value in override_dict.items():
            if value is not None:
                base_dict[key] = value

        return AgentConfig(**base_dict)

    @staticmethod
    def _parse_bool(value: str) -> bool:
        """Parse boolean from string"""
        if isinstance(value, bool):
            return value
        return value.lower() in ("true", "1", "yes", "on")

    def validate(self) -> None:
        """
        Validate configuration values

        Raises:
            ConfigurationError: If configuration is invalid
        """
        errors = []

        # Validate polling_interval
        if self.polling_interval <= 0:
            errors.append(f"polling_interval must be > 0, got {self.polling_interval}")

        # Validate context_threshold
        if not 0 <= self.context_threshold <= 100:
            errors.append(
                f"context_threshold must be between 0-100, got {self.context_threshold}"
            )

        # Validate sensor_timeout
        if self.sensor_timeout <= 0:
            errors.append(f"sensor_timeout must be > 0, got {self.sensor_timeout}")

        # Validate log_level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            errors.append(
                f"log_level must be one of {valid_log_levels}, got {self.log_level}"
            )

        # Validate log_format
        valid_log_formats = ["json", "text"]
        if self.log_format.lower() not in valid_log_formats:
            errors.append(
                f"log_format must be one of {valid_log_formats}, got {self.log_format}"
            )

        # Warn if ZeroDB is enabled but credentials are missing
        if self.enable_zerodb:
            warnings = []
            if not self.zerodb_api_key:
                warnings.append("ZERODB_API_KEY is not set")
            if not self.zerodb_project_id:
                warnings.append("ZERODB_PROJECT_ID is not set")

            if warnings:
                logger.warning(
                    f"ZeroDB is enabled but configuration is incomplete: {', '.join(warnings)}"
                )

        if errors:
            raise ConfigurationError(
                f"Configuration validation failed: {'; '.join(errors)}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return asdict(self)

    def to_json(self) -> str:
        """Convert configuration to JSON string"""
        return json.dumps(self.to_dict(), indent=2)

    def __repr__(self) -> str:
        """String representation (hides sensitive data)"""
        safe_dict = self.to_dict()

        # Mask sensitive values
        if safe_dict.get("zerodb_api_key"):
            safe_dict["zerodb_api_key"] = "***REDACTED***"

        return f"AgentConfig({safe_dict})"
