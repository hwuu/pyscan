"""
测试 Layer 1 统一分析器
"""

import pytest
import tempfile
import os

from pyscan.layer1.analyzer import Layer1Analyzer
from pyscan.layer1.base import StaticFacts


class TestLayer1Analyzer:
    """测试 Layer1Analyzer"""

    @pytest.fixture
    def temp_file(self):
        """创建临时文件"""
        fd, path = tempfile.mkstemp(suffix='.py')
        yield path
        os.close(fd)
        os.unlink(path)

    def test_init_default(self):
        """测试默认初始化"""
        analyzer = Layer1Analyzer()

        # 至少应该尝试启用工具
        assert isinstance(analyzer.analyzers, list)

    def test_init_disable_all(self):
        """测试禁用所有工具"""
        analyzer = Layer1Analyzer(enable_mypy=False, enable_bandit=False)

        # 应该没有分析器
        assert len(analyzer.analyzers) == 0
        assert not analyzer.is_enabled()

    def test_get_enabled_tools(self):
        """测试获取启用的工具"""
        analyzer = Layer1Analyzer()
        tools = analyzer.get_enabled_tools()

        assert isinstance(tools, list)
        # 工具名称应该是字符串
        assert all(isinstance(tool, str) for tool in tools)

    def test_is_enabled(self):
        """测试是否启用"""
        analyzer1 = Layer1Analyzer(enable_mypy=False, enable_bandit=False)
        assert not analyzer1.is_enabled()

        analyzer2 = Layer1Analyzer()
        # 如果有任何工具可用，应该返回 True
        if len(analyzer2.analyzers) > 0:
            assert analyzer2.is_enabled()

    def test_check_type_annotations(self, temp_file):
        """测试类型注解检查"""
        analyzer = Layer1Analyzer(enable_mypy=False, enable_bandit=False)

        # 有类型注解的函数
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write("""
def func_with_annotations(x: int) -> str:
    return str(x)
""")

        has_annotations = analyzer._check_type_annotations(temp_file, 2, 3)
        assert has_annotations

        # 无类型注解的函数
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write("""
def func_without_annotations(x):
    return str(x)
""")

        has_annotations = analyzer._check_type_annotations(temp_file, 2, 3)
        assert not has_annotations

    def test_analyze_function_no_tools(self, temp_file):
        """测试在没有工具的情况下分析函数"""
        analyzer = Layer1Analyzer(enable_mypy=False, enable_bandit=False)

        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write("""
def test_func(x):
    return x * 2
""")

        facts = analyzer.analyze_function(temp_file, "test_func", 2, 3)

        # 应该返回 StaticFacts
        assert isinstance(facts, StaticFacts)
        assert facts.function_name == "test_func"
        assert facts.function_start_line == 2
        assert len(facts.type_issues) == 0
        assert len(facts.security_issues) == 0

    def test_analyze_function_with_type_annotations(self, temp_file):
        """测试分析有类型注解的函数"""
        analyzer = Layer1Analyzer(enable_mypy=False, enable_bandit=False)

        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write("""
def func(x: int) -> str:
    return str(x)
""")

        facts = analyzer.analyze_function(temp_file, "func", 2, 3)

        assert facts.has_type_annotations is True

    def test_analyze_function_complexity(self, temp_file):
        """测试传入复杂度分数"""
        analyzer = Layer1Analyzer(enable_mypy=False, enable_bandit=False)

        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write("def test(): pass")

        facts = analyzer.analyze_function(
            temp_file, "test", 1, 1, complexity_score=10
        )

        assert facts.complexity_score == 10
