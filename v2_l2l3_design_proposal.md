# PyScan Layer 2 + Layer 3 深度分析设计方案

**版本**: v1.0
**日期**: 2025-01-03
**状态**: 设计中

---

## 一、概述

### 1.1 背景

Layer 1（静态分析工具如 mypy、bandit）能检测到基础的类型错误、安全问题，但对于以下深层次问题无能为力：

- **逻辑错误**：算法错误、边界条件处理错误、状态转换错误
- **并发问题**：竞态条件、死锁风险
- **资源管理**：资源未成对释放、泄漏
- **复杂数据流**：跨函数的数据依赖、污点传播
- **隐式约束违反**：函数调用顺序依赖、前置条件未满足

**Layer 2（符号分析）+ Layer 3（LLM 增强）** 的目标是通过**程序分析技术**和**LLM 的语义理解能力**，检测这些深层次问题。

### 1.2 设计目标

1. **检测深层次逻辑错误**：静态工具无法发现的业务逻辑问题
2. **数据流与控制流分析**：追踪变量的来源、传播、使用
3. **上下文感知**：结合调用链路、并发环境、文档约束
4. **可解释性**：提供详细的证据链和修复建议
5. **低误报率**：通过多层验证降低误报

### 1.3 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                         PyScan Layer 2                       │
│                    (符号分析 & 数据流分析)                     │
├─────────────────────────────────────────────────────────────┤
│  1. CFG 构建          │  2. 数据流分析    │  3. 污点分析     │
│  - 控制流图           │  - Reaching Defs  │  - 不可信输入    │
│  - 基本块划分         │  - Def-Use Chain  │  - 危险函数      │
│  - 支配树分析         │  - 活跃变量分析   │  - 传播路径      │
├─────────────────────────────────────────────────────────────┤
│  4. 符号执行          │  5. 约束求解      │  6. 模式匹配     │
│  - 路径探索           │  - SMT Solver     │  - 已知漏洞模式  │
│  - 符号状态           │  - 可行性检查     │  - 反模式检测    │
│  - 路径条件收集       │  - 反例生成       │                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                         PyScan Layer 3                       │
│                      (LLM 增强深度分析)                       │
├─────────────────────────────────────────────────────────────┤
│  输入：Layer 2 分析结果 + 源代码 + 调用上下文                 │
│  输出：确认的 Bug 报告 + 证据链 + 修复建议                    │
├─────────────────────────────────────────────────────────────┤
│  1. 增强型 Prompt     │  2. 结构化推理    │  3. 交叉验证     │
│  - CFG/DFG 可视化     │  - 问题分解       │  - Layer 2 结果  │
│  - 路径条件展示       │  - 逐步推理       │  - 调用链验证    │
│  - 污点传播路径       │  - 证据收集       │  - 文档一致性    │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、Layer 2: 符号分析与数据流分析

### 2.1 核心能力

Layer 2 通过程序分析技术，自动提取代码的结构化信息，为 Layer 3 提供强证据支持。

#### 2.1.1 使用 astroid 的优势

[astroid](https://github.com/pylint-dev/astroid) 是 pylint 的底层库，提供：

1. **增强的 AST**：比 Python 标准库的 `ast` 更强大
2. **类型推断**：可以推断变量、返回值的类型
3. **调用图构建**：追踪函数调用关系
4. **名称解析**：解析变量、函数、类的定义位置
5. **控制流分析**：基础的 CFG 构建能力

**对比 Python `ast` 模块**：

| 功能 | Python `ast` | astroid |
|------|-------------|---------|
| 基础 AST 解析 | ✅ | ✅ |
| 类型推断 | ❌ | ✅ |
| 调用图分析 | ❌ | ✅ |
| 跨文件引用解析 | ❌ | ✅ |
| 控制流图 | ❌ | 部分支持 |

### 2.2 检测能力清单

基于用户提供的分析，Layer 2 需要检测以下问题：

---

### 📋 **类别 1：函数自身逻辑与实现细节**

#### 1.1 状态依赖与共享资源操作

**检测目标**：竞态条件、线程安全问题

**检测方法**：
```python
class RaceConditionDetector:
    def detect(self, function_node):
        """检测竞态条件风险"""
        # 1. 识别共享资源
        shared_resources = self._find_shared_resources(function_node)
        #    - 全局变量
        #    - 类静态变量
        #    - 文件句柄、数据库连接等

        # 2. 检查是否有同步机制
        has_lock = self._check_synchronization(function_node)
        #    - threading.Lock
        #    - with lock:
        #    - @synchronized decorator

        # 3. 检查是否在多线程环境中调用
        is_async = self._is_async_function(function_node)
        has_thread_calls = self._check_thread_usage(function_node)

        if shared_resources and not has_lock and (is_async or has_thread_calls):
            return SuspiciousFinding(
                type="race_condition",
                evidence={
                    "shared_resources": shared_resources,
                    "no_synchronization": True,
                    "concurrent_context": True
                }
            )
```

**astroid 实现**：
```python
def _find_shared_resources(self, node):
    """使用 astroid 查找共享资源"""
    shared = []

    for child in node.nodes_of_class(astroid.Name):
        # 推断变量定义位置
        inferred = safe_infer(child)

        if isinstance(inferred, astroid.Global):
            shared.append({
                "name": child.name,
                "type": "global_variable",
                "line": child.lineno
            })

        elif isinstance(inferred, astroid.ClassDef):
            # 检查是否是类静态变量
            if child.name in inferred.locals:
                shared.append({
                    "name": child.name,
                    "type": "class_variable",
                    "line": child.lineno
                })

    return shared
```

---

#### 1.2 分支覆盖与边界条件

**检测目标**：未覆盖的分支、边界值未处理、无限循环

**检测方法**：
```python
class BranchCoverageAnalyzer:
    def analyze_branches(self, function_node):
        """分析分支覆盖"""
        cfg = self._build_cfg(function_node)

        # 1. 检测不可达代码
        unreachable = self._find_unreachable_blocks(cfg)

        # 2. 检测矛盾条件
        contradictions = self._find_contradictory_conditions(cfg)

        # 3. 检测边界值处理
        boundary_issues = self._check_boundary_handling(function_node)

        return {
            "unreachable_code": unreachable,
            "contradictions": contradictions,
            "boundary_issues": boundary_issues
        }

    def _check_boundary_handling(self, node):
        """检查边界值处理"""
        issues = []

        # 查找可能的除法运算
        for binop in node.nodes_of_class(astroid.BinOp):
            if binop.op == '/':
                # 检查分母是否可能为 0
                denominator = binop.right
                if self._may_be_zero(denominator):
                    issues.append({
                        "type": "division_by_zero",
                        "line": binop.lineno,
                        "denominator": denominator.as_string()
                    })

        return issues
```

**无限循环检测**：
```python
def detect_infinite_loop(self, loop_node):
    """检测潜在的无限循环"""
    # 1. 提取循环条件
    condition = loop_node.test

    # 2. 追踪条件变量的修改
    modified_vars = self._find_modified_vars_in_loop(loop_node)

    # 3. 判断条件变量是否会改变
    condition_vars = self._extract_vars_from_condition(condition)

    # 如果条件变量在循环中未修改，可能是无限循环
    if condition_vars and not any(v in modified_vars for v in condition_vars):
        return SuspiciousFinding(
            type="potential_infinite_loop",
            condition=condition.as_string(),
            unmodified_vars=condition_vars
        )
```

---

#### 1.3 资源申请与释放的成对性

**检测目标**：资源泄漏（文件、锁、连接等未释放）

**检测方法**：
```python
class ResourceLeakDetector:
    # 资源申请/释放函数对
    RESOURCE_PAIRS = {
        'open': 'close',
        'acquire': 'release',
        'lock': 'unlock',
        'connect': 'disconnect',
        'start': 'stop',
    }

    def detect(self, function_node):
        """检测资源泄漏"""
        cfg = self._build_cfg(function_node)

        # 1. 识别资源申请点
        allocations = self._find_resource_allocations(function_node)

        leaks = []
        for alloc in allocations:
            # 2. 检查所有路径是否都有释放
            if not self._all_paths_release(cfg, alloc):
                leaks.append({
                    "resource": alloc['name'],
                    "alloc_line": alloc['line'],
                    "missing_release": True,
                    "paths_without_release": self._find_leak_paths(cfg, alloc)
                })

        return leaks

    def _find_resource_allocations(self, node):
        """查找资源申请"""
        allocations = []

        for assign in node.nodes_of_class(astroid.Assign):
            if isinstance(assign.value, astroid.Call):
                func_name = assign.value.func.as_string()

                # 检查是否是资源申请函数
                if func_name in self.RESOURCE_PAIRS or func_name in ['open', 'socket.socket']:
                    allocations.append({
                        "name": assign.targets[0].as_string(),
                        "type": func_name,
                        "line": assign.lineno,
                        "node": assign
                    })

        return allocations

    def _all_paths_release(self, cfg, allocation):
        """检查所有路径是否释放资源"""
        release_func = self.RESOURCE_PAIRS.get(allocation['type'], 'close')

        # DFS 遍历所有从申请点到出口的路径
        for path in self._enumerate_paths(cfg, allocation['node']):
            has_release = False

            for block in path:
                for stmt in block.statements:
                    if self._is_release_call(stmt, allocation['name'], release_func):
                        has_release = True
                        break

            if not has_release:
                return False

        return True
```

**with 语句检测**：
```python
def _is_in_with_statement(self, node):
    """检查资源是否在 with 语句中使用"""
    parent = node.parent
    while parent:
        if isinstance(parent, astroid.With):
            # 检查 node 是否是 with 的上下文表达式
            for item in parent.items:
                if item[0] == node or self._is_descendant(item[0], node):
                    return True
        parent = parent.parent
    return False
```

---

#### 1.4 递归与循环的终止条件

**检测目标**：无限递归、循环退出条件错误

**检测方法**：
```python
class TerminationAnalyzer:
    def analyze_recursion(self, function_node):
        """分析递归终止条件"""
        # 1. 检测递归调用
        recursive_calls = self._find_recursive_calls(function_node)

        if not recursive_calls:
            return None

        # 2. 查找基准情况（base case）
        base_cases = self._find_base_cases(function_node)

        if not base_cases:
            return SuspiciousFinding(
                type="missing_base_case",
                message="递归函数缺少基准情况"
            )

        # 3. 检查递归参数是否向基准情况收敛
        for call in recursive_calls:
            converges = self._check_convergence(call, base_cases)
            if not converges:
                return SuspiciousFinding(
                    type="non_converging_recursion",
                    call_line=call.lineno,
                    evidence="递归参数未向基准情况收敛"
                )

    def _find_base_cases(self, node):
        """查找基准情况（if 语句中的 return）"""
        base_cases = []

        for if_node in node.nodes_of_class(astroid.If):
            # 检查 if 分支是否直接返回（无递归调用）
            if self._has_return_without_recursion(if_node.body):
                base_cases.append({
                    "condition": if_node.test.as_string(),
                    "line": if_node.lineno
                })

        return base_cases
```

---

### 📋 **类别 2：函数的调用链路与上下文**

#### 2.1 调用者传递的参数来源

**检测目标**：参数可能为 None、非法值

**检测方法**：
```python
class ParameterSourceAnalyzer:
    def analyze_parameter_sources(self, function, callers):
        """分析参数来源"""
        issues = []

        for caller in callers:
            # 1. 获取调用点的参数
            call_args = self._extract_call_arguments(caller)

            for param_name, arg_value in call_args.items():
                # 2. 追踪参数值的来源
                source = self._trace_value_source(arg_value, caller)

                # 3. 检查可能的问题
                if source['may_be_none'] and not self._has_none_check(function, param_name):
                    issues.append({
                        "type": "none_propagation",
                        "param": param_name,
                        "caller": caller['function_name'],
                        "source": source
                    })

        return issues

    def _trace_value_source(self, arg_node, context):
        """追踪参数值的来源"""
        inferred = safe_infer(arg_node)

        source = {
            "type": "unknown",
            "may_be_none": False,
            "source_line": arg_node.lineno
        }

        if isinstance(inferred, astroid.Const):
            if inferred.value is None:
                source['may_be_none'] = True
                source['type'] = "constant_none"

        elif isinstance(inferred, astroid.FunctionDef):
            # 追踪函数返回值
            returns = list(inferred.nodes_of_class(astroid.Return))
            if any(r.value is None or safe_infer(r.value) is None for r in returns):
                source['may_be_none'] = True
                source['type'] = "function_return"
                source['function'] = inferred.name

        elif isinstance(inferred, astroid.Call):
            # 检查是否是可能返回 None 的调用（如数据库查询）
            func_name = inferred.func.as_string()
            if func_name in ['dict.get', 'find', 'query', 'fetch']:
                source['may_be_none'] = True
                source['type'] = "nullable_call"

        return source
```

**None 值传播图**：
```python
def build_none_propagation_graph(self, module):
    """构建 None 值传播图"""
    graph = nx.DiGraph()

    # 1. 找出所有可能返回 None 的函数
    for func in module.nodes_of_class(astroid.FunctionDef):
        if self._may_return_none(func):
            graph.add_node(func.name, type='none_source')

    # 2. 追踪 None 值的传播
    for func in module.nodes_of_class(astroid.FunctionDef):
        for call in func.nodes_of_class(astroid.Call):
            callee = safe_infer(call.func)
            if callee and callee.name in graph:
                # None 值从 callee 传播到 func
                graph.add_edge(callee.name, func.name)

    return graph
```

---

#### 2.2 调用时机与并发环境

**检测目标**：并发调用时的线程安全问题

**检测方法**：
```python
class ConcurrencyAnalyzer:
    def analyze_concurrency(self, function, context):
        """分析并发环境"""
        # 1. 检查函数是否被多线程调用
        concurrent_calls = self._find_concurrent_calls(function, context)

        if not concurrent_calls:
            return None

        # 2. 检查是否操作共享状态
        shared_state = self._find_shared_state_access(function)

        # 3. 检查是否有同步机制
        has_sync = self._check_synchronization(function)

        if shared_state and not has_sync:
            return SuspiciousFinding(
                type="thread_safety_issue",
                concurrent_calls=concurrent_calls,
                shared_state=shared_state,
                missing_synchronization=True
            )

    def _find_concurrent_calls(self, function, context):
        """查找并发调用点"""
        concurrent = []

        for caller in context['callers']:
            caller_code = caller['code']

            # 检查调用者是否使用了并发相关的模块
            if any(keyword in caller_code for keyword in [
                'threading.Thread',
                'multiprocessing.Process',
                'asyncio',
                'ThreadPoolExecutor',
                'ProcessPoolExecutor'
            ]):
                concurrent.append(caller)

        return concurrent
```

---

#### 2.3 配套函数的调用关系

**检测目标**：成对函数调用缺失（如 init/destroy, start/stop）

**检测方法**：
```python
class PairedCallAnalyzer:
    # 定义成对函数
    PAIRED_FUNCTIONS = {
        'init': 'destroy',
        'start': 'stop',
        'open': 'close',
        'acquire': 'release',
        'begin': 'commit',
        'connect': 'disconnect',
    }

    def analyze_paired_calls(self, function):
        """检查成对函数调用"""
        issues = []

        # 1. 查找所有函数调用
        calls = [call.func.as_string() for call in function.nodes_of_class(astroid.Call)]

        # 2. 检查成对性
        for init_func, destroy_func in self.PAIRED_FUNCTIONS.items():
            if init_func in calls and destroy_func not in calls:
                issues.append({
                    "type": "missing_paired_call",
                    "called": init_func,
                    "missing": destroy_func,
                    "message": f"调用了 {init_func}() 但未调用 {destroy_func}()"
                })

        return issues
```

---

### 📋 **类别 3：数据流与污点分析**

#### 3.1 SQL 注入检测

**检测目标**：不可信输入流向 SQL 执行函数

**检测方法**：
```python
class TaintAnalyzer:
    # 污点源（不可信输入）
    TAINT_SOURCES = [
        'request.args',
        'request.form',
        'request.json',
        'input(',
        'sys.argv',
    ]

    # 污点汇聚点（危险函数）
    TAINT_SINKS = {
        'sql_injection': ['execute', 'executemany', 'raw', 'cursor.execute'],
        'command_injection': ['os.system', 'subprocess.call', 'os.popen'],
        'path_traversal': ['open', 'os.path.join', 'shutil.copy'],
    }

    def detect_taint_flow(self, function):
        """检测污点传播"""
        # 1. 标记污点源
        tainted_vars = self._mark_taint_sources(function)

        # 2. 追踪污点传播
        dfg = self._build_data_flow_graph(function)
        propagated = self._propagate_taint(dfg, tainted_vars)

        # 3. 检查污点是否流向危险函数
        vulnerabilities = []
        for sink_type, sink_funcs in self.TAINT_SINKS.items():
            for call in function.nodes_of_class(astroid.Call):
                func_name = call.func.as_string()
                if func_name in sink_funcs:
                    # 检查参数是否被污染
                    for arg in call.args:
                        if self._is_tainted(arg, propagated):
                            # 检查是否经过净化
                            if not self._is_sanitized(arg, function):
                                vulnerabilities.append({
                                    "type": sink_type,
                                    "sink": func_name,
                                    "line": call.lineno,
                                    "tainted_arg": arg.as_string(),
                                    "source": self._trace_taint_source(arg, tainted_vars)
                                })

        return vulnerabilities

    def _mark_taint_sources(self, node):
        """标记污点源"""
        tainted = set()

        for assign in node.nodes_of_class(astroid.Assign):
            if isinstance(assign.value, astroid.Attribute):
                attr_name = assign.value.as_string()
                if any(source in attr_name for source in self.TAINT_SOURCES):
                    # 标记变量为污点
                    tainted.add(assign.targets[0].as_string())

        return tainted
```

---

### 📋 **类别 4：符号执行与约束求解**

#### 4.1 路径可行性分析

**检测目标**：不可达代码、矛盾条件

**检测方法**：
```python
class SymbolicExecutor:
    def analyze_path_feasibility(self, function):
        """符号执行分析路径可行性"""
        cfg = self._build_cfg(function)

        # 1. 枚举所有路径
        paths = self._enumerate_paths(cfg)

        infeasible_paths = []
        for path in paths:
            # 2. 收集路径条件
            constraints = self._collect_path_constraints(path)

            # 3. 使用 SMT Solver 检查可行性
            if not self._is_satisfiable(constraints):
                infeasible_paths.append({
                    "path": path,
                    "constraints": constraints,
                    "unreachable_code": path[-1].statements
                })

        return infeasible_paths

    def _collect_path_constraints(self, path):
        """收集路径条件"""
        constraints = []

        for block in path:
            # 查找条件判断
            for stmt in block.statements:
                if isinstance(stmt, astroid.If):
                    condition = stmt.test.as_string()

                    # 判断路径走的是 true 还是 false 分支
                    if block in self._get_true_successors(stmt):
                        constraints.append(f"({condition}) == True")
                    else:
                        constraints.append(f"({condition}) == False")

        return constraints

    def _is_satisfiable(self, constraints):
        """使用 Z3 检查约束可满足性"""
        try:
            from z3 import Solver, parse_smt2_string

            solver = Solver()
            for constraint in constraints:
                # 将约束转换为 Z3 表达式
                solver.add(self._to_z3_expr(constraint))

            return solver.check() == sat
        except:
            # 如果 Z3 不可用或解析失败，保守返回 True
            return True
```

---

## 三、Layer 3: LLM 增强深度分析

### 3.1 增强型 Prompt 设计

Layer 3 接收 Layer 2 的分析结果，构建包含结构化信息的 Prompt，让 LLM 进行语义理解和推理。

#### 3.1.1 Prompt 结构

```markdown
# 深度 Bug 分析任务

## 函数信息
**函数名**: {function_name}
**文件**: {file_path}:{start_line}-{end_line}

## 函数代码
```python
{annotated_code_with_line_numbers}
```

## Layer 2 分析结果

### 1. 控制流图
{cfg_visualization}

### 2. 数据流分析
**Reaching Definitions**:
- 变量 x: 定义于行 10, 15
- 变量 y: 定义于行 12

**Def-Use Chains**:
- x@10 → 使用于行 18, 20
- y@12 → 使用于行 19

### 3. 可疑点发现

#### 🚨 可疑点 1: 潜在竞态条件
- **位置**: 行 15-20
- **证据**:
  - 访问全局变量 `counter`
  - 无同步机制（无 lock）
  - 调用者在多线程环境中调用（见 Caller 1）

#### 🚨 可疑点 2: 资源泄漏风险
- **位置**: 行 25
- **证据**:
  - `f = open("data.txt")` 申请文件资源
  - 路径分析：存在未释放的执行路径
  - 缺失的释放路径: 行 25 → 行 30 (异常分支) → 函数出口

### 4. 污点分析
**发现污点流**:
- 源: `user_input = request.args.get('id')` (行 10)
- 传播: user_input → query (行 12)
- 汇: `cursor.execute(query)` (行 15)
- **未经净化**: 无 SQL 转义或参数化查询

## 调用上下文

### Caller 1: process_requests()
```python
# 文件: server.py:45
def process_requests():
    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.submit(target_function, data)  # 多线程调用
```

### Caller 2: handle_upload()
```python
# 文件: upload.py:30
def handle_upload():
    file_path = request.form.get('path')  # 不可信输入
    target_function(file_path)
```

## 分析任务

请基于以上信息，回答以下问题：

1. **可疑点 1 是否是真正的 bug？**
   - 请结合代码逻辑、调用上下文判断
   - 如果是 bug，给出具体的触发条件和后果

2. **可疑点 2 是否会导致资源泄漏？**
   - 分析所有执行路径
   - 判断是否存在未释放资源的路径

3. **污点流是否构成 SQL 注入漏洞？**
   - 是否有净化机制被遗漏？
   - 评估风险等级

请使用 JSON 格式返回：
{
  "findings": [
    {
      "confirmed": true/false,
      "suspicious_point": "可疑点 1/2/3",
      "bug_type": "race_condition/resource_leak/sql_injection/...",
      "severity": "high/medium/low",
      "description": "详细描述",
      "evidence": ["证据1", "证据2"],
      "trigger_condition": "触发条件",
      "fix_suggestion": "修复建议"
    }
  ]
}
```

---

### 3.2 结构化推理

Layer 3 引导 LLM 进行逐步推理：

```python
class Layer3Analyzer:
    def analyze_with_llm(self, function, layer2_results):
        """使用 LLM 进行深度分析"""
        # 1. 构建增强型 prompt
        prompt = self._build_enhanced_prompt(function, layer2_results)

        # 2. LLM 分析
        response = self.llm_client.chat.completions.create(
            model=self.config.llm_model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2  # 降低随机性，提高准确性
        )

        # 3. 解析结果
        findings = self._parse_llm_response(response)

        # 4. 交叉验证
        validated_findings = self._cross_validate(findings, layer2_results)

        return validated_findings

    def _cross_validate(self, llm_findings, layer2_results):
        """交叉验证 LLM 结果"""
        validated = []

        for finding in llm_findings:
            # 验证 LLM 的结论是否与 Layer 2 证据一致
            if finding['confirmed']:
                # 检查证据链
                evidence_valid = self._verify_evidence_chain(
                    finding,
                    layer2_results
                )

                if evidence_valid:
                    # 计算置信度
                    confidence = self._calculate_confidence(finding, layer2_results)
                    finding['confidence'] = confidence
                    validated.append(finding)

        return validated
```

---

## 四、实现计划

### 4.1 Phase 1: 基础设施 (2 周)

**目标**: 搭建 Layer 2 的核心能力

- [ ] astroid 集成与 AST 增强解析
- [ ] CFG 构建器（基于 astroid）
- [ ] 基础数据流分析（Reaching Definitions）
- [ ] 简单的调用图构建

**交付物**:
- `pyscan/layer2/cfg_builder.py`
- `pyscan/layer2/dataflow.py`
- `pyscan/layer2/callgraph.py`

---

### 4.2 Phase 2: 核心检测器 (3 周)

**目标**: 实现各类问题检测器

#### Week 1: 资源管理
- [ ] 资源泄漏检测器
- [ ] 成对函数调用检测器

#### Week 2: 并发与竞态
- [ ] 竞态条件检测器
- [ ] 线程安全分析器

#### Week 3: 数据流
- [ ] 污点分析器（SQL 注入、命令注入）
- [ ] None 值传播分析器

**交付物**:
- `pyscan/layer2/detectors/resource_leak.py`
- `pyscan/layer2/detectors/race_condition.py`
- `pyscan/layer2/detectors/taint_analysis.py`

---

### 4.3 Phase 3: Layer 3 增强 (2 周)

**目标**: LLM 集成与验证

- [ ] 增强型 Prompt 模板
- [ ] LLM 调用与结果解析
- [ ] 交叉验证机制

**交付物**:
- `pyscan/layer3/enhanced_analyzer.py`
- `pyscan/layer3/prompt_builder.py`
- `pyscan/layer3/cross_validator.py`

---

### 4.4 Phase 4: 集成与测试 (2 周)

- [ ] Layer 2 + Layer 3 集成
- [ ] Benchmark 测试集构建
- [ ] 性能优化

---

## 五、技术挑战与解决方案

### 5.1 挑战 1: astroid 类型推断的局限性

**问题**: astroid 无法推断所有情况的类型（特别是动态特性）

**解决方案**:
1. 结合类型注解（type hints）
2. 使用启发式规则补充
3. 将不确定的情况交给 Layer 3（LLM）判断

---

### 5.2 挑战 2: 路径爆炸问题

**问题**: 符号执行时路径数量指数增长

**解决方案**:
1. 限制路径深度（最多 10 层嵌套）
2. 启发式路径剪枝（优先探索可疑路径）
3. 使用抽象解释简化状态

---

### 5.3 挑战 3: 误报率控制

**问题**: 静态分析容易产生误报

**解决方案**:
1. Layer 2 + Layer 3 双重验证
2. 引入置信度评分
3. 用户反馈机制（持续学习）

---

## 六、测试与评估

### 6.1 Benchmark 数据集

构建包含以下问题的测试集：

| 类别 | 数量 | 示例 |
|------|------|------|
| 竞态条件 | 20 | 多线程访问全局变量 |
| 资源泄漏 | 30 | 文件/锁未释放 |
| SQL 注入 | 15 | 用户输入拼接 SQL |
| 无限循环 | 10 | 循环条件错误 |
| None 传播 | 25 | 未检查 None 就调用 |

---

### 6.2 评估指标

- **准确率** (Precision): 检测出的 bug 中真实 bug 的比例
- **召回率** (Recall): 真实 bug 中被检测出的比例
- **F1 Score**: 准确率和召回率的调和平均
- **分析时间**: 每个函数的平均分析时间

---

## 七、总结

### 7.1 关键创新点

1. **Layer 2 (符号分析) + Layer 3 (LLM) 协同**：静态分析提供证据，LLM 理解语义
2. **多维度检测**：逻辑、数据流、控制流、并发、资源管理
3. **低误报率**：双重验证 + 置信度评分
4. **可解释性**：提供详细证据链和修复建议

### 7.2 预期效果

相比纯 LLM 方法（Layer 3 单独）：
- **准确率提升 30%**：Layer 2 提供强证据支持
- **召回率提升 20%**：Layer 2 发现 LLM 可能遗漏的问题
- **分析速度提升 50%**：Layer 2 过滤掉大量无问题代码

---

## 八、参考资料

1. **astroid 文档**: https://pylint.readthedocs.io/projects/astroid/
2. **Pylint 源码**: https://github.com/pylint-dev/pylint
3. **Z3 SMT Solver**: https://github.com/Z3Prover/z3
4. **符号执行综述**: Baldoni et al., "A Survey of Symbolic Execution Techniques"
5. **污点分析**: Arzt et al., "FlowDroid: Precise Context, Flow, Field, Object-sensitive and Lifecycle-aware Taint Analysis for Android Apps"

---

**文档版本**: v1.0
**最后更新**: 2025-01-03
