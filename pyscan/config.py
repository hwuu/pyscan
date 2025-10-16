"""Configuration management module."""
import os
from pathlib import Path
from typing import List, Any, Dict
import yaml


class ConfigError(Exception):
    """Configuration related errors."""
    pass


class Config:
    """Configuration class for PyScan."""

    # 默认值
    DEFAULT_MAX_TOKENS = 8000
    DEFAULT_TEMPERATURE = 0.2
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_CONCURRENCY = 1
    DEFAULT_CONTEXT_TOKEN_LIMIT = 6000
    DEFAULT_EXCLUDE_PATTERNS = [
        "test_*.py",
        "*_test.py",
        "config.py",
        "settings.py",
        "*/site-packages/*",
        "*/venv/*",
        "*/.venv/*",
    ]

    def __init__(self, config_dict: Dict[str, Any]):
        """
        Initialize Config from dictionary.

        Args:
            config_dict: Configuration dictionary parsed from YAML.

        Raises:
            ConfigError: If required fields are missing or validation fails.
        """
        self._validate_required_fields(config_dict)
        self._load_config(config_dict)
        self._validate_values()

    def _validate_required_fields(self, config_dict: Dict[str, Any]) -> None:
        """Validate that all required fields are present."""
        if "llm" not in config_dict:
            raise ConfigError("Missing required section: llm")

        llm_config = config_dict["llm"]
        required_llm_fields = ["base_url", "api_key", "model"]

        for field in required_llm_fields:
            if field not in llm_config:
                raise ConfigError(f"Missing required field: llm.{field}")

    def _load_config(self, config_dict: Dict[str, Any]) -> None:
        """Load configuration from dictionary."""
        llm_config = config_dict["llm"]
        scan_config = config_dict.get("scan", {})
        detector_config = config_dict.get("detector", {})

        # LLM 配置
        self.llm_base_url = llm_config["base_url"]
        self.llm_api_key = llm_config["api_key"]
        self.llm_model = llm_config["model"]
        self.llm_max_tokens = llm_config.get("max_tokens", self.DEFAULT_MAX_TOKENS)
        self.llm_temperature = llm_config.get("temperature", self.DEFAULT_TEMPERATURE)

        # 扫描配置
        self.scan_exclude_patterns = scan_config.get(
            "exclude_patterns", self.DEFAULT_EXCLUDE_PATTERNS
        )

        # 检测器配置
        self.detector_max_retries = detector_config.get(
            "max_retries", self.DEFAULT_MAX_RETRIES
        )
        self.detector_concurrency = detector_config.get(
            "concurrency", self.DEFAULT_CONCURRENCY
        )
        self.detector_context_token_limit = detector_config.get(
            "context_token_limit", self.DEFAULT_CONTEXT_TOKEN_LIMIT
        )

    def _validate_values(self) -> None:
        """Validate configuration values."""
        if self.llm_max_tokens <= 0:
            raise ConfigError("llm.max_tokens must be positive")

        if not (0 <= self.llm_temperature <= 2):
            raise ConfigError("llm.temperature must be between 0 and 2")

        if self.detector_max_retries < 0:
            raise ConfigError("detector.max_retries must be non-negative")

        if self.detector_concurrency <= 0:
            raise ConfigError("detector.concurrency must be positive")

        if self.detector_context_token_limit <= 0:
            raise ConfigError("detector.context_token_limit must be positive")

    @classmethod
    def from_file(cls, config_path: str) -> "Config":
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to configuration file.

        Returns:
            Config instance.

        Raises:
            ConfigError: If file not found or parsing fails.
        """
        config_file = Path(config_path)

        if not config_file.exists():
            raise ConfigError(f"Config file not found: {config_path}")

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config_dict = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigError(f"Failed to parse YAML: {e}")
        except Exception as e:
            raise ConfigError(f"Failed to read config file: {e}")

        if not isinstance(config_dict, dict):
            raise ConfigError("Config file must contain a YAML dictionary")

        return cls(config_dict)
