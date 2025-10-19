"""
Layer 1 端到端测试

测试 Layer 1 在实际代码上的表现
"""

import pytest
import tempfile
import os
from pathlib import Path

from pyscan.layer1 import Layer1Analyzer


class TestLayer1E2E:
    """Layer 1 端到端测试"""

    @pytest.fixture
    def test_code_dir(self):
        """创建测试代码目录"""
        tmpdir = tempfile.mkdtemp()
        yield tmpdir
        # 清理
        import shutil
        shutil.rmtree(tmpdir)

    def test_analyze_code_with_type_errors(self, test_code_dir):
        """测试分析有类型错误的代码"""
        # 创建测试文件
        test_file = os.path.join(test_code_dir, "test_types.py")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("""\
def add_numbers(a: int, b: int) -> int:
    # 类型错误：返回字符串而不是整数
    return str(a + b)

def divide(x: int, y: int) -> float:
    # 正确的实现
    return x / y
""")

        # 创建分析器
        analyzer = Layer1Analyzer(enable_mypy=True, enable_bandit=False)

        if not analyzer.is_enabled():
            pytest.skip("No analyzers available")

        # 分析第一个函数（有错误）
        facts1 = analyzer.analyze_function(test_file, "add_numbers", 1, 3)

        print(f"\n=== add_numbers 分析结果 ===")
        print(f"函数: {facts1.function_name}")
        print(f"类型问题数: {len(facts1.type_issues)}")
        print(f"安全问题数: {len(facts1.security_issues)}")
        print(f"有类型注解: {facts1.has_type_annotations}")

        for issue in facts1.type_issues:
            print(f"  - {issue}")

        # 验证
        assert facts1.has_type_annotations is True
        if 'mypy' in analyzer.get_enabled_tools():
            assert len(facts1.type_issues) > 0, "应该发现类型错误"

        # 分析第二个函数（无错误）
        facts2 = analyzer.analyze_function(test_file, "divide", 5, 7)

        print(f"\n=== divide 分析结果 ===")
        print(f"函数: {facts2.function_name}")
        print(f"类型问题数: {len(facts2.type_issues)}")
        print(f"安全问题数: {len(facts2.security_issues)}")
        print(f"有类型注解: {facts2.has_type_annotations}")

        assert facts2.has_type_annotations is True

    def test_analyze_code_with_security_issues(self, test_code_dir):
        """测试分析有安全问题的代码"""
        # 创建测试文件
        test_file = os.path.join(test_code_dir, "test_security.py")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("""import os
import subprocess

def run_command(cmd):
    # 安全问题：命令注入风险
    os.system(cmd)
    return "done"

def safe_function(x, y):
    # 安全的代码
    return x + y
""")

        # 创建分析器
        analyzer = Layer1Analyzer(enable_mypy=False, enable_bandit=True)

        if not analyzer.is_enabled():
            pytest.skip("No analyzers available")

        # 分析第一个函数（有安全问题）
        facts1 = analyzer.analyze_function(test_file, "run_command", 4, 7)

        print(f"\n=== run_command 分析结果 ===")
        print(f"函数: {facts1.function_name}")
        print(f"类型问题数: {len(facts1.type_issues)}")
        print(f"安全问题数: {len(facts1.security_issues)}")

        for issue in facts1.security_issues:
            print(f"  - {issue}")

        # 验证
        if 'bandit' in analyzer.get_enabled_tools():
            assert len(facts1.security_issues) > 0, "应该发现安全问题"

        # 分析第二个函数（无安全问题）
        facts2 = analyzer.analyze_function(test_file, "safe_function", 9, 11)

        print(f"\n=== safe_function 分析结果 ===")
        print(f"函数: {facts2.function_name}")
        print(f"安全问题数: {len(facts2.security_issues)}")

    def test_analyze_code_with_both_tools(self, test_code_dir):
        """测试同时使用两个工具"""
        # 创建测试文件
        test_file = os.path.join(test_code_dir, "test_combined.py")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("""\
import os

def bad_function(cmd: str) -> int:
    # 既有类型错误，又有安全问题
    os.system(cmd)  # 安全问题
    return "not an int"  # 类型错误
""")

        # 创建分析器（两个工具都启用）
        analyzer = Layer1Analyzer(enable_mypy=True, enable_bandit=True)

        if not analyzer.is_enabled():
            pytest.skip("No analyzers available")

        # 分析函数
        facts = analyzer.analyze_function(test_file, "bad_function", 3, 6)

        print(f"\n=== bad_function 分析结果 ===")
        print(f"函数: {facts.function_name}")
        print(f"类型问题数: {len(facts.type_issues)}")
        print(f"安全问题数: {len(facts.security_issues)}")
        print(f"总问题数: {facts.total_issues()}")
        print(f"高严重度问题数: {facts.high_severity_count()}")
        print(f"有严重问题: {facts.has_critical_issues()}")

        print("\n类型问题:")
        for issue in facts.type_issues:
            print(f"  - {issue}")

        print("\n安全问题:")
        for issue in facts.security_issues:
            print(f"  - {issue}")

        # 验证
        enabled_tools = analyzer.get_enabled_tools()
        if 'mypy' in enabled_tools:
            assert len(facts.type_issues) > 0, "应该发现类型错误"
        if 'bandit' in enabled_tools:
            assert len(facts.security_issues) > 0, "应该发现安全问题"

        assert facts.total_issues() > 0
        assert facts.has_critical_issues()  # 应该有高严重度问题

    def test_performance(self, test_code_dir):
        """测试性能（确保缓存有效）"""
        import time

        # 创建测试文件
        test_file = os.path.join(test_code_dir, "test_perf.py")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("""def func1():
    pass

def func2():
    pass

def func3():
    pass
""")

        analyzer = Layer1Analyzer()

        if not analyzer.is_enabled():
            pytest.skip("No analyzers available")

        # 第一次分析（会调用工具）
        start = time.time()
        facts1 = analyzer.analyze_function(test_file, "func1", 1, 2)
        first_time = time.time() - start

        # 第二次分析同文件的不同函数（应该使用缓存）
        start = time.time()
        facts2 = analyzer.analyze_function(test_file, "func2", 4, 5)
        second_time = time.time() - start

        print(f"\n=== 性能测试 ===")
        print(f"第一次分析耗时: {first_time:.3f}s")
        print(f"第二次分析耗时: {second_time:.3f}s")
        print(f"加速比: {first_time/second_time:.2f}x")

        # 第二次应该明显更快（使用缓存）
        assert second_time < first_time, "缓存应该提升性能"
