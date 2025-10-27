"""Configuration management module."""
import os
import re
from pathlib import Path
from typing import List, Any, Dict, Optional
from dataclasses import dataclass
import yaml


class ConfigError(Exception):
    """Configuration related errors."""
    pass


@dataclass
class GitPlatformConfig:
    """Configuration for a Git platform."""
    name: str
    detect_pattern: str
    repo_path_regex: str
    commit_url_template: str

    def __post_init__(self):
        """Validate configuration after initialization."""
        # 验证 name
        if not self.name or not self.name.strip():
            raise ConfigError("Git platform 'name' cannot be empty")

        # 验证 detect_pattern
        if not self.detect_pattern or not self.detect_pattern.strip():
            raise ConfigError(f"Git platform '{self.name}': 'detect_pattern' cannot be empty")

        # 验证正则表达式
        if not self.repo_path_regex or not self.repo_path_regex.strip():
            raise ConfigError(f"Git platform '{self.name}': 'repo_path_regex' cannot be empty")

        try:
            compiled = re.compile(self.repo_path_regex)
            if compiled.groups < 1:
                raise ConfigError(
                    f"Git platform '{self.name}': 'repo_path_regex' must contain at least one capture group (...) to extract repo_path"
                )
        except re.error as e:
            raise ConfigError(
                f"Git platform '{self.name}': Invalid regex pattern in 'repo_path_regex': {e}"
            )

        # 验证模板占位符
        if not self.commit_url_template or not self.commit_url_template.strip():
            raise ConfigError(f"Git platform '{self.name}': 'commit_url_template' cannot be empty")

        if '{repo_path}' not in self.commit_url_template:
            raise ConfigError(
                f"Git platform '{self.name}': 'commit_url_template' must contain {{repo_path}} placeholder"
            )

        if '{hash}' not in self.commit_url_template:
            raise ConfigError(
                f"Git platform '{self.name}': 'commit_url_template' must contain {{hash}} placeholder"
            )


class Config:
    """Configuration class for PyScan."""

    # 默认值
    DEFAULT_MAX_TOKENS = 8000
    DEFAULT_TEMPERATURE = 0.2
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_CONCURRENCY = 1
    DEFAULT_CONTEXT_TOKEN_LIMIT = 6000
    DEFAULT_USE_TIKTOKEN = False
    DEFAULT_ENABLE_ADVANCED_ANALYSIS = True
    DEFAULT_PUBLIC_API_DECORATORS = ["route", "get", "post", "put", "delete", "patch", "api_view", "endpoint"]
    DEFAULT_PUBLIC_API_FILE_PATTERNS = ["*/api/*", "*/endpoints/*", "*/handlers/*", "*/controllers/*", "*/views/*"]
    DEFAULT_PUBLIC_API_NAME_PREFIXES = ["api_", "handle_", "endpoint_"]
    DEFAULT_MAX_CALLERS = 3
    DEFAULT_MAX_INFERRED = 3
    DEFAULT_EXCLUDE_PATTERNS = [
        "test_*.py",
        "*_test.py",
        "config.py",
        "settings.py",
        "*/site-packages/*",
        "*/venv/*",
        "*/.venv/*",
    ]
    # Layer 1 默认值
    DEFAULT_LAYER1_ENABLE_MYPY = True
    DEFAULT_LAYER1_ENABLE_BANDIT = True

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
        self.detector_use_tiktoken = detector_config.get(
            "use_tiktoken", self.DEFAULT_USE_TIKTOKEN
        )
        self.detector_enable_advanced_analysis = detector_config.get(
            "enable_advanced_analysis", self.DEFAULT_ENABLE_ADVANCED_ANALYSIS
        )

        # 公共 API 识别配置
        public_api_config = detector_config.get("public_api_indicators", {})
        self.detector_public_api_decorators = public_api_config.get(
            "decorators", self.DEFAULT_PUBLIC_API_DECORATORS
        )
        self.detector_public_api_file_patterns = public_api_config.get(
            "file_patterns", self.DEFAULT_PUBLIC_API_FILE_PATTERNS
        )
        self.detector_public_api_name_prefixes = public_api_config.get(
            "name_prefixes", self.DEFAULT_PUBLIC_API_NAME_PREFIXES
        )

        # 压缩配置
        compression_config = detector_config.get("compression", {})
        self.detector_max_callers = compression_config.get(
            "max_callers", self.DEFAULT_MAX_CALLERS
        )
        self.detector_max_inferred = compression_config.get(
            "max_inferred", self.DEFAULT_MAX_INFERRED
        )

        # Layer 1 静态分析配置
        layer1_config = config_dict.get("layer1", {})
        self.layer1 = {
            "enable_mypy": layer1_config.get("enable_mypy", self.DEFAULT_LAYER1_ENABLE_MYPY),
            "enable_bandit": layer1_config.get("enable_bandit", self.DEFAULT_LAYER1_ENABLE_BANDIT),
        }

        # Layer 4 交叉验证配置
        layer4_config = config_dict.get("layer4", {})
        self.layer4 = {
            "enable_cross_validation": layer4_config.get("enable_cross_validation", True),
            "confidence_threshold": layer4_config.get("confidence_threshold", 0.7),
            "position_tolerance": layer4_config.get("position_tolerance", 2),
            "enable_deduplication": layer4_config.get("enable_deduplication", True),
        }

        # Bug 过滤配置
        filter_config = config_dict.get("filter", {})
        self.filter = {
            "exclude_types": filter_config.get("exclude_types", []) or [],
            "exclude_severities": filter_config.get("exclude_severities", []) or [],
        }

        # Git 平台配置（可选）
        git_config = config_dict.get("git", {})
        self.git_platforms: Optional[List[GitPlatformConfig]] = None
        if "platforms" in git_config:
            platforms_data = git_config["platforms"]
            if not isinstance(platforms_data, list):
                raise ConfigError("git.platforms must be a list")

            self.git_platforms = []
            for i, platform_dict in enumerate(platforms_data):
                if not isinstance(platform_dict, dict):
                    raise ConfigError(f"git.platforms[{i}] must be a dictionary")

                # 验证必填字段
                required_fields = ["name", "detect_pattern", "repo_path_regex", "commit_url_template"]
                for field in required_fields:
                    if field not in platform_dict:
                        raise ConfigError(f"git.platforms[{i}]: Missing required field '{field}'")

                try:
                    platform = GitPlatformConfig(**platform_dict)
                    self.git_platforms.append(platform)
                except ConfigError:
                    # Re-raise ConfigError as-is
                    raise
                except Exception as e:
                    raise ConfigError(f"git.platforms[{i}]: Failed to create platform config: {e}")

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
