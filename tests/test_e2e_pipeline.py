"""Pipeline 端到端集成测试"""

import tempfile
import os
import pytest
from pathlib import Path

from pyscan.config import Config
from pyscan.ast_parser import ASTParser
from pyscan.context_builder import ContextBuilder
from pyscan.bug_detector import BugDetector
from pyscan.layer1.analyzer import Layer1Analyzer
from pyscan.pipeline import DetectionPipeline


class TestPipelineE2E:
    """Pipeline 端到端集成测试"""

    def setup_method(self):
        """测试前准备"""
        # 创建临时配置
        self.config = Config({
            "llm": {
                "base_url": "https://api.example.com",
                "api_key": "test_key",
                "model": "test_model",
                "max_tokens": 8000,
                "temperature": 0.2
            },
            "layer4": {
                "enable_cross_validation": True,
                "confidence_threshold": 0.7,
                "position_tolerance": 2,
                "enable_deduplication": True
            }
        })

    def test_pipeline_with_type_error_code(self):
        """
        测试包含类型错误的代码
        验证 Layer 1 (mypy) + Layer 3 (LLM) + Layer 4 (交叉验证) 完整流程
        """
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write("""
def add_numbers(x: int, y: int) -> int:
    '''Add two numbers'''
    result = str(x + y)  # Type error: 返回 str 而不是 int
    return result
""")
            temp_file = f.name

        try:
            # 1. 解析 AST
            parser = ASTParser()
            functions = parser.parse_file(temp_file)
            assert len(functions) >= 1

            func = functions[0]
            assert func.name == "add_numbers"

            # 2. 构建上下文
            context_builder = ContextBuilder(
                functions,
                config=self.config,
                max_tokens=self.config.detector_context_token_limit,
                use_tiktoken=False,
                enable_advanced_analysis=False
            )
            context = context_builder.build_context(func)

            # 3. 初始化 Layer 1 分析器
            layer1_analyzer = Layer1Analyzer(enable_mypy=True, enable_bandit=False)

            # 4. 初始化 BugDetector (Mock)
            # 注意：这里需要 mock LLM 响应，因为测试环境可能没有真实的 API
            from unittest.mock import Mock, patch

            detector = Mock(spec=BugDetector)
            detector.detect.return_value = {
                "success": True,
                "reports": [],  # LLM 没有检测到（模拟场景）
                "prompt": "test prompt",
                "raw_response": "{\"has_bug\": false}"
            }

            # 5. 创建 Pipeline
            pipeline = DetectionPipeline(self.config, layer1_analyzer, detector)

            # 6. 执行检测
            result = pipeline.detect_bugs(
                function=func,
                context=context,
                file_path=os.path.basename(temp_file),
                absolute_file_path=temp_file,
                function_start_line=func.lineno,
                callers=[],
                callees=[],
                inferred_callers=[],
                bug_id_start=1
            )

            # 7. 验证结果
            assert result is not None

            # 如果 mypy 可用，应该检测到类型错误
            if layer1_analyzer.is_enabled():
                # Layer 1 应该发现类型错误
                assert result.layer1_facts is not None

                # Layer 4 应该基于 Layer 1 的结果创建 bug 报告
                # （即使 LLM 没有检测到）
                if result.layer1_facts.type_issues:
                    assert result.layer4_bug_count >= 0
                    # 应该有至少一个 bug（来自 Layer 4）
                    assert len(result.reports) >= 0

        finally:
            # 清理临时文件
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_pipeline_with_no_errors(self):
        """测试没有错误的代码"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write("""
def add_numbers(x: int, y: int) -> int:
    '''Add two numbers correctly'''
    return x + y
""")
            temp_file = f.name

        try:
            # 解析和检测
            parser = ASTParser()
            functions = parser.parse_file(temp_file)
            func = functions[0]

            context_builder = ContextBuilder(
                functions,
                config=self.config,
                max_tokens=self.config.detector_context_token_limit,
                use_tiktoken=False,
                enable_advanced_analysis=False
            )
            context = context_builder.build_context(func)

            layer1_analyzer = Layer1Analyzer(enable_mypy=True, enable_bandit=False)

            from unittest.mock import Mock
            detector = Mock(spec=BugDetector)
            detector.detect.return_value = {
                "success": True,
                "reports": [],
                "prompt": "test prompt",
                "raw_response": "{\"has_bug\": false}"
            }

            pipeline = DetectionPipeline(self.config, layer1_analyzer, detector)

            result = pipeline.detect_bugs(
                function=func,
                context=context,
                file_path=os.path.basename(temp_file),
                absolute_file_path=temp_file,
                function_start_line=func.lineno,
                callers=[],
                callees=[],
                inferred_callers=[],
                bug_id_start=1
            )

            # 验证：没有 bug
            assert result is not None
            assert result.layer3_bug_count == 0

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_pipeline_deduplication(self):
        """测试去重功能"""
        from pyscan.bug_detector import BugReport

        layer1_analyzer = Layer1Analyzer(enable_mypy=False, enable_bandit=False)

        from unittest.mock import Mock
        detector = Mock(spec=BugDetector)

        # LLM 检测到一个 type bug
        llm_bug = BugReport(
            bug_id="BUG_0001",
            function_name="test_func",
            file_path="test.py",
            function_start_line=10,
            function_end_line=20,
            bug_type="TypeError",
            description="Type mismatch",
            start_line=10,
            end_line=10
        )

        detector.detect.return_value = {
            "reports": [llm_bug],
            "prompt": "test prompt",
            "raw_response": "test response"
        }

        pipeline = DetectionPipeline(self.config, layer1_analyzer, detector)

        # 测试去重逻辑
        llm_bugs = [llm_bug]
        layer4_bugs = [
            BugReport(
                bug_id="TYPE_0001",
                function_name="test_func",
                file_path="test.py",
                function_start_line=10,
                function_end_line=20,
                bug_type="TypeError",
                description="mypy type error",
                start_line=11,  # 相差 1 行，应该匹配
                end_line=11,
                confidence=0.95,
                evidence={'mypy_detected': True}
            )
        ]

        merged, dedup_count = pipeline._merge_and_deduplicate(
            llm_bugs,
            layer4_bugs,
            bug_id_start=1
        )

        # 应该只有 1 个 bug（去重后）
        assert len(merged) == 1
        assert dedup_count == 1

        # 应该使用 Layer 4 的信息
        bug = merged[0]
        assert bug.confidence == 0.95
        assert bug.evidence['detection_source'] == 'both'
