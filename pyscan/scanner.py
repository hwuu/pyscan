"""Code scanner module."""
import os
from pathlib import Path
from typing import List
from fnmatch import fnmatch


class Scanner:
    """Scanner for Python code files."""

    def __init__(self, exclude_patterns: List[str] = None):
        """
        Initialize Scanner.

        Args:
            exclude_patterns: List of glob patterns to exclude files/directories.
        """
        self.exclude_patterns = exclude_patterns or []

    def scan(self, directory: str) -> List[str]:
        """
        Scan directory for Python files.

        Args:
            directory: Directory path to scan.

        Returns:
            List of absolute paths to Python files.

        Raises:
            FileNotFoundError: If directory does not exist.
        """
        dir_path = Path(directory)

        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        if not dir_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")

        python_files = []

        for root, dirs, files in os.walk(dir_path):
            # 过滤目录
            dirs[:] = [
                d for d in dirs if not self._should_exclude(Path(root) / d)
            ]

            # 收集 Python 文件
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    if not self._should_exclude(file_path):
                        python_files.append(str(file_path.absolute()))

        return python_files

    def _should_exclude(self, path: Path) -> bool:
        """
        Check if path should be excluded based on patterns.

        Args:
            path: Path to check.

        Returns:
            True if path should be excluded, False otherwise.
        """
        path_str = str(path)

        for pattern in self.exclude_patterns:
            # 支持两种模式:
            # 1. 简单文件名匹配: "test_*.py"
            # 2. 路径模式匹配: "*/venv/*"
            if fnmatch(path.name, pattern):
                return True

            # 路径模式匹配
            if fnmatch(path_str.replace('\\', '/'), pattern):
                return True

            # 检查路径中是否包含模式片段
            path_parts = path_str.replace('\\', '/').split('/')
            pattern_parts = pattern.strip('*/').split('/')

            # 如果模式片段都在路径中,则匹配
            if all(any(fnmatch(part, p) for part in path_parts) for p in pattern_parts):
                return True

        return False
