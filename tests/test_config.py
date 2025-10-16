"""Tests for config module."""
import os
import tempfile
import pytest
from pathlib import Path
from pyscan.config import Config, ConfigError


class TestConfig:
    """Test Config class."""

    def test_load_valid_config(self, tmp_path):
        """测试加载有效配置文件。"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
llm:
  base_url: "https://api.openai.com/v1"
  api_key: "sk-test-key"
  model: "gpt-4"
  max_tokens: 8000
  temperature: 0.2

scan:
  exclude_patterns:
    - "test_*.py"
    - "*_test.py"

detector:
  max_retries: 3
  concurrency: 1
  context_token_limit: 6000
""")

        config = Config.from_file(str(config_file))

        assert config.llm_base_url == "https://api.openai.com/v1"
        assert config.llm_api_key == "sk-test-key"
        assert config.llm_model == "gpt-4"
        assert config.llm_max_tokens == 8000
        assert config.llm_temperature == 0.2
        assert "test_*.py" in config.scan_exclude_patterns
        assert config.detector_max_retries == 3
        assert config.detector_concurrency == 1
        assert config.detector_context_token_limit == 6000

    def test_load_config_with_defaults(self, tmp_path):
        """测试加载配置文件时应用默认值。"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
llm:
  base_url: "https://api.openai.com/v1"
  api_key: "sk-test-key"
  model: "gpt-4"
""")

        config = Config.from_file(str(config_file))

        # 必须字段
        assert config.llm_base_url == "https://api.openai.com/v1"
        assert config.llm_api_key == "sk-test-key"
        assert config.llm_model == "gpt-4"

        # 默认值
        assert config.llm_max_tokens == 8000
        assert config.llm_temperature == 0.2
        assert config.detector_max_retries == 3
        assert config.detector_concurrency == 1
        assert config.detector_context_token_limit == 6000
        assert len(config.scan_exclude_patterns) > 0

    def test_missing_required_field(self, tmp_path):
        """测试缺少必需字段时抛出异常。"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
llm:
  base_url: "https://api.openai.com/v1"
  model: "gpt-4"
""")

        with pytest.raises(ConfigError, match="api_key"):
            Config.from_file(str(config_file))

    def test_file_not_found(self):
        """测试配置文件不存在时抛出异常。"""
        with pytest.raises(ConfigError, match="not found"):
            Config.from_file("non_existent_config.yaml")

    def test_invalid_yaml(self, tmp_path):
        """测试无效的 YAML 格式。"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
llm:
  base_url: "https://api.openai.com/v1"
  api_key: "sk-test-key
  model: "gpt-4"
""")

        with pytest.raises(ConfigError, match="Failed to parse"):
            Config.from_file(str(config_file))

    def test_config_validation(self, tmp_path):
        """测试配置验证逻辑。"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
llm:
  base_url: "https://api.openai.com/v1"
  api_key: "sk-test-key"
  model: "gpt-4"
  max_tokens: -100
""")

        with pytest.raises(ConfigError, match="max_tokens"):
            Config.from_file(str(config_file))
