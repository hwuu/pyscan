"""CrossValidator 单元测试"""

import pytest
from pyscan.layer4.cross_validator import CrossValidator
from pyscan.layer1.base import StaticFacts, StaticIssue
from pyscan.bug_detector import BugReport


class TestCrossValidator:
    """CrossValidator 测试类"""

    def setup_method(self):
        """测试前准备"""
        self.validator = CrossValidator()

    def test_validate_type_safety_with_llm_confirmation(self):
        """测试 mypy error + LLM 确认 = 高置信度（0.95）"""
        # 准备 mypy 发现的类型错误
        static_facts = StaticFacts(
            file_path="test.py",
            function_name="test_func",
            function_start_line=1
        )
        static_facts.type_issues = [
            StaticIssue(
                tool='mypy',
                type='type-error',
                severity='error',
                message="Incompatible types in assignment",
                file_path="test.py",
                line=10,
                column=5,
                code='assignment'
            )
        ]

        # 准备 LLM 也发现了同位置的类型问题
        llm_bugs = [
            BugReport(
                bug_id="BUG_0001",
                function_name="test_func",
                file_path="test.py",
                function_start_line=1,
                function_end_line=20,
                bug_type="TypeError",
                description="Type mismatch in assignment",
                start_line=10,  # 相对行号
                end_line=10
            )
        ]

        # 执行验证
        verified_bugs = self.validator.validate_type_safety(static_facts, llm_bugs)

        # 断言
        assert len(verified_bugs) == 1
        bug = verified_bugs[0]
        assert bug.bug_type == "TypeError"
        assert bug.confidence == 0.95  # LLM 确认，高置信度
        assert bug.evidence['mypy_detected'] is True
        assert bug.evidence['llm_confirmed'] is True
        assert bug.start_line == 10  # 相对行号

    def test_validate_type_safety_without_llm_confirmation(self):
        """测试 mypy error + LLM 未确认 = 中等置信度（0.75）"""
        # 准备 mypy 发现的类型错误
        static_facts = StaticFacts(
            file_path="test.py",
            function_name="test_func",
            function_start_line=1
        )
        static_facts.type_issues = [
            StaticIssue(
                tool='mypy',
                type='arg-type',
                severity='error',
                message="Argument 1 has incompatible type",
                file_path="test.py",
                line=15,
                column=8,
                code='arg-type'
            )
        ]

        # LLM 没有发现同位置的问题
        llm_bugs = []

        # 执行验证
        verified_bugs = self.validator.validate_type_safety(static_facts, llm_bugs)

        # 断言
        assert len(verified_bugs) == 1
        bug = verified_bugs[0]
        assert bug.bug_type == "TypeError"
        assert bug.confidence == 0.75  # LLM 未确认，中等置信度
        assert bug.evidence['mypy_detected'] is True
        assert bug.evidence['llm_confirmed'] is False

    def test_validate_type_safety_llm_position_tolerance(self):
        """测试 LLM 位置匹配容忍度（±2 行）"""
        # mypy 在第 10 行发现问题
        static_facts = StaticFacts(
            file_path="test.py",
            function_name="test_func",
            function_start_line=1
        )
        static_facts.type_issues = [
            StaticIssue(
                tool='mypy',
                type='type-error',
                severity='error',
                message="Type error",
                file_path="test.py",
                line=10,
                column=5,
                code='type-error'
            )
        ]

        # LLM 在第 12 行发现（绝对行号 1+12-1=12，相差 2 行，应该匹配）
        llm_bugs = [
            BugReport(
                bug_id="BUG_0001",
                function_name="test_func",
                file_path="test.py",
                function_start_line=1,
                function_end_line=20,
                bug_type="TypeError",
                description="Type issue",
                start_line=12,  # 相对行号
                end_line=12
            )
        ]

        verified_bugs = self.validator.validate_type_safety(static_facts, llm_bugs)

        # 应该匹配上
        assert len(verified_bugs) == 1
        assert verified_bugs[0].confidence == 0.95

    def test_validate_type_safety_llm_keyword_match(self):
        """测试 LLM 类型关键字匹配"""
        static_facts = StaticFacts(
            file_path="test.py",
            function_name="test_func",
            function_start_line=1
        )
        static_facts.type_issues = [
            StaticIssue(
                tool='mypy',
                type='type-error',
                severity='error',
                message="Type mismatch",
                file_path="test.py",
                line=10,
                column=5,
                code='type-error'
            )
        ]

        # LLM bug 的 bug_type 字段包含 'type'
        llm_bugs_type_field = [
            BugReport(
                bug_id="BUG_0001",
                function_name="test_func",
                file_path="test.py",
                function_start_line=1,
                function_end_line=20,
                bug_type="TypeError",  # bug_type 字段包含 'type'
                description="Some issue",
                start_line=10,  # 相对行号
                end_line=10
            )
        ]

        verified_bugs = self.validator.validate_type_safety(static_facts, llm_bugs_type_field)
        assert len(verified_bugs) == 1
        assert verified_bugs[0].confidence == 0.95

        # LLM bug 的 description 字段包含 'type'
        llm_bugs_desc_field = [
            BugReport(
                bug_id="BUG_0002",
                function_name="test_func",
                file_path="test.py",
                function_start_line=1,
                function_end_line=20,
                bug_type="SomeError",
                description="This is a type mismatch issue",  # description 包含 'type'
                start_line=10,
                end_line=10
            )
        ]

        verified_bugs = self.validator.validate_type_safety(static_facts, llm_bugs_desc_field)
        assert len(verified_bugs) == 1
        assert verified_bugs[0].confidence == 0.95

    def test_validate_type_safety_no_errors(self):
        """测试没有类型错误的情况"""
        static_facts = StaticFacts(
            file_path="test.py",
            function_name="test_func",
            function_start_line=1
        )
        static_facts.type_issues = []

        llm_bugs = []

        verified_bugs = self.validator.validate_type_safety(static_facts, llm_bugs)

        assert len(verified_bugs) == 0

    def test_validate_type_safety_only_warnings(self):
        """测试只有 warning 级别的问题（不应报告）"""
        static_facts = StaticFacts(
            file_path="test.py",
            function_name="test_func",
            function_start_line=1
        )
        static_facts.type_issues = [
            StaticIssue(
                tool='mypy',
                type='type-warning',
                severity='warning',  # warning 级别
                message="Possible type issue",
                file_path="test.py",
                line=10,
                column=5,
                code='type-warning'
            )
        ]

        llm_bugs = []

        verified_bugs = self.validator.validate_type_safety(static_facts, llm_bugs)

        # warning 级别不应报告
        assert len(verified_bugs) == 0

    def test_generate_fix_suggestion_incompatible_types(self):
        """测试修复建议生成 - 类型不兼容"""
        issue = StaticIssue(
            tool='mypy',
            type='assignment',
            severity='error',
            message="Incompatible types in assignment (expression has type 'str', variable has type 'int')",
            file_path="test.py",
            line=10,
            column=5,
            code='assignment'
        )

        suggestion = self.validator._generate_fix_suggestion(issue)
        assert "类型注解" in suggestion or "类型" in suggestion

    def test_generate_fix_suggestion_no_attribute(self):
        """测试修复建议生成 - 属性不存在"""
        issue = StaticIssue(
            tool='mypy',
            type='attr-defined',
            severity='error',
            message="'str' object has no attribute 'append'",
            file_path="test.py",
            line=10,
            column=5,
            code='attr-defined'
        )

        suggestion = self.validator._generate_fix_suggestion(issue)
        assert "属性" in suggestion

    def test_generate_fix_suggestion_none(self):
        """测试修复建议生成 - None 相关"""
        issue = StaticIssue(
            tool='mypy',
            type='arg-type',
            severity='error',
            message="Argument 1 to 'len' has incompatible type 'Optional[List[int]]'; expected 'Sized'",
            file_path="test.py",
            line=10,
            column=5,
            code='arg-type'
        )

        suggestion = self.validator._generate_fix_suggestion(issue)
        assert "None" in suggestion or "Optional" in suggestion

    def test_multiple_type_errors(self):
        """测试多个类型错误"""
        static_facts = StaticFacts(
            file_path="test.py",
            function_name="test_func",
            function_start_line=1
        )
        static_facts.type_issues = [
            StaticIssue(
                tool='mypy',
                type='error1',
                severity='error',
                message="Type error 1",
                file_path="test.py",
                line=10,
                column=5,
                code='error1'
            ),
            StaticIssue(
                tool='mypy',
                type='error2',
                severity='error',
                message="Type error 2",
                file_path="test.py",
                line=20,
                column=8,
                code='error2'
            ),
            StaticIssue(
                tool='mypy',
                type='error3',
                severity='error',
                message="Type error 3",
                file_path="test.py",
                line=30,
                column=12,
                code='error3'
            )
        ]

        # LLM 只确认了第一个和第三个
        llm_bugs = [
            BugReport(
                bug_id="BUG_0001",
                function_name="test_func",
                file_path="test.py",
                function_start_line=1,
                function_end_line=50,
                bug_type="TypeError",
                description="Type issue",
                start_line=10,  # 相对行号
                end_line=10
            ),
            BugReport(
                bug_id="BUG_0002",
                function_name="test_func",
                file_path="test.py",
                function_start_line=1,
                function_end_line=50,
                bug_type="TypeError",
                description="Type issue",
                start_line=30,
                end_line=30
            )
        ]

        verified_bugs = self.validator.validate_type_safety(static_facts, llm_bugs)

        # 应该有 3 个 bug（都是 error 级别）
        assert len(verified_bugs) == 3

        # 第一个：LLM 确认，高置信度
        assert verified_bugs[0].start_line == 10
        assert verified_bugs[0].confidence == 0.95

        # 第二个：LLM 未确认，中等置信度
        assert verified_bugs[1].start_line == 20
        assert verified_bugs[1].confidence == 0.75

        # 第三个：LLM 确认，高置信度
        assert verified_bugs[2].start_line == 30
        assert verified_bugs[2].confidence == 0.95
