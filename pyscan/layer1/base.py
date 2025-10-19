"""
Layer 1 基础模块

定义静态分析工具的基础数据结构和抽象接口
"""

from dataclasses import dataclass, field
from typing import List, Optional
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


@dataclass
class StaticIssue:
    """工具发现的单个问题"""
    tool: str              # 工具名称：mypy/bandit/pylint
    type: str              # 问题类型
    severity: str          # 严重程度：high/medium/low
    message: str           # 问题描述
    file_path: str         # 文件路径
    line: int              # 行号
    column: Optional[int] = None  # 列号
    code: Optional[str] = None    # 错误代码（如 E501）

    def __str__(self):
        col_info = f":{self.column}" if self.column else ""
        code_info = f" [{self.code}]" if self.code else ""
        return f"{self.tool} {self.severity} @ {self.file_path}:{self.line}{col_info}{code_info}: {self.message}"


@dataclass
class StaticFacts:
    """Layer 1 工具收集的所有事实"""
    file_path: str
    function_name: str
    function_start_line: int

    # 各工具发现的问题
    type_issues: List[StaticIssue] = field(default_factory=list)      # mypy
    security_issues: List[StaticIssue] = field(default_factory=list)  # bandit

    # 元信息
    has_type_annotations: bool = False
    complexity_score: int = 0

    def total_issues(self) -> int:
        """返回总问题数"""
        return len(self.type_issues) + len(self.security_issues)

    def high_severity_count(self) -> int:
        """返回高严重度问题数"""
        count = 0
        for issue in self.type_issues + self.security_issues:
            if issue.severity == 'high':
                count += 1
        return count

    def has_critical_issues(self) -> bool:
        """是否有严重问题"""
        return self.high_severity_count() > 0

    def __str__(self):
        return f"StaticFacts({self.function_name} @ {self.file_path}:{self.function_start_line}, " \
               f"{self.total_issues()} issues)"


class StaticAnalyzer(ABC):
    """静态分析工具的抽象基类"""

    @abstractmethod
    def analyze_file(self, file_path: str) -> List[StaticIssue]:
        """
        分析整个文件，返回问题列表

        Args:
            file_path: 文件路径

        Returns:
            问题列表
        """
        pass

    @abstractmethod
    def analyze_function(self, file_path: str, func_name: str,
                        start_line: int, end_line: int) -> List[StaticIssue]:
        """
        分析特定函数，返回问题列表

        Args:
            file_path: 文件路径
            func_name: 函数名
            start_line: 函数起始行号
            end_line: 函数结束行号

        Returns:
            函数范围内的问题列表
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """返回分析器名称"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查工具是否可用"""
        pass
