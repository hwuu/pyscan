"""Tests for bug detector module."""
import pytest
from unittest.mock import Mock, patch
from pyscan.bug_detector import BugDetector, BugReport
from pyscan.ast_parser import FunctionInfo
from pyscan.config import Config


class TestBugDetector:
    """Test BugDetector class."""

    @pytest.fixture
    def mock_config(self, tmp_path):
        """Create mock configuration."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
llm:
  base_url: "https://api.openai.com/v1"
  api_key: "sk-test-key"
  model: "gpt-4"
  temperature: 0.2

detector:
  max_retries: 3
  concurrency: 1
""")
        return Config.from_file(str(config_file))

    @pytest.fixture
    def sample_function(self):
        """Create sample function info."""
        return FunctionInfo(
            name="test_func",
            args=["x", "y"],
            lineno=1,
            end_lineno=3,
            col_offset=0,
            end_col_offset=0,
            code="def test_func(x, y):\n    return x / y",
            decorators=[],
            is_async=False,
            calls=set(),
            docstring=""
        )

    def test_detector_initialization(self, mock_config):
        """测试检测器初始化。"""
        detector = BugDetector(mock_config)

        assert detector.config == mock_config
        assert detector.client is not None

    @patch('pyscan.bug_detector.OpenAI')
    def test_detect_bugs_with_mock(
        self, mock_openai, mock_config, sample_function
    ):
        """测试使用 mock 的 bug 检测。"""
        # Mock OpenAI response
        mock_client = Mock()
        mock_openai.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content='{"has_bug": true, "severity": "high", "bugs": [{"type": "ZeroDivisionError", "description": "Division by zero", "location": "line 2", "suggestion": "Add check"}]}'
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response

        detector = BugDetector(mock_config)
        context = {
            "current_function": sample_function.code,
            "callers": [],
            "callees": []
        }

        result = detector.detect(sample_function, context)

        assert result is not None
        assert result.has_bug is True
        assert result.severity == "high"
        assert len(result.bugs) > 0

    @patch('pyscan.bug_detector.OpenAI')
    def test_detect_no_bugs(self, mock_openai, mock_config, sample_function):
        """测试没有 bug 的情况。"""
        mock_client = Mock()
        mock_openai.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content='{"has_bug": false, "severity": "low", "bugs": []}'
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response

        detector = BugDetector(mock_config)
        context = {
            "current_function": sample_function.code,
            "callers": [],
            "callees": []
        }

        result = detector.detect(sample_function, context)

        assert result.has_bug is False
        assert len(result.bugs) == 0

    @patch('pyscan.bug_detector.OpenAI')
    def test_retry_on_failure(self, mock_openai, mock_config, sample_function):
        """测试失败重试机制。"""
        mock_client = Mock()
        mock_openai.return_value = mock_client

        # 第一次失败，第二次成功
        mock_client.chat.completions.create.side_effect = [
            Exception("API Error"),
            Mock(
                choices=[
                    Mock(
                        message=Mock(
                            content='{"has_bug": false, "severity": "low", "bugs": []}'
                        )
                    )
                ]
            )
        ]

        detector = BugDetector(mock_config)
        context = {
            "current_function": sample_function.code,
            "callers": [],
            "callees": []
        }

        result = detector.detect(sample_function, context)

        # 应该成功（经过重试）
        assert result is not None
        assert mock_client.chat.completions.create.call_count == 2

    @patch('pyscan.bug_detector.OpenAI')
    def test_max_retries_exceeded(
        self, mock_openai, mock_config, sample_function
    ):
        """测试超过最大重试次数。"""
        mock_client = Mock()
        mock_openai.return_value = mock_client

        # 所有尝试都失败
        mock_client.chat.completions.create.side_effect = Exception(
            "API Error"
        )

        detector = BugDetector(mock_config)
        context = {
            "current_function": sample_function.code,
            "callers": [],
            "callees": []
        }

        result = detector.detect(sample_function, context)

        # 应该返回 None（失败）
        assert result is None

    def test_bug_report_dataclass(self):
        """测试 BugReport 数据类。"""
        bug_report = BugReport(
            function_name="test_func",
            file_path="/path/to/file.py",
            has_bug=True,
            severity="medium",
            bugs=[
                {
                    "type": "TypeError",
                    "description": "Type mismatch",
                    "location": "line 5",
                    "suggestion": "Add type check"
                }
            ]
        )

        assert bug_report.function_name == "test_func"
        assert bug_report.has_bug is True
        assert len(bug_report.bugs) == 1
