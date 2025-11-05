"""
测试 CFG 构建器
"""

import ast
import pytest
from pyscan.layer2.cfg_builder import CFGBuilder, BasicBlock, ControlFlowGraph, BlockType


class TestBasicBlock:
    """测试基本块"""

    def test_basic_block_init(self):
        """测试基本块初始化"""
        block = BasicBlock(BlockType.NORMAL)
        assert block.type == BlockType.NORMAL
        assert block.statements == []
        assert block.successors == []
        assert block.predecessors == []

    def test_add_statement(self):
        """测试添加语句"""
        block = BasicBlock()
        code = "x = 1"
        stmt = ast.parse(code).body[0]
        block.add_statement(stmt)
        assert len(block.statements) == 1
        assert block.statements[0] == stmt

    def test_add_successor(self):
        """测试添加后继块"""
        block1 = BasicBlock()
        block2 = BasicBlock()
        block1.add_successor(block2)

        assert block2 in block1.successors
        assert block1 in block2.predecessors

    def test_add_successor_idempotent(self):
        """测试添加后继块的幂等性"""
        block1 = BasicBlock()
        block2 = BasicBlock()
        block1.add_successor(block2)
        block1.add_successor(block2)  # 第二次添加

        assert len(block1.successors) == 1
        assert len(block2.predecessors) == 1

    def test_remove_successor(self):
        """测试移除后继块"""
        block1 = BasicBlock()
        block2 = BasicBlock()
        block1.add_successor(block2)
        block1.remove_successor(block2)

        assert block2 not in block1.successors
        assert block1 not in block2.predecessors

    def test_is_entry(self):
        """测试是否为入口块"""
        entry_block = BasicBlock(BlockType.ENTRY)
        normal_block = BasicBlock(BlockType.NORMAL)

        assert entry_block.is_entry()
        assert not normal_block.is_entry()

    def test_is_exit(self):
        """测试是否为出口块"""
        exit_block = BasicBlock(BlockType.EXIT)
        normal_block = BasicBlock(BlockType.NORMAL)

        assert exit_block.is_exit()
        assert not normal_block.is_exit()


class TestControlFlowGraph:
    """测试控制流图"""

    def test_cfg_init(self):
        """测试 CFG 初始化"""
        code = "def foo():\n    pass"
        tree = ast.parse(code)
        func_node = tree.body[0]

        cfg = ControlFlowGraph(func_node)

        assert cfg.function_node == func_node
        assert cfg.entry_block.is_entry()
        assert cfg.exit_block.is_exit()
        assert len(cfg.blocks) == 2

    def test_add_block(self):
        """测试添加基本块"""
        code = "def foo():\n    pass"
        tree = ast.parse(code)
        func_node = tree.body[0]
        cfg = ControlFlowGraph(func_node)

        new_block = BasicBlock()
        cfg.add_block(new_block)

        assert new_block in cfg.blocks
        assert len(cfg.blocks) == 3

    def test_get_reachable_blocks(self):
        """测试获取可达块"""
        code = "def foo():\n    pass"
        tree = ast.parse(code)
        func_node = tree.body[0]
        cfg = ControlFlowGraph(func_node)

        # 添加几个块
        block1 = BasicBlock()
        block2 = BasicBlock()
        block3 = BasicBlock()
        cfg.add_block(block1)
        cfg.add_block(block2)
        cfg.add_block(block3)

        # 构建路径: entry -> block1 -> block2 -> exit
        cfg.entry_block.add_successor(block1)
        block1.add_successor(block2)
        block2.add_successor(cfg.exit_block)
        # block3 不连接到任何块（不可达）

        reachable = cfg.get_reachable_blocks()

        assert cfg.entry_block in reachable
        assert block1 in reachable
        assert block2 in reachable
        assert cfg.exit_block in reachable
        assert block3 not in reachable

    def test_get_unreachable_blocks(self):
        """测试获取不可达块"""
        code = "def foo():\n    pass"
        tree = ast.parse(code)
        func_node = tree.body[0]
        cfg = ControlFlowGraph(func_node)

        block1 = BasicBlock()
        block2 = BasicBlock()
        cfg.add_block(block1)
        cfg.add_block(block2)

        cfg.entry_block.add_successor(block1)
        block1.add_successor(cfg.exit_block)
        # block2 不可达

        unreachable = cfg.get_unreachable_blocks()
        assert block2 in unreachable
        assert len(unreachable) == 1


class TestCFGBuilder:
    """测试 CFG 构建器"""

    def test_build_simple_function(self):
        """测试构建简单函数的 CFG"""
        code = """
def foo():
    x = 1
    y = 2
    return x + y
"""
        tree = ast.parse(code)
        func_node = tree.body[0]

        builder = CFGBuilder()
        cfg = builder.build_cfg(func_node)

        # 应该有: entry -> 普通块 -> exit
        assert len(cfg.blocks) >= 3
        assert cfg.entry_block.is_entry()
        assert cfg.exit_block.is_exit()

    def test_build_if_statement(self):
        """测试构建包含 if 语句的 CFG"""
        code = """
def foo(x):
    if x > 0:
        y = 1
    else:
        y = -1
    return y
"""
        tree = ast.parse(code)
        func_node = tree.body[0]

        builder = CFGBuilder()
        cfg = builder.build_cfg(func_node)

        # 应该有: entry -> branch -> if_body/else_body -> merge -> exit
        assert len(cfg.blocks) >= 6

        # 检查是否有分支块
        branch_blocks = [b for b in cfg.blocks if b.type == BlockType.BRANCH]
        assert len(branch_blocks) >= 1

    def test_build_if_without_else(self):
        """测试构建没有 else 的 if 语句"""
        code = """
def foo(x):
    if x > 0:
        print(x)
    return x
"""
        tree = ast.parse(code)
        func_node = tree.body[0]

        builder = CFGBuilder()
        cfg = builder.build_cfg(func_node)

        # 应该有: entry -> branch -> if_body + direct_path -> merge -> exit
        assert len(cfg.blocks) >= 4

    def test_build_while_loop(self):
        """测试构建 while 循环的 CFG"""
        code = """
def foo():
    i = 0
    while i < 10:
        i += 1
    return i
"""
        tree = ast.parse(code)
        func_node = tree.body[0]

        builder = CFGBuilder()
        cfg = builder.build_cfg(func_node)

        # 应该有: entry -> loop_header -> loop_body -> back_to_header + exit_loop -> exit
        assert len(cfg.blocks) >= 4

        # 检查是否有循环块
        loop_blocks = [b for b in cfg.blocks if b.type == BlockType.LOOP]
        assert len(loop_blocks) >= 1

    def test_build_for_loop(self):
        """测试构建 for 循环的 CFG"""
        code = """
def foo():
    total = 0
    for i in range(10):
        total += i
    return total
"""
        tree = ast.parse(code)
        func_node = tree.body[0]

        builder = CFGBuilder()
        cfg = builder.build_cfg(func_node)

        # 应该有循环块
        loop_blocks = [b for b in cfg.blocks if b.type == BlockType.LOOP]
        assert len(loop_blocks) >= 1

    def test_build_try_except(self):
        """测试构建 try-except 的 CFG"""
        code = """
def foo():
    try:
        x = risky_operation()
    except ValueError:
        x = 0
    return x
"""
        tree = ast.parse(code)
        func_node = tree.body[0]

        builder = CFGBuilder()
        cfg = builder.build_cfg(func_node)

        # 应该有异常处理块
        exception_blocks = [b for b in cfg.blocks if b.type == BlockType.EXCEPTION]
        assert len(exception_blocks) >= 1

    def test_build_try_except_finally(self):
        """测试构建 try-except-finally 的 CFG"""
        code = """
def foo():
    try:
        x = risky_operation()
    except ValueError:
        x = 0
    finally:
        cleanup()
    return x
"""
        tree = ast.parse(code)
        func_node = tree.body[0]

        builder = CFGBuilder()
        cfg = builder.build_cfg(func_node)

        # 检查是否有 finally 块
        finally_blocks = [
            b for b in cfg.blocks
            if b.metadata.get('is_finally', False)
        ]
        assert len(finally_blocks) >= 1

    def test_build_nested_if(self):
        """测试构建嵌套 if 的 CFG"""
        code = """
def foo(x, y):
    if x > 0:
        if y > 0:
            return x + y
        else:
            return x - y
    else:
        return 0
"""
        tree = ast.parse(code)
        func_node = tree.body[0]

        builder = CFGBuilder()
        cfg = builder.build_cfg(func_node)

        # 应该有至少 2 个分支块
        branch_blocks = [b for b in cfg.blocks if b.type == BlockType.BRANCH]
        assert len(branch_blocks) >= 2

    def test_build_return_statement(self):
        """测试 return 语句创建到出口的边"""
        code = """
def foo(x):
    if x > 0:
        return x
    return 0
"""
        tree = ast.parse(code)
        func_node = tree.body[0]

        builder = CFGBuilder()
        cfg = builder.build_cfg(func_node)

        # 检查是否有块连接到出口
        blocks_to_exit = [
            b for b in cfg.blocks
            if cfg.exit_block in b.successors
        ]
        assert len(blocks_to_exit) >= 1

    def test_get_all_paths_simple(self):
        """测试获取简单函数的所有路径"""
        code = """
def foo():
    x = 1
    return x
"""
        tree = ast.parse(code)
        func_node = tree.body[0]

        builder = CFGBuilder()
        cfg = builder.build_cfg(func_node)

        paths = cfg.get_all_paths()
        assert len(paths) >= 1  # 至少有一条路径

        # 每条路径应该从 entry 开始，到 exit 结束
        for path in paths:
            assert path[0].is_entry()
            assert path[-1].is_exit()

    def test_get_all_paths_with_branch(self):
        """测试获取包含分支的所有路径"""
        code = """
def foo(x):
    if x > 0:
        y = 1
    else:
        y = -1
    return y
"""
        tree = ast.parse(code)
        func_node = tree.body[0]

        builder = CFGBuilder()
        cfg = builder.build_cfg(func_node)

        paths = cfg.get_all_paths()
        # 应该有至少 2 条路径（if 和 else）
        assert len(paths) >= 2

    def test_visualize(self):
        """测试 CFG 可视化"""
        code = """
def foo(x):
    if x > 0:
        return x
    return 0
"""
        tree = ast.parse(code)
        func_node = tree.body[0]

        builder = CFGBuilder()
        cfg = builder.build_cfg(func_node)

        visualization = cfg.visualize()
        assert "CFG for function: foo" in visualization
        assert "Total blocks:" in visualization
