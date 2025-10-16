"""Tests for context builder module."""
import pytest
from pathlib import Path
from pyscan.context_builder import ContextBuilder
from pyscan.ast_parser import ASTParser, FunctionInfo


class TestContextBuilder:
    """Test ContextBuilder class."""

    @pytest.fixture
    def sample_functions(self):
        """Get sample functions from fixture."""
        sample_code_path = str(
            Path(__file__).parent / "fixtures" / "sample_code.py"
        )
        parser = ASTParser()
        return parser.parse_file(sample_code_path)

    def test_build_context(self, sample_functions):
        """测试构建上下文。"""
        builder = ContextBuilder(sample_functions)

        func_with_calls = next(
            f for f in sample_functions if f.name == "function_with_calls"
        )

        context = builder.build_context(func_with_calls)

        assert context["current_function"] == func_with_calls.code
        assert len(context["callees"]) > 0
        assert any("simple_function" in c for c in context["callees"])

    def test_find_callers(self, sample_functions):
        """测试查找调用者。"""
        builder = ContextBuilder(sample_functions)

        simple_func = next(
            f for f in sample_functions if f.name == "simple_function"
        )

        context = builder.build_context(simple_func)

        # simple_function 被 function_with_calls 调用
        assert len(context["callers"]) > 0
        assert any("function_with_calls" in c for c in context["callers"])

    def test_context_with_no_calls(self, sample_functions):
        """测试没有调用的函数。"""
        builder = ContextBuilder(sample_functions)

        simple_func = next(
            f for f in sample_functions if f.name == "simple_function"
        )

        context = builder.build_context(simple_func)

        # simple_function 不调用其他函数
        assert len(context["callees"]) == 0

    def test_build_context_summary(self):
        """测试构建上下文摘要。"""
        builder = ContextBuilder([])

        # 模拟一个很长的上下文
        long_context = {
            "current_function": "def func():\n" + "    pass\n" * 1000,
            "callers": ["caller1", "caller2"],
            "callees": ["callee1", "callee2"]
        }

        summary = builder._build_context_text(long_context)
        assert len(summary) > 0
        assert "当前函数" in summary or "current" in summary.lower()

    def test_token_limit_handling(self, sample_functions):
        """测试 token 限制处理。"""
        # 设置很小的 token 限制
        builder = ContextBuilder(sample_functions, max_tokens=100)

        func = sample_functions[0]
        context = builder.build_context(func)

        # 即使 token 限制很小，也应该返回有效上下文
        assert "current_function" in context
        assert context["current_function"] is not None
