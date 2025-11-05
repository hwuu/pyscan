"""
测试 Layer 2 检测器基类
"""

import ast
import pytest
from pyscan.layer2.detectors.base import BaseDetector
from pyscan.layer2 import Layer2Result, ConfirmedBug, SuspiciousFinding


class DummyDetector(BaseDetector):
    """用于测试的虚拟检测器"""

    def detect(self, function_node: ast.FunctionDef, context: dict) -> Layer2Result:
        """简单实现：总是返回空结果"""
        return Layer2Result(
            confirmed_bugs=[],
            suspicious_findings=[],
            cfg_summary={},
            dataflow_summary={},
            analysis_time=0.0,
            covered_areas=[]
        )


class TestBaseDetector:
    """测试检测器基类"""

    def test_init_with_default_thresholds(self):
        """测试默认阈值初始化"""
        detector = DummyDetector()
        assert detector.confidence_threshold == 0.9
        assert detector.suspicious_threshold == 0.5

    def test_init_with_custom_thresholds(self):
        """测试自定义阈值初始化"""
        detector = DummyDetector(confidence_threshold=0.95, suspicious_threshold=0.6)
        assert detector.confidence_threshold == 0.95
        assert detector.suspicious_threshold == 0.6

    def test_create_confirmed_bug(self):
        """测试创建确认的 bug"""
        detector = DummyDetector()

        bug = detector._create_confirmed_bug(
            bug_type="资源泄漏",
            severity="high",
            confidence=0.95,
            description="文件未关闭",
            location={"start_line": 10, "end_line": 10},
            evidence={"file_handle": "f"},
            suggestion="使用 with 语句"
        )

        assert isinstance(bug, ConfirmedBug)
        assert bug.type == "资源泄漏"
        assert bug.severity == "high"
        assert bug.confidence == 0.95
        assert bug.description == "文件未关闭"
        assert bug.location == {"start_line": 10, "end_line": 10}
        assert bug.evidence == {"file_handle": "f"}
        assert bug.suggestion == "使用 with 语句"

    def test_create_suspicious_finding(self):
        """测试创建可疑发现"""
        detector = DummyDetector()

        finding = detector._create_suspicious_finding(
            finding_type="潜在死锁",
            confidence=0.7,
            description="可能存在死锁风险",
            location={"start_line": 20, "end_line": 25},
            evidence={"lock_order": ["A", "B"]},
            suggestion="统一锁顺序"
        )

        assert isinstance(finding, SuspiciousFinding)
        assert finding.type == "潜在死锁"
        assert finding.confidence == 0.7
        assert finding.description == "可能存在死锁风险"
        assert finding.location == {"start_line": 20, "end_line": 25}
        assert finding.evidence == {"lock_order": ["A", "B"]}
        assert finding.suggestion == "统一锁顺序"

    def test_get_location_without_file_path(self):
        """测试获取位置信息（不包含文件路径）"""
        detector = DummyDetector()

        # 创建一个简单的 AST 节点
        code = "def foo():\n    pass"
        tree = ast.parse(code)
        func_node = tree.body[0]

        location = detector._get_location(func_node)

        assert location['start_line'] == 1
        assert location['end_line'] == 2
        assert 'file_path' not in location

    def test_get_location_with_file_path(self):
        """测试获取位置信息（包含文件路径）"""
        detector = DummyDetector()

        code = "def foo():\n    pass"
        tree = ast.parse(code)
        func_node = tree.body[0]

        location = detector._get_location(func_node, file_path="test.py")

        assert location['start_line'] == 1
        assert location['end_line'] == 2
        assert location['file_path'] == "test.py"

    def test_detect_returns_layer2_result(self):
        """测试 detect 方法返回 Layer2Result"""
        detector = DummyDetector()

        code = "def foo():\n    pass"
        tree = ast.parse(code)
        func_node = tree.body[0]

        result = detector.detect(func_node, context={})

        assert isinstance(result, Layer2Result)
        assert result.confirmed_bugs == []
        assert result.suspicious_findings == []
