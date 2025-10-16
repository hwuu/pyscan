"""Tests for AST parser module."""
import pytest
from pathlib import Path
from pyscan.ast_parser import ASTParser, FunctionInfo


class TestASTParser:
    """Test ASTParser class."""

    @pytest.fixture
    def sample_code_path(self):
        """Get path to sample code fixture."""
        return str(Path(__file__).parent / "fixtures" / "sample_code.py")

    def test_parse_file(self, sample_code_path):
        """测试解析 Python 文件。"""
        parser = ASTParser()
        functions = parser.parse_file(sample_code_path)

        assert len(functions) > 0
        assert any(f.name == "simple_function" for f in functions)
        assert any(f.name == "function_with_calls" for f in functions)

    def test_function_info_extraction(self, sample_code_path):
        """测试函数信息提取。"""
        parser = ASTParser()
        functions = parser.parse_file(sample_code_path)

        simple_func = next(f for f in functions if f.name == "simple_function")

        assert simple_func.name == "simple_function"
        assert simple_func.args == ["x", "y"]
        assert simple_func.lineno > 0
        assert simple_func.end_lineno > simple_func.lineno
        assert len(simple_func.code) > 0

    def test_extract_function_calls(self, sample_code_path):
        """测试提取函数调用关系。"""
        parser = ASTParser()
        functions = parser.parse_file(sample_code_path)

        func_with_calls = next(
            f for f in functions if f.name == "function_with_calls"
        )

        assert "simple_function" in func_with_calls.calls

    def test_class_methods(self, sample_code_path):
        """测试类方法解析。"""
        parser = ASTParser()
        functions = parser.parse_file(sample_code_path)

        add_method = next(f for f in functions if f.name == "add")
        multiply_method = next(f for f in functions if f.name == "multiply")

        assert add_method.name == "add"
        assert "self" in add_method.args
        assert "add" in multiply_method.calls  # 调用 self.add

    def test_async_function(self, sample_code_path):
        """测试 async 函数。"""
        parser = ASTParser()
        functions = parser.parse_file(sample_code_path)

        async_func = next(f for f in functions if f.name == "async_function")
        assert async_func.name == "async_function"
        assert async_func.is_async is True

    def test_decorators(self, tmp_path):
        """测试装饰器。"""
        code_file = tmp_path / "decorated.py"
        code_file.write_text("""
@decorator
def decorated_func():
    pass

@property
def prop_func(self):
    return self._value
""")

        parser = ASTParser()
        functions = parser.parse_file(str(code_file))

        decorated = next(f for f in functions if f.name == "decorated_func")
        assert "decorator" in decorated.decorators

        prop = next(f for f in functions if f.name == "prop_func")
        assert "property" in prop.decorators

    def test_invalid_python_file(self, tmp_path):
        """测试无效的 Python 文件。"""
        invalid_file = tmp_path / "invalid.py"
        invalid_file.write_text("def invalid syntax here")

        parser = ASTParser()
        with pytest.raises(SyntaxError):
            parser.parse_file(str(invalid_file))

    def test_file_not_found(self):
        """测试文件不存在。"""
        parser = ASTParser()
        with pytest.raises(FileNotFoundError):
            parser.parse_file("non_existent_file.py")
