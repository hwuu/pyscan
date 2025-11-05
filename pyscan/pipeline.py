"""
Bug 检测流水线

负责协调 Layer 1（静态分析）、Layer 2（符号分析）、Layer 3（LLM 检测）、Layer 4（交叉验证）的完整流程。
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from pyscan.config import Config
from pyscan.ast_parser import FunctionInfo
from pyscan.bug_detector import BugDetector, BugReport
from pyscan.layer1.analyzer import Layer1Analyzer
from pyscan.layer1.base import StaticFacts
from pyscan.layer2 import Layer2Result
from pyscan.layer2.detectors.resource_leak import ResourceLeakDetector

logger = logging.getLogger(__name__)


@dataclass
class DetectionResult:
    """检测结果"""
    success: bool = True                      # 检测是否成功
    reports: List[BugReport] = field(default_factory=list)  # 去重后的 bug 报告列表
    prompt: str = ""                      # LLM prompt
    raw_response: str = ""                # LLM 原始响应
    layer1_facts: Optional[StaticFacts] = None  # Layer 1 分析结果
    layer2_result: Optional[Layer2Result] = None  # Layer 2 分析结果
    layer3_bug_count: int = 0             # Layer 3 检测到的 bug 数量
    layer4_bug_count: int = 0             # Layer 4 新增的 bug 数量
    deduped_count: int = 0                # 去重数量
    error: str = ""                       # 错误信息（仅当 success=False 时）


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

        # Layer 2 检测器（可选）
        self.layer2_detectors = []
        layer2_config = getattr(config, 'layer2', {})
        if isinstance(layer2_config, dict):
            layer2_enable = layer2_config.get('enable', True)
            layer2_detectors_config = layer2_config.get('detectors', {})
            confidence_threshold = layer2_config.get('confidence_threshold', 0.9)
            suspicious_threshold = layer2_config.get('suspicious_threshold', 0.5)
        else:
            layer2_enable = getattr(layer2_config, 'enable', True)
            layer2_detectors_config = {}
            confidence_threshold = 0.9
            suspicious_threshold = 0.5

        if layer2_enable:
            # 根据配置启用检测器
            if layer2_detectors_config.get('resource_leak', True):
                resource_leak_detector = ResourceLeakDetector(
                    confidence_threshold=confidence_threshold,
                    suspicious_threshold=suspicious_threshold
                )
                self.layer2_detectors.append(resource_leak_detector)
                logger.info("Layer 2: Resource leak detector enabled")

        if self.layer2_detectors:
            logger.info(f"Layer 2 enabled with {len(self.layer2_detectors)} detectors")

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
    ) -> DetectionResult:
        """
        执行完整的 bug 检测流程

        流程：
        1. Layer 1: 静态分析 (mypy + bandit)
        2. Layer 2: 符号分析 (资源泄漏等)
        3. Layer 3: LLM 检测
        4. Layer 4: 交叉验证 (如果启用)
        5. 合并结果（去重 + 标记来源）

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
            DetectionResult: 检测结果（success 字段标记是否成功）
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
                    complexity_score=0,  # 暂时不计算复杂度
                    relative_file_path=file_path  # 传递相对路径用于报告
                )
            except Exception as e:
                logger.warning(f"Layer 1 analysis failed for {function.name}: {e}")

        # Step 2: Layer 2 符号分析
        layer2_result = None
        layer2_bugs = []
        if self.layer2_detectors:
            try:
                # 从函数代码重新解析 AST 节点
                import ast
                try:
                    func_tree = ast.parse(function.code)
                    if func_tree.body and isinstance(func_tree.body[0], ast.FunctionDef):
                        func_node = func_tree.body[0]
                    else:
                        raise ValueError("Failed to parse function AST")
                except Exception as parse_error:
                    logger.warning(f"Failed to parse function {function.name} for Layer 2: {parse_error}")
                    func_node = None

                if func_node:
                    # 合并所有 Layer 2 检测器的结果
                    all_confirmed_bugs = []
                    all_suspicious_findings = []

                    for detector in self.layer2_detectors:
                        result = detector.detect(
                            func_node,
                            context={'file_path': file_path}
                        )
                        all_confirmed_bugs.extend(result.confirmed_bugs)
                        all_suspicious_findings.extend(result.suspicious_findings)

                    # 创建合并的 Layer2Result
                    from pyscan.layer2 import Layer2Result
                    layer2_result = Layer2Result(
                        confirmed_bugs=all_confirmed_bugs,
                        suspicious_findings=all_suspicious_findings
                    )

                    # 转换 confirmed_bugs 为 BugReport
                    for confirmed_bug in all_confirmed_bugs:
                        bug_report = self._convert_layer2_bug_to_report(
                            confirmed_bug,
                            function,
                            file_path,
                            function_start_line
                        )
                        layer2_bugs.append(bug_report)

                    logger.debug(
                        f"Layer 2 detected {len(all_confirmed_bugs)} confirmed bugs, "
                        f"{len(all_suspicious_findings)} suspicious findings for {function.name}"
                    )
            except Exception as e:
                logger.warning(f"Layer 2 analysis failed for {function.name}: {e}")

        # Step 3: Layer 3 LLM 检测
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

        if not llm_result["success"]:
            # LLM 检测失败
            return DetectionResult(
                success=False,
                error=llm_result.get("error", "Unknown error"),
                prompt=llm_result.get("prompt", ""),
                raw_response=llm_result.get("raw_response", "")
            )

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

        # Step 5: 合并和去重
        merged_reports, dedup_count = self._merge_and_deduplicate(
            llm_bugs,
            layer4_bugs,
            layer2_bugs,
            bug_id_start
        )

        return DetectionResult(
            reports=merged_reports,
            prompt=prompt,
            raw_response=raw_response,
            layer1_facts=static_facts,
            layer2_result=layer2_result,
            layer3_bug_count=len(llm_bugs),
            layer4_bug_count=len(layer4_bugs),
            deduped_count=dedup_count
        )

    def _merge_and_deduplicate(
        self,
        llm_bugs: List[BugReport],
        layer4_bugs: List[BugReport],
        layer2_bugs: List[BugReport],
        bug_id_start: int
    ) -> tuple[List[BugReport], int]:
        """
        合并 LLM bugs、Layer 2 bugs 和 Layer 4 bugs，去重并标记来源

        去重规则（选项B - 宽松匹配）：
        - 位置相近（±2行）AND (类型完全相同 OR 都是类型相关)
        - 优先级：Layer 4 > Layer 2 > LLM
        - 如果匹配，使用高优先级的信息
        - 保留低优先级的原始信息在 evidence 中

        来源标记：
        evidence = {
            'llm_detected': True/False,
            'layer2_detected': True/False,
            'mypy_detected': True/False,
            'detection_source': 'llm' | 'layer2' | 'layer4' | 'both',
            'llm_description': <original LLM description>  # 如果重复
        }

        Args:
            llm_bugs: LLM 检测到的 bugs
            layer4_bugs: Layer 4 验证的 bugs
            layer2_bugs: Layer 2 检测到的 bugs
            bug_id_start: Bug ID 起始编号

        Returns:
            (merged_reports, dedup_count): 合并后的报告列表和去重数量
        """
        # 标记 LLM bugs 的来源
        for bug in llm_bugs:
            if not bug.evidence:
                bug.evidence = {}
            bug.evidence['llm_detected'] = True
            bug.evidence['layer2_detected'] = False
            bug.evidence['mypy_detected'] = False
            bug.evidence['detection_source'] = 'llm'

        # 标记 Layer 2 bugs 的来源
        for bug in layer2_bugs:
            if not bug.evidence:
                bug.evidence = {}
            bug.evidence['llm_detected'] = False
            bug.evidence['layer2_detected'] = True
            bug.evidence['mypy_detected'] = False
            bug.evidence['detection_source'] = 'layer2'

        # 检查是否启用去重
        layer4_config = getattr(self.config, 'layer4', {})
        if isinstance(layer4_config, dict):
            enable_dedup = layer4_config.get('enable_deduplication', True)
        else:
            enable_dedup = getattr(layer4_config, 'enable_deduplication', True)

        if not enable_dedup:
            # 不去重，直接合并
            all_bugs = layer2_bugs + llm_bugs + layer4_bugs
            # 重新分配 bug_id
            for i, bug in enumerate(all_bugs):
                bug.bug_id = f"BUG_{bug_id_start + i:04d}"
            return all_bugs, 0

        # 去重逻辑
        merged = []
        dedup_count = 0
        used_layer4_indices = set()
        used_layer2_indices = set()

        # 遍历 LLM bugs，检查是否与 Layer 4 或 Layer 2 bugs 重复
        for llm_bug in llm_bugs:
            matched = False

            # 优先与 Layer 4 匹配
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
                # 再与 Layer 2 匹配
                for i, layer2_bug in enumerate(layer2_bugs):
                    if i in used_layer2_indices:
                        continue

                    if self._is_duplicate(llm_bug, layer2_bug):
                        # 重复，使用 Layer 2 的信息（优先 Layer 2）
                        dedup_count += 1
                        used_layer2_indices.add(i)
                        matched = True

                        # 保留 LLM 的原始描述在 evidence 中
                        layer2_bug.evidence['llm_description'] = llm_bug.description
                        layer2_bug.evidence['llm_detected'] = True
                        layer2_bug.evidence['detection_source'] = 'both'

                        merged.append(layer2_bug)
                        break

            if not matched:
                # LLM bug 没有匹配，直接添加，标记来源
                if 'detection_source' not in llm_bug.evidence:
                    llm_bug.evidence['detection_source'] = 'llm'
                merged.append(llm_bug)

        # 添加未匹配的 Layer 2 bugs
        for i, layer2_bug in enumerate(layer2_bugs):
            if i not in used_layer2_indices:
                merged.append(layer2_bug)

        # 添加未匹配的 Layer 4 bugs
        for i, layer4_bug in enumerate(layer4_bugs):
            if i not in used_layer4_indices:
                merged.append(layer4_bug)

        # 重新分配 bug_id（保持连续）
        for i, bug in enumerate(merged):
            bug.bug_id = f"BUG_{bug_id_start + i:04d}"

        logger.debug(
            f"Merged {len(layer2_bugs)} Layer2 bugs + {len(llm_bugs)} LLM bugs + "
            f"{len(layer4_bugs)} Layer4 bugs = {len(merged)} bugs (deduped {dedup_count})"
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

    def _convert_layer2_bug_to_report(
        self,
        confirmed_bug,
        function: FunctionInfo,
        file_path: str,
        function_start_line: int
    ) -> BugReport:
        """
        将 Layer 2 的 ConfirmedBug 转换为 BugReport

        Args:
            confirmed_bug: Layer 2 的 ConfirmedBug 对象
            function: 函数信息
            file_path: 文件路径
            function_start_line: 函数起始行号

        Returns:
            BugReport 对象
        """
        from pyscan.bug_detector import BugReport

        # 从 location 中提取位置信息
        location = confirmed_bug.location

        # Layer 2 的行号是相对于重新解析的函数代码的（从 1 开始）
        # 需要转换为文件的绝对行号
        # 公式：绝对行号 = function.lineno + 相对行号 - 1
        # 例如：function.lineno=9, 相对行号=3 => 绝对行号=9+3-1=11
        relative_start_line = location.get('start_line', 1)
        relative_end_line = location.get('end_line', relative_start_line)

        start_line = function.lineno + relative_start_line - 1
        end_line = function.lineno + relative_end_line - 1
        start_col = location.get('start_col', 0)
        end_col = location.get('end_col', 0)

        # 创建 BugReport
        return BugReport(
            bug_id="",  # 将在合并时重新分配
            function_name=function.name,
            file_path=file_path,
            function_start_line=function.lineno,
            function_end_line=function.end_lineno,
            function_start_col=function.col_offset,
            function_end_col=function.end_col_offset,
            severity=confirmed_bug.severity,
            bug_type=confirmed_bug.type,
            description=confirmed_bug.description,
            location=f"第 {start_line} 行",
            start_line=start_line,
            end_line=end_line,
            start_col=start_col,
            end_col=end_col,
            suggestion=confirmed_bug.suggestion,
            confidence=confirmed_bug.confidence,
            evidence=confirmed_bug.evidence.copy() if confirmed_bug.evidence else {}
        )
