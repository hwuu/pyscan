"""Pipeline 单元测试"""

import pytest
from unittest.mock import Mock, MagicMock
from pyscan.pipeline import DetectionPipeline, DetectionResult
from pyscan.config import Config
from pyscan.bug_detector import BugReport
from pyscan.layer1.base import StaticFacts, StaticIssue
from pyscan.ast_parser import FunctionInfo


class TestDetectionPipeline:
    """DetectionPipeline 测试类"""

    def setup_method(self):
        """测试前准备"""
        # Mock config
        self.config = Mock(spec=Config)
        self.config.layer4 = {
            'enable_cross_validation': True,
            'confidence_threshold': 0.7,
            'position_tolerance': 2,
            'enable_deduplication': True
        }

        # Mock layer1 analyzer
        self.layer1_analyzer = Mock()
        self.layer1_analyzer.is_enabled.return_value = True

        # Mock bug detector
        self.bug_detector = Mock()

    def test_pipeline_initialization(self):
        """测试 Pipeline 初始化"""
        pipeline = DetectionPipeline(self.config, self.layer1_analyzer, self.bug_detector)

        assert pipeline.config == self.config
        assert pipeline.layer1_analyzer == self.layer1_analyzer
        assert pipeline.bug_detector == self.bug_detector
        assert pipeline.cross_validator is not None  # Layer 4 enabled

    def test_pipeline_initialization_layer4_disabled(self):
        """测试 Layer 4 禁用时的初始化"""
        self.config.layer4 = {'enable_cross_validation': False}
        pipeline = DetectionPipeline(self.config, self.layer1_analyzer, self.bug_detector)

        assert pipeline.cross_validator is None

    def test_detect_bugs_success(self):
        """测试完整检测流程成功"""
        pipeline = DetectionPipeline(self.config, self.layer1_analyzer, self.bug_detector)

        # Mock function info
        func = Mock(spec=FunctionInfo)
        func.name = "test_func"
        func.lineno = 10
        func.end_lineno = 20

        # Mock Layer 1 result
        static_facts = StaticFacts(
            file_path="test.py",
            function_name="test_func",
            function_start_line=10
        )
        self.layer1_analyzer.analyze_function.return_value = static_facts

        # Mock Layer 3 result (LLM)
        llm_bug = BugReport(
            bug_id="BUG_0001",
            function_name="test_func",
            file_path="test.py",
            function_start_line=10,
            function_end_line=20,
            bug_type="LogicError",
            description="Logic error",
            start_line=5,
            end_line=5
        )
        self.bug_detector.detect.return_value = {
            "success": True,
            "reports": [llm_bug],
            "prompt": "test prompt",
            "raw_response": "test response"
        }

        result = pipeline.detect_bugs(
            function=func,
            context={},
            file_path="test.py",
            absolute_file_path="/abs/test.py",
            function_start_line=10,
            callers=[],
            callees=[],
            inferred_callers=[],
            bug_id_start=1
        )

        # Assertions
        assert result is not None
        assert isinstance(result, DetectionResult)
        assert len(result.reports) >= 1
        assert result.prompt == "test prompt"
        assert result.raw_response == "test response"
        assert result.layer1_facts == static_facts

    def test_detect_bugs_llm_failure(self):
        """测试 LLM 检测失败"""
        pipeline = DetectionPipeline(self.config, self.layer1_analyzer, self.bug_detector)

        func = Mock(spec=FunctionInfo)
        func.name = "test_func"
        func.lineno = 10
        func.end_lineno = 20

        # LLM 返回失败标记
        self.bug_detector.detect.return_value = {
            "success": False,
            "error": "API Error",
            "reports": [],
            "prompt": "test prompt",
            "raw_response": ""
        }

        result = pipeline.detect_bugs(
            function=func,
            context={},
            file_path="test.py",
            absolute_file_path="/abs/test.py",
            function_start_line=10,
            callers=[],
            callees=[],
            inferred_callers=[],
            bug_id_start=1
        )

        assert result is not None
        assert isinstance(result, DetectionResult)
        assert result.success is False
        assert result.error == "API Error"

    def test_merge_and_deduplicate_no_duplicates(self):
        """测试合并无重复的 bugs"""
        pipeline = DetectionPipeline(self.config, self.layer1_analyzer, self.bug_detector)

        llm_bug = BugReport(
            bug_id="BUG_0001",
            function_name="test_func",
            file_path="test.py",
            function_start_line=10,
            function_end_line=20,
            bug_type="LogicError",
            description="Logic error",
            start_line=5,
            end_line=5
        )

        layer4_bug = BugReport(
            bug_id="TYPE_abcd1234",
            function_name="test_func",
            file_path="test.py",
            function_start_line=10,
            function_end_line=20,
            bug_type="TypeError",
            description="Type error",
            start_line=15,  # 不同位置
            end_line=15,
            confidence=0.95,
            evidence={'mypy_detected': True}
        )

        merged, dedup_count = pipeline._merge_and_deduplicate(
            [llm_bug],
            [layer4_bug],
            bug_id_start=1
        )

        # 应该有 2 个 bugs（没有重复）
        assert len(merged) == 2
        assert dedup_count == 0

        # 检查来源标记
        assert merged[0].evidence['llm_detected'] is True
        assert merged[0].evidence['mypy_detected'] is False
        assert merged[0].evidence['detection_source'] == 'llm'

    def test_merge_and_deduplicate_with_duplicates(self):
        """测试合并有重复的 bugs"""
        pipeline = DetectionPipeline(self.config, self.layer1_analyzer, self.bug_detector)

        # LLM 检测到的 type bug（位置在第 10 行）
        llm_bug = BugReport(
            bug_id="BUG_0001",
            function_name="test_func",
            file_path="test.py",
            function_start_line=10,
            function_end_line=20,
            bug_type="TypeError",
            description="LLM detected type error",
            start_line=10,
            end_line=10
        )

        # Layer 4 检测到的 type bug（位置在第 11 行，±2 容忍度内）
        layer4_bug = BugReport(
            bug_id="TYPE_abcd1234",
            function_name="test_func",
            file_path="test.py",
            function_start_line=10,
            function_end_line=20,
            bug_type="TypeError",
            description="mypy type error",
            start_line=11,  # 相差 1 行
            end_line=11,
            confidence=0.95,
            evidence={'mypy_detected': True, 'llm_confirmed': True}
        )

        merged, dedup_count = pipeline._merge_and_deduplicate(
            [llm_bug],
            [layer4_bug],
            bug_id_start=1
        )

        # 应该只有 1 个 bug（去重后）
        assert len(merged) == 1
        assert dedup_count == 1

        # 应该使用 Layer 4 的 bug（优先 Layer 4）
        bug = merged[0]
        assert bug.description == "mypy type error"
        assert bug.confidence == 0.95

        # 检查来源标记
        assert bug.evidence['llm_detected'] is True
        assert bug.evidence['mypy_detected'] is True
        assert bug.evidence['detection_source'] == 'both'
        assert 'llm_description' in bug.evidence
        assert bug.evidence['llm_description'] == "LLM detected type error"

    def test_is_duplicate_same_type(self):
        """测试重复检测 - 类型完全相同"""
        pipeline = DetectionPipeline(self.config, self.layer1_analyzer, self.bug_detector)

        bug1 = BugReport(
            bug_id="BUG_0001",
            function_name="test_func",
            file_path="test.py",
            function_start_line=10,
            function_end_line=20,
            bug_type="TypeError",
            start_line=10,
            end_line=10
        )

        bug2 = BugReport(
            bug_id="BUG_0002",
            function_name="test_func",
            file_path="test.py",
            function_start_line=10,
            function_end_line=20,
            bug_type="TypeError",
            start_line=11,  # 相差 1 行
            end_line=11
        )

        assert pipeline._is_duplicate(bug1, bug2) is True

    def test_is_duplicate_both_type_related(self):
        """测试重复检测 - 都是类型相关（宽松匹配）"""
        pipeline = DetectionPipeline(self.config, self.layer1_analyzer, self.bug_detector)

        bug1 = BugReport(
            bug_id="BUG_0001",
            function_name="test_func",
            file_path="test.py",
            function_start_line=10,
            function_end_line=20,
            bug_type="TypeError",
            start_line=10,
            end_line=10
        )

        bug2 = BugReport(
            bug_id="BUG_0002",
            function_name="test_func",
            file_path="test.py",
            function_start_line=10,
            function_end_line=20,
            bug_type="TypeMismatch",  # 不同但都包含 'type'
            start_line=11,
            end_line=11
        )

        assert pipeline._is_duplicate(bug1, bug2) is True

    def test_is_duplicate_position_too_far(self):
        """测试重复检测 - 位置太远"""
        pipeline = DetectionPipeline(self.config, self.layer1_analyzer, self.bug_detector)

        bug1 = BugReport(
            bug_id="BUG_0001",
            function_name="test_func",
            file_path="test.py",
            function_start_line=10,
            function_end_line=20,
            bug_type="TypeError",
            start_line=10,
            end_line=10
        )

        bug2 = BugReport(
            bug_id="BUG_0002",
            function_name="test_func",
            file_path="test.py",
            function_start_line=10,
            function_end_line=20,
            bug_type="TypeError",
            start_line=15,  # 相差 5 行，超过容忍度
            end_line=15
        )

        assert pipeline._is_duplicate(bug1, bug2) is False

    def test_is_duplicate_different_type(self):
        """测试重复检测 - 类型完全不同"""
        pipeline = DetectionPipeline(self.config, self.layer1_analyzer, self.bug_detector)

        bug1 = BugReport(
            bug_id="BUG_0001",
            function_name="test_func",
            file_path="test.py",
            function_start_line=10,
            function_end_line=20,
            bug_type="LogicError",
            start_line=10,
            end_line=10
        )

        bug2 = BugReport(
            bug_id="BUG_0002",
            function_name="test_func",
            file_path="test.py",
            function_start_line=10,
            function_end_line=20,
            bug_type="SecurityError",
            start_line=11,
            end_line=11
        )

        assert pipeline._is_duplicate(bug1, bug2) is False

    def test_deduplication_disabled(self):
        """测试禁用去重"""
        self.config.layer4 = {'enable_deduplication': False}
        pipeline = DetectionPipeline(self.config, self.layer1_analyzer, self.bug_detector)

        llm_bug = BugReport(
            bug_id="BUG_0001",
            function_name="test_func",
            file_path="test.py",
            function_start_line=10,
            function_end_line=20,
            bug_type="TypeError",
            start_line=10,
            end_line=10
        )

        layer4_bug = BugReport(
            bug_id="TYPE_abcd1234",
            function_name="test_func",
            file_path="test.py",
            function_start_line=10,
            function_end_line=20,
            bug_type="TypeError",
            start_line=11,
            end_line=11
        )

        merged, dedup_count = pipeline._merge_and_deduplicate(
            [llm_bug],
            [layer4_bug],
            bug_id_start=1
        )

        # 禁用去重，应该保留所有 bugs
        assert len(merged) == 2
        assert dedup_count == 0
