"""
测试 Mypy 分析器
"""

import pytest
import tempfile
import os
from pathlib import Path

from pyscan.layer1.mypy_analyzer import MypyAnalyzer


class TestMypyAnalyzer:
    """测试 MypyAnalyzer"""

    @pytest.fixture
    def analyzer(self):
        """创建分析器实例"""
        return MypyAnalyzer()

    @pytest.fixture
    def temp_file(self):
        """创建临时文件"""
        fd, path = tempfile.mkstemp(suffix='.py')
        yield path
        os.close(fd)
        os.unlink(path)

    def test_get_name(self, analyzer):
        """测试获取名称"""
        assert analyzer.get_name() == "mypy"

    def test_is_available(self, analyzer):
        """测试检查可用性"""
        # 至少应该返回 bool
        available = analyzer.is_available()
        assert isinstance(available, bool)

        # 第二次调用应该使用缓存
        available2 = analyzer.is_available()
        assert available == available2

    def test_parse_output_error(self, analyzer):
        """测试解析 error 输出"""
        output = "test.py:10:5: error: Incompatible types [assignment]"
        issues = analyzer._parse_output(output, "test.py")

        assert len(issues) == 1
        issue = issues[0]
        assert issue.tool == 'mypy'
        assert issue.type == 'type-error'
        assert issue.severity == 'high'
        assert issue.line == 10
        assert issue.column == 5
        assert issue.message == "Incompatible types"
        assert issue.code == "assignment"

    def test_parse_output_note(self, analyzer):
        """测试解析 note 输出"""
        output = "test.py:20:1: note: Some note message"
        issues = analyzer._parse_output(output, "test.py")

        assert len(issues) == 1
        issue = issues[0]
        assert issue.severity == 'low'
        assert issue.line == 20
        assert issue.column == 1
        assert "note message" in issue.message

    def test_parse_output_multiple(self, analyzer):
        """测试解析多个问题"""
        output = """test.py:10:5: error: Error 1 [code1]
test.py:20:1: note: Note 1
test.py:30:10: error: Error 2 [code2]"""

        issues = analyzer._parse_output(output, "test.py")

        assert len(issues) == 3
        assert issues[0].line == 10
        assert issues[1].line == 20
        assert issues[2].line == 30

    def test_parse_output_empty(self, analyzer):
        """测试解析空输出"""
        issues = analyzer._parse_output("", "test.py")
        assert len(issues) == 0

    def test_parse_output_invalid(self, analyzer):
        """测试解析无效输出"""
        output = "invalid line\nanother invalid line"
        issues = analyzer._parse_output(output, "test.py")
        assert len(issues) == 0

    def test_analyze_file_with_type_error(self, analyzer, temp_file):
        """测试分析有类型错误的文件"""
        # 写入有类型错误的代码
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write("""def test_func() -> int:
    x: str = 123  # Type error
    return "not an int"  # Type error
""")

        if not analyzer.is_available():
            pytest.skip("Mypy not available")

        issues = analyzer.analyze_file(temp_file)

        # 应该发现至少一个类型错误
        assert len(issues) > 0
        assert all(issue.tool == 'mypy' for issue in issues)

    def test_analyze_file_caching(self, analyzer, temp_file):
        """测试文件分析缓存"""
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write("def test(): pass")

        if not analyzer.is_available():
            pytest.skip("Mypy not available")

        # 第一次分析
        issues1 = analyzer.analyze_file(temp_file)

        # 第二次应该使用缓存
        issues2 = analyzer.analyze_file(temp_file)

        assert issues1 == issues2

    def test_analyze_function(self, analyzer, temp_file):
        """测试分析特定函数"""
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write("""
def func1() -> int:
    x: str = 123  # Line 3
    return x

def func2() -> str:
    y: int = "abc"  # Line 7
    return y
""")

        if not analyzer.is_available():
            pytest.skip("Mypy not available")

        # 分析 func1（第 2-4 行）
        issues = analyzer.analyze_function(temp_file, "func1", 2, 4)

        # 应该只包含 func1 的问题
        assert all(2 <= issue.line <= 4 for issue in issues)

    def test_analyze_file_not_available(self, analyzer, temp_file, monkeypatch):
        """测试工具不可用时的行为"""
        # Mock is_available 返回 False
        monkeypatch.setattr(analyzer, 'is_available', lambda: False)

        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write("def test(): pass")

        issues = analyzer.analyze_file(temp_file)
        assert len(issues) == 0
