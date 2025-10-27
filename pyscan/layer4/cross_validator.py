"""
Layer 4 交叉验证引擎

负责验证和融合来自 Layer 1（静态工具）和 Layer 3（LLM）的分析结果。
"""

import uuid
from typing import List, Optional
from pyscan.layer1.base import StaticFacts, StaticIssue
from pyscan.bug_detector import BugReport


class CrossValidator:
    """Layer 1 (工具) + Layer 3 (LLM) 交叉验证引擎"""

    def validate_type_safety(
        self,
        static_facts: StaticFacts,
        llm_bugs: List[BugReport]
    ) -> List[BugReport]:
        """
        验证类型安全问题

        策略：
        1. mypy 发现 error 级别 + LLM 确认 = 高置信度（0.95）
        2. mypy 发现 error 级别 + LLM 未提及 = 中等置信度（0.75）
        3. mypy 发现 note/warning = 低置信度（0.5），需 LLM 确认

        Args:
            static_facts: Layer 1 收集的静态分析事实
            llm_bugs: Layer 3 LLM 检测到的 bugs

        Returns:
            验证后的类型安全 bug 列表
        """
        verified_bugs = []

        # 处理 mypy type issues
        for issue in static_facts.type_issues:
            # mypy 的 error 会被映射为 severity='high'
            if issue.severity in ['error', 'high']:
                # 检查 LLM 是否确认
                llm_confirmed = self._check_llm_confirmation(issue, llm_bugs)

                # 根据确认情况设置置信度
                confidence = 0.95 if llm_confirmed else 0.75

                # 如果置信度足够，直接报告
                if confidence >= 0.7:
                    verified_bugs.append(BugReport(
                        bug_id=self._generate_bug_id(),
                        function_name=static_facts.function_name,
                        file_path=static_facts.file_path,
                        function_start_line=static_facts.function_start_line,
                        function_end_line=static_facts.function_start_line,  # 暂时使用相同值
                        bug_type="TypeError",
                        severity="high",
                        description=issue.message,
                        location=f"行 {issue.line}",
                        start_line=issue.line,  # 直接使用绝对行号
                        end_line=issue.line,  # 直接使用绝对行号
                        start_col=issue.column if issue.column else 0,
                        end_col=issue.column if issue.column else 0,
                        suggestion=self._generate_fix_suggestion(issue),
                        confidence=confidence,
                        evidence={
                            'mypy_detected': True,
                            'llm_confirmed': llm_confirmed,
                            'tool': 'mypy',
                            'detection_source': 'layer4'
                        }
                    ))

        return verified_bugs

    def _check_llm_confirmation(
        self,
        mypy_issue: StaticIssue,
        llm_bugs: List[BugReport]
    ) -> bool:
        """检查 LLM 是否确认了 mypy 发现的问题"""
        for bug in llm_bugs:
            # 位置匹配（允许 ±2 行误差）
            # bug.start_line 已经是绝对行号，直接比较
            if abs(bug.start_line - mypy_issue.line) <= 2:
                # 类型检查关键字匹配
                if 'type' in bug.bug_type.lower() or 'type' in bug.description.lower():
                    return True
        return False

    def _generate_fix_suggestion(self, issue: StaticIssue) -> str:
        """基于 mypy 错误信息生成修复建议"""
        message = issue.message.lower()

        if 'incompatible types' in message:
            return "检查类型注解是否正确，确保赋值类型与声明一致"
        elif 'has no attribute' in message:
            return "检查对象类型，确保访问的属性存在"
        elif 'none' in message or 'optional' in message:
            return "添加 None 检查或使用 Optional 类型注解"
        else:
            return "修复类型不匹配问题"

    def _generate_bug_id(self) -> str:
        """生成唯一的 bug ID"""
        return f"TYPE_{uuid.uuid4().hex[:8]}"
