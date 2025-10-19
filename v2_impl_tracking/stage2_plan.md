# Stage 2 实施计划（基于 Astroid）

## 文档信息

- **版本**: v1.0
- **日期**: 2025-10-19
- **状态**: 计划中
- **前置**: Stage 1 已完成（82 测试通过）

---

## 1. 实施背景

**当前状态**: Stage 1 完成，Layer 1 静态工具集成（mypy + bandit）已验证
**下一目标**: 实现 Layer 2 深度静态分析核心能力

### 1.1 技术选型：Astroid

经过 PoC 验证（`poc_context_manager_detector.py`），决定采用 **Astroid** 作为 Layer 2 的核心引擎。

#### 选择 Astroid 的理由

| 能力 | Astroid | 自建 CFG | 优势 |
|------|---------|----------|------|
| **名称解析** | ✅ 完整支持 | ❌ 需大量工作 | 处理作用域、导入、继承 |
| **类型推断** | ✅ 强大 | ❌ 非常困难 | 可推断复杂表达式类型 |
| **调用图** | ✅ 精确 | ⚠️ 基础 | 处理装饰器、元类、动态调用 |
| **异常分析** | ✅ 内置 | ❌ 需实现 | 理解 Python 异常语义 |
| **维护成本** | ✅ 低（Pylint 团队维护） | ❌ 高 | 跟进 Python 新特性 |
| **隐式调用** | ✅ 支持魔法方法 | ❌ 需手工实现 | `__enter__`, `__exit__`, `__call__` 等 |

#### PoC 验证结果

**测试代码**: `poc_context_manager_detector.py`
**检测目标**: 上下文管理器误用（对应 BUG_0001, BUG_0010, BUG_0011）

**结果**:
- ✅ 成功检测 3/3 个坏例子（100% 召回）
- ✅ 正确通过 2/2 个好例子（0% 误报）
- ✅ 成功检测 BUG_0010 类型问题（ThreadPoolExecutor 泄露）

**关键代码**:
```python
# Astroid 可以检测资源类型并判断是否在 with 中
for assign in func_node.nodes_of_class(astroid.Assign):
    if isinstance(assign.value, astroid.Call):
        # 检查是否是资源类型
        if self._is_resource_call(assign.value):
            # 检查是否在 with 语句中
            if not self._is_in_with_statement(assign):
                # 检查是否有显式 cleanup
                if not self._has_cleanup_call(func_node, var_names):
                    report_bug("ResourceLeakRisk")
```

---

## 2. 实施计划（4 周）

### Week 1-2: 上下文管理器检测器

**目标**: 集成 PoC 到 PyScan Layer 2

**任务**:
1. 创建 `pyscan/layer2/` 模块结构
2. 实现 `ContextManagerDetector` 类
3. 扩展资源类型列表（文件、网络、数据库等）
4. 支持异步上下文管理器（`async with`）
5. 集成到现有 bug 检测流程
6. 添加测试用例（基于 benchmark）

**预期收益**:
- 直接解决 **BUG_0001, BUG_0010, BUG_0011, BUG_0015**
- 检测准确率: ~95%（基于 PoC）
- 假阳性率: <5%

**代码结构**:
```python
# pyscan/layer2/__init__.py
from .context_manager_detector import ContextManagerDetector
from .implicit_call_detector import ImplicitCallDetector
from .concurrency_detector import ConcurrencyDetector

# pyscan/layer2/context_manager_detector.py

import astroid
from typing import List, Dict, Any
from pyscan.ast_parser import FunctionInfo
from pyscan.bug_detector import BugReport


class ContextManagerDetector:
    """基于 Astroid 的上下文管理器检测器"""

    # 已知的资源类型（实现了上下文管理器协议）
    RESOURCE_TYPES = {
        'open',  # 文件
        'ThreadPoolExecutor',
        'ProcessPoolExecutor',
        'Lock',
        'RLock',
        'Semaphore',
        'Condition',
        'socket',
        'urlopen',
        'Session',  # requests.Session
        'connection',  # 数据库连接
        'cursor',  # 数据库游标
    }

    def analyze_function(
        self,
        func_node: astroid.FunctionDef,
        func_info: FunctionInfo,
        file_path: str
    ) -> List[BugReport]:
        """
        分析函数中的资源管理问题

        Args:
            func_node: Astroid 函数节点
            func_info: PyScan 函数信息
            file_path: 文件路径

        Returns:
            检测到的 bug 列表
        """
        bugs = []

        # 检测赋值语句中的资源创建
        for assign in func_node.nodes_of_class(astroid.Assign):
            if self._is_resource_creation(assign):
                if not self._is_safely_managed(assign, func_node):
                    bug = self._create_bug_report(assign, func_info, file_path)
                    bugs.append(bug)

        # 检测直接调用（未赋值）
        for call in func_node.nodes_of_class(astroid.Call):
            if isinstance(call.parent, astroid.Assign):
                continue  # 已在上面处理

            if self._is_resource_call(call):
                if not self._is_in_with_statement(call):
                    bug = self._create_implicit_cleanup_bug(call, func_info, file_path)
                    bugs.append(bug)

        return bugs

    def _is_resource_creation(self, assign: astroid.Assign) -> bool:
        """检查赋值是否创建了资源对象"""
        if not isinstance(assign.value, astroid.Call):
            return False
        return self._is_resource_call(assign.value)

    def _is_resource_call(self, call: astroid.Call) -> bool:
        """判断调用是否创建了资源对象"""
        # 方法 1: 检查函数名
        func_name = self._get_call_name(call)
        if func_name in self.RESOURCE_TYPES:
            return True

        # 方法 2: 使用 Astroid 推断，检查返回类型是否实现了上下文管理器协议
        try:
            for inferred in call.infer():
                if isinstance(inferred, astroid.Instance):
                    cls = inferred._proxied
                    if self._has_context_manager_protocol(cls):
                        return True
        except (astroid.InferenceError, AttributeError):
            pass

        return False

    def _is_safely_managed(
        self,
        assign: astroid.Assign,
        func_node: astroid.FunctionDef
    ) -> bool:
        """检查资源是否安全管理"""
        # 1. 检查是否在 with 语句中
        if self._is_in_with_statement(assign):
            return True

        # 2. 检查是否有显式的清理调用
        var_names = [target.as_string() for target in assign.targets]
        if self._has_cleanup_call(func_node, var_names, assign.value):
            return True

        return False

    # ... 其他辅助方法（参考 poc_context_manager_detector.py）
```

**集成到 BugDetector**:
```python
# pyscan/bug_detector.py

from pyscan.layer2 import ContextManagerDetector

class BugDetector:
    def __init__(self, config, llm_client):
        self.config = config
        self.llm_client = llm_client
        # Layer 2 检测器
        self.context_manager_detector = ContextManagerDetector()

    def detect_bugs(self, function: FunctionInfo, context: str) -> List[BugReport]:
        bugs = []

        # Layer 2: 深度静态分析
        if self.config.get('enable_layer2', True):
            astroid_bugs = self._run_layer2_analysis(function)
            bugs.extend(astroid_bugs)

        # Layer 3: LLM 分析（保留原有逻辑）
        llm_bugs = self._run_llm_analysis(function, context)
        bugs.extend(llm_bugs)

        return bugs

    def _run_layer2_analysis(self, function: FunctionInfo) -> List[BugReport]:
        """运行 Layer 2 深度静态分析"""
        try:
            # 解析函数为 Astroid 节点
            astroid_node = astroid.parse(function.code)
            func_nodes = list(astroid_node.nodes_of_class(astroid.FunctionDef))

            if not func_nodes:
                return []

            func_node = func_nodes[0]

            # 运行上下文管理器检测
            bugs = self.context_manager_detector.analyze_function(
                func_node,
                function,
                function.file_path
            )

            return bugs

        except Exception as e:
            # 静态分析失败，回退到 LLM
            return []
```

### Week 3: 隐式调用关系检测

**目标**: 检测魔法方法和隐式调用问题

**检测类型**:
1. **Property 方法副作用**: Property 中有 I/O、网络请求
2. **魔法方法契约**: `__enter__`/`__exit__` 配对、`__eq__` 未实现 `__hash__`
3. **迭代器协议**: `__iter__`/`__next__` 实现错误
4. **上下文管理器实现**: `__exit__` 未正确处理异常

**实现示例**:
```python
# pyscan/layer2/implicit_call_detector.py

class ImplicitCallDetector:
    """检测隐式调用问题"""

    def detect_property_side_effects(
        self,
        func_node: astroid.FunctionDef
    ) -> List[BugReport]:
        """检测 property 方法中的副作用"""
        if not self._is_property(func_node):
            return []

        bugs = []

        # 检查是否有 I/O 操作
        for call in func_node.nodes_of_class(astroid.Call):
            if self._is_io_operation(call):
                bugs.append(BugReport(
                    bug_id=self._generate_bug_id(),
                    type="PropertySideEffect",
                    description="Property 方法不应有副作用（I/O 操作）",
                    severity="medium",
                    # ... 其他字段
                ))

        return bugs

    def _is_property(self, func_node: astroid.FunctionDef) -> bool:
        """检查函数是否是 property"""
        if not func_node.decorators:
            return False

        for decorator in func_node.decorators.nodes:
            if decorator.as_string() == 'property':
                return True

        return False

    def _is_io_operation(self, call: astroid.Call) -> bool:
        """检查调用是否是 I/O 操作"""
        io_functions = {'open', 'read', 'write', 'urlopen', 'requests.get'}
        func_name = self._get_call_name(call)
        return func_name in io_functions
```

### Week 4: 并发安全检测

**目标**: 检测多线程竞态条件和锁管理问题

**检测类型**:
1. **全局变量竞态**: 多线程访问全局变量未加锁（BUG_0002, BUG_0005）
2. **锁配对**: `acquire()` 后未在 `finally` 中 `release()`
3. **死锁风险**: 嵌套锁按不同顺序获取

**实现策略**:
```python
# pyscan/layer2/concurrency_detector.py

class ConcurrencyDetector:
    """并发安全检测器"""

    def detect_race_condition(
        self,
        func_node: astroid.FunctionDef,
        func_info: FunctionInfo
    ) -> List[BugReport]:
        """检测竞态条件"""
        bugs = []

        # 1. 检测全局变量写入
        for assign in func_node.nodes_of_class(astroid.Assign):
            if self._is_global_write(assign, func_node):
                # 2. 检查函数是否可能在多线程调用
                if self._is_called_in_multithread(func_info):
                    # 3. 检查是否有锁保护
                    if not self._has_lock_protection(assign, func_node):
                        bugs.append(BugReport(
                            type="RaceCondition",
                            description="全局变量写入未加锁，存在竞态条件",
                            severity="high",
                            # ... 其他字段
                        ))

        return bugs

    def _is_global_write(
        self,
        assign: astroid.Assign,
        func_node: astroid.FunctionDef
    ) -> bool:
        """检查赋值是否写入全局变量"""
        for target in assign.targets:
            if isinstance(target, astroid.Name):
                # 检查是否在函数的 global 声明中
                if self._is_global_variable(target.name, func_node):
                    return True

        return False

    def _is_called_in_multithread(self, func_info: FunctionInfo) -> bool:
        """推断函数是否可能在多线程环境调用"""
        # 方法 1: 检查 inferred_callers 中是否有线程相关调用
        for caller in func_info.inferred_callers:
            hint = caller.get('hint', '')
            if 'thread' in hint.lower() or 'executor' in hint.lower():
                return True

        # 方法 2: 检查函数名模式（如 handle_request, process_task）
        multithread_patterns = ['handle', 'process', 'worker']
        func_name_lower = func_info.name.lower()
        for pattern in multithread_patterns:
            if pattern in func_name_lower:
                return True

        return False

    def _has_lock_protection(
        self,
        assign: astroid.Assign,
        func_node: astroid.FunctionDef
    ) -> bool:
        """检查赋值是否在锁保护下"""
        # 向上遍历 AST，检查是否在 with Lock: 块中
        parent = assign.parent
        while parent and parent != func_node:
            if isinstance(parent, astroid.With):
                # 检查 with 表达式是否是锁
                for item_expr, _ in parent.items:
                    if self._is_lock_object(item_expr):
                        return True
            parent = parent.parent

        return False
```

---

## 3. Astroid 核心能力应用

### 能力 1: 控制流分析

```python
# Astroid 可以提取控制流节点
for node in func_node.nodes_of_class(astroid.If):
    # 分析条件分支
    condition = node.test
    # 检测恒真/恒假条件
    if self._is_constant_condition(condition):
        report_bug("恒定条件")
```

### 能力 2: 数据流追踪

```python
# 追踪变量定义和使用
for node in func_node.nodes_of_class(astroid.Name):
    if node.name == 'result':
        # 找到所有对 'result' 的引用
        # 检查是否有未初始化使用
        if not self._has_definition_before(node):
            report_bug("未初始化变量")
```

### 能力 3: 调用图构建

```python
# 获取被调用函数的定义
for call in func_node.nodes_of_class(astroid.Call):
    try:
        for inferred_func in call.func.inferred():
            # 分析被调用函数的类型签名
            expected_types = self._get_parameter_types(inferred_func)
            # 检查参数类型匹配
            actual_types = self._infer_argument_types(call.args)
            if not self._types_compatible(expected_types, actual_types):
                report_bug("类型不匹配")
    except astroid.InferenceError:
        pass
```

### 能力 4: 作用域分析

```python
# 分析变量作用域和生命周期
for scope in module.nodes_of_class(astroid.FunctionDef):
    local_vars = scope.locals  # 局部变量
    # 检查资源生命周期
    for var_name, definitions in local_vars.items():
        if self._is_resource_type(definitions[0]):
            if not self._released_before_scope_exit(var_name, scope):
                report_bug("资源生命周期问题")
```

### 能力 5: 异常传播分析

```python
# 分析异常处理覆盖
for try_node in func_node.nodes_of_class(astroid.Try):
    # 获取所有 except 子句
    caught_exceptions = set()
    for handler in try_node.handlers:
        if handler.type:
            caught_exceptions.add(handler.type.as_string())

    # 检查是否覆盖所有可能异常
    possible_exceptions = self._infer_exceptions_in_try(try_node.body)
    uncaught = possible_exceptions - caught_exceptions
    if uncaught:
        report_bug(f"未捕获异常: {uncaught}")
```

---

## 4. 与 Benchmark 集成

### 评估流程

1. 运行 PyScan（含 Layer 2）扫描 benchmark:
   ```bash
   python -m pyscan benchmarks/categories -o benchmark_report_stage2.json
   ```

2. 评估结果:
   ```bash
   python benchmarks/evaluation/evaluate.py \
       --ground-truth benchmarks/ground_truth.json \
       --report benchmark_report_stage2.json \
       --output evaluation_stage2.json
   ```

3. 对比 Stage 1 vs Stage 2:
   ```bash
   python benchmarks/evaluation/compare.py \
       evaluation_stage1.json \
       evaluation_stage2.json
   ```

### 预期改进

| 指标 | Stage 1 (仅 Layer 1) | Stage 2 目标 (Layer 1+2) | 改进 |
|------|---------------------|------------------------|------|
| Precision | ~60% | 80%+ | +20% |
| Recall | ~40% | 70%+ | +30% |
| F1 Score | ~0.48 | 0.75+ | +0.27 |

**解决的 Bug**:
- BUG_0001, BUG_0010, BUG_0011, BUG_0015 (上下文管理器)
- BUG_0002, BUG_0005 (并发安全)

---

## 5. 实施优先级

| 优先级 | 时间 | 任务 | 预期收益 |
|--------|------|------|----------|
| **P0** | Week 1-2 | 上下文管理器检测器 | 直接解决 4 个已知 bug |
| **P1** | Week 3 | 隐式调用检测 | 提升代码质量 |
| **P2** | Week 4 | 并发安全检测 | 解决 2 个已知并发 bug |

---

## 6. 风险与缓解

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| Astroid API 变更 | 中 | 中 | 锁定版本 (astroid==4.0.1)，监控更新 |
| 性能问题 | 低 | 中 | 增量分析，缓存 Astroid 解析结果 |
| 复杂场景误报 | 中 | 高 | LLM 二次验证，持续优化规则 |
| 与现有代码冲突 | 低 | 高 | 充分测试，渐进式集成 |

---

## 7. 成功标准

Stage 2 完成的标准：

1. ✅ 实现 3 个检测器（上下文、隐式调用、并发）
2. ✅ Benchmark 测试通过（Precision ≥ 80%, Recall ≥ 70%）
3. ✅ 单元测试覆盖率 ≥ 85%
4. ✅ 文档完整（API 文档 + 用户指南）
5. ✅ 性能可接受（扫描速度 <2x Stage 1）
6. ✅ 与 Stage 1 无冲突（所有现有测试通过）

---

## 8. 依赖和资源

### 依赖库

```txt
# requirements.txt 新增
astroid>=4.0.1
```

### 参考资源

- **Astroid 文档**: https://pylint.readthedocs.io/projects/astroid/
- **Astroid GitHub**: https://github.com/pylint-dev/astroid
- **PoC 代码**: `poc_context_manager_detector.py`

---

## 9. 里程碑

| 里程碑 | 日期 | 交付物 |
|--------|------|--------|
| M1: 上下文管理器检测器完成 | Week 2 end | `pyscan/layer2/context_manager_detector.py` + 测试 |
| M2: 隐式调用检测器完成 | Week 3 end | `pyscan/layer2/implicit_call_detector.py` + 测试 |
| M3: 并发安全检测器完成 | Week 4 end | `pyscan/layer2/concurrency_detector.py` + 测试 |
| M4: Benchmark 评估通过 | Week 4 end | 评估报告，达到目标指标 |

---

**下一步行动**:
1. Review 本实施计划
2. 确认资源和时间安排
3. 启动 Week 1 任务（创建 layer2 模块）

---

**文档版本历史**:
- v1.0 (2025-10-19): 初始版本
