"""
Layer 2 检测器基类
"""

import ast
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from pyscan.layer2 import Layer2Result, ConfirmedBug, SuspiciousFinding


class BaseDetector(ABC):
    """检测器基类

    所有 Layer 2 检测器都应继承此类并实现 detect 方法。
    """

    def __init__(self, confidence_threshold: float = 0.9, suspicious_threshold: float = 0.5):
        """
        初始化检测器

        Args:
            confidence_threshold: 高置信度阈值（≥此值直接报告为 bug）
            suspicious_threshold: 可疑点阈值（≥此值但<confidence_threshold 时标记为可疑点）
        """
        self.confidence_threshold = confidence_threshold
        self.suspicious_threshold = suspicious_threshold

    @abstractmethod
    def detect(self, function_node: ast.FunctionDef, context: Dict[str, Any]) -> Layer2Result:
        """
        检测函数中的问题

        Args:
            function_node: AST 函数节点
            context: 上下文信息，可能包含：
                - file_path: 文件路径
                - module_ast: 模块级 AST
                - callers: 调用者信息列表
                - callees: 被调用函数信息列表
                - global_vars: 全局变量信息
                - class_context: 类上下文（如果函数是方法）

        Returns:
            Layer2Result: 包含确认的 bug、可疑发现和分析结果
        """
        raise NotImplementedError

    def _create_confirmed_bug(
        self,
        bug_type: str,
        severity: str,
        confidence: float,
        description: str,
        location: Dict[str, Any],
        evidence: Dict[str, Any],
        suggestion: str
    ) -> ConfirmedBug:
        """
        创建确认的 bug

        Args:
            bug_type: bug 类型
            severity: 严重程度 (high/medium/low)
            confidence: 置信度 (≥0.9)
            description: 问题描述
            location: 位置信息
            evidence: 证据信息
            suggestion: 修复建议

        Returns:
            ConfirmedBug 实例
        """
        return ConfirmedBug(
            type=bug_type,
            severity=severity,
            confidence=confidence,
            description=description,
            location=location,
            evidence=evidence,
            suggestion=suggestion
        )

    def _create_suspicious_finding(
        self,
        finding_type: str,
        confidence: float,
        description: str,
        location: Dict[str, Any],
        evidence: Dict[str, Any],
        suggestion: str
    ) -> SuspiciousFinding:
        """
        创建可疑发现

        Args:
            finding_type: 发现类型
            confidence: 置信度 (0.5-0.9)
            description: 问题描述
            location: 位置信息
            evidence: 证据信息
            suggestion: 修复建议

        Returns:
            SuspiciousFinding 实例
        """
        return SuspiciousFinding(
            type=finding_type,
            confidence=confidence,
            description=description,
            location=location,
            evidence=evidence,
            suggestion=suggestion
        )

    def _get_location(self, node: ast.AST, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        获取 AST 节点的位置信息

        Args:
            node: AST 节点
            file_path: 文件路径

        Returns:
            位置信息字典
        """
        location = {
            'start_line': getattr(node, 'lineno', 0),
            'end_line': getattr(node, 'end_lineno', 0),
            'start_col': getattr(node, 'col_offset', 0),
            'end_col': getattr(node, 'end_col_offset', 0),
        }

        if file_path:
            location['file_path'] = file_path

        return location
