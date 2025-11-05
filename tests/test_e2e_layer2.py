"""
Layer 2 端到端集成测试
"""

import ast
import tempfile
import os
from pathlib import Path
from pyscan.config import Config
from pyscan.pipeline import DetectionPipeline
from pyscan.layer1.analyzer import Layer1Analyzer
from pyscan.bug_detector import BugDetector
from pyscan.ast_parser import FunctionInfo


class TestLayer2Integration:
    """测试 Layer 2 与 Pipeline 的集成"""

    def test_pipeline_with_layer2_disabled(self):
        """测试 Layer 2 禁用时的情况"""
        # 创建临时配置（禁用 Layer 2）
        config_dict = {
            "llm": {
                "base_url": "https://api.test.com",
                "api_key": "test_key",
                "model": "test_model"
            },
            "layer2": {
                "enable": False
            }
        }
        config = Config(config_dict)

        # 创建 pipeline
        layer1 = Layer1Analyzer(config)
        bug_detector = BugDetector(config)
        pipeline = DetectionPipeline(config, layer1, bug_detector)

        # 验证 Layer 2 检测器列表为空
        assert len(pipeline.layer2_detectors) == 0

    def test_pipeline_with_layer2_enabled(self):
        """测试 Layer 2 启用时的情况"""
        # 创建临时配置（启用 Layer 2）
        config_dict = {
            "llm": {
                "base_url": "https://api.test.com",
                "api_key": "test_key",
                "model": "test_model"
            },
            "layer2": {
                "enable": True,
                "confidence_threshold": 0.9,
                "suspicious_threshold": 0.5,
                "detectors": {
                    "resource_leak": True
                }
            }
        }
        config = Config(config_dict)

        # 创建 pipeline
        layer1 = Layer1Analyzer(config)
        bug_detector = BugDetector(config)
        pipeline = DetectionPipeline(config, layer1, bug_detector)

        # 验证 Layer 2 检测器已初始化
        assert len(pipeline.layer2_detectors) == 1

    def test_layer2_detects_resource_leak(self):
        """测试 Layer 2 能够检测资源泄漏"""
        # 创建测试代码
        code = """def read_file():
    f = open("test.txt", "r")
    content = f.read()
    return content
"""
        tree = ast.parse(code)
        func_node = tree.body[0]

        # 创建 FunctionInfo（不包含 node 字段）
        function = FunctionInfo(
            name="read_file",
            args=[],
            lineno=1,
            end_lineno=4,
            col_offset=0,
            end_col_offset=0,
            code=code
        )

        # 创建临时配置
        config_dict = {
            "llm": {
                "base_url": "https://api.test.com",
                "api_key": "test_key",
                "model": "test_model"
            },
            "layer2": {
                "enable": True,
                "confidence_threshold": 0.9,
                "suspicious_threshold": 0.5,
                "detectors": {
                    "resource_leak": True
                }
            },
            "layer4": {
                "enable_cross_validation": False
            }
        }
        config = Config(config_dict)

        # 创建临时文件
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text(code)

            # 创建 pipeline
            layer1 = Layer1Analyzer(config)
            bug_detector = BugDetector(config)
            pipeline = DetectionPipeline(config, layer1, bug_detector)

            # 执行检测（注意：这个测试会调用 LLM API，我们暂时跳过）
            # 实际测试中，我们需要 mock BugDetector.detect 方法
            # 这里只测试 Layer 2 检测器被正确调用

            # 验证 Layer 2 检测器存在
            assert len(pipeline.layer2_detectors) == 1

            # 直接调用 Layer 2 检测器
            detector = pipeline.layer2_detectors[0]
            result = detector.detect(func_node, context={'file_path': 'test.py'})

            # 验证检测到资源泄漏
            assert len(result.confirmed_bugs) + len(result.suspicious_findings) > 0

    def test_layer2_bug_conversion_to_report(self):
        """测试 Layer 2 bug 能够正确转换为 BugReport"""
        # 创建测试代码
        code = """def read_file():
    f = open("test.txt", "r")
    return f.read()
"""
        tree = ast.parse(code)
        func_node = tree.body[0]

        # 创建 FunctionInfo
        function = FunctionInfo(
            name="read_file",
            args=[],
            lineno=1,
            end_lineno=3,
            col_offset=0,
            end_col_offset=0,
            code=code
        )

        # 创建配置
        config_dict = {
            "llm": {
                "base_url": "https://api.test.com",
                "api_key": "test_key",
                "model": "test_model"
            },
            "layer2": {
                "enable": True,
                "confidence_threshold": 0.9,
                "suspicious_threshold": 0.5
            }
        }
        config = Config(config_dict)

        # 创建 pipeline
        layer1 = Layer1Analyzer(config)
        bug_detector = BugDetector(config)
        pipeline = DetectionPipeline(config, layer1, bug_detector)

        # 调用 Layer 2 检测器
        from pyscan.layer2.detectors.resource_leak import ResourceLeakDetector
        detector = ResourceLeakDetector(confidence_threshold=0.9, suspicious_threshold=0.5)
        layer2_result = detector.detect(func_node, context={'file_path': 'test.py'})

        # 如果有 confirmed_bugs，测试转换
        if layer2_result.confirmed_bugs:
            confirmed_bug = layer2_result.confirmed_bugs[0]
            bug_report = pipeline._convert_layer2_bug_to_report(
                confirmed_bug,
                function,
                "test.py",
                2
            )

            # 验证转换结果
            assert bug_report.function_name == "read_file"
            assert bug_report.file_path == "test.py"
            assert bug_report.bug_type == confirmed_bug.type
            assert bug_report.severity == confirmed_bug.severity
            assert bug_report.confidence == confirmed_bug.confidence

    def test_layer2_bugs_merged_with_llm_bugs(self):
        """测试 Layer 2 bugs 能够与 LLM bugs 正确合并"""
        from pyscan.bug_detector import BugReport

        # 创建配置
        config_dict = {
            "llm": {
                "base_url": "https://api.test.com",
                "api_key": "test_key",
                "model": "test_model"
            },
            "layer4": {
                "enable_deduplication": True,
                "position_tolerance": 2
            }
        }
        config = Config(config_dict)

        # 创建 pipeline
        layer1 = Layer1Analyzer(config)
        bug_detector = BugDetector(config)
        pipeline = DetectionPipeline(config, layer1, bug_detector)

        # 创建测试 bugs
        layer2_bug = BugReport(
            bug_id="",
            function_name="test_func",
            file_path="test.py",
            function_start_line=1,
            function_end_line=10,
            severity="high",
            bug_type="资源管理错误",
            description="资源泄漏",
            start_line=5,
            end_line=5,
            evidence={'layer2_detected': True, 'detection_source': 'layer2'}
        )

        llm_bug = BugReport(
            bug_id="",
            function_name="test_func",
            file_path="test.py",
            function_start_line=1,
            function_end_line=10,
            severity="medium",
            bug_type="业务逻辑错误",
            description="逻辑问题",
            start_line=8,
            end_line=8,
            evidence={'llm_detected': True, 'detection_source': 'llm'}
        )

        # 测试合并
        merged, dedup_count = pipeline._merge_and_deduplicate(
            llm_bugs=[llm_bug],
            layer4_bugs=[],
            layer2_bugs=[layer2_bug],
            bug_id_start=1
        )

        # 验证合并结果
        assert len(merged) == 2  # 两个不同的 bugs
        assert dedup_count == 0  # 没有重复

        # 验证 bug_id 被正确分配
        assert merged[0].bug_id == "BUG_0001"
        assert merged[1].bug_id == "BUG_0002"

    def test_layer2_deduplication_with_llm(self):
        """测试 Layer 2 与 LLM 检测到相同 bug 时的去重"""
        from pyscan.bug_detector import BugReport

        # 创建配置
        config_dict = {
            "llm": {
                "base_url": "https://api.test.com",
                "api_key": "test_key",
                "model": "test_model"
            },
            "layer4": {
                "enable_deduplication": True,
                "position_tolerance": 2
            }
        }
        config = Config(config_dict)

        # 创建 pipeline
        layer1 = Layer1Analyzer(config)
        bug_detector = BugDetector(config)
        pipeline = DetectionPipeline(config, layer1, bug_detector)

        # 创建相同位置、相同类型的 bugs
        layer2_bug = BugReport(
            bug_id="",
            function_name="test_func",
            file_path="test.py",
            function_start_line=1,
            function_end_line=10,
            severity="high",
            bug_type="资源管理错误",
            description="Layer 2 检测到的资源泄漏",
            start_line=5,
            end_line=5,
            evidence={'layer2_detected': True, 'detection_source': 'layer2'}
        )

        llm_bug = BugReport(
            bug_id="",
            function_name="test_func",
            file_path="test.py",
            function_start_line=1,
            function_end_line=10,
            severity="high",
            bug_type="资源管理错误",
            description="LLM 检测到的资源泄漏",
            start_line=5,  # 同一位置
            end_line=5,
            evidence={'llm_detected': True, 'detection_source': 'llm'}
        )

        # 测试合并
        merged, dedup_count = pipeline._merge_and_deduplicate(
            llm_bugs=[llm_bug],
            layer4_bugs=[],
            layer2_bugs=[layer2_bug],
            bug_id_start=1
        )

        # 验证去重结果
        assert len(merged) == 1  # 去重后只剩 1 个
        assert dedup_count == 1  # 有 1 个重复

        # 验证使用了 Layer 2 的信息（优先级高）
        assert merged[0].description == "Layer 2 检测到的资源泄漏"

        # 验证保留了 LLM 的信息
        assert merged[0].evidence['llm_detected'] == True
        assert merged[0].evidence['layer2_detected'] == True
        assert merged[0].evidence['detection_source'] == 'both'
        assert merged[0].evidence['llm_description'] == "LLM 检测到的资源泄漏"
