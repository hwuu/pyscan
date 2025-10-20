"""
Bug 检测流水线

负责协调 Layer 1（静态分析）、Layer 3（LLM 检测）、Layer 4（交叉验证）的完整流程。
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from pyscan.config import Config
from pyscan.ast_parser import FunctionInfo
from pyscan.bug_detector import BugDetector, BugReport
from pyscan.layer1.analyzer import Layer1Analyzer
from pyscan.layer1.base import StaticFacts

logger = logging.getLogger(__name__)


@dataclass
class DetectionResult:
    """检测结果"""
    reports: List[BugReport] = field(default_factory=list)  # 去重后的 bug 报告列表
    prompt: str = ""                      # LLM prompt
    raw_response: str = ""                # LLM 原始响应
    layer1_facts: Optional[StaticFacts] = None  # Layer 1 分析结果
    layer3_bug_count: int = 0             # Layer 3 检测到的 bug 数量
    layer4_bug_count: int = 0             # Layer 4 新增的 bug 数量
    deduped_count: int = 0                # 去重数量


class DetectionPipeline:
    """Bug 检测流水线，协调多层检测"""

    def __init__(
        self,
        config: Config,
        layer1_analyzer: Layer1Analyzer,
        bug_detector: BugDetector
    ):
        """
        初始化检测流水线

        Args:
            config: 配置对象
            layer1_analyzer: Layer 1 静态分析器
            bug_detector: Layer 3 LLM 检测器
        """
        self.config = config
        self.layer1_analyzer = layer1_analyzer
        self.bug_detector = bug_detector

        # Layer 4 交叉验证器（可选）
        self.cross_validator = None
        layer4_config = getattr(config, 'layer4', {})
        if isinstance(layer4_config, dict):
            enable_cross_validation = layer4_config.get('enable_cross_validation', True)
        else:
            enable_cross_validation = getattr(layer4_config, 'enable_cross_validation', True)

        if enable_cross_validation:
            from pyscan.layer4.cross_validator import CrossValidator
            self.cross_validator = CrossValidator()
            logger.info("Layer 4 cross-validation enabled")

    def detect_bugs(
        self,
        function: FunctionInfo,
        context: Dict[str, Any],
        file_path: str,
        absolute_file_path: str,
        function_start_line: int,
        callers: List[Dict[str, Any]],
        callees: List[str],
        inferred_callers: List[Dict[str, Any]],
        bug_id_start: int
    ) -> Optional[DetectionResult]:
        """
        执行完整的 bug 检测流程

        流程：
        1. Layer 1: 静态分析 (mypy + bandit)
        2. Layer 3: LLM 检测
        3. Layer 4: 交叉验证 (如果启用)
        4. 合并结果（去重 + 标记来源）

        Args:
            function: 函数信息
            context: 函数上下文
            file_path: 相对文件路径
            absolute_file_path: 绝对文件路径（用于 Layer 1）
            function_start_line: 函数起始行号
            callers: 调用者信息列表
            callees: 被调用函数列表
            inferred_callers: 推断的调用者列表
            bug_id_start: Bug ID 起始编号

        Returns:
            DetectionResult: 检测结果，如果失败返回 None
        """
        # Step 1: Layer 1 静态分析
        static_facts = None
        if self.layer1_analyzer.is_enabled():
            try:
                static_facts = self.layer1_analyzer.analyze_function(
                    file_path=absolute_file_path,
                    func_name=function.name,
                    start_line=function.lineno,
                    end_line=function.end_lineno,
                    complexity_score=0  # 暂时不计算复杂度
                )
            except Exception as e:
                logger.warning(f"Layer 1 analysis failed for {function.name}: {e}")

        # Step 2: Layer 3 LLM 检测
        llm_result = self.bug_detector.detect(
            function,
            context,
            file_path=file_path,
            function_start_line=function_start_line,
            callers=callers,
            callees=callees,
            inferred_callers=inferred_callers,
            bug_id_start=bug_id_start,
            static_facts=static_facts
        )

        if llm_result is None:
            # LLM 检测失败
            return None

        llm_bugs = llm_result["reports"]
        prompt = llm_result["prompt"]
        raw_response = llm_result["raw_response"]

        # Step 3: Layer 4 交叉验证
        layer4_bugs = []
        if self.cross_validator and static_facts:
            try:
                layer4_bugs = self.cross_validator.validate_type_safety(
                    static_facts,
                    llm_bugs
                )
                logger.debug(f"Layer 4 validated {len(layer4_bugs)} type safety bugs")
            except Exception as e:
                logger.warning(f"Layer 4 validation failed for {function.name}: {e}")

        # Step 4: 合并和去重
        merged_reports, dedup_count = self._merge_and_deduplicate(
            llm_bugs,
            layer4_bugs,
            bug_id_start
        )

        return DetectionResult(
            reports=merged_reports,
            prompt=prompt,
            raw_response=raw_response,
            layer1_facts=static_facts,
            layer3_bug_count=len(llm_bugs),
            layer4_bug_count=len(layer4_bugs),
            deduped_count=dedup_count
        )

    def _merge_and_deduplicate(
        self,
        llm_bugs: List[BugReport],
        layer4_bugs: List[BugReport],
        bug_id_start: int
    ) -> tuple[List[BugReport], int]:
        """
        合并 LLM bugs 和 Layer 4 bugs，去重并标记来源

        去重规则（选项B - 宽松匹配）：
        - 位置相近（±2行）AND (类型完全相同 OR 都是类型相关)
        - 如果匹配，使用 Layer 4 的信息（选项A - 优先 Layer 4）
        - 保留 LLM 的原始信息在 evidence 中

        来源标记：
        evidence = {
            'llm_detected': True/False,
            'mypy_detected': True/False,
            'llm_confirmed': True/False,
            'detection_source': 'llm' | 'layer4' | 'both',
            'llm_description': <original LLM description>  # 如果重复
        }

        Args:
            llm_bugs: LLM 检测到的 bugs
            layer4_bugs: Layer 4 验证的 bugs
            bug_id_start: Bug ID 起始编号

        Returns:
            (merged_reports, dedup_count): 合并后的报告列表和去重数量
        """
        # 标记 LLM bugs 的来源
        for bug in llm_bugs:
            if not bug.evidence:
                bug.evidence = {}
            bug.evidence['llm_detected'] = True
            bug.evidence['mypy_detected'] = False
            bug.evidence['detection_source'] = 'llm'

        # 检查是否启用去重
        layer4_config = getattr(self.config, 'layer4', {})
        if isinstance(layer4_config, dict):
            enable_dedup = layer4_config.get('enable_deduplication', True)
        else:
            enable_dedup = getattr(layer4_config, 'enable_deduplication', True)

        if not enable_dedup:
            # 不去重，直接合并
            all_bugs = llm_bugs + layer4_bugs
            # 重新分配 bug_id
            for i, bug in enumerate(all_bugs):
                bug.bug_id = f"BUG_{bug_id_start + i:04d}"
            return all_bugs, 0

        # 去重逻辑
        merged = []
        dedup_count = 0
        used_layer4_indices = set()

        # 遍历 LLM bugs，检查是否与 Layer 4 bugs 重复
        for llm_bug in llm_bugs:
            matched = False

            for i, layer4_bug in enumerate(layer4_bugs):
                if i in used_layer4_indices:
                    continue

                if self._is_duplicate(llm_bug, layer4_bug):
                    # 重复，使用 Layer 4 的信息（优先 Layer 4）
                    dedup_count += 1
                    used_layer4_indices.add(i)
                    matched = True

                    # 保留 LLM 的原始描述在 evidence 中
                    layer4_bug.evidence['llm_description'] = llm_bug.description
                    layer4_bug.evidence['llm_detected'] = True
                    layer4_bug.evidence['detection_source'] = 'both'

                    merged.append(layer4_bug)
                    break

            if not matched:
                # LLM bug 没有匹配，直接添加
                merged.append(llm_bug)

        # 添加未匹配的 Layer 4 bugs
        for i, layer4_bug in enumerate(layer4_bugs):
            if i not in used_layer4_indices:
                merged.append(layer4_bug)

        # 重新分配 bug_id（保持连续）
        for i, bug in enumerate(merged):
            bug.bug_id = f"BUG_{bug_id_start + i:04d}"

        logger.debug(
            f"Merged {len(llm_bugs)} LLM bugs + {len(layer4_bugs)} Layer4 bugs "
            f"= {len(merged)} bugs (deduped {dedup_count})"
        )

        return merged, dedup_count

    def _is_duplicate(self, bug1: BugReport, bug2: BugReport) -> bool:
        """
        判断两个 bug 是否重复

        规则（选项B - 宽松匹配）：
        - 位置相近（±2行）AND
        - (类型完全相同 OR 都是类型相关)

        Args:
            bug1: Bug 1
            bug2: Bug 2

        Returns:
            是否重复
        """
        # 获取容忍度配置
        layer4_config = getattr(self.config, 'layer4', {})
        if isinstance(layer4_config, dict):
            tolerance = layer4_config.get('position_tolerance', 2)
        else:
            tolerance = getattr(layer4_config, 'position_tolerance', 2)

        # 位置相近检查
        position_close = abs(bug1.start_line - bug2.start_line) <= tolerance

        if not position_close:
            return False

        # 类型匹配检查
        type1 = bug1.bug_type.lower()
        type2 = bug2.bug_type.lower()

        # 类型完全相同
        if type1 == type2:
            return True

        # 都是类型相关（包含 'type' 关键字）
        if 'type' in type1 and 'type' in type2:
            return True

        return False
