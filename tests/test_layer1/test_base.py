"""
测试 Layer 1 基础模块
"""

import pytest
from pyscan.layer1.base import StaticIssue, StaticFacts


class TestStaticIssue:
    """测试 StaticIssue 数据结构"""

    def test_create_issue(self):
        """测试创建问题"""
        issue = StaticIssue(
            tool='mypy',
            type='type-error',
            severity='high',
            message='Incompatible types',
            file_path='test.py',
            line=10,
            column=5,
            code='assignment'
        )

        assert issue.tool == 'mypy'
        assert issue.type == 'type-error'
        assert issue.severity == 'high'
        assert issue.message == 'Incompatible types'
        assert issue.file_path == 'test.py'
        assert issue.line == 10
        assert issue.column == 5
        assert issue.code == 'assignment'

    def test_issue_str(self):
        """测试问题的字符串表示"""
        issue = StaticIssue(
            tool='mypy',
            type='type-error',
            severity='high',
            message='Incompatible types',
            file_path='test.py',
            line=10,
            column=5,
            code='assignment'
        )

        str_repr = str(issue)
        assert 'mypy' in str_repr
        assert 'high' in str_repr
        assert 'test.py:10:5' in str_repr
        assert 'Incompatible types' in str_repr


class TestStaticFacts:
    """测试 StaticFacts 数据结构"""

    def test_create_facts(self):
        """测试创建 facts"""
        facts = StaticFacts(
            file_path='test.py',
            function_name='test_func',
            function_start_line=10,
            has_type_annotations=True,
            complexity_score=5
        )

        assert facts.file_path == 'test.py'
        assert facts.function_name == 'test_func'
        assert facts.function_start_line == 10
        assert facts.has_type_annotations is True
        assert facts.complexity_score == 5
        assert len(facts.type_issues) == 0
        assert len(facts.security_issues) == 0

    def test_total_issues(self):
        """测试总问题数计算"""
        facts = StaticFacts(
            file_path='test.py',
            function_name='test_func',
            function_start_line=10
        )

        # 添加问题
        facts.type_issues.append(StaticIssue(
            tool='mypy', type='type-error', severity='high',
            message='Error 1', file_path='test.py', line=11
        ))
        facts.type_issues.append(StaticIssue(
            tool='mypy', type='type-error', severity='medium',
            message='Error 2', file_path='test.py', line=12
        ))
        facts.security_issues.append(StaticIssue(
            tool='bandit', type='security', severity='high',
            message='Security issue', file_path='test.py', line=13
        ))

        assert facts.total_issues() == 3

    def test_high_severity_count(self):
        """测试高严重度问题计数"""
        facts = StaticFacts(
            file_path='test.py',
            function_name='test_func',
            function_start_line=10
        )

        # 添加不同严重度的问题
        facts.type_issues.append(StaticIssue(
            tool='mypy', type='type-error', severity='high',
            message='Error 1', file_path='test.py', line=11
        ))
        facts.type_issues.append(StaticIssue(
            tool='mypy', type='type-error', severity='medium',
            message='Error 2', file_path='test.py', line=12
        ))
        facts.security_issues.append(StaticIssue(
            tool='bandit', type='security', severity='high',
            message='Security issue', file_path='test.py', line=13
        ))
        facts.security_issues.append(StaticIssue(
            tool='bandit', type='security', severity='low',
            message='Low issue', file_path='test.py', line=14
        ))

        assert facts.high_severity_count() == 2

    def test_has_critical_issues(self):
        """测试是否有严重问题"""
        facts = StaticFacts(
            file_path='test.py',
            function_name='test_func',
            function_start_line=10
        )

        # 没有问题
        assert facts.has_critical_issues() is False

        # 添加低严重度问题
        facts.type_issues.append(StaticIssue(
            tool='mypy', type='type-error', severity='low',
            message='Error', file_path='test.py', line=11
        ))
        assert facts.has_critical_issues() is False

        # 添加高严重度问题
        facts.security_issues.append(StaticIssue(
            tool='bandit', type='security', severity='high',
            message='Security issue', file_path='test.py', line=13
        ))
        assert facts.has_critical_issues() is True

    def test_facts_str(self):
        """测试 facts 的字符串表示"""
        facts = StaticFacts(
            file_path='test.py',
            function_name='test_func',
            function_start_line=10
        )
        facts.type_issues.append(StaticIssue(
            tool='mypy', type='type-error', severity='high',
            message='Error', file_path='test.py', line=11
        ))

        str_repr = str(facts)
        assert 'test_func' in str_repr
        assert 'test.py:10' in str_repr
        assert '1 issues' in str_repr
