"""
Mypy 静态类型检查器集成
"""

import subprocess
import shutil
from pathlib import Path
from typing import List, Dict
import logging

from .base import StaticAnalyzer, StaticIssue

logger = logging.getLogger(__name__)


class MypyAnalyzer(StaticAnalyzer):
    """Mypy 类型检查器"""

    def __init__(self):
        self.cache: Dict[str, List[StaticIssue]] = {}  # 缓存文件级别的分析结果
        self._available = None  # 懒加载检查

    def get_name(self) -> str:
        """返回分析器名称"""
        return "mypy"

    def is_available(self) -> bool:
        """检查 mypy 是否可用"""
        if self._available is not None:
            return self._available

        try:
            # 检查 mypy 是否安装
            result = subprocess.run(
                ['mypy', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            self._available = result.returncode == 0
            if self._available:
                logger.debug(f"Mypy found: {result.stdout.strip()}")
            else:
                logger.warning("Mypy not available (non-zero return code)")
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning(f"Mypy not available: {e}")
            self._available = False

        return self._available

    def analyze_file(self, file_path: str) -> List[StaticIssue]:
        """
        运行 mypy 分析文件

        Args:
            file_path: 文件路径

        Returns:
            问题列表
        """
        # 检查缓存
        if file_path in self.cache:
            logger.debug(f"Using cached mypy results for {file_path}")
            return self.cache[file_path]

        # 检查工具是否可用
        if not self.is_available():
            logger.debug("Mypy not available, skipping analysis")
            return []

        try:
            # 运行 mypy
            # --show-column-numbers: 显示列号
            # --no-error-summary: 不显示错误摘要
            # --no-color-output: 不使用颜色输出
            # --ignore-missing-imports: 忽略缺失的导入
            result = subprocess.run(
                [
                    'mypy',
                    '--show-column-numbers',
                    '--no-error-summary',
                    '--no-color-output',
                    '--ignore-missing-imports',
                    file_path
                ],
                capture_output=True,
                text=True,
                timeout=30
            )

            issues = self._parse_output(result.stdout, file_path)
            self.cache[file_path] = issues

            logger.debug(f"Mypy found {len(issues)} issues in {file_path}")
            return issues

        except subprocess.TimeoutExpired:
            logger.warning(f"Mypy analysis timeout for {file_path}")
            return []
        except Exception as e:
            logger.warning(f"Mypy analysis failed for {file_path}: {e}")
            return []

    def analyze_function(self, file_path: str, func_name: str,
                        start_line: int, end_line: int) -> List[StaticIssue]:
        """
        获取特定函数范围内的问题

        Args:
            file_path: 文件路径
            func_name: 函数名
            start_line: 函数起始行号
            end_line: 函数结束行号

        Returns:
            函数范围内的问题列表
        """
        all_issues = self.analyze_file(file_path)
        return [
            issue for issue in all_issues
            if start_line <= issue.line <= end_line
        ]

    def _parse_output(self, output: str, file_path: str) -> List[StaticIssue]:
        """
        解析 mypy 输出

        Mypy 输出格式：
        file.py:10:5: error: Message [error-code]
        file.py:20:1: note: Note message

        Windows 下可能是：
        C:\\path\\to\\file.py:10:5: error: Message [error-code]

        Args:
            output: mypy 标准输出
            file_path: 文件路径

        Returns:
            问题列表
        """
        import re
        issues = []

        for line in output.strip().split('\n'):
            if not line:
                continue

            try:
                # 格式: file.py:10:5: error: Message [error-code]
                # 注意：Windows 路径可能包含 C:\，需要特殊处理
                # 例如: C:\path\to\file.py:10:5: error: Message

                # 使用正则表达式匹配: <任意路径>:<行号>:<列号>: <严重程度>: <消息>
                # 查找第一个":<数字>:"模式（这是行号）
                match = re.search(r':(\d+):(\d+):\s*(\w+):\s*(.+)', line)
                if not match:
                    continue

                line_num = int(match.group(1))
                col_num = int(match.group(2))
                severity_str = match.group(3)
                message = match.group(4)

                # 判断严重程度
                if severity_str == 'error':
                    severity = 'high'
                elif severity_str == 'note':
                    severity = 'low'
                elif severity_str == 'warning':
                    severity = 'medium'
                else:
                    severity = 'medium'

                # 提取错误代码（如果有）
                error_code = None
                if '[' in message and ']' in message:
                    code_start = message.rfind('[')
                    code_end = message.rfind(']')
                    error_code = message[code_start+1:code_end]
                    message = message[:code_start].strip()

                issues.append(StaticIssue(
                    tool='mypy',
                    type='type-error',
                    severity=severity,
                    message=message,
                    file_path=file_path,
                    line=line_num,
                    column=col_num,
                    code=error_code
                ))

            except Exception as e:
                logger.debug(f"Failed to parse mypy line: {line}, error: {e}")
                continue

        return issues
