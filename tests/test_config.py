"""Tests for config module."""
import os
import tempfile
import pytest
from pathlib import Path
from pyscan.config import Config, ConfigError, GitPlatformConfig


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

    def test_git_config_valid(self, tmp_path):
        """测试有效的 Git 配置。"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
llm:
  base_url: "https://api.openai.com/v1"
  api_key: "sk-test-key"
  model: "gpt-4"

git:
  platforms:
    - name: company-gitlab
      detect_pattern: gitlab.company.com
      repo_path_regex: '[:/]([^/:]+/[^/]+?)(?:\\.git)?$'
      commit_url_template: 'https://gitlab.company.com/{repo_path}/-/commit/{hash}'
    - name: github
      detect_pattern: github.com
      repo_path_regex: '[:/]([^/:]+/[^/]+?)(?:\\.git)?$'
      commit_url_template: 'https://github.com/{repo_path}/commit/{hash}'
""")

        config = Config.from_file(str(config_file))

        assert config.git_platforms is not None
        assert len(config.git_platforms) == 2
        assert config.git_platforms[0].name == "company-gitlab"
        assert config.git_platforms[0].detect_pattern == "gitlab.company.com"
        assert config.git_platforms[1].name == "github"

    def test_git_config_no_git_section(self, tmp_path):
        """测试没有 git 配置段时向后兼容。"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
llm:
  base_url: "https://api.openai.com/v1"
  api_key: "sk-test-key"
  model: "gpt-4"
""")

        config = Config.from_file(str(config_file))

        assert config.git_platforms is None

    def test_git_config_invalid_regex(self, tmp_path):
        """测试无效的正则表达式。"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
llm:
  base_url: "https://api.openai.com/v1"
  api_key: "sk-test-key"
  model: "gpt-4"

git:
  platforms:
    - name: company-gitlab
      detect_pattern: gitlab.company.com
      repo_path_regex: '[:/]([^/:]+/[^/]+?(?:\\.git)?$'
      commit_url_template: 'https://gitlab.company.com/{repo_path}/-/commit/{hash}'
""")

        with pytest.raises(ConfigError, match="Invalid regex pattern"):
            Config.from_file(str(config_file))

    def test_git_config_no_capture_group(self, tmp_path):
        """测试正则表达式缺少捕获组。"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
llm:
  base_url: "https://api.openai.com/v1"
  api_key: "sk-test-key"
  model: "gpt-4"

git:
  platforms:
    - name: company-gitlab
      detect_pattern: gitlab.company.com
      repo_path_regex: '[:/][^/:]+/[^/]+?(?:\\.git)?$'
      commit_url_template: 'https://gitlab.company.com/{repo_path}/-/commit/{hash}'
""")

        with pytest.raises(ConfigError, match="must contain at least one capture group"):
            Config.from_file(str(config_file))

    def test_git_config_missing_placeholder(self, tmp_path):
        """测试 commit URL 模板缺少占位符。"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
llm:
  base_url: "https://api.openai.com/v1"
  api_key: "sk-test-key"
  model: "gpt-4"

git:
  platforms:
    - name: company-gitlab
      detect_pattern: gitlab.company.com
      repo_path_regex: '[:/]([^/:]+/[^/]+?)(?:\\.git)?$'
      commit_url_template: 'https://gitlab.company.com/commit/{hash}'
""")

        with pytest.raises(ConfigError, match=r"must contain \{repo_path\}"):
            Config.from_file(str(config_file))

    def test_git_config_missing_required_field(self, tmp_path):
        """测试 git 平台配置缺少必填字段。"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
llm:
  base_url: "https://api.openai.com/v1"
  api_key: "sk-test-key"
  model: "gpt-4"

git:
  platforms:
    - name: company-gitlab
      detect_pattern: gitlab.company.com
      repo_path_regex: '[:/]([^/:]+/[^/]+?)(?:\\.git)?$'
""")

        with pytest.raises(ConfigError, match="Missing required field 'commit_url_template'"):
            Config.from_file(str(config_file))

    def test_git_config_platforms_not_list(self, tmp_path):
        """测试 git.platforms 不是列表。"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
llm:
  base_url: "https://api.openai.com/v1"
  api_key: "sk-test-key"
  model: "gpt-4"

git:
  platforms: "not a list"
""")

        with pytest.raises(ConfigError, match="git.platforms must be a list"):
            Config.from_file(str(config_file))
