"""
控制流图（CFG）构建器

用于分析函数的控制流，支持：
- 基本块划分
- 分支处理（if/else）
- 循环处理（while/for）
- 异常处理（try/except/finally）
"""

import ast
from typing import List, Set, Optional, Dict, Any
from enum import Enum


class BlockType(Enum):
    """基本块类型"""
    ENTRY = "entry"  # 入口块
    EXIT = "exit"  # 出口块
    NORMAL = "normal"  # 普通块
    BRANCH = "branch"  # 分支块
    LOOP = "loop"  # 循环块
    EXCEPTION = "exception"  # 异常处理块


class BasicBlock:
    """基本块

    基本块是控制流图的基本单元，包含一系列顺序执行的语句。
    """

    _id_counter = 0  # 全局计数器

    def __init__(self, block_type: BlockType = BlockType.NORMAL):
        """
        初始化基本块

        Args:
            block_type: 块类型
        """
        self.id = BasicBlock._id_counter
        BasicBlock._id_counter += 1

        self.type = block_type
        self.statements: List[ast.stmt] = []  # AST 语句列表
        self.successors: List['BasicBlock'] = []  # 后继基本块
        self.predecessors: List['BasicBlock'] = []  # 前驱基本块

        # 额外信息
        self.metadata: Dict[str, Any] = {}  # 元数据（如循环条件、分支条件等）

    def add_statement(self, stmt: ast.stmt):
        """添加语句到基本块"""
        self.statements.append(stmt)

    def add_successor(self, block: 'BasicBlock'):
        """添加后继块"""
        if block not in self.successors:
            self.successors.append(block)
            block.predecessors.append(self)

    def remove_successor(self, block: 'BasicBlock'):
        """移除后继块"""
        if block in self.successors:
            self.successors.remove(block)
            block.predecessors.remove(self)

    def is_entry(self) -> bool:
        """是否为入口块"""
        return self.type == BlockType.ENTRY

    def is_exit(self) -> bool:
        """是否为出口块"""
        return self.type == BlockType.EXIT

    def __repr__(self):
        return f"Block({self.id}, type={self.type.value}, stmts={len(self.statements)})"


class ControlFlowGraph:
    """控制流图（CFG）"""

    def __init__(self, function_node: ast.FunctionDef):
        """
        初始化 CFG

        Args:
            function_node: 函数 AST 节点
        """
        self.function_node = function_node
        self.entry_block = BasicBlock(BlockType.ENTRY)
        self.exit_block = BasicBlock(BlockType.EXIT)
        self.blocks: List[BasicBlock] = [self.entry_block, self.exit_block]

    def add_block(self, block: BasicBlock):
        """添加基本块"""
        if block not in self.blocks:
            self.blocks.append(block)

    def get_all_paths(self, max_depth: int = 10) -> List[List[BasicBlock]]:
        """
        获取从入口到出口的所有路径

        Args:
            max_depth: 最大路径深度（防止无限循环）

        Returns:
            路径列表，每条路径是基本块列表
        """
        paths = []
        visited = set()

        def dfs(block: BasicBlock, path: List[BasicBlock], depth: int):
            if depth > max_depth:
                return

            if block in visited and len(path) > 1:
                # 检测到循环，停止探索
                return

            path.append(block)

            if block.is_exit():
                paths.append(path[:])
            else:
                visited.add(block)
                for successor in block.successors:
                    dfs(successor, path, depth + 1)
                visited.discard(block)

            path.pop()

        dfs(self.entry_block, [], 0)
        return paths

    def get_reachable_blocks(self) -> Set[BasicBlock]:
        """获取从入口可达的所有基本块"""
        reachable = set()
        queue = [self.entry_block]

        while queue:
            block = queue.pop(0)
            if block in reachable:
                continue

            reachable.add(block)
            queue.extend(block.successors)

        return reachable

    def get_unreachable_blocks(self) -> Set[BasicBlock]:
        """获取不可达的基本块"""
        reachable = self.get_reachable_blocks()
        return set(self.blocks) - reachable

    def visualize(self) -> str:
        """
        可视化 CFG（文本格式）

        Returns:
            CFG 的文本表示
        """
        lines = [f"CFG for function: {self.function_node.name}"]
        lines.append(f"Total blocks: {len(self.blocks)}")
        lines.append("")

        for block in self.blocks:
            lines.append(f"{block}")
            lines.append(f"  Successors: {[b.id for b in block.successors]}")
            lines.append(f"  Predecessors: {[b.id for b in block.predecessors]}")
            if block.statements:
                lines.append(f"  Statements: {len(block.statements)}")
                for stmt in block.statements[:3]:  # 最多显示前3条语句
                    lines.append(f"    - {ast.unparse(stmt)[:50]}")
                if len(block.statements) > 3:
                    lines.append(f"    ... ({len(block.statements) - 3} more)")
            lines.append("")

        return "\n".join(lines)

    def __repr__(self):
        return f"CFG(blocks={len(self.blocks)}, entry={self.entry_block.id}, exit={self.exit_block.id})"


class CFGBuilder:
    """CFG 构建器"""

    def __init__(self, max_path_depth: int = 10):
        """
        初始化构建器

        Args:
            max_path_depth: 路径探索最大深度
        """
        self.max_path_depth = max_path_depth

    def build_cfg(self, function_node: ast.FunctionDef) -> ControlFlowGraph:
        """
        构建函数的控制流图

        Args:
            function_node: 函数 AST 节点

        Returns:
            ControlFlowGraph 实例
        """
        cfg = ControlFlowGraph(function_node)

        # 重置基本块 ID 计数器
        BasicBlock._id_counter = 0

        # 重新创建入口和出口块
        cfg.entry_block = BasicBlock(BlockType.ENTRY)
        cfg.exit_block = BasicBlock(BlockType.EXIT)
        cfg.blocks = [cfg.entry_block, cfg.exit_block]

        # 构建函数体的 CFG
        current_block = cfg.entry_block
        for stmt in function_node.body:
            current_block = self._process_statement(stmt, current_block, cfg)

        # 连接最后一个块到出口
        if current_block and not current_block.is_exit():
            current_block.add_successor(cfg.exit_block)

        return cfg

    def _process_statement(
        self,
        stmt: ast.stmt,
        current_block: BasicBlock,
        cfg: ControlFlowGraph
    ) -> BasicBlock:
        """
        处理单个语句

        Args:
            stmt: AST 语句
            current_block: 当前基本块
            cfg: CFG 实例

        Returns:
            处理后的当前基本块
        """
        # 处理不同类型的语句
        if isinstance(stmt, ast.If):
            return self._process_if(stmt, current_block, cfg)
        elif isinstance(stmt, (ast.While, ast.For)):
            return self._process_loop(stmt, current_block, cfg)
        elif isinstance(stmt, ast.Try):
            return self._process_try(stmt, current_block, cfg)
        elif isinstance(stmt, (ast.Return, ast.Raise)):
            # Return/Raise 语句结束当前块
            current_block.add_statement(stmt)
            current_block.add_successor(cfg.exit_block)
            # 创建新块（可能不可达）
            new_block = BasicBlock(BlockType.NORMAL)
            cfg.add_block(new_block)
            return new_block
        elif isinstance(stmt, (ast.Break, ast.Continue)):
            # Break/Continue 的处理需要循环上下文
            # 这里简化处理：添加到当前块
            current_block.add_statement(stmt)
            return current_block
        else:
            # 普通语句：添加到当前块
            current_block.add_statement(stmt)
            return current_block

    def _process_if(
        self,
        if_stmt: ast.If,
        current_block: BasicBlock,
        cfg: ControlFlowGraph
    ) -> BasicBlock:
        """处理 if 语句"""
        # 创建分支块
        branch_block = BasicBlock(BlockType.BRANCH)
        branch_block.metadata['condition'] = if_stmt.test
        cfg.add_block(branch_block)
        current_block.add_successor(branch_block)

        # 创建汇聚块
        merge_block = BasicBlock(BlockType.NORMAL)
        cfg.add_block(merge_block)

        # 处理 if 分支
        if_body_block = BasicBlock(BlockType.NORMAL)
        cfg.add_block(if_body_block)
        branch_block.add_successor(if_body_block)

        current = if_body_block
        for stmt in if_stmt.body:
            current = self._process_statement(stmt, current, cfg)
        if current and not current.is_exit():
            current.add_successor(merge_block)

        # 处理 else 分支
        if if_stmt.orelse:
            else_body_block = BasicBlock(BlockType.NORMAL)
            cfg.add_block(else_body_block)
            branch_block.add_successor(else_body_block)

            current = else_body_block
            for stmt in if_stmt.orelse:
                current = self._process_statement(stmt, current, cfg)
            if current and not current.is_exit():
                current.add_successor(merge_block)
        else:
            # 没有 else 分支，直接连接到汇聚块
            branch_block.add_successor(merge_block)

        return merge_block

    def _process_loop(
        self,
        loop_stmt: ast.stmt,
        current_block: BasicBlock,
        cfg: ControlFlowGraph
    ) -> BasicBlock:
        """处理循环语句"""
        # 创建循环头块
        loop_header = BasicBlock(BlockType.LOOP)
        if isinstance(loop_stmt, ast.While):
            loop_header.metadata['condition'] = loop_stmt.test
        elif isinstance(loop_stmt, ast.For):
            loop_header.metadata['target'] = loop_stmt.target
            loop_header.metadata['iter'] = loop_stmt.iter
        cfg.add_block(loop_header)
        current_block.add_successor(loop_header)

        # 创建循环体块
        loop_body = BasicBlock(BlockType.NORMAL)
        cfg.add_block(loop_body)
        loop_header.add_successor(loop_body)

        # 处理循环体
        current = loop_body
        for stmt in loop_stmt.body:
            current = self._process_statement(stmt, current, cfg)

        # 循环体结束后回到循环头
        if current and not current.is_exit():
            current.add_successor(loop_header)

        # 创建循环出口块
        exit_block = BasicBlock(BlockType.NORMAL)
        cfg.add_block(exit_block)
        loop_header.add_successor(exit_block)

        # 处理 else 子句（循环正常结束时执行）
        if loop_stmt.orelse:
            else_block = BasicBlock(BlockType.NORMAL)
            cfg.add_block(else_block)
            loop_header.add_successor(else_block)

            current = else_block
            for stmt in loop_stmt.orelse:
                current = self._process_statement(stmt, current, cfg)
            if current and not current.is_exit():
                current.add_successor(exit_block)

        return exit_block

    def _process_try(
        self,
        try_stmt: ast.Try,
        current_block: BasicBlock,
        cfg: ControlFlowGraph
    ) -> BasicBlock:
        """处理 try-except-finally 语句"""
        # 创建汇聚块
        merge_block = BasicBlock(BlockType.NORMAL)
        cfg.add_block(merge_block)

        # 处理 try 块
        try_block = BasicBlock(BlockType.NORMAL)
        cfg.add_block(try_block)
        current_block.add_successor(try_block)

        current = try_block
        for stmt in try_stmt.body:
            current = self._process_statement(stmt, current, cfg)

        # try 块正常结束
        if current and not current.is_exit():
            current.add_successor(merge_block)

        # 处理 except 子句
        for handler in try_stmt.handlers:
            except_block = BasicBlock(BlockType.EXCEPTION)
            except_block.metadata['exception_type'] = handler.type
            cfg.add_block(except_block)
            try_block.add_successor(except_block)  # 从 try 块可能跳转到 except

            current = except_block
            for stmt in handler.body:
                current = self._process_statement(stmt, current, cfg)
            if current and not current.is_exit():
                current.add_successor(merge_block)

        # 处理 finally 子句
        if try_stmt.finalbody:
            finally_block = BasicBlock(BlockType.NORMAL)
            finally_block.metadata['is_finally'] = True
            cfg.add_block(finally_block)

            # finally 在所有路径上都会执行，包括 return 路径
            # 收集所有需要经过 finally 的块
            blocks_to_redirect = []

            # 收集 try 块的所有出口
            for block in cfg.blocks:
                if block.is_exit() or block == merge_block:
                    continue
                # 检查这个块是否在 try/except 范围内且指向 exit 或 merge
                for successor in list(block.successors):
                    if successor == merge_block or successor == cfg.exit_block:
                        # 检查这个块是否在 try_block 之后（简化判断：id > try_block.id）
                        if block.id >= try_block.id:
                            blocks_to_redirect.append((block, successor))

            # 重定向这些边到 finally 块
            for block, original_target in blocks_to_redirect:
                block.remove_successor(original_target)
                block.add_successor(finally_block)

            # 处理 finally 块的语句
            current = finally_block
            for stmt in try_stmt.finalbody:
                current = self._process_statement(stmt, current, cfg)

            # finally 块执行完后，连接到原来的目标
            # 简化处理：连接到 merge_block，或如果 finally 本身有 return 则连接到 exit
            if current and not current.is_exit():
                # 如果有指向 exit 的边，finally 也应该指向 exit
                has_exit_path = any(target == cfg.exit_block for _, target in blocks_to_redirect)
                if has_exit_path:
                    current.add_successor(cfg.exit_block)
                # 总是连接到 merge_block（正常流程）
                current.add_successor(merge_block)

        # 处理 else 子句（try 块正常结束且没有异常时执行）
        if try_stmt.orelse:
            else_block = BasicBlock(BlockType.NORMAL)
            cfg.add_block(else_block)
            try_block.add_successor(else_block)

            current = else_block
            for stmt in try_stmt.orelse:
                current = self._process_statement(stmt, current, cfg)
            if current and not current.is_exit():
                current.add_successor(merge_block)

        return merge_block
