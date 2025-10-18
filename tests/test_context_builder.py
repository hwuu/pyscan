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
        # callees 已被移除，不再检查
        assert "is_public_api" in context

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

        # 确认 context 包含必需字段
        assert "current_function" in context
        assert "is_public_api" in context

    def test_build_context_summary(self):
        """测试构建上下文摘要。"""
        builder = ContextBuilder([])

        # 模拟一个很长的上下文
        long_context = {
            "current_function": "def func():\n" + "    pass\n" * 1000,
            "callers": ["caller1", "caller2"],
            "is_public_api": False,
            "inferred_callers": []
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

    def test_decorator_inference(self):
        """测试装饰器调用关系推断。"""
        # 创建测试函数
        decorator_func = FunctionInfo(
            name="my_decorator",
            args=["func"],
            lineno=1,
            end_lineno=3,
            col_offset=0,
            end_col_offset=0,
            code="def my_decorator(func):\n    return func",
            decorators=[],
            calls=set()
        )

        decorated_func = FunctionInfo(
            name="decorated_func",
            args=[],
            lineno=5,
            end_lineno=7,
            col_offset=0,
            end_col_offset=0,
            code="@my_decorator\ndef decorated_func():\n    pass",
            decorators=["my_decorator"],
            calls=set()
        )

        builder = ContextBuilder([decorator_func, decorated_func], enable_advanced_analysis=True)

        # 测试装饰器函数的上下文
        context = builder.build_context(decorator_func)
        assert "inferred_callees" in context
        assert len(context["inferred_callees"]) > 0

        # 测试被装饰函数的上下文
        context = builder.build_context(decorated_func)
        assert "inferred_callers" in context
        assert len(context["inferred_callers"]) > 0

    def test_callable_inference(self):
        """测试 Callable 类型参数推断。"""
        # 创建测试函数
        processor_func = FunctionInfo(
            name="processor",
            args=["callback", "data"],
            lineno=1,
            end_lineno=3,
            col_offset=0,
            end_col_offset=0,
            code="def processor(callback, data):\n    callback(data)",
            decorators=[],
            calls=set(["callback"]),
            arg_types={"callback": "Callable[[int], None]", "data": "int"}
        )

        handler_func = FunctionInfo(
            name="handler",
            args=["value"],
            lineno=5,
            end_lineno=7,
            col_offset=0,
            end_col_offset=0,
            code="def handler(value):\n    print(value)",
            decorators=[],
            calls=set(["print"])
        )

        builder = ContextBuilder([processor_func, handler_func], enable_advanced_analysis=True)

        # 测试有 Callable 参数的函数
        context = builder.build_context(processor_func)
        assert "inferred_callees" in context
        # 应该推断 handler 可能作为 callback 传入

        # 测试可能被作为 Callable 传入的函数
        context = builder.build_context(handler_func)
        assert "inferred_callers" in context
        # 应该推断可能被 processor 调用

    def test_advanced_analysis_disabled(self):
        """测试禁用高级分析。"""
        decorator_func = FunctionInfo(
            name="my_decorator",
            args=["func"],
            lineno=1,
            end_lineno=3,
            col_offset=0,
            end_col_offset=0,
            code="def my_decorator(func):\n    return func",
            decorators=[],
            calls=set()
        )

        decorated_func = FunctionInfo(
            name="decorated_func",
            args=[],
            lineno=5,
            end_lineno=7,
            col_offset=0,
            end_col_offset=0,
            code="@my_decorator\ndef decorated_func():\n    pass",
            decorators=["my_decorator"],
            calls=set()
        )

        builder = ContextBuilder([decorator_func, decorated_func], enable_advanced_analysis=False)

        context = builder.build_context(decorator_func)
        # 禁用高级分析时，不应该有推断的调用关系
        assert "inferred_callees" in context
        assert len(context["inferred_callees"]) == 0

    def test_is_public_api_by_decorator(self, tmp_path):
        """测试通过装饰器识别公共 API。"""
        from pyscan.config import Config

        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
llm:
  base_url: "https://api.openai.com/v1"
  api_key: "sk-test-key"
  model: "gpt-4"
""")
        config = Config.from_file(str(config_file))

        api_func = FunctionInfo(
            name="handle_request",
            args=["request"],
            lineno=1,
            end_lineno=3,
            col_offset=0,
            end_col_offset=0,
            code="@route('/api')\ndef handle_request(request):\n    pass",
            decorators=["route"],
            calls=set()
        )

        builder = ContextBuilder([api_func], config=config)
        context = builder.build_context(api_func)

        assert context["is_public_api"] is True

    def test_is_public_api_by_name_prefix(self, tmp_path):
        """测试通过函数名前缀识别公共 API。"""
        from pyscan.config import Config

        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
llm:
  base_url: "https://api.openai.com/v1"
  api_key: "sk-test-key"
  model: "gpt-4"
""")
        config = Config.from_file(str(config_file))

        api_func = FunctionInfo(
            name="api_get_users",
            args=[],
            lineno=1,
            end_lineno=3,
            col_offset=0,
            end_col_offset=0,
            code="def api_get_users():\n    pass",
            decorators=[],
            calls=set()
        )

        builder = ContextBuilder([api_func], config=config)
        context = builder.build_context(api_func)

        assert context["is_public_api"] is True

    def test_internal_function_not_public_api(self, tmp_path):
        """测试内部函数不被识别为公共 API。"""
        from pyscan.config import Config

        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
llm:
  base_url: "https://api.openai.com/v1"
  api_key: "sk-test-key"
  model: "gpt-4"
""")
        config = Config.from_file(str(config_file))

        internal_func = FunctionInfo(
            name="helper_function",
            args=["data"],
            lineno=1,
            end_lineno=3,
            col_offset=0,
            end_col_offset=0,
            code="def helper_function(data):\n    pass",
            decorators=[],
            calls=set()
        )

        caller_func = FunctionInfo(
            name="caller",
            args=[],
            lineno=5,
            end_lineno=7,
            col_offset=0,
            end_col_offset=0,
            code="def caller():\n    helper_function({})",
            decorators=[],
            calls=set(["helper_function"])
        )

        builder = ContextBuilder([internal_func, caller_func], config=config)
        context = builder.build_context(internal_func)

        # 有内部调用者，应该被识别为内部函数
        assert context["is_public_api"] is False
