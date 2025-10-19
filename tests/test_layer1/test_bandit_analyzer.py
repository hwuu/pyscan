"""
测试 Bandit 分析器
"""

import pytest
import tempfile
import os
import json

from pyscan.layer1.bandit_analyzer import BanditAnalyzer


class TestBanditAnalyzer:
    """测试 BanditAnalyzer"""

    @pytest.fixture
    def analyzer(self):
        """创建分析器实例"""
        return BanditAnalyzer()

    @pytest.fixture
    def temp_file(self):
        """创建临时文件"""
        fd, path = tempfile.mkstemp(suffix='.py')
        yield path
        os.close(fd)
        os.unlink(path)

    def test_get_name(self, analyzer):
        """测试获取名称"""
        assert analyzer.get_name() == "bandit"

    def test_is_available(self, analyzer):
        """测试检查可用性"""
        # 至少应该返回 bool
        available = analyzer.is_available()
        assert isinstance(available, bool)

        # 第二次调用应该使用缓存
        available2 = analyzer.is_available()
        assert available == available2

    def test_parse_output_valid_json(self, analyzer):
        """测试解析有效的 JSON 输出"""
        output = json.dumps({
            "results": [
                {
                    "code": "exec(user_input)",
                    "col_offset": 0,
                    "filename": "test.py",
                    "issue_severity": "HIGH",
                    "issue_text": "Use of exec detected.",
                    "line_number": 5,
                    "test_id": "B102"
                },
                {
                    "code": "assert True",
                    "col_offset": 4,
                    "filename": "test.py",
                    "issue_severity": "LOW",
                    "issue_text": "Use of assert detected.",
                    "line_number": 10,
                    "test_id": "B101"
                }
            ]
        })

        issues = analyzer._parse_output(output, "test.py")

        assert len(issues) == 2

        # 第一个问题
        assert issues[0].tool == 'bandit'
        assert issues[0].type == 'security'
        assert issues[0].severity == 'high'
        assert issues[0].line == 5
        assert issues[0].column == 0
        assert "exec" in issues[0].message
        assert issues[0].code == "B102"

        # 第二个问题
        assert issues[1].severity == 'low'
        assert issues[1].line == 10
        assert issues[1].column == 4

    def test_parse_output_empty(self, analyzer):
        """测试解析空输出"""
        issues = analyzer._parse_output("", "test.py")
        assert len(issues) == 0

    def test_parse_output_no_results(self, analyzer):
        """测试解析无结果的 JSON"""
        output = json.dumps({"results": []})
        issues = analyzer._parse_output(output, "test.py")
        assert len(issues) == 0

    def test_parse_output_invalid_json(self, analyzer):
        """测试解析无效的 JSON"""
        output = "invalid json{"
        issues = analyzer._parse_output(output, "test.py")
        assert len(issues) == 0

    def test_severity_mapping(self, analyzer):
        """测试严重度映射"""
        output = json.dumps({
            "results": [
                {
                    "filename": "test.py",
                    "issue_severity": "HIGH",
                    "issue_text": "High severity issue",
                    "line_number": 1,
                    "test_id": "B001"
                },
                {
                    "filename": "test.py",
                    "issue_severity": "MEDIUM",
                    "issue_text": "Medium severity issue",
                    "line_number": 2,
                    "test_id": "B002"
                },
                {
                    "filename": "test.py",
                    "issue_severity": "LOW",
                    "issue_text": "Low severity issue",
                    "line_number": 3,
                    "test_id": "B003"
                }
            ]
        })

        issues = analyzer._parse_output(output, "test.py")

        assert len(issues) == 3
        assert issues[0].severity == 'high'
        assert issues[1].severity == 'medium'
        assert issues[2].severity == 'low'

    def test_analyze_file_with_security_issue(self, analyzer, temp_file):
        """测试分析有安全问题的文件"""
        # 写入有安全问题的代码
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write("""
import os
def run_command(cmd):
    os.system(cmd)  # 安全问题：命令注入
""")

        if not analyzer.is_available():
            pytest.skip("Bandit not available")

        issues = analyzer.analyze_file(temp_file)

        # 应该发现至少一个安全问题
        assert len(issues) > 0
        assert all(issue.tool == 'bandit' for issue in issues)
        assert all(issue.type == 'security' for issue in issues)

    def test_analyze_file_caching(self, analyzer, temp_file):
        """测试文件分析缓存"""
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write("def test(): pass")

        if not analyzer.is_available():
            pytest.skip("Bandit not available")

        # 第一次分析
        issues1 = analyzer.analyze_file(temp_file)

        # 第二次应该使用缓存
        issues2 = analyzer.analyze_file(temp_file)

        assert issues1 == issues2

    def test_analyze_function(self, analyzer, temp_file):
        """测试分析特定函数"""
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write("""
import os

def func1():
    os.system("ls")  # Line 5

def func2():
    exec("code")  # Line 8
""")

        if not analyzer.is_available():
            pytest.skip("Bandit not available")

        # 分析 func1（第 4-5 行）
        issues = analyzer.analyze_function(temp_file, "func1", 4, 5)

        # 应该只包含 func1 的问题
        assert all(4 <= issue.line <= 5 for issue in issues)

    def test_analyze_file_not_available(self, analyzer, temp_file, monkeypatch):
        """测试工具不可用时的行为"""
        # Mock is_available 返回 False
        monkeypatch.setattr(analyzer, 'is_available', lambda: False)

        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write("def test(): pass")

        issues = analyzer.analyze_file(temp_file)
        assert len(issues) == 0
