"""
资源泄漏检测器

检测以下资源管理问题：
- 文件未关闭（open/close）
- 锁未释放（acquire/release）
- 连接未关闭（connect/disconnect, connection/close）
- 其他资源未释放
"""

import ast
from typing import Dict, Any, List, Set, Tuple, Optional

from pyscan.layer2.detectors.base import BaseDetector
from pyscan.layer2 import Layer2Result
from pyscan.layer2.cfg_builder import CFGBuilder, ControlFlowGraph, BasicBlock


class ResourceLeakDetector(BaseDetector):
    """资源泄漏检测器

    检测资源申请后未在所有路径上释放的情况。
    """

    # 资源对（申请方法 -> 释放方法）
    RESOURCE_PAIRS = {
        'open': 'close',
        'acquire': 'release',
        'lock': 'release',
        'connect': 'close',
        'cursor': 'close',
        '__enter__': '__exit__',  # 上下文管理器
    }

    # 需要释放的资源类型（基于类型名称）
    RESOURCE_TYPES = {
        'file', 'File', 'TextIO', 'BinaryIO',
        'lock', 'Lock', 'RLock', 'Semaphore', 'Condition',
        'connection', 'Connection', 'HTTPConnection', 'HTTPSConnection',
        'socket', 'Socket',
        'cursor', 'Cursor',
        'SMTP', 'SMTP_SSL',
        'ThreadPoolExecutor', 'ProcessPoolExecutor',
    }

    def __init__(self, confidence_threshold: float = 0.9, suspicious_threshold: float = 0.5):
        super().__init__(confidence_threshold, suspicious_threshold)
        self.cfg_builder = CFGBuilder()

    def detect(self, function_node: ast.FunctionDef, context: Dict[str, Any]) -> Layer2Result:
        """
        检测资源泄漏

        Args:
            function_node: 函数 AST 节点
            context: 上下文信息

        Returns:
            Layer2Result
        """
        confirmed_bugs = []
        suspicious_findings = []

        # 构建 CFG
        cfg = self.cfg_builder.build_cfg(function_node)

        # 查找资源申请点
        resource_allocations = self._find_resource_allocations(function_node)

        # 检查每个资源是否在所有路径上都被释放
        for var_name, alloc_info in resource_allocations.items():
            leak_info = self._check_resource_leak(var_name, alloc_info, cfg, function_node, context)

            if leak_info:
                confidence, evidence, missing_paths = leak_info

                if confidence >= self.confidence_threshold:
                    # 高置信度：直接报告为 bug
                    bug = self._create_confirmed_bug(
                        bug_type="资源泄漏",
                        severity="high",
                        confidence=confidence,
                        description=f"资源 '{var_name}' 未在所有路径上释放，可能导致资源泄露。",
                        location=self._get_location(alloc_info['node'], context.get('file_path')),
                        evidence={
                            'variable_name': var_name,
                            'allocation_type': alloc_info['type'],
                            'allocation_method': alloc_info['method'],
                            'missing_release_paths': missing_paths,
                            'cfg_summary': evidence
                        },
                        suggestion=f"使用 'with' 语句管理资源，或确保在所有路径上调用 {alloc_info['release_method']}()"
                    )
                    confirmed_bugs.append(bug)

                elif confidence >= self.suspicious_threshold:
                    # 中置信度：标记为可疑点
                    finding = self._create_suspicious_finding(
                        finding_type="潜在资源泄漏",
                        confidence=confidence,
                        description=f"资源 '{var_name}' 可能未正确释放",
                        location=self._get_location(alloc_info['node'], context.get('file_path')),
                        evidence={
                            'variable_name': var_name,
                            'allocation_type': alloc_info['type'],
                            'missing_release_paths': missing_paths
                        },
                        suggestion=f"检查资源释放逻辑，建议使用 with 语句"
                    )
                    suspicious_findings.append(finding)

        return Layer2Result(
            confirmed_bugs=confirmed_bugs,
            suspicious_findings=suspicious_findings,
            cfg_summary={'blocks': len(cfg.blocks), 'paths': len(cfg.get_all_paths())},
            covered_areas=['资源泄漏']
        )

    def _find_resource_allocations(self, function_node: ast.FunctionDef) -> Dict[str, Dict[str, Any]]:
        """
        查找函数中的资源申请点

        Returns:
            {变量名: {type, method, node, release_method, parent_resource}}
        """
        allocations = {}

        class AllocationVisitor(ast.NodeVisitor):
            def __init__(self, detector):
                self.detector = detector
                self.allocations = {}

            def visit_Assign(self, node):
                """检查赋值语句"""
                # 检查是否是资源申请
                if isinstance(node.value, ast.Call):
                    alloc_info = self.detector._is_resource_allocation(node.value)
                    if alloc_info:
                        # 获取变量名
                        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                            var_name = node.targets[0].id
                            self.allocations[var_name] = {
                                **alloc_info,
                                'node': node,
                                'lineno': node.lineno
                            }

                self.generic_visit(node)

            def visit_With(self, node):
                """检查 with 语句（这些资源是正确管理的，不报告）"""
                # with 语句中的资源不需要检查
                # 因为它们会自动调用 __exit__
                self.generic_visit(node)

        visitor = AllocationVisitor(self)
        visitor.visit(function_node)
        return visitor.allocations

    def _is_resource_allocation(self, call_node: ast.Call) -> Optional[Dict[str, Any]]:
        """
        判断是否为资源申请

        Returns:
            None 或 {type, method, release_method, parent_resource}
        """
        # 检查函数调用
        if isinstance(call_node.func, ast.Name):
            method_name = call_node.func.id

            if method_name in self.RESOURCE_PAIRS:
                return {
                    'type': method_name,
                    'method': method_name,
                    'release_method': self.RESOURCE_PAIRS[method_name],
                    'parent_resource': None  # 顶层资源，无父资源
                }

        # 检查方法调用（obj.method()）
        elif isinstance(call_node.func, ast.Attribute):
            method_name = call_node.func.attr

            if method_name in self.RESOURCE_PAIRS:
                # 尝试获取父资源的变量名
                parent_var = None
                if isinstance(call_node.func.value, ast.Name):
                    parent_var = call_node.func.value.id

                return {
                    'type': method_name,
                    'method': method_name,
                    'release_method': self.RESOURCE_PAIRS[method_name],
                    'parent_resource': parent_var  # 记录父资源
                }

        return None

    def _check_resource_leak(
        self,
        var_name: str,
        alloc_info: Dict[str, Any],
        cfg: ControlFlowGraph,
        function_node: ast.FunctionDef,
        context: Dict[str, Any]
    ) -> Optional[Tuple[float, Dict[str, Any], List[str]]]:
        """
        检查资源是否在所有路径上都被释放

        Returns:
            None 或 (confidence, evidence, missing_paths)
        """
        release_method = alloc_info['release_method']
        parent_resource = alloc_info.get('parent_resource')

        # 如果是派生资源，检查父资源是否被正确管理
        if parent_resource:
            # 检查父资源是否在 with 语句中或是否被正确释放
            if self._is_parent_resource_managed(parent_resource, cfg, function_node):
                # 父资源被正确管理，派生资源也被隐式管理，不报告
                return None

        # 查找所有路径
        all_paths = cfg.get_all_paths(max_depth=20)

        missing_release_paths = []
        total_paths = len(all_paths)

        for path in all_paths:
            # 检查这条路径是否释放了资源
            if not self._path_releases_resource(path, var_name, release_method):
                # 记录未释放的路径
                path_desc = " → ".join([f"Block{b.id}" for b in path])
                missing_release_paths.append(path_desc)

        if missing_release_paths:
            # 计算置信度
            leak_ratio = len(missing_release_paths) / total_paths
            confidence = min(0.9, 0.5 + leak_ratio * 0.4)  # 0.5-0.9

            evidence = {
                'total_paths': total_paths,
                'missing_release_paths_count': len(missing_release_paths),
                'leak_ratio': leak_ratio
            }

            return (confidence, evidence, missing_release_paths)

        return None

    def _path_releases_resource(
        self,
        path: List[BasicBlock],
        var_name: str,
        release_method: str
    ) -> bool:
        """
        检查路径是否释放了资源

        Args:
            path: 基本块路径
            var_name: 资源变量名
            release_method: 释放方法名

        Returns:
            True 如果路径上有释放资源的调用
        """
        for block in path:
            for stmt in block.statements:
                if self._is_resource_release(stmt, var_name, release_method):
                    return True

        return False

    def _is_resource_release(
        self,
        stmt: ast.stmt,
        var_name: str,
        release_method: str
    ) -> bool:
        """
        判断语句是否释放了资源

        Args:
            stmt: AST 语句
            var_name: 资源变量名
            release_method: 释放方法名（如 'close'）

        Returns:
            True 如果语句释放了资源
        """
        # 检查表达式语句
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            call = stmt.value

            # 检查是否是 var_name.release_method() 调用
            if isinstance(call.func, ast.Attribute):
                if call.func.attr == release_method:
                    # 检查对象是否是目标变量
                    if isinstance(call.func.value, ast.Name):
                        if call.func.value.id == var_name:
                            return True

        return False

    def _is_parent_resource_managed(
        self,
        parent_var: str,
        cfg: ControlFlowGraph,
        function_node: ast.FunctionDef
    ) -> bool:
        """
        检查父资源是否被正确管理

        Args:
            parent_var: 父资源变量名
            cfg: 控制流图
            function_node: 函数节点

        Returns:
            True 如果父资源被正确管理（在 with 语句中或在所有路径上被释放）
        """
        # 检查父资源是否在 with 语句中
        if self._is_resource_in_with_statement(parent_var, function_node):
            return True

        # 检查父资源是否在所有路径上被释放
        # 查找父资源的释放方法（通常是 'close'）
        release_method = 'close'  # 大多数资源使用 close

        all_paths = cfg.get_all_paths(max_depth=20)
        for path in all_paths:
            if not self._path_releases_resource(path, parent_var, release_method):
                # 至少有一条路径未释放父资源
                return False

        # 所有路径都释放了父资源
        return True

    def _is_resource_in_with_statement(
        self,
        var_name: str,
        function_node: ast.FunctionDef
    ) -> bool:
        """
        检查资源是否在 with 语句中创建

        Args:
            var_name: 资源变量名
            function_node: 函数节点

        Returns:
            True 如果资源在 with 语句中创建
        """
        class WithVisitor(ast.NodeVisitor):
            def __init__(self):
                self.in_with = False
                self.with_vars = set()

            def visit_With(self, node):
                # 检查 with 语句的上下文项
                for item in node.items:
                    if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                        self.with_vars.add(item.optional_vars.id)
                self.generic_visit(node)

        visitor = WithVisitor()
        visitor.visit(function_node)
        return var_name in visitor.with_vars
