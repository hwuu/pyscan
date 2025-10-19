"""
Layer 1 统一分析器

整合所有静态分析工具，提供统一接口
"""

from typing import List, Optional
import logging

from .base import StaticFacts, StaticIssue, StaticAnalyzer
from .mypy_analyzer import MypyAnalyzer
from .bandit_analyzer import BanditAnalyzer

logger = logging.getLogger(__name__)


class Layer1Analyzer:
    """Layer 1 统一分析器"""

    def __init__(self, enable_mypy: bool = True, enable_bandit: bool = True):
        """
        初始化 Layer 1 分析器

        Args:
            enable_mypy: 是否启用 mypy
            enable_bandit: 是否启用 bandit
        """
        self.analyzers: List[StaticAnalyzer] = []

        # 添加分析器
        if enable_mypy:
            mypy = MypyAnalyzer()
            if mypy.is_available():
                self.analyzers.append(mypy)
                logger.info("Mypy analyzer enabled")
            else:
                logger.warning("Mypy requested but not available, skipping")

        if enable_bandit:
            bandit = BanditAnalyzer()
            if bandit.is_available():
                self.analyzers.append(bandit)
                logger.info("Bandit analyzer enabled")
            else:
                logger.warning("Bandit requested but not available, skipping")

        if not self.analyzers:
            logger.warning("No static analyzers available!")

    def analyze_function(self,
                        file_path: str,
                        func_name: str,
                        start_line: int,
                        end_line: int,
                        complexity_score: int = 0) -> StaticFacts:
        """
        分析单个函数，收集所有工具的结果

        Args:
            file_path: 文件路径
            func_name: 函数名
            start_line: 函数起始行号
            end_line: 函数结束行号
            complexity_score: 复杂度分数

        Returns:
            静态分析事实
        """
        type_issues = []
        security_issues = []

        # 运行所有分析器
        for analyzer in self.analyzers:
            try:
                issues = analyzer.analyze_function(
                    file_path, func_name, start_line, end_line
                )

                # 按工具分类
                for issue in issues:
                    if issue.tool == 'mypy':
                        type_issues.append(issue)
                    elif issue.tool == 'bandit':
                        security_issues.append(issue)

            except Exception as e:
                logger.warning(
                    f"{analyzer.get_name()} failed for {func_name} "
                    f"in {file_path}: {e}"
                )

        # 检查是否有类型注解
        has_type_annotations = self._check_type_annotations(
            file_path, start_line, end_line
        )

        facts = StaticFacts(
            file_path=file_path,
            function_name=func_name,
            function_start_line=start_line,
            type_issues=type_issues,
            security_issues=security_issues,
            has_type_annotations=has_type_annotations,
            complexity_score=complexity_score
        )

        logger.debug(
            f"Layer 1 analysis complete for {func_name}: "
            f"{facts.total_issues()} issues found"
        )

        return facts

    def _check_type_annotations(self,
                                file_path: str,
                                start_line: int,
                                end_line: int) -> bool:
        """
        简单检查函数是否有类型注解

        Args:
            file_path: 文件路径
            start_line: 起始行号
            end_line: 结束行号

        Returns:
            是否有类型注解
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

                # 检查函数范围内的代码
                func_code = ''.join(lines[start_line - 1:end_line])

                # 简单启发式检查
                # 1. 返回类型注解: ->
                # 2. 参数类型注解: : (后面跟类型)
                has_return_annotation = '->' in func_code
                has_param_annotation = ': ' in func_code and 'def ' in func_code

                return has_return_annotation or has_param_annotation

        except Exception as e:
            logger.debug(f"Failed to check type annotations: {e}")
            return False

    def get_enabled_tools(self) -> List[str]:
        """
        获取已启用的工具列表

        Returns:
            工具名称列表
        """
        return [analyzer.get_name() for analyzer in self.analyzers]

    def is_enabled(self) -> bool:
        """
        检查是否有至少一个工具可用

        Returns:
            是否可用
        """
        return len(self.analyzers) > 0
