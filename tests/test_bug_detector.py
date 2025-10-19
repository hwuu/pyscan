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
                    content='{"has_bug": true, "severity": "high", "bugs": [{"type": "ZeroDivisionError", "description": "除零错误", "location": "line 2", "start_line": 2, "end_line": 2, "start_col": 0, "end_col": 0, "suggestion": "添加检查"}]}'
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response

        detector = BugDetector(mock_config)
        context = {
            "current_function": sample_function.code,
            "callers": [],
            "is_public_api": False,
            "inferred_callers": []
        }

        result = detector.detect(sample_function, context, bug_id_start=1)

        assert result is not None
        assert "reports" in result
        assert "prompt" in result
        assert "raw_response" in result

        reports = result["reports"]
        assert len(reports) == 1
        report = reports[0]
        assert report.bug_id == "BUG_0001"
        assert report.severity == "high"
        assert report.bug_type == "ZeroDivisionError"

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
            "is_public_api": False,
            "inferred_callers": []
        }

        result = detector.detect(sample_function, context)

        assert result is not None
        assert "reports" in result
        reports = result["reports"]
        assert len(reports) == 0  # 无 bug 时返回空列表

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
            "is_public_api": False,
            "inferred_callers": []
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
            "is_public_api": False,
            "inferred_callers": []
        }

        result = detector.detect(sample_function, context)

        # 应该返回 None（失败）
        assert result is None

    def test_bug_report_dataclass(self):
        """测试 BugReport 数据类。"""
        bug_report = BugReport(
            bug_id="BUG_0001",
            function_name="test_func",
            file_path="/path/to/file.py",
            function_start_line=10,
            function_end_line=20,
            severity="medium",
            bug_type="TypeError",
            description="类型不匹配",
            location="line 5",
            start_line=5,
            end_line=5,
            start_col=0,
            end_col=10,
            suggestion="添加类型检查"
        )

        assert bug_report.bug_id == "BUG_0001"
        assert bug_report.function_name == "test_func"
        assert bug_report.severity == "medium"
        assert bug_report.bug_type == "TypeError"

    def test_bug_report_with_callers(self):
        """测试包含 caller 信息的 BugReport。"""
        callers = [
            {
                'file_path': '/path/to/caller.py',
                'function_name': 'caller_func',
                'code_snippet': 'def caller_func():\n    result = test_func(x, y)'
            }
        ]
        inferred_callers = [
            {
                'hint': '(推断): @decorator装饰器',
                'code': 'def decorator(func):\n    return wrapper'
            }
        ]

        bug_report = BugReport(
            bug_id="BUG_0002",
            function_name="test_func",
            file_path="/path/to/file.py",
            function_start_line=10,
            function_end_line=25,
            severity="high",
            bug_type="ValueError",
            description="参数验证错误",
            location="line 12",
            start_line=12,
            end_line=12,
            start_col=4,
            end_col=20,
            suggestion="添加参数验证",
            callers=callers,
            callees=["helper_func"],
            inferred_callers=inferred_callers
        )

        assert bug_report.bug_id == "BUG_0002"
        assert len(bug_report.callers) == 1
        assert bug_report.callers[0]['file_path'] == '/path/to/caller.py'
        assert bug_report.callers[0]['function_name'] == 'caller_func'
        assert 'result = test_func' in bug_report.callers[0]['code_snippet']
        assert len(bug_report.inferred_callers) == 1
        assert bug_report.inferred_callers[0]['hint'] == '(推断): @decorator装饰器'
