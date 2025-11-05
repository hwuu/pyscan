"""
Layer 2: 符号分析与数据流分析

提供确定性问题检测，包括：
- 资源泄漏检测
- 控制流问题检测
- 并发问题检测
- 数据流分析
"""

from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class SuspiciousFinding:
    """可疑发现（中低置信度）"""

    type: str  # 问题类型
    confidence: float  # 置信度 (0.0-1.0)
    description: str  # 问题描述
    location: Dict[str, Any]  # 位置信息 (start_line, end_line, etc.)
    evidence: Dict[str, Any]  # 证据信息
    suggestion: str  # 修复建议


@dataclass
class ConfirmedBug:
    """确认的 Bug（高置信度）"""

    type: str  # 问题类型
    severity: str  # 严重程度 (high/medium/low)
    confidence: float  # 置信度 (≥0.9)
    description: str  # 问题描述
    location: Dict[str, Any]  # 位置信息
    evidence: Dict[str, Any]  # 证据信息
    suggestion: str  # 修复建议


@dataclass
class Layer2Result:
    """Layer 2 分析结果"""

    confirmed_bugs: List[ConfirmedBug]  # 高置信度 bug（直接报告）
    suspicious_findings: List[SuspiciousFinding]  # 中低置信度可疑点（传递给 Layer 3）

    # 结构化分析结果（用于 Layer 3 增强上下文）
    cfg_summary: Dict[str, Any] = None  # CFG 摘要
    dataflow_summary: Dict[str, Any] = None  # 数据流分析摘要

    # 元数据
    analysis_time: float = 0.0  # 分析耗时（秒）
    covered_areas: List[str] = None  # Layer 2 已覆盖的问题类型


__all__ = [
    'SuspiciousFinding',
    'ConfirmedBug',
    'Layer2Result',
]
