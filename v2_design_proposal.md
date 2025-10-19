# PyScan v2.0 设计提案

## 文档信息

- **版本**: v2.0
- **日期**: 2025-01-19
- **作者**: Claude & hwuu
- **状态**: 提案阶段

---

## 1. 背景与动机

### 1.1 当前版本的局限性

PyScan v1.0 采用纯 LLM 驱动的方式进行代码分析，存在以下问题：

| 问题 | 描述 | 影响 |
|------|------|------|
| **高误报率** | LLM 可能产生误报，约 35% | 降低用户信任度 |
| **低召回率** | 依赖 LLM 的"直觉"，约 40% | 漏掉真实 bug |
| **高成本** | 每个函数都调用 LLM API | 大项目成本高 |
| **分析浅** | 缺乏深度静态分析支持 | 只能发现表面问题 |
| **可解释性差** | 缺乏推理链和证据 | 难以验证结果 |
| **速度慢** | 串行调用 API | 大项目耗时长 |

### 1.2 设计目标

PyScan v2.0 的核心目标：

1. **提升准确率**：从 60% → 85%+（通过多层验证）
2. **降低误报**：从 35% → 15%（通过交叉验证）
3. **提高召回率**：从 40% → 70%+（通过深度分析）
4. **降低成本**：减少 50% API 调用（通过分层过滤）
5. **增强可解释性**：提供完整推理链和证据
6. **保持灵活性**：LLM 负责复杂推理，工具负责基础分析

---

## 2. 核心设计理念

### 2.1 设计哲学

**"人如何做深度静态分析？"**

```
人的流程：
1. 快速扫描代码，识别明显问题（语法、类型）
2. 构建代码的心智模型（控制流、数据流）
3. 深度推理业务逻辑和边界条件
4. 验证发现的问题（构造测试用例）
5. 生成报告和修复建议
```

**PyScan v2.0 模拟这个流程：**

```
Layer 1: 开源工具快速扫描
    ↓
Layer 2: 深度静态分析引擎
    ↓
Layer 3: LLM 深度推理
    ↓
Layer 4: 验证和融合
    ↓
输出: 高置信度报告
```

### 2.2 三个核心原则

1. **分层处理 (Layered Analysis)**
   - 每层专注于自己擅长的任务
   - 层与层之间传递结构化信息
   - 避免重复计算

2. **优势互补 (Complementary Strengths)**
   - 工具：精确、快速、便宜（规则匹配、类型检查）
   - LLM：灵活、深度、昂贵（业务逻辑、复杂推理）
   - 符号执行：严格、慢、准确（路径验证）

3. **相互验证 (Cross-Validation)**
   - 工具发现 + LLM 确认 = 高置信度
   - LLM 发现 + 符号验证 = 可靠结果
   - 多个证据链 = 低误报率

---

## 3. 系统架构设计

### 3.1 总体架构

```
┌──────────────────────────────────────────────────────────┐
│                   输入：Python 代码库                      │
└──────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────┐
│  Layer 1: 快速静态检查（开源工具集成）                     │
│  ┌────────────┬────────────┬────────────┬──────────────┐ │
│  │   Pylint   │   Mypy     │  Bandit    │   Semgrep    │ │
│  │  语法/风格  │  类型检查   │  安全扫描   │  模式匹配    │ │
│  └────────────┴────────────┴────────────┴──────────────┘ │
│  输出: Facts（类型信息、已知问题、安全漏洞）                 │
└──────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────┐
│  Layer 2: 深度静态分析（自研分析引擎）                      │
│  ┌────────────┬────────────┬────────────┬──────────────┐ │
│  │  CFG/DFG   │  调用图     │  污点分析   │  符号执行    │ │
│  │  构建       │  分析       │  引擎       │  引擎        │ │
│  └────────────┴────────────┴────────────┴──────────────┘ │
│  输出: 分析结果（可疑点、污点流、路径约束）                  │
└──────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────┐
│  Layer 3: LLM 深度推理（增强的 Prompt）                    │
│  输入: 代码 + Layer 1 Facts + Layer 2 分析结果              │
│  任务:                                                     │
│  • 业务逻辑错误识别                                         │
│  • 复杂约束推理                                            │
│  • 边界条件分析                                            │
│  • 新型 bug 模式发现                                       │
│  输出: 候选 Bug + 推理链 + 置信度                           │
└──────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────┐
│  Layer 4: 验证和融合（智能过滤引擎）                        │
│  ┌────────────┬────────────┬────────────┬──────────────┐ │
│  │ 交叉验证    │ 测试生成    │ 符号验证    │ 优先级排序  │ │
│  │ (多源确认)  │ (Hypothesis)│    (Z3)    │  (评分)     │ │
│  └────────────┴────────────┴────────────┴──────────────┘ │
│  输出: 高置信度 Bug + 证据链                                │
└──────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────┐
│         输出：增强的 Bug 报告（含推理链和证据）              │
└──────────────────────────────────────────────────────────┘
```

### 3.2 数据流设计

```python
# 数据结构示例

# Layer 1 输出: Facts
class StaticFacts:
    file_path: str
    function: FunctionInfo

    # 工具发现的问题
    type_errors: List[TypeIssue]        # mypy
    security_issues: List[SecurityIssue] # bandit
    lint_warnings: List[LintWarning]     # pylint
    pattern_matches: List[PatternMatch]  # semgrep

    # 提取的元信息
    type_annotations: Dict[str, Type]    # 类型信息
    decorators: List[str]
    complexity_score: int

# Layer 2 输出: 分析结果
class DeepAnalysisResult:
    # 图结构
    cfg: ControlFlowGraph
    dfg: DataFlowGraph
    call_graph: CallGraph

    # 分析结果
    taint_flows: List[TaintFlow]
    suspicious_points: List[SuspiciousPoint]
    path_constraints: List[PathConstraint]

    # 推断信息
    invariants: List[Invariant]
    possible_values: Dict[Var, ValueRange]

# Layer 3 输出: LLM 分析
class LLMAnalysisResult:
    bugs: List[CandidateBug]

    class CandidateBug:
        type: str
        severity: str
        description: str
        location: Location
        trigger_condition: str       # 触发条件
        reasoning_chain: List[str]   # 推理链
        confidence: float            # LLM 自评置信度
        fix_suggestion: str

# Layer 4 输出: 验证结果
class VerifiedBug:
    bug: CandidateBug

    # 验证证据
    evidence: Evidence

    class Evidence:
        supported_by_layer1: bool    # 是否被工具确认
        supported_by_layer2: bool    # 是否被深度分析支持
        test_case: Optional[TestCase] # 生成的测试用例
        symbolic_proof: Optional[Proof] # 符号验证结果

    # 最终评分
    final_confidence: float          # 0.0 - 1.0
    priority_score: float            # 综合优先级
```

---

## 4. 各层详细设计

### 4.1 Layer 1: 快速静态检查

#### 4.1.1 集成的工具

| 工具 | 用途 | 输出 |
|------|------|------|
| **mypy** | 类型检查 | 类型错误、类型推断结果 |
| **pyright** | 高级类型检查 | 更严格的类型错误 |
| **pylint** | 代码质量 | 代码风格、潜在问题 |
| **bandit** | 安全扫描 | SQL 注入、命令注入等 |
| **semgrep** | 模式匹配 | 自定义规则匹配 |

#### 4.1.2 实现接口

```python
class Layer1Analyzer:
    """快速静态检查层"""

    def __init__(self):
        self.mypy_runner = MypyRunner()
        self.bandit_runner = BanditRunner()
        self.pylint_runner = PylintRunner()
        self.semgrep_runner = SemgrepRunner()

    def analyze(self, file_path: str) -> StaticFacts:
        """
        运行所有第一层工具，收集基础 facts

        执行流程：
        1. 并行运行所有工具（节省时间）
        2. 解析工具输出，转换为统一格式
        3. 提取类型信息、安全问题等
        4. 计算代码复杂度
        """
        # 并行运行工具
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {
                'mypy': executor.submit(self.mypy_runner.run, file_path),
                'bandit': executor.submit(self.bandit_runner.run, file_path),
                'pylint': executor.submit(self.pylint_runner.run, file_path),
                'semgrep': executor.submit(self.semgrep_runner.run, file_path),
            }

            results = {
                name: future.result()
                for name, future in futures.items()
            }

        # 转换为统一格式
        facts = self._convert_to_facts(results, file_path)
        return facts

    def _convert_to_facts(self, results, file_path):
        """将工具输出转换为 StaticFacts 对象"""
        pass
```

#### 4.1.3 预期收益

- **过滤 70% 的低级错误**（类型错误、语法错误）
- **提供准确的类型信息**（辅助后续分析）
- **快速识别安全漏洞**（SQL 注入、XSS 等）
- **减少 LLM 负担**（不需要 LLM 分析明显问题）

---

### 4.2 Layer 2: 深度静态分析

#### 4.2.1 核心组件

##### a) CFG/DFG 构建器

```python
class CFGBuilder:
    """控制流图构建器"""

    def build(self, function: FunctionInfo) -> ControlFlowGraph:
        """
        构建控制流图

        节点类型：
        - BasicBlock: 基本块（顺序执行）
        - BranchNode: 分支节点（if/while）
        - ReturnNode: 返回节点
        - ExceptionNode: 异常节点

        边类型：
        - 正常流
        - 真分支
        - 假分支
        - 异常流
        """
        ast_tree = ast.parse(function.code)

        cfg = ControlFlowGraph()
        # AST -> CFG 转换逻辑
        # ...

        return cfg

class DFGBuilder:
    """数据流图构建器"""

    def build(self, function: FunctionInfo, cfg: CFG) -> DataFlowGraph:
        """
        构建数据流图（基于 CFG）

        分析内容：
        - 变量定义点（def）
        - 变量使用点（use）
        - 到达定义（reaching definitions）
        - 活跃变量（live variables）
        """
        dfg = DataFlowGraph()

        # 到达定义分析
        reaching_defs = self._compute_reaching_definitions(cfg)

        # 构建 def-use 链
        def_use_chains = self._build_def_use_chains(reaching_defs)

        dfg.def_use_chains = def_use_chains
        return dfg
```

##### b) 污点分析引擎

```python
class TaintAnalyzer:
    """污点分析引擎"""

    # 污点源（不可信输入）
    SOURCES = {
        'input', 'raw_input',
        'request.args', 'request.form', 'request.json',
        'os.environ', 'sys.argv',
        'socket.recv', 'file.read'
    }

    # 污点汇（危险操作）
    SINKS = {
        'eval', 'exec', 'compile',
        'os.system', 'subprocess.call', 'subprocess.Popen',
        'open', 'file',
        '*.execute',  # SQL 执行
        '*.render',   # 模板渲染
    }

    # 净化函数（消毒）
    SANITIZERS = {
        'html.escape', 'urllib.parse.quote',
        'bleach.clean', 'markupsafe.escape',
    }

    def analyze(self, dfg: DataFlowGraph) -> List[TaintFlow]:
        """
        污点分析算法（前向数据流分析）

        步骤：
        1. 标记所有污点源
        2. 沿着数据流传播污点
        3. 检查污点是否到达危险汇
        4. 检查中间是否经过净化
        """
        taint_flows = []

        # 1. 初始化：标记污点源
        tainted_vars = self._mark_sources(dfg)

        # 2. 传播污点（不动点迭代）
        changed = True
        while changed:
            changed = False
            for node in dfg.nodes:
                if isinstance(node, AssignNode):
                    # var = expr
                    # 如果 expr 中有污点变量，var 也被污染
                    if any(v in tainted_vars for v in node.expr_vars):
                        if node.target not in tainted_vars:
                            tainted_vars.add(node.target)
                            changed = True

        # 3. 检查污点是否到达 sink
        for node in dfg.nodes:
            if self._is_sink(node):
                for arg in node.args:
                    if arg in tainted_vars:
                        # 检查是否经过净化
                        if not self._is_sanitized(arg, node, dfg):
                            taint_flows.append(TaintFlow(
                                source=self._find_source(arg, dfg),
                                sink=node,
                                path=self._trace_path(arg, node, dfg),
                                sanitized=False
                            ))

        return taint_flows
```

##### c) 符号执行引擎

```python
class SymbolicExecutor:
    """轻量级符号执行引擎（基于 Z3）"""

    def __init__(self):
        from z3 import Solver, Int, Bool, sat, unsat
        self.solver = Solver()

    def explore_paths(self, cfg: CFG, max_depth: int = 5) -> List[Path]:
        """
        探索可行路径（深度优先，有限深度）

        对于每条路径：
        - 收集路径约束（条件）
        - 使用 Z3 检查可满足性
        - 保存可行路径
        """
        feasible_paths = []

        def dfs(node, path, constraints, depth):
            if depth > max_depth or node in path:
                return

            path = path + [node]

            # 到达出口
            if cfg.is_exit(node):
                # 检查路径约束是否可满足
                if self._is_satisfiable(constraints):
                    feasible_paths.append(Path(path, constraints))
                return

            # 分支节点
            if isinstance(node, BranchNode):
                condition = node.condition

                # 探索真分支
                true_constraints = constraints + [condition]
                if self._is_satisfiable(true_constraints):
                    dfs(node.true_succ, path, true_constraints, depth + 1)

                # 探索假分支
                false_constraints = constraints + [Not(condition)]
                if self._is_satisfiable(false_constraints):
                    dfs(node.false_succ, path, false_constraints, depth + 1)
            else:
                # 普通节点
                for succ in cfg.successors(node):
                    dfs(succ, path, constraints, depth + 1)

        dfs(cfg.entry, [], [], 0)
        return feasible_paths

    def _is_satisfiable(self, constraints: List) -> bool:
        """使用 Z3 检查约束可满足性"""
        from z3 import Solver, sat

        solver = Solver()
        for c in constraints:
            solver.add(c)

        return solver.check() == sat

    def find_bug_trigger(self, bug: Bug, cfg: CFG) -> Optional[Input]:
        """
        为 bug 生成触发输入（反向符号执行）

        给定：bug 位置和触发条件
        求解：满足到达该位置的输入
        """
        # 找到从入口到 bug 位置的路径
        path = self._find_path_to_bug(cfg, bug.location)
        if not path:
            return None

        # 收集路径约束
        constraints = self._collect_path_constraints(path)

        # 添加 bug 触发条件
        constraints.append(bug.trigger_condition)

        # 求解
        from z3 import Solver, sat
        solver = Solver()
        for c in constraints:
            solver.add(c)

        if solver.check() == sat:
            model = solver.model()
            return self._extract_input(model)

        return None
```

##### d) 可疑点识别器

```python
class SuspiciousPointDetector:
    """识别代码中的可疑点"""

    def detect(self, function: FunctionInfo,
               facts: StaticFacts,
               cfg: CFG, dfg: DFG) -> List[SuspiciousPoint]:
        """
        识别可疑点（启发式规则）

        可疑模式：
        1. 空指针解引用风险
        2. 数组越界风险
        3. 除零风险
        4. 资源泄漏风险
        5. 类型不匹配
        6. 未检查的返回值
        """
        suspicious = []

        # 规则 1: None 检查缺失
        suspicious.extend(self._detect_null_deref(dfg, facts))

        # 规则 2: 除零检查缺失
        suspicious.extend(self._detect_div_by_zero(cfg, dfg))

        # 规则 3: 数组访问未检查边界
        suspicious.extend(self._detect_array_bounds(cfg, dfg))

        # 规则 4: 资源未释放
        suspicious.extend(self._detect_resource_leak(cfg, dfg))

        # 规则 5: 类型不匹配（基于 mypy 结果）
        suspicious.extend(self._detect_type_mismatch(facts))

        return suspicious

    def _detect_null_deref(self, dfg, facts):
        """检测潜在的 None 解引用"""
        suspicious = []

        for node in dfg.nodes:
            if isinstance(node, AttributeAccessNode):
                # obj.attr
                obj_var = node.object

                # 检查 obj 是否可能为 None
                if self._may_be_none(obj_var, dfg, facts):
                    # 检查之前是否有 None 检查
                    if not self._has_none_check_before(obj_var, node, dfg):
                        suspicious.append(SuspiciousPoint(
                            type='potential_null_deref',
                            location=node.location,
                            description=f'{obj_var} 可能为 None，但未检查',
                            severity='high'
                        ))

        return suspicious
```

#### 4.2.2 实现接口

```python
class Layer2Analyzer:
    """深度静态分析层"""

    def __init__(self):
        self.cfg_builder = CFGBuilder()
        self.dfg_builder = DFGBuilder()
        self.taint_analyzer = TaintAnalyzer()
        self.symbolic_executor = SymbolicExecutor()
        self.suspicious_detector = SuspiciousPointDetector()

    def analyze(self, function: FunctionInfo,
                facts: StaticFacts) -> DeepAnalysisResult:
        """
        深度静态分析主流程
        """
        # 1. 构建 CFG
        cfg = self.cfg_builder.build(function)

        # 2. 构建 DFG
        dfg = self.dfg_builder.build(function, cfg)

        # 3. 污点分析
        taint_flows = self.taint_analyzer.analyze(dfg)

        # 4. 符号执行（有限深度）
        paths = self.symbolic_executor.explore_paths(cfg, max_depth=5)

        # 5. 识别可疑点
        suspicious = self.suspicious_detector.detect(
            function, facts, cfg, dfg
        )

        return DeepAnalysisResult(
            cfg=cfg,
            dfg=dfg,
            taint_flows=taint_flows,
            paths=paths,
            suspicious_points=suspicious,
            path_constraints=[p.constraints for p in paths]
        )
```

---

### 4.3 Layer 3: LLM 深度推理

#### 4.3.1 增强的 Prompt 设计

```python
class Layer3Analyzer:
    """LLM 深度推理层"""

    def analyze(self, function: FunctionInfo,
                facts: StaticFacts,
                deep_analysis: DeepAnalysisResult,
                context: Dict) -> LLMAnalysisResult:
        """
        构建增强的 prompt 并调用 LLM
        """
        prompt = self._build_enhanced_prompt(
            function, facts, deep_analysis, context
        )

        response = self.llm.chat(prompt)

        result = self._parse_llm_response(response)
        return result

    def _build_enhanced_prompt(self, function, facts, analysis, context):
        """
        构建分层的、结构化的 prompt

        Prompt 结构示例（作为字符串发送给 LLM）：
        - 第 1 部分：目标代码（函数源码 + 元信息）
        - 第 2 部分：静态检查结果（Layer 1 工具发现的问题）
        - 第 3 部分：深度分析结果（Layer 2 的可疑点、污点流、路径分析）
        - 第 4 部分：调用上下文（callers/callees）
        - 第 5 部分：任务描述（要求 LLM 专注深层次逻辑错误）
        """
        sections = []

        # 第 1 部分：构建目标函数信息
        code_section = f"# 目标函数\n\n"
        code_section += f"```python\n{function.code}\n```\n\n"
        code_section += "**元信息**：\n"
        code_section += f"- 文件：{function.file_path}\n"
        code_section += f"- 行号：{function.start_line} - {function.end_line}\n"
        code_section += f"- 复杂度：{facts.complexity_score}\n"
        code_section += f"- 是否公共 API：{context.get('is_public_api', False)}\n"
        sections.append(code_section)

        # 第 2 部分：静态检查结果
        if facts.type_errors or facts.security_issues or facts.lint_warnings:
            static_section = "# 静态检查工具发现的问题\n\n"

            if facts.type_errors:
                static_section += "## 类型错误（Mypy）\n"
                for err in facts.type_errors:
                    static_section += f"- Line {err.line}: {err.message}\n"

            if facts.security_issues:
                static_section += "\n## 安全问题（Bandit）\n"
                for issue in facts.security_issues:
                    static_section += f"- Line {issue.line}: [{issue.severity}] {issue.message}\n"

            if facts.lint_warnings:
                static_section += "\n## 代码质量问题（Pylint）\n"
                for warn in facts.lint_warnings[:5]:
                    static_section += f"- Line {warn.line}: {warn.message}\n"

            sections.append(static_section)

        # 第 3 部分：深度分析结果
        deep_section = "# 深度静态分析结果\n\n"

        if analysis.suspicious_points:
            deep_section += "## 识别的可疑点\n"
            for sp in analysis.suspicious_points:
                deep_section += f"- **类型**: {sp.type}\n"
                deep_section += f"- **位置**: Line {sp.location.line}\n"
                deep_section += f"- **描述**: {sp.description}\n"
                deep_section += f"- **严重程度**: {sp.severity}\n\n"

        if analysis.taint_flows:
            deep_section += "## 污点流分析\n"
            for flow in analysis.taint_flows:
                deep_section += f"- **污点源**: {flow.source} (Line {flow.source_line})\n"
                deep_section += f"- **污点汇**: {flow.sink} (Line {flow.sink_line})\n"
                deep_section += f"- **路径**: {' → '.join(flow.path)}\n"
                deep_section += f"- **已净化**: {flow.sanitized}\n\n"

        if analysis.path_constraints:
            deep_section += "## 路径分析\n"
            deep_section += f"- 发现 {len(analysis.paths)} 条可行路径\n"
            for i, path in enumerate(analysis.paths[:3], 1):
                deep_section += f"\n**路径 {i}**:\n"
                deep_section += f"- 约束: {path.constraints}\n"

        sections.append(deep_section)

        # 第 4 部分：调用上下文
        context_section = "# 调用上下文\n\n"

        if context.get('callers'):
            context_section += f"## 调用者 ({len(context['callers'])} 个)\n"
            for caller in context['callers'][:3]:
                context_section += f"- **函数**: {caller['function_name']}\n"
                context_section += f"- **文件**: {caller['file_path']}\n"
                context_section += f"- **调用行**: {caller['highlight_lines']}\n\n"

        if context.get('callees'):
            context_section += f"## 被调用函数\n"
            context_section += f"- {', '.join(context['callees'])}\n"

        sections.append(context_section)

        # 第 5 部分：任务描述
        task_section = """# 分析任务

你是一个专业的 Python 代码审查专家。基于以上信息，请进行**深度逻辑分析**。

## 重点关注（按优先级）

1. **业务逻辑错误** ⭐⭐⭐
   - 是否违反业务规则或隐式约束？
   - 边界条件处理是否正确？
   - 状态转换是否合法？

2. **数据流问题** ⭐⭐⭐
   - 变量是否可能未初始化？
   - None/null 检查是否充分？
   - 类型转换是否安全？

3. **控制流问题** ⭐⭐
   - 是否有不可达代码？
   - 循环是否可能无限？
   - 异常处理是否完整？

4. **资源管理** ⭐⭐
   - 文件/连接/锁是否正确释放？
   - 是否有内存泄漏风险？

5. **并发问题** ⭐
   - 是否有竞态条件？
   - 共享状态是否正确保护？

## 分析策略

- **已有工具结果**：静态检查和深度分析已发现的问题，请进一步确认和解释
- **遗漏分析**：关注工具**未能发现**的深层次逻辑错误
- **证据支持**：每个 bug 需要有清晰的推理链
- **优先级**：严重的逻辑错误 > 潜在风险 > 代码风格

## 输出格式

对于每个发现的 bug，请提供 JSON 格式的结果，包含以下字段：
- type: bug 类型
- severity: high/medium/low
- description: 清晰的问题描述
- location: {start_line: 行号, end_line: 行号}
- trigger_condition: 具体的触发条件（输入/状态）
- reasoning_chain: [推理步骤列表]
- confidence: 0.0-1.0
- fix_suggestion: 修复建议

请专注于**深层次、复杂的逻辑错误**，避免重复报告工具已发现的简单问题。
"""
        sections.append(task_section)

        return "\n\n".join(sections)
```

#### 4.3.2 结果解析

```python
def _parse_llm_response(self, response: str) -> LLMAnalysisResult:
    """
    解析 LLM 返回的结构化结果

    支持两种格式：
    1. JSON 格式（首选）
    2. Markdown 格式（备用）
    """
    # 尝试提取 JSON
    import re
    import json

    json_pattern = r'```json\s*(\[.*?\])\s*```'
    match = re.search(json_pattern, response, re.DOTALL)

    if match:
        bugs_json = json.loads(match.group(1))
        bugs = [CandidateBug(**bug) for bug in bugs_json]
    else:
        # 备用：解析 Markdown 格式
        bugs = self._parse_markdown_format(response)

    return LLMAnalysisResult(bugs=bugs)
```

---

### 4.4 Layer 4: 验证和融合

#### 4.4.1 交叉验证

```python
class Layer4Validator:
    """验证和融合层"""

    def validate_and_fuse(self,
                         facts: StaticFacts,
                         deep_analysis: DeepAnalysisResult,
                         llm_result: LLMAnalysisResult) -> List[VerifiedBug]:
        """
        多源验证和结果融合
        """
        verified_bugs = []

        for candidate in llm_result.bugs:
            # 1. 交叉验证
            cross_val_score = self._cross_validate(
                candidate, facts, deep_analysis
            )

            # 2. 符号验证
            is_feasible = self._symbolic_verify(
                candidate, deep_analysis
            )

            # 3. 测试用例生成
            test_case = self._generate_test_case(candidate)

            # 4. 计算最终置信度
            confidence = self._calculate_confidence(
                candidate.confidence,      # LLM 自评
                cross_val_score,          # 交叉验证分数
                is_feasible,              # 符号验证结果
                test_case is not None     # 是否能生成测试
            )

            # 5. 过滤低置信度结果
            if confidence >= 0.7:  # 阈值
                verified_bugs.append(VerifiedBug(
                    bug=candidate,
                    evidence=Evidence(
                        supported_by_layer1=cross_val_score > 0.6,
                        supported_by_layer2=cross_val_score > 0.8,
                        test_case=test_case,
                        symbolic_proof=is_feasible
                    ),
                    final_confidence=confidence,
                    priority_score=self._calculate_priority(
                        candidate, confidence
                    )
                ))

        # 6. 按优先级排序
        verified_bugs.sort(
            key=lambda x: x.priority_score,
            reverse=True
        )

        return verified_bugs

    def _cross_validate(self, bug, facts, analysis):
        """
        交叉验证：检查多个来源是否支持这个 bug

        评分逻辑：
        - 基础分：0.5（LLM 发现）
        - Layer 1 支持：+0.2
        - Layer 2 支持：+0.2
        - 有污点流到达：+0.1
        """
        score = 0.5

        # 检查 Layer 1 是否发现相关问题
        if self._layer1_supports(bug, facts):
            score += 0.2

        # 检查 Layer 2 是否发现可疑点
        if self._layer2_supports(bug, analysis):
            score += 0.2

        # 检查是否有污点流
        if self._has_related_taint_flow(bug, analysis.taint_flows):
            score += 0.1

        return min(score, 1.0)

    def _symbolic_verify(self, bug, analysis):
        """
        符号验证：使用符号执行验证 bug 是否可达
        """
        # 查找到达 bug 位置的路径
        bug_location = bug.location.start_line

        for path in analysis.paths:
            if any(node.line == bug_location for node in path.nodes):
                # 找到了包含 bug 位置的路径
                # 检查约束是否可满足
                if path.is_feasible:
                    return True

        return False

    def _generate_test_case(self, bug):
        """
        测试用例生成：尝试自动生成触发 bug 的测试

        使用 hypothesis 进行属性测试
        """
        # 根据 bug 的 trigger_condition 生成测试
        # 这里是简化版本，实际实现需要更复杂的逻辑
        pass

    def _calculate_confidence(self, llm_conf, cross_val, feasible, has_test):
        """
        计算最终置信度（加权平均）

        权重：
        - LLM 置信度：40%
        - 交叉验证分数：30%
        - 符号验证：20%
        - 测试用例：10%
        """
        weights = {
            'llm': 0.4,
            'cross_val': 0.3,
            'symbolic': 0.2,
            'test': 0.1
        }

        confidence = (
            weights['llm'] * llm_conf +
            weights['cross_val'] * cross_val +
            weights['symbolic'] * (1.0 if feasible else 0.0) +
            weights['test'] * (1.0 if has_test else 0.0)
        )

        return confidence
```

---

## 5. 实施计划

### 5.1 整体路线图

```
Phase 1: 基础设施 (2 周)
    ↓
Phase 2: Layer 1 (2 周)
    ↓
Phase 3: Layer 2 (6 周)
    ↓
Phase 4: Layer 3 (2 周)
    ↓
Phase 5: Layer 4 (2 周)
    ↓
Phase 6: 集成测试 (2 周)
    ↓
Phase 7: 优化调优 (2 周)

总计：18 周（约 4.5 个月）
```

### 5.2 详细分阶段计划

#### Phase 1: 基础设施搭建 (2 周)

**目标**：搭建 v2.0 的项目结构和基础框架

**任务**：
- [ ] 创建新的项目结构 (`pyscan_v2/`)
- [ ] 设计统一的数据结构（`StaticFacts`, `DeepAnalysisResult` 等）
- [ ] 实现多层分析的 Pipeline 框架
- [ ] 配置管理（支持各层独立配置）
- [ ] 日志和监控系统

**产出**：
- `pyscan_v2/` 项目框架
- 统一的数据模型定义
- Pipeline 执行引擎
- 配置文件模板

**验收标准**：
- 能够运行空的 4 层 pipeline
- 各层能够接收和传递数据
- 有完整的日志输出

---

#### Phase 2: Layer 1 实现 (2 周)

**目标**：集成开源静态分析工具

**Week 1: 工具集成**
- [ ] 集成 mypy（类型检查）
- [ ] 集成 bandit（安全扫描）
- [ ] 集成 pylint（代码质量）
- [ ] 集成 semgrep（模式匹配）

**Week 2: 结果转换和测试**
- [ ] 实现统一的结果转换器
- [ ] 提取类型信息、安全问题等
- [ ] 单元测试（覆盖率 > 80%）
- [ ] 性能测试（处理速度）

**产出**：
- `Layer1Analyzer` 完整实现
- 工具输出 -> `StaticFacts` 转换器
- 单元测试套件

**验收标准**：
- 能够并行运行所有工具
- 正确解析工具输出
- 转换为统一的 `StaticFacts` 格式
- 性能：1000 行代码 < 5 秒

---

#### Phase 3: Layer 2 实现 (6 周)

**目标**：构建深度静态分析引擎

**Week 1-2: CFG/DFG 构建器**
- [ ] 实现 CFG 构建器（基于 AST）
- [ ] 实现 DFG 构建器（到达定义分析）
- [ ] 实现 def-use 链构建
- [ ] 单元测试

**Week 3-4: 污点分析引擎**
- [ ] 实现污点源/汇/净化器配置
- [ ] 实现前向污点传播算法
- [ ] 实现污点流追踪
- [ ] 集成测试（SQL 注入、XSS 等）

**Week 5: 符号执行引擎**
- [ ] 集成 Z3 求解器
- [ ] 实现路径探索算法（DFS，有限深度）
- [ ] 实现约束收集和求解
- [ ] 测试（简单函数的路径枚举）

**Week 6: 可疑点检测器**
- [ ] 实现 None 检查检测
- [ ] 实现除零检测
- [ ] 实现数组边界检测
- [ ] 实现资源泄漏检测
- [ ] 集成测试

**产出**：
- `Layer2Analyzer` 完整实现
- CFG/DFG 构建器
- 污点分析引擎
- 符号执行引擎
- 可疑点检测器

**验收标准**：
- CFG/DFG 正确性测试通过
- 污点分析能检测出标准测试集的问题
- 符号执行能枚举简单函数的所有路径
- 可疑点检测准确率 > 70%

---

#### Phase 4: Layer 3 优化 (2 周)

**目标**：优化 LLM 提示工程

**Week 1: Prompt 设计**
- [ ] 设计分层的 prompt 结构
- [ ] 实现 prompt 构建器
- [ ] 融合 Layer 1/2 的结果
- [ ] 添加推理链要求

**Week 2: 结果解析和测试**
- [ ] 实现 JSON/Markdown 格式解析
- [ ] 实现推理链提取
- [ ] A/B 测试（对比 v1.0）
- [ ] 调优 prompt 模板

**产出**：
- `Layer3Analyzer` 优化版
- 增强的 prompt 模板
- 结果解析器

**验收标准**：
- LLM 能够正确理解 Layer 1/2 结果
- 返回结构化的 JSON 结果
- 包含推理链
- 准确率相比 v1.0 提升 > 10%

---

#### Phase 5: Layer 4 实现 (2 周)

**目标**：实现验证和融合层

**Week 1: 交叉验证**
- [ ] 实现多源验证逻辑
- [ ] 实现置信度计算
- [ ] 实现优先级排序

**Week 2: 符号验证和测试生成**
- [ ] 实现基于符号执行的验证
- [ ] 实现测试用例生成（hypothesis）
- [ ] 集成测试

**产出**：
- `Layer4Validator` 完整实现
- 置信度计算模块
- 测试生成模块

**验收标准**：
- 交叉验证能正确评分
- 误报率降低 > 50%
- 能生成部分 bug 的测试用例

---

#### Phase 6: 集成测试 (2 周)

**目标**：端到端测试和验证

**Week 1: 功能测试**
- [ ] 端到端测试（真实项目）
- [ ] 性能测试（大型项目）
- [ ] 准确率测试（标准测试集）

**Week 2: 对比测试**
- [ ] vs v1.0 对比
- [ ] vs 开源工具对比
- [ ] 生成对比报告

**产出**：
- 测试报告
- 性能报告
- 对比分析

**验收标准**：
- 准确率 > 85%
- 误报率 < 15%
- 召回率 > 70%
- 处理速度：1000 行/分钟

---

#### Phase 7: 优化调优 (2 周)

**目标**：性能优化和文档完善

**Week 1: 性能优化**
- [ ] 并行处理优化
- [ ] 缓存机制
- [ ] 内存优化

**Week 2: 文档和发布**
- [ ] 用户文档
- [ ] API 文档
- [ ] 迁移指南（v1.0 -> v2.0）
- [ ] 发布 v2.0-beta

**产出**：
- 优化后的系统
- 完整文档
- v2.0-beta 版本

---

### 5.3 资源需求

**人力**：
- 核心开发者：1-2 人
- 测试工程师：1 人（Phase 6 加入）

**技术栈**：
- Python 3.9+
- Z3-solver（符号执行）
- 开源工具：mypy, bandit, pylint, semgrep
- LLM API（OpenAI/Claude/自定义）

**硬件**：
- 开发机：8GB+ RAM
- 测试环境：16GB+ RAM（大项目测试）

---

## 6. 风险和挑战

### 6.1 技术风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| **符号执行性能** | 路径爆炸导致速度慢 | 限制深度、使用启发式剪枝 |
| **工具集成复杂** | 不同工具输出格式不一 | 统一的适配层 |
| **LLM 理解能力** | 可能无法理解复杂分析结果 | 优化 prompt、分步骤推理 |
| **误报过滤困难** | 仍然有误报 | 多轮验证、用户反馈学习 |

### 6.2 工程风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| **开发周期延长** | 4.5 个月可能不够 | 分阶段发布、MVP 优先 |
| **向后兼容性** | v2.0 与 v1.0 不兼容 | 提供迁移工具 |
| **依赖管理** | 外部工具依赖多 | Docker 容器化 |

---

## 7. 成功指标

### 7.1 定量指标

| 指标 | v1.0 | v2.0 目标 | 测量方法 |
|------|------|-----------|---------|
| **准确率** | ~60% | 85%+ | 标准测试集 |
| **误报率** | ~35% | <15% | 人工验证 |
| **召回率** | ~40% | 70%+ | 对比真实 bug |
| **API 成本** | 基准 | -50% | Token 消耗统计 |
| **分析速度** | 基准 | 1000 行/分钟 | 性能测试 |

### 7.2 定性指标

- [ ] 用户满意度提升
- [ ] 可解释性增强（推理链）
- [ ] 社区认可度提高
- [ ] 文档完善度

---

## 8. 后续演进

### v2.1 计划
- 机器学习模型训练（基于用户反馈）
- 增量分析（只分析变更部分）
- IDE 插件（VSCode/PyCharm）

### v3.0 愿景
- 多语言支持（JavaScript、Java）
- 分布式分析（处理超大项目）
- 自动修复（CodeGen）

---

## 9. 附录

### 9.1 参考资料

- **学术论文**：
  - "Symbolic Execution for Software Testing" (CACM 2013)
  - "Taint Analysis for Security" (IEEE S&P 2005)
  - "Neural Program Analysis" (NeurIPS 2020)

- **开源项目**：
  - Pysa (Facebook): Taint analysis
  - Bandit: Security scanner
  - Semgrep: Pattern matching

- **工具文档**：
  - Z3 Solver: https://github.com/Z3Prover/z3
  - Mypy: https://mypy.readthedocs.io/

### 9.2 术语表

| 术语 | 定义 |
|------|------|
| **CFG** | Control Flow Graph，控制流图 |
| **DFG** | Data Flow Graph，数据流图 |
| **Taint Analysis** | 污点分析，追踪不可信数据流 |
| **Symbolic Execution** | 符号执行，路径枚举和约束求解 |
| **SMT Solver** | 可满足性模理论求解器 |

---

## 10. 总结

PyScan v2.0 通过**分层分析架构**，充分发挥开源工具、深度静态分析和 LLM 的各自优势：

1. **Layer 1**（开源工具）：快速过滤低级错误
2. **Layer 2**（深度分析）：构建代码的精确模型
3. **Layer 3**（LLM）：深度推理业务逻辑
4. **Layer 4**（验证融合）：多源验证，降低误报

预期效果：
- ✅ 准确率 85%+
- ✅ 误报率 <15%
- ✅ 召回率 70%+
- ✅ 成本降低 50%
- ✅ 完整推理链

实施周期：**18 周**（约 4.5 个月）

**下一步行动**：
1. Review 本设计文档
2. 确认技术选型和资源
3. 启动 Phase 1（基础设施搭建）

---

**文档版本历史**：
- v1.0 (2025-01-19): 初始版本
- v1.1 (2025-10-19): 添加 Stage 2 实施方案（已移至 v2_impl_tracking/stage2_plan.md）
