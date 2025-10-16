"""AST parser module for extracting function information and call relationships."""
import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Set


@dataclass
class FunctionInfo:
    """Information about a function."""

    name: str
    args: List[str]
    lineno: int
    end_lineno: int
    col_offset: int
    end_col_offset: int
    code: str
    decorators: List[str] = field(default_factory=list)
    is_async: bool = False
    calls: Set[str] = field(default_factory=set)
    docstring: str = ""


class ASTParser:
    """Parser for Python AST."""

    def parse_file(self, file_path: str) -> List[FunctionInfo]:
        """
        Parse a Python file and extract function information.

        Args:
            file_path: Path to Python file.

        Returns:
            List of FunctionInfo objects.

        Raises:
            FileNotFoundError: If file does not exist.
            SyntaxError: If file contains invalid Python syntax.
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, 'r', encoding='utf-8') as f:
            source_code = f.read()

        try:
            tree = ast.parse(source_code, filename=file_path)
        except SyntaxError as e:
            raise SyntaxError(f"Syntax error in {file_path}: {e}")

        # 提取源代码行
        source_lines = source_code.splitlines()

        # 提取所有函数
        functions = []
        visitor = FunctionVisitor(source_lines)
        visitor.visit(tree)
        functions.extend(visitor.functions)

        return functions


class FunctionVisitor(ast.NodeVisitor):
    """AST visitor for extracting function information."""

    def __init__(self, source_lines: List[str]):
        """
        Initialize visitor.

        Args:
            source_lines: Lines of source code.
        """
        self.source_lines = source_lines
        self.functions: List[FunctionInfo] = []

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definition node."""
        self._process_function(node, is_async=False)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit async function definition node."""
        self._process_function(node, is_async=True)
        self.generic_visit(node)

    def _process_function(self, node, is_async: bool):
        """Process function node and extract information."""
        # 提取参数
        args = []
        for arg in node.args.args:
            args.append(arg.arg)

        # 提取装饰器
        decorators = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
            elif isinstance(decorator, ast.Attribute):
                decorators.append(decorator.attr)

        # 提取函数代码
        start_line = node.lineno - 1  # 0-indexed
        end_line = node.end_lineno  # Inclusive, 1-indexed
        code_lines = self.source_lines[start_line:end_line]
        code = '\n'.join(code_lines)

        # 提取文档字符串
        docstring = ast.get_docstring(node) or ""

        # 提取函数调用
        call_visitor = CallVisitor()
        call_visitor.visit(node)

        func_info = FunctionInfo(
            name=node.name,
            args=args,
            lineno=node.lineno,
            end_lineno=node.end_lineno,
            col_offset=node.col_offset,
            end_col_offset=node.end_col_offset if hasattr(node, 'end_col_offset') else 0,
            code=code,
            decorators=decorators,
            is_async=is_async,
            calls=call_visitor.calls,
            docstring=docstring,
        )

        self.functions.append(func_info)


class CallVisitor(ast.NodeVisitor):
    """Visitor for extracting function calls."""

    def __init__(self):
        """Initialize call visitor."""
        self.calls: Set[str] = set()

    def visit_Call(self, node: ast.Call):
        """Visit function call node."""
        # 处理不同类型的调用
        if isinstance(node.func, ast.Name):
            # 直接函数调用: func()
            self.calls.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            # 方法调用: obj.method() 或 self.method()
            self.calls.add(node.func.attr)
        elif isinstance(node.func, ast.Call):
            # 链式调用: func()()
            self.visit(node.func)

        self.generic_visit(node)
