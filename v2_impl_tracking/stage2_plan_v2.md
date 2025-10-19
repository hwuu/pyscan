# Stage 2 实施计划 v2.0（基于 Benchmark 评估结果调整）

## 文档信息

- **版本**: v2.0
- **日期**: 2025-10-20
- **状态**: 计划中
- **前置**: Stage 1 已完成（82 测试通过）
- **调整依据**: Benchmark 评估结果（105 bugs，Precision 52.27%, Recall 65.71%）

---

## 🔄 重要变更说明

**相比 v1.0 的主要调整**:

1. **优先级重排**：基于 benchmark 评估，将 Layer 4 交叉验证提到最高优先级
2. **目标重新聚焦**：从"完善资源管理检测"转向"解决最大 Gap（类型安全、注入漏洞）"
3. **实施策略调整**：采用"数据驱动"的方式，优先解决 Recall 最低的类别

---

## 1. Benchmark 评估结果分析

### 1.1 当前检测能力概览

| Bug 类别 | Ground Truth | 检测到 | Recall | 现状评估 | Stage 2 能否改进 |
|---------|-------------|--------|--------|---------|----------------|
| **类型安全** | 7 | **0** | **0%** ❌ | 最大 Gap | ✅ **是**（Layer 4 验证） |
| **输入验证** | 10 | 3 | 30.0% ⚠️ | 严重不足 | ⚠️ 部分（需后续 Stage） |
| **API 使用** | 6 | 2 | 33.3% ⚠️ | 严重不足 | ❌ 否（需后续 Stage） |
| **注入漏洞** | 18 | 7 | 38.9% ⚠️ | 不足 | ✅ **是**（污点分析） |
| **数据流问题** | 15 | 10 | 66.7% | 中等 | ✅ **是**（数据流分析） |
| **错误处理** | 15 | 13 | 86.7% ✅ | 良好 | ❌ 否 |
| **资源管理** | 17 | 17 | **100%** ✅ | 完美 | ⚠️ 降低误报 |
| **并发安全** | 17 | 17 | **100%** ✅ | 完美 | ⚠️ 降低误报 |

### 1.2 关键发现

#### ✅ 优势领域（无需重点投入）
- **资源管理**: Recall 100%，说明 LLM 已经能很好检测
- **并发安全**: Recall 100%，说明 LLM 已经能很好检测
- **结论**: PoC 中的上下文管理器检测器收益**有限**，优先级应**降低**

#### ❌ 最大 Gap（需要重点投入）
1. **类型安全**: 0% Recall（**7 个漏报**）
   - 原因：mypy 已检测，但未被有效利用
   - 解决方案：**Layer 4 交叉验证**（mypy + LLM 确认）

2. **注入漏洞**: 38.9% Recall（**11 个漏报**）
   - 原因：缺少污点分析
   - 解决方案：**简化污点分析**（针对常见注入模式）

3. **数据流问题**: 66.7% Recall（**5 个漏报，3 个 None 解引用**）
   - 原因：缺少数据流追踪
   - 解决方案：**基于 Astroid 的数据流分析**

#### ⚠️ 误报率过高
- False Positive: 63 个（47.7%）
- 目标：降低到 <30%
- 策略：通过多层验证过滤误报

---

## 2. 调整后的实施计划（4 周）

### 总体策略：数据驱动，聚焦 Gap

**新的优先级排序**:
1. **P0**: 解决类型安全 0% Recall（直接影响 7 个 bugs）
2. **P1**: 解决注入漏洞低 Recall（直接影响 11 个 bugs）
3. **P1**: 改进数据流问题检测（直接影响 5 个 bugs）
4. **P2**: 降低误报率（改善用户体验）

---

### Week 1: Layer 4 基础验证（交叉验证引擎）

**目标**: 实现 mypy + LLM 的交叉验证，解决类型安全 0% Recall 问题

**动机**:
- mypy 已检测到类型错误，但未被报告（Layer 1 只是收集，未验证）
- 需要一个机制将 mypy 发现的高置信度问题直接报告

**任务**:
1. 创建 `pyscan/layer4/` 模块
2. 实现 `CrossValidator` 类
3. 实现 mypy 结果的置信度评分
4. 集成到 bug 检测流程
5. 编写测试用例（基于 benchmark 类型安全 bugs）

**代码结构**:
```python
# pyscan/layer4/cross_validator.py

from typing import List, Dict
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
        """
        verified_bugs = []

        # 处理 mypy type errors
        for issue in static_facts.type_errors:
            if issue.severity == 'error':
                # 检查 LLM 是否确认
                llm_confirmed = self._check_llm_confirmation(issue, llm_bugs)

                # 根据确认情况设置置信度
                confidence = 0.95 if llm_confirmed else 0.75

                # 如果置信度足够，直接报告
                if confidence >= 0.7:
                    verified_bugs.append(BugReport(
                        bug_id=self._generate_bug_id(),
                        type="TypeError",
                        severity="high",
                        description=issue.message,
                        location={
                            'start_line': issue.line,
                            'end_line': issue.line,
                            'start_col': issue.column,
                            'end_col': issue.column
                        },
                        confidence=confidence,
                        evidence={
                            'mypy_detected': True,
                            'llm_confirmed': llm_confirmed,
                            'tool': 'mypy'
                        },
                        suggestion=self._generate_fix_suggestion(issue)
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
            if abs(bug.location['start_line'] - mypy_issue.line) <= 2:
                # 类型检查关键字匹配
                if 'type' in bug.type.lower() or 'type' in bug.description.lower():
                    return True
        return False

    def _generate_fix_suggestion(self, issue: StaticIssue) -> str:
        """基于 mypy 错误信息生成修复建议"""
        message = issue.message.lower()

        if 'incompatible types' in message:
            return "检查类型注解是否正确，确保赋值类型与声明一致"
        elif 'has no attribute' in message:
            return "检查对象类型，确保访问的属性存在"
        elif 'none' in message:
            return "添加 None 检查或使用 Optional 类型注解"
        else:
            return "修复类型不匹配问题"
```

**集成到 BugDetector**:
```python
# pyscan/bug_detector.py

from pyscan.layer4 import CrossValidator

class BugDetector:
    def __init__(self, config, llm_client):
        self.config = config
        self.llm_client = llm_client
        self.cross_validator = CrossValidator()

    def detect_bugs(
        self,
        function: FunctionInfo,
        context: str,
        static_facts: Optional[StaticFacts] = None
    ) -> List[BugReport]:
        bugs = []

        # Layer 3: LLM 分析
        llm_bugs = self._run_llm_analysis(function, context, static_facts)

        # Layer 4: 交叉验证（如果有 static_facts）
        if static_facts:
            verified_type_bugs = self.cross_validator.validate_type_safety(
                static_facts, llm_bugs
            )
            bugs.extend(verified_type_bugs)

        bugs.extend(llm_bugs)

        return bugs
```

**预期收益**:
- **类型安全 Recall**: 0% → **70%+**（直接解决 7 个漏报中的 5 个）
- **Precision**: 提升到 **90%+**（mypy error 级别置信度高）
- **整体 F1 Score**: 58.23% → **65%+**

**验收标准**:
- [ ] 能正确识别 mypy 的 error 级别问题
- [ ] 能区分 LLM 确认和未确认的情况
- [ ] Benchmark 类型安全类别 Recall ≥ 70%
- [ ] 单元测试覆盖率 ≥ 85%

---

### Week 2: 简化污点分析（针对注入漏洞）

**目标**: 实现单函数内的污点追踪，检测常见注入漏洞

**动机**:
- 注入漏洞 Recall 仅 38.9%（18 个中仅检测 7 个）
- 漏报的 11 个中包含：eval/exec (5 个), 路径遍历 (6 个)

**任务**:
1. 实现 `SimpleTaintDetector` 类
2. 定义污点源、汇、净化器规则
3. 实现单函数内的污点传播分析
4. 集成到 Layer 2
5. 编写测试用例（基于 benchmark 注入漏洞 bugs）

**代码结构**:
```python
# pyscan/layer2/simple_taint_detector.py

import astroid
from typing import List, Set, Dict
from pyscan.bug_detector import BugReport


class SimpleTaintDetector:
    """简化的污点分析（单函数内）"""

    # 污点源（不可信输入）
    SOURCES = {
        'input', 'raw_input',
        'request.args', 'request.form', 'request.json',
        'os.environ', 'sys.argv',
        'socket.recv', 'file.read'
    }

    # 污点汇（危险操作）
    SINKS = {
        'eval': 'CodeInjection',
        'exec': 'CodeInjection',
        'compile': 'CodeInjection',
        'os.system': 'CommandInjection',
        'os.popen': 'CommandInjection',
        'subprocess.call': 'CommandInjection',
        'subprocess.Popen': 'CommandInjection',
        'open': 'PathTraversal',  # 如果参数来自用户输入
    }

    # 净化函数（消毒）
    SANITIZERS = {
        'html.escape', 'urllib.parse.quote',
        'shlex.quote', 'pathlib.Path.resolve'
    }

    def detect_injection_risks(
        self,
        func_node: astroid.FunctionDef,
        func_info
    ) -> List[BugReport]:
        """检测注入漏洞风险"""
        bugs = []

        # 1. 识别污点源
        tainted_vars = self._identify_taint_sources(func_node)

        # 2. 追踪污点传播（简化：赋值传播）
        tainted_vars = self._propagate_taints(func_node, tainted_vars)

        # 3. 检查污点是否到达危险汇
        sink_bugs = self._check_dangerous_sinks(func_node, tainted_vars, func_info)
        bugs.extend(sink_bugs)

        return bugs

    def _identify_taint_sources(
        self,
        func_node: astroid.FunctionDef
    ) -> Set[str]:
        """识别污点源变量"""
        tainted = set()

        for call in func_node.nodes_of_class(astroid.Call):
            func_name = self._get_call_name(call)
            if func_name in self.SOURCES:
                # 如果是赋值，标记目标变量为污点
                if isinstance(call.parent, astroid.Assign):
                    for target in call.parent.targets:
                        if isinstance(target, astroid.AssignName):
                            tainted.add(target.name)

        # 也标记函数参数为潜在污点源
        for arg in func_node.args.args:
            tainted.add(arg.name)

        return tainted

    def _propagate_taints(
        self,
        func_node: astroid.FunctionDef,
        tainted_vars: Set[str]
    ) -> Set[str]:
        """追踪污点传播（简化版：赋值传播）"""
        changed = True
        while changed:
            changed = False
            for assign in func_node.nodes_of_class(astroid.Assign):
                # 检查右侧是否包含污点变量
                value_str = assign.value.as_string()
                if any(var in value_str for var in tainted_vars):
                    # 标记左侧变量为污点
                    for target in assign.targets:
                        if isinstance(target, astroid.AssignName):
                            if target.name not in tainted_vars:
                                tainted_vars.add(target.name)
                                changed = True

        return tainted_vars

    def _check_dangerous_sinks(
        self,
        func_node: astroid.FunctionDef,
        tainted_vars: Set[str],
        func_info
    ) -> List[BugReport]:
        """检查污点是否到达危险汇"""
        bugs = []

        for call in func_node.nodes_of_class(astroid.Call):
            func_name = self._get_call_name(call)
            if func_name in self.SINKS:
                # 检查参数是否污染
                for arg in call.args:
                    arg_str = arg.as_string()
                    if any(var in arg_str for var in tainted_vars):
                        # 检查是否经过净化
                        if not self._is_sanitized(arg, func_node):
                            bugs.append(BugReport(
                                bug_id=self._generate_bug_id(),
                                type=self.SINKS[func_name],
                                severity="critical",
                                description=f"污点数据流向危险函数 {func_name}，可能导致{self.SINKS[func_name]}",
                                location={
                                    'start_line': call.lineno,
                                    'end_line': call.lineno,
                                    'start_col': call.col_offset,
                                    'end_col': call.col_offset
                                },
                                confidence=0.85,
                                evidence={
                                    'taint_source': 'user_input',
                                    'taint_sink': func_name,
                                    'sanitized': False
                                },
                                suggestion=f"对用户输入进行验证和转义后再传递给 {func_name}"
                            ))

        return bugs

    def _is_sanitized(self, arg_node, func_node) -> bool:
        """检查参数是否经过净化"""
        # 简化检查：看参数表达式中是否包含净化函数
        arg_str = arg_node.as_string()
        for sanitizer in self.SANITIZERS:
            if sanitizer in arg_str:
                return True
        return False

    def _get_call_name(self, call: astroid.Call) -> str:
        """获取调用的函数名"""
        try:
            if isinstance(call.func, astroid.Name):
                return call.func.name
            elif isinstance(call.func, astroid.Attribute):
                # os.system -> os.system
                return call.func.as_string()
        except:
            pass
        return ""

    def _generate_bug_id(self) -> str:
        import uuid
        return f"TAINT_{uuid.uuid4().hex[:8]}"
```

**预期收益**:
- **注入漏洞 Recall**: 38.9% → **70%+**（直接解决 11 个漏报中的 8 个）
- **检测的注入类型**: CodeInjection (eval/exec/compile), CommandInjection (os.system/popen), PathTraversal
- **整体 F1 Score**: 65% → **72%+**

**验收标准**:
- [ ] 能检测 eval/exec/compile 代码注入
- [ ] 能检测 os.system/os.popen 命令注入
- [ ] 能检测基本的污点传播（赋值）
- [ ] Benchmark 注入漏洞类别 Recall ≥ 70%
- [ ] 单元测试覆盖率 ≥ 80%

---

### Week 3: 数据流分析（None 检查、变量初始化）

**目标**: 实现基于 Astroid 的数据流分析，检测 None 解引用和未初始化变量

**动机**:
- 数据流问题 Recall 66.7%（15 个中检测 10 个）
- 漏报的 5 个中有 3 个是 None 解引用

**任务**:
1. 实现 `DataFlowAnalyzer` 类
2. 实现 None 检查检测
3. 实现变量初始化检测
4. 集成到 Layer 2
5. 编写测试用例（基于 benchmark 数据流 bugs）

**代码结构**:
```python
# pyscan/layer2/dataflow_analyzer.py

import astroid
from typing import List, Set, Dict
from pyscan.bug_detector import BugReport


class DataFlowAnalyzer:
    """数据流分析器"""

    def detect_none_dereference(
        self,
        func_node: astroid.FunctionDef,
        func_info
    ) -> List[BugReport]:
        """检测潜在的 None 解引用"""
        bugs = []

        # 识别可能为 None 的变量
        nullable_vars = self._identify_nullable_vars(func_node)

        # 检查属性访问和方法调用
        for node in func_node.nodes_of_class(astroid.Attribute):
            obj_name = self._get_object_name(node.expr)
            if obj_name in nullable_vars:
                # 检查之前是否有 None 检查
                if not self._has_none_check_before(obj_name, node, func_node):
                    bugs.append(BugReport(
                        bug_id=self._generate_bug_id(),
                        type="NullPointerDereference",
                        severity="high",
                        description=f"变量 '{obj_name}' 可能为 None，但未检查就访问属性",
                        location={
                            'start_line': node.lineno,
                            'end_line': node.lineno,
                            'start_col': node.col_offset,
                            'end_col': node.col_offset
                        },
                        confidence=0.8,
                        evidence={
                            'variable': obj_name,
                            'nullable': True,
                            'checked': False
                        },
                        suggestion=f"在访问前添加 None 检查：if {obj_name} is not None:"
                    ))

        return bugs

    def _identify_nullable_vars(self, func_node: astroid.FunctionDef) -> Set[str]:
        """识别可能为 None 的变量"""
        nullable = set()

        # 1. 显式赋值为 None
        for assign in func_node.nodes_of_class(astroid.Assign):
            if isinstance(assign.value, astroid.Const) and assign.value.value is None:
                for target in assign.targets:
                    if isinstance(target, astroid.AssignName):
                        nullable.add(target.name)

        # 2. 调用可能返回 None 的函数（如 dict.get）
        for assign in func_node.nodes_of_class(astroid.Assign):
            if isinstance(assign.value, astroid.Call):
                func_name = self._get_call_name(assign.value)
                if func_name in {'get', 'find', 'pop'}:  # 常见返回 None 的方法
                    for target in assign.targets:
                        if isinstance(target, astroid.AssignName):
                            nullable.add(target.name)

        # 3. 有 Optional 类型注解的参数
        for arg in func_node.args.args:
            if arg.annotation:
                annotation_str = arg.annotation.as_string()
                if 'Optional' in annotation_str or 'None' in annotation_str:
                    nullable.add(arg.name)

        return nullable

    def _has_none_check_before(
        self,
        var_name: str,
        usage_node,
        func_node: astroid.FunctionDef
    ) -> bool:
        """检查变量使用前是否有 None 检查"""
        # 向上遍历，查找 if 语句
        parent = usage_node.parent
        while parent and parent != func_node:
            if isinstance(parent, astroid.If):
                # 检查条件是否包含 None 检查
                condition_str = parent.test.as_string()
                if var_name in condition_str and ('is not None' in condition_str or '!= None' in condition_str):
                    return True
            parent = parent.parent

        return False

    def detect_uninitialized_vars(
        self,
        func_node: astroid.FunctionDef,
        func_info
    ) -> List[BugReport]:
        """检测未初始化的变量使用"""
        bugs = []

        # 收集所有变量定义
        defined_vars = set()
        for assign in func_node.nodes_of_class(astroid.Assign):
            for target in assign.targets:
                if isinstance(target, astroid.AssignName):
                    defined_vars.add(target.name)

        # 检查所有变量使用
        for name_node in func_node.nodes_of_class(astroid.Name):
            if name_node.name not in defined_vars:
                # 排除函数参数和全局变量
                if not self._is_param_or_global(name_node.name, func_node):
                    bugs.append(BugReport(
                        bug_id=self._generate_bug_id(),
                        type="UninitializedVariable",
                        severity="high",
                        description=f"变量 '{name_node.name}' 可能在初始化前被使用",
                        location={
                            'start_line': name_node.lineno,
                            'end_line': name_node.lineno,
                            'start_col': name_node.col_offset,
                            'end_col': name_node.col_offset
                        },
                        confidence=0.75,
                        evidence={
                            'variable': name_node.name,
                            'initialized': False
                        },
                        suggestion=f"在使用前初始化变量 {name_node.name}"
                    ))

        return bugs

    def _is_param_or_global(self, var_name: str, func_node: astroid.FunctionDef) -> bool:
        """检查变量是否是参数或全局变量"""
        # 检查参数
        for arg in func_node.args.args:
            if arg.name == var_name:
                return True

        # 检查 global 声明
        for node in func_node.nodes_of_class(astroid.Global):
            if var_name in node.names:
                return True

        return False

    def _get_object_name(self, node) -> str:
        """获取对象名称"""
        if isinstance(node, astroid.Name):
            return node.name
        return ""

    def _get_call_name(self, call: astroid.Call) -> str:
        """获取调用的函数名"""
        if isinstance(call.func, astroid.Attribute):
            return call.func.attrname
        elif isinstance(call.func, astroid.Name):
            return call.func.name
        return ""

    def _generate_bug_id(self) -> str:
        import uuid
        return f"DATAFLOW_{uuid.uuid4().hex[:8]}"
```

**预期收益**:
- **数据流问题 Recall**: 66.7% → **85%+**（直接解决 5 个漏报中的 4 个）
- **检测的数据流问题**: None 解引用、未初始化变量
- **整体 F1 Score**: 72% → **78%+**

**验收标准**:
- [ ] 能检测可能为 None 的变量访问
- [ ] 能检测未初始化变量使用
- [ ] 能识别 None 检查（if var is not None）
- [ ] Benchmark 数据流问题类别 Recall ≥ 85%
- [ ] 单元测试覆盖率 ≥ 80%

---

### Week 4: 降低误报率（上下文管理器检测 + 验证增强）

**目标**: 实现上下文管理器检测器，通过静态分析降低 LLM 的误报

**动机**:
- 当前 False Positive 率 47.7%（63 个误报）
- 资源管理和并发安全 Recall 已 100%，但可能有误报
- 通过静态分析验证，可以过滤掉不合理的 LLM 报告

**任务**:
1. 实现 `ContextManagerDetector` 类（基于 PoC）
2. 实现误报过滤逻辑
3. 集成到 Layer 4 验证流程
4. 编写测试用例

**代码结构**:
```python
# pyscan/layer2/context_manager_detector.py

import astroid
from typing import List, Set
from pyscan.bug_detector import BugReport


class ContextManagerDetector:
    """基于 Astroid 的上下文管理器检测器"""

    RESOURCE_TYPES = {
        'open', 'ThreadPoolExecutor', 'ProcessPoolExecutor',
        'Lock', 'RLock', 'Semaphore', 'Condition',
        'socket', 'urlopen', 'Session', 'connection', 'cursor'
    }

    def detect_resource_leaks(
        self,
        func_node: astroid.FunctionDef,
        func_info
    ) -> List[BugReport]:
        """检测资源泄漏风险"""
        bugs = []

        for assign in func_node.nodes_of_class(astroid.Assign):
            if not isinstance(assign.value, astroid.Call):
                continue

            func_name = self._get_call_name(assign.value)
            if func_name in self.RESOURCE_TYPES:
                # 检查是否在 with 中或有显式 cleanup
                if not self._is_safely_managed(assign, func_node):
                    bugs.append(BugReport(
                        bug_id=self._generate_bug_id(),
                        type="ResourceLeakRisk",
                        severity="high",
                        description=f"资源 {func_name} 未使用上下文管理器，可能泄漏",
                        location={
                            'start_line': assign.lineno,
                            'end_line': assign.lineno,
                            'start_col': assign.col_offset,
                            'end_col': assign.col_offset
                        },
                        confidence=0.9,
                        evidence={
                            'resource_type': func_name,
                            'in_with': False,
                            'explicit_cleanup': False
                        },
                        suggestion=f"使用 with 语句管理资源：with {func_name}(...) as var:"
                    ))

        return bugs

    def _is_safely_managed(self, assign, func_node) -> bool:
        """检查资源是否安全管理"""
        # 1. 检查是否在 with 中
        if self._is_in_with_statement(assign):
            return True

        # 2. 检查是否有显式 cleanup（如 .close(), .release()）
        var_names = [t.name for t in assign.targets if isinstance(t, astroid.AssignName)]
        if self._has_cleanup_call(func_node, var_names):
            return True

        return False

    def _is_in_with_statement(self, node) -> bool:
        """检查节点是否在 with 语句中"""
        parent = node.parent
        while parent:
            if isinstance(parent, astroid.With):
                return True
            parent = parent.parent
        return False

    def _has_cleanup_call(self, func_node, var_names) -> bool:
        """检查是否有显式的清理调用"""
        cleanup_methods = {'close', 'release', 'shutdown', 'quit'}

        for call in func_node.nodes_of_class(astroid.Call):
            if isinstance(call.func, astroid.Attribute):
                if call.func.attrname in cleanup_methods:
                    obj_name = self._get_object_name(call.func.expr)
                    if obj_name in var_names:
                        return True
        return False

    def _get_call_name(self, call: astroid.Call) -> str:
        """获取调用的函数名"""
        if isinstance(call.func, astroid.Name):
            return call.func.name
        elif isinstance(call.func, astroid.Attribute):
            return call.func.attrname
        return ""

    def _get_object_name(self, node) -> str:
        """获取对象名称"""
        if isinstance(node, astroid.Name):
            return node.name
        return ""

    def _generate_bug_id(self) -> str:
        import uuid
        return f"RESOURCE_{uuid.uuid4().hex[:8]}"
```

**误报过滤逻辑**:
```python
# pyscan/layer4/false_positive_filter.py

class FalsePositiveFilter:
    """误报过滤器"""

    def filter_llm_bugs(
        self,
        llm_bugs: List[BugReport],
        layer2_bugs: List[BugReport]
    ) -> List[BugReport]:
        """
        过滤 LLM 的误报

        策略：
        1. 如果 Layer 2 未发现问题，但 LLM 报告了，降低置信度
        2. 如果两者都发现，提升置信度
        """
        filtered = []

        for llm_bug in llm_bugs:
            # 检查 Layer 2 是否确认
            layer2_confirmed = self._check_layer2_confirmation(llm_bug, layer2_bugs)

            if layer2_confirmed:
                # 提升置信度
                llm_bug.confidence = min(llm_bug.confidence * 1.2, 0.99)
                filtered.append(llm_bug)
            else:
                # 降低置信度
                llm_bug.confidence = llm_bug.confidence * 0.8
                # 只保留高置信度的
                if llm_bug.confidence >= 0.7:
                    filtered.append(llm_bug)

        return filtered

    def _check_layer2_confirmation(
        self,
        llm_bug: BugReport,
        layer2_bugs: List[BugReport]
    ) -> bool:
        """检查 Layer 2 是否确认了 LLM 的发现"""
        for l2_bug in layer2_bugs:
            # 位置匹配
            if abs(l2_bug.location['start_line'] - llm_bug.location['start_line']) <= 3:
                # 类型匹配
                if l2_bug.type == llm_bug.type or l2_bug.type in llm_bug.description:
                    return True
        return False
```

**预期收益**:
- **False Positive 率**: 47.7% → **<30%**
- **Precision**: 52.27% → **65%+**
- **整体 F1 Score**: 78% → **82%+**

**验收标准**:
- [ ] 能检测常见资源泄漏模式
- [ ] 能识别 with 语句中的安全管理
- [ ] 能识别显式的 cleanup 调用
- [ ] False Positive 率 < 30%
- [ ] 单元测试覆盖率 ≥ 80%

---

## 3. 整体架构调整

### 新的 Pipeline 流程

```
┌───────────────────────────────────────────────────────────────┐
│                      输入：Python 代码库                        │
└───────────────────────────────────────────────────────────────┘
                                ↓
┌───────────────────────────────────────────────────────────────┐
│  Layer 1: 快速静态检查（mypy + bandit）                        │
│  输出: StaticFacts（类型错误、安全问题）                         │
└───────────────────────────────────────────────────────────────┘
                                ↓
┌───────────────────────────────────────────────────────────────┐
│  Layer 2: 深度静态分析（Astroid）                               │
│  ┌─────────────┬─────────────┬─────────────────────────────┐ │
│  │ 污点分析     │ 数据流分析   │ 上下文管理器检测             │ │
│  │ (Week 2)    │ (Week 3)    │ (Week 4)                    │ │
│  └─────────────┴─────────────┴─────────────────────────────┘ │
│  输出: Layer2Bugs（高置信度的静态分析结果）                      │
└───────────────────────────────────────────────────────────────┘
                                ↓
┌───────────────────────────────────────────────────────────────┐
│  Layer 3: LLM 深度推理                                          │
│  输入: 代码 + Layer 1 Facts + Layer 2 Bugs                     │
│  输出: LLMBugs（候选 Bug + 推理链）                             │
└───────────────────────────────────────────────────────────────┘
                                ↓
┌───────────────────────────────────────────────────────────────┐
│  Layer 4: 验证和融合（NEW）                                     │
│  ┌─────────────┬─────────────┬─────────────────────────────┐ │
│  │ 交叉验证     │ 置信度评分   │ 误报过滤                     │ │
│  │ (Week 1)    │ (Week 1)    │ (Week 4)                    │ │
│  └─────────────┴─────────────┴─────────────────────────────┘ │
│  输出: VerifiedBugs（高置信度 Bug + 证据链）                    │
└───────────────────────────────────────────────────────────────┘
                                ↓
┌───────────────────────────────────────────────────────────────┐
│                输出：增强的 Bug 报告                             │
└───────────────────────────────────────────────────────────────┘
```

---

## 4. 预期效果评估

### 4.1 按类别改进预测

| Bug 类别 | 当前 Recall | Stage 2 目标 | 改进方案 | 预期改进幅度 |
|---------|------------|------------|---------|-------------|
| **类型安全** | 0% | **80%** | Week 1: 交叉验证 | +80% |
| **注入漏洞** | 38.9% | **75%** | Week 2: 污点分析 | +36.1% |
| **数据流问题** | 66.7% | **85%** | Week 3: 数据流分析 | +18.3% |
| **输入验证** | 30.0% | 35% | 间接改进（污点分析） | +5% |
| **API 使用** | 33.3% | 35% | 暂无直接改进 | +1.7% |
| **错误处理** | 86.7% | 90% | 保持 | +3.3% |
| **资源管理** | 100% | 100% | Week 4: 降低误报 | 0% |
| **并发安全** | 100% | 100% | Week 4: 降低误报 | 0% |

### 4.2 整体指标预测

| 指标 | 当前 v1.1 | Stage 2 目标 | 改进幅度 | 达成策略 |
|------|----------|------------|---------|---------|
| **Precision** | 52.27% | **70%+** | +17.7% | Week 4: 误报过滤 |
| **Recall** | 65.71% | **85%+** | +19.3% | Week 1-3: 填补 Gap |
| **F1 Score** | 58.23% | **77%+** | +18.8% | 综合改进 |
| **FP 率** | 47.7% | **<30%** | -17.7% | Week 4: 过滤 |
| **FN 数** | 36 | **<20** | -44% | Week 1-3: 检测能力 |

### 4.3 里程碑指标

| 里程碑 | 日期 | 目标 F1 Score | 验收标准 |
|--------|------|--------------|---------|
| **M1: Week 1 完成** | Week 1 end | 65%+ | 类型安全 Recall ≥ 70% |
| **M2: Week 2 完成** | Week 2 end | 70%+ | 注入漏洞 Recall ≥ 70% |
| **M3: Week 3 完成** | Week 3 end | 75%+ | 数据流问题 Recall ≥ 85% |
| **M4: Week 4 完成** | Week 4 end | **77%+** | FP 率 < 30% |

---

## 5. 风险管理

### 5.1 技术风险

| 风险 | 可能性 | 影响 | 缓解措施 | 应对计划 |
|------|--------|------|---------|---------|
| **Astroid 解析失败** | 中 | 高 | 优雅降级到 LLM | 添加 try-except 保护 |
| **污点分析误报** | 高 | 中 | LLM 二次确认 | Week 4 过滤机制 |
| **性能下降** | 中 | 中 | 增量分析、缓存 | 性能测试验证 |
| **Week 1 目标过高** | 中 | 高 | 降低目标到 60% | 灵活调整计划 |

### 5.2 进度风险

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|---------|
| **Week 1 延期** | 中 | 高 | 预留 buffer，可延 2 天 |
| **Week 2 污点分析复杂** | 高 | 中 | 简化规则，仅覆盖常见模式 |
| **Week 3-4 时间不足** | 中 | 中 | 降低 Week 4 优先级 |

---

## 6. 成功标准

### 6.1 必达指标（P0）

- [ ] **类型安全 Recall ≥ 70%**（直接解决 7 个漏报中的 5 个）
- [ ] **注入漏洞 Recall ≥ 70%**（直接解决 11 个漏报中的 8 个）
- [ ] **整体 F1 Score ≥ 75%**
- [ ] **所有 Stage 1 测试仍通过**（无回归）

### 6.2 期望指标（P1）

- [ ] **数据流问题 Recall ≥ 85%**
- [ ] **False Positive 率 < 30%**
- [ ] **整体 F1 Score ≥ 77%**
- [ ] **单元测试覆盖率 ≥ 85%**

### 6.3 挑战指标（P2）

- [ ] **整体 Precision ≥ 70%**
- [ ] **整体 Recall ≥ 85%**
- [ ] **F1 Score ≥ 80%**

---

## 7. 测试策略

### 7.1 单元测试

每个 Week 完成后，编写对应的单元测试：

- **Week 1**: `tests/test_layer4/test_cross_validator.py`（≥20 个测试）
- **Week 2**: `tests/test_layer2/test_simple_taint_detector.py`（≥25 个测试）
- **Week 3**: `tests/test_layer2/test_dataflow_analyzer.py`（≥25 个测试）
- **Week 4**: `tests/test_layer2/test_context_manager_detector.py`（≥20 个测试）

### 7.2 集成测试

每个 Week 完成后，在 benchmark 上运行完整评估：

```bash
# 运行 PyScan
python -m pyscan benchmark/categories -o benchmark_report_week{N}.json

# 评估结果
python benchmark/analyze_evaluation.py

# 对比上一 Week
python benchmark/compare_weeks.py week{N-1} week{N}
```

### 7.3 性能测试

Week 4 完成后，验证性能：

- 扫描速度: < 2x Stage 1（目标：1000 行代码 < 10 秒）
- 内存占用: < 500MB（中等项目）
- 缓存效果: 第二次扫描 < 5 秒

---

## 8. 依赖和资源

### 8.1 新增依赖

```txt
# requirements.txt 新增
astroid>=4.0.1
```

### 8.2 开发资源

- **开发者**: 1 人（全职 4 周）
- **测试**: 每周末进行 benchmark 评估（半天）
- **Review**: 每周五进行 code review（1 小时）

### 8.3 参考资料

- **Astroid 文档**: https://pylint.readthedocs.io/projects/astroid/
- **PoC 代码**: `poc_context_manager_detector.py`
- **Benchmark 评估**: `benchmark/DETAILED_ANALYSIS.md`

---

## 9. 下一步行动

### 立即开始（本周）

1. **Review 本计划**：确认优先级和目标
2. **准备环境**：安装 astroid，验证 PoC
3. **启动 Week 1**：创建 `pyscan/layer4/` 目录，实现 CrossValidator

### Week 1 第一天任务

- [ ] 创建 `pyscan/layer4/__init__.py`
- [ ] 创建 `pyscan/layer4/cross_validator.py`
- [ ] 实现 `CrossValidator.validate_type_safety()` 方法
- [ ] 编写前 5 个单元测试
- [ ] 集成到 `bug_detector.py`

---

## 10. 版本历史

- **v1.0** (2025-10-19): 初始版本（基于 Astroid PoC）
- **v2.0** (2025-10-20): 基于 Benchmark 评估结果重大调整
  - 优先级重排：Layer 4 → 污点分析 → 数据流分析 → 上下文管理器
  - 目标重定：从"完善资源管理"转向"解决最大 Gap"
  - 新增 Week 1 Layer 4 交叉验证任务
  - 调整 Week 2-4 任务优先级

---

**本计划是数据驱动的决策结果，基于真实的 benchmark 评估数据。通过聚焦最大 Gap（类型安全、注入漏洞、数据流），预期可以将 F1 Score 从 58.23% 提升到 77%+。**
