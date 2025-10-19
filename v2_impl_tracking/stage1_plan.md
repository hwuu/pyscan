# Stage 1 执行计划：Layer 1 工具集成

**时间估算**: 2 周
**状态**: 规划中
**负责人**: Claude + hwuu

---

## 1. 目标

在 PyScan v1.0 基础上集成开源静态分析工具（mypy + bandit），将工具发现的问题融入 LLM prompt，减少 LLM 负担并提升检测准确率。

**预期效果**：
- 过滤掉 50%+ 的低级错误（类型错误、明显安全问题）
- 减少 30% 的 LLM API 调用成本
- 为 LLM 提供更多上下文信息

---

## 2. 技术方案

### 2.1 架构设计

```
┌─────────────────────────────────────────────────┐
│  现有 PyScan v1.0 流程                           │
│  AST 解析 → 上下文构建 → LLM 分析 → 报告生成      │
└─────────────────────────────────────────────────┘
                    ↓ 增强
┌─────────────────────────────────────────────────┐
│  PyScan v1.1 流程（Stage 1）                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ AST 解析 │→ │ Layer 1  │→ │上下文构建│       │
│  └──────────┘  │工具集成  │  └──────────┘       │
│                │(新增)    │       ↓              │
│                └──────────┘  ┌──────────┐       │
│                              │增强 Prompt│       │
│                              │(修改)     │       │
│                              └──────────┘       │
│                                   ↓              │
│                              ┌──────────┐       │
│                              │ LLM 分析 │       │
│                              └──────────┘       │
│                                   ↓              │
│                              ┌──────────┐       │
│                              │报告生成  │       │
│                              └──────────┘       │
└─────────────────────────────────────────────────┘
```

### 2.2 新增模块

#### 模块 1: `pyscan/layer1/base.py`
定义基础数据结构和接口

```python
from dataclasses import dataclass
from typing import List, Optional
from abc import ABC, abstractmethod

@dataclass
class StaticIssue:
    """工具发现的单个问题"""
    tool: str              # 工具名称：mypy/bandit/pylint
    type: str              # 问题类型
    severity: str          # 严重程度：high/medium/low
    message: str           # 问题描述
    file_path: str         # 文件路径
    line: int              # 行号
    column: Optional[int]  # 列号
    code: Optional[str]    # 错误代码（如 E501）

@dataclass
class StaticFacts:
    """Layer 1 工具收集的所有事实"""
    file_path: str
    function_name: str
    function_start_line: int

    # 各工具发现的问题
    type_issues: List[StaticIssue]      # mypy
    security_issues: List[StaticIssue]  # bandit

    # 元信息
    has_type_annotations: bool
    complexity_score: int

class StaticAnalyzer(ABC):
    """静态分析工具的抽象基类"""

    @abstractmethod
    def analyze_file(self, file_path: str) -> List[StaticIssue]:
        """分析文件，返回问题列表"""
        pass

    @abstractmethod
    def analyze_function(self, file_path: str, func_name: str,
                        start_line: int, end_line: int) -> List[StaticIssue]:
        """分析特定函数，返回问题列表"""
        pass
```

#### 模块 2: `pyscan/layer1/mypy_analyzer.py`
Mypy 集成

```python
import subprocess
import json
from pathlib import Path
from typing import List
from .base import StaticAnalyzer, StaticIssue

class MypyAnalyzer(StaticAnalyzer):
    """Mypy 类型检查器"""

    def __init__(self):
        self.cache = {}  # 缓存文件级别的分析结果

    def analyze_file(self, file_path: str) -> List[StaticIssue]:
        """运行 mypy 分析文件"""
        if file_path in self.cache:
            return self.cache[file_path]

        try:
            # 运行 mypy --show-column-numbers --no-error-summary
            result = subprocess.run(
                ['mypy', '--show-column-numbers', '--no-error-summary', file_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            issues = self._parse_output(result.stdout, file_path)
            self.cache[file_path] = issues
            return issues

        except Exception as e:
            logger.warning(f"Mypy analysis failed for {file_path}: {e}")
            return []

    def analyze_function(self, file_path: str, func_name: str,
                        start_line: int, end_line: int) -> List[StaticIssue]:
        """获取特定函数范围内的问题"""
        all_issues = self.analyze_file(file_path)
        return [
            issue for issue in all_issues
            if start_line <= issue.line <= end_line
        ]

    def _parse_output(self, output: str, file_path: str) -> List[StaticIssue]:
        """解析 mypy 输出"""
        issues = []
        for line in output.strip().split('\n'):
            if not line:
                continue

            # 格式: file.py:10:5: error: Message [error-code]
            try:
                parts = line.split(':', 4)
                if len(parts) >= 4:
                    line_num = int(parts[1])
                    col_num = int(parts[2]) if parts[2].isdigit() else None
                    severity_and_msg = parts[3].strip()

                    # 提取 severity 和 message
                    if severity_and_msg.startswith('error'):
                        severity = 'high'
                        message = severity_and_msg[6:].strip()
                    elif severity_and_msg.startswith('note'):
                        severity = 'low'
                        message = severity_and_msg[5:].strip()
                    else:
                        severity = 'medium'
                        message = severity_and_msg

                    issues.append(StaticIssue(
                        tool='mypy',
                        type='type-error',
                        severity=severity,
                        message=message,
                        file_path=file_path,
                        line=line_num,
                        column=col_num,
                        code=None
                    ))
            except Exception as e:
                logger.debug(f"Failed to parse mypy line: {line}, error: {e}")
                continue

        return issues
```

#### 模块 3: `pyscan/layer1/bandit_analyzer.py`
Bandit 集成

```python
import subprocess
import json
from typing import List
from .base import StaticAnalyzer, StaticIssue

class BanditAnalyzer(StaticAnalyzer):
    """Bandit 安全扫描器"""

    def __init__(self):
        self.cache = {}

    def analyze_file(self, file_path: str) -> List[StaticIssue]:
        """运行 bandit 分析文件"""
        if file_path in self.cache:
            return self.cache[file_path]

        try:
            # 运行 bandit -f json
            result = subprocess.run(
                ['bandit', '-f', 'json', file_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            issues = self._parse_output(result.stdout, file_path)
            self.cache[file_path] = issues
            return issues

        except Exception as e:
            logger.warning(f"Bandit analysis failed for {file_path}: {e}")
            return []

    def analyze_function(self, file_path: str, func_name: str,
                        start_line: int, end_line: int) -> List[StaticIssue]:
        """获取特定函数范围内的问题"""
        all_issues = self.analyze_file(file_path)
        return [
            issue for issue in all_issues
            if start_line <= issue.line <= end_line
        ]

    def _parse_output(self, output: str, file_path: str) -> List[StaticIssue]:
        """解析 bandit JSON 输出"""
        issues = []
        try:
            data = json.loads(output)
            for result in data.get('results', []):
                # Bandit severity: HIGH/MEDIUM/LOW
                severity_map = {
                    'HIGH': 'high',
                    'MEDIUM': 'medium',
                    'LOW': 'low'
                }

                issues.append(StaticIssue(
                    tool='bandit',
                    type='security',
                    severity=severity_map.get(result['issue_severity'], 'medium'),
                    message=result['issue_text'],
                    file_path=file_path,
                    line=result['line_number'],
                    column=None,
                    code=result['test_id']
                ))
        except Exception as e:
            logger.debug(f"Failed to parse bandit output: {e}")

        return issues
```

#### 模块 4: `pyscan/layer1/__init__.py`
统一接口

```python
from typing import List
from .base import StaticFacts, StaticIssue
from .mypy_analyzer import MypyAnalyzer
from .bandit_analyzer import BanditAnalyzer

class Layer1Analyzer:
    """Layer 1 统一分析器"""

    def __init__(self, enable_mypy=True, enable_bandit=True):
        self.analyzers = []

        if enable_mypy:
            self.analyzers.append(MypyAnalyzer())
        if enable_bandit:
            self.analyzers.append(BanditAnalyzer())

    def analyze_function(self, file_path: str, func_name: str,
                        start_line: int, end_line: int,
                        complexity_score: int = 0) -> StaticFacts:
        """分析单个函数，收集所有工具的结果"""
        type_issues = []
        security_issues = []

        for analyzer in self.analyzers:
            issues = analyzer.analyze_function(
                file_path, func_name, start_line, end_line
            )

            for issue in issues:
                if issue.tool == 'mypy':
                    type_issues.append(issue)
                elif issue.tool == 'bandit':
                    security_issues.append(issue)

        return StaticFacts(
            file_path=file_path,
            function_name=func_name,
            function_start_line=start_line,
            type_issues=type_issues,
            security_issues=security_issues,
            has_type_annotations=self._check_type_annotations(file_path, start_line, end_line),
            complexity_score=complexity_score
        )

    def _check_type_annotations(self, file_path: str, start_line: int, end_line: int) -> bool:
        """简单检查是否有类型注解"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                func_code = ''.join(lines[start_line-1:end_line])
                return '->' in func_code or ': ' in func_code
        except:
            return False
```

### 2.3 修改现有模块

#### 修改 1: `pyscan/bug_detector.py`

在 `_build_prompt` 方法中融入 Layer 1 结果：

```python
def _build_prompt(self, func: FunctionInfo, context: Dict, static_facts: StaticFacts = None) -> str:
    """构建增强的 prompt"""
    sections = []

    # 第 1 部分：函数代码（保持不变）
    sections.append(self._build_function_section(func))

    # 第 2 部分：Layer 1 静态分析结果（新增）
    if static_facts:
        sections.append(self._build_static_facts_section(static_facts))

    # 第 3 部分：调用上下文（保持不变）
    sections.append(self._build_context_section(context))

    # 第 4 部分：任务描述（修改）
    sections.append(self._build_task_section(has_static_facts=static_facts is not None))

    return '\n\n'.join(sections)

def _build_static_facts_section(self, facts: StaticFacts) -> str:
    """构建静态分析结果部分"""
    section = "# 静态分析工具发现的问题\n\n"

    if facts.type_issues:
        section += "## 类型检查（Mypy）\n"
        for issue in facts.type_issues:
            section += f"- Line {issue.line}: {issue.message}\n"
        section += "\n"

    if facts.security_issues:
        section += "## 安全扫描（Bandit）\n"
        for issue in facts.security_issues:
            section += f"- Line {issue.line}: [{issue.severity}] {issue.message}\n"
        section += "\n"

    if not facts.type_issues and not facts.security_issues:
        section += "未发现明显的类型错误或安全问题。\n\n"

    return section

def _build_task_section(self, has_static_facts: bool) -> str:
    """构建任务描述"""
    if has_static_facts:
        return """# 分析任务

你是一个专业的 Python 代码审查专家。静态分析工具已经发现了一些基础问题（见上文）。

请专注于发现**静态工具无法检测的深层次问题**：
1. **业务逻辑错误**：边界条件、状态转换、隐式约束
2. **复杂数据流问题**：跨函数的数据依赖、间接引用
3. **资源管理**：文件/连接/锁的正确释放
4. **并发问题**：竞态条件、死锁风险

对于静态工具已发现的问题，可以补充说明其影响，但**不要重复报告**。

输出格式保持不变（JSON）。
"""
    else:
        # 保持原有的任务描述
        return self._original_task_description()
```

#### 修改 2: `pyscan/cli.py`

在主流程中集成 Layer 1：

```python
from pyscan.layer1 import Layer1Analyzer

def main():
    # ... 现有代码 ...

    # 初始化 Layer 1 分析器
    layer1 = Layer1Analyzer(
        enable_mypy=config.get('layer1', {}).get('enable_mypy', True),
        enable_bandit=config.get('layer1', {}).get('enable_bandit', True)
    )

    # 遍历所有函数
    for func in all_functions:
        # Layer 1 分析
        static_facts = layer1.analyze_function(
            file_path=func.file_path,
            func_name=func.name,
            start_line=func.lineno,
            end_line=func.end_lineno,
            complexity_score=calculate_complexity(func)
        )

        # 如果静态工具发现严重错误，可以跳过 LLM 分析（节省成本）
        if should_skip_llm(static_facts):
            # 直接生成报告
            bugs = convert_static_issues_to_bugs(static_facts)
        else:
            # 构建上下文
            context = context_builder.build_context(func, all_functions)

            # LLM 分析（传入 static_facts）
            bugs = bug_detector.detect(func, context, static_facts)

        # ... 保存结果 ...
```

### 2.4 配置文件更新

`config.yaml` 添加 Layer 1 配置：

```yaml
# Layer 1 静态分析工具配置
layer1:
  enable_mypy: true
  enable_bandit: true

  # 跳过 LLM 的策略
  skip_llm_if:
    no_issues_found: false  # 如果工具未发现问题，是否跳过 LLM
    only_low_severity: false  # 如果只有低严重度问题，是否跳过 LLM
```

---

## 3. 实施步骤

### Step 1: 创建基础架构（1天）
- [ ] 创建 `pyscan/layer1/` 目录
- [ ] 实现 `base.py`（数据结构和接口）
- [ ] 编写单元测试

### Step 2: 实现 Mypy 集成（2天）
- [ ] 实现 `mypy_analyzer.py`
- [ ] 测试 mypy 输出解析
- [ ] 处理边界情况（超时、解析失败等）
- [ ] 单元测试

### Step 3: 实现 Bandit 集成（2天）
- [ ] 实现 `bandit_analyzer.py`
- [ ] 测试 bandit JSON 解析
- [ ] 处理边界情况
- [ ] 单元测试

### Step 4: 实现统一接口（1天）
- [ ] 实现 `Layer1Analyzer`
- [ ] 添加缓存机制
- [ ] 集成测试

### Step 5: 修改现有模块（2天）
- [ ] 修改 `bug_detector.py`
- [ ] 增强 prompt 构建逻辑
- [ ] 修改 `cli.py` 主流程
- [ ] 更新配置文件

### Step 6: 测试验证（2天）
- [ ] 在测试项目上运行
- [ ] 对比 v1.0 和 v1.1 的结果
- [ ] 验证准确率提升
- [ ] 验证成本降低

### Step 7: 文档和收尾（1天）
- [ ] 更新 README
- [ ] 编写 `stage1_result.md`
- [ ] 提交代码

**总计**: 约 11 天（2 周内）

---

## 4. 验收标准

### 4.1 功能验收
- [ ] mypy 能正确分析 Python 文件并返回类型错误
- [ ] bandit 能正确分析 Python 文件并返回安全问题
- [ ] Layer 1 结果正确融入 LLM prompt
- [ ] 报告格式保持兼容（或按需扩展）

### 4.2 性能验收
- [ ] Layer 1 工具的总耗时 < 原总耗时的 20%
- [ ] 缓存机制有效（同一文件不重复分析）

### 4.3 效果验收
在测试数据集上：
- [ ] 误报率下降 > 10%
- [ ] 召回率保持不变或提升
- [ ] API 调用成本降低 > 20%

---

## 5. 风险点和缓解措施

### 风险 1: 工具输出格式不稳定
**影响**: 解析失败，无法获取问题
**缓解**:
- 使用工具的稳定输出格式（mypy 文本格式、bandit JSON）
- 添加版本检查和兼容性处理
- 解析失败时优雅降级（跳过 Layer 1）

### 风险 2: 工具运行时间过长
**影响**: 整体扫描时间增加
**缓解**:
- 设置超时限制（30秒）
- 文件级别缓存
- 可选禁用慢速工具

### 风险 3: 工具依赖安装问题
**影响**: 用户环境缺少工具
**缓解**:
- 在 `requirements.txt` 中添加依赖
- 启动时检查工具可用性
- 工具不可用时自动禁用（而非报错）

### 风险 4: Prompt 过长
**影响**: 超过 LLM token 限制
**缓解**:
- 限制显示的问题数量（每类最多 5 个）
- 优先显示高严重度问题
- 保留原有的 token 压缩机制

---

## 6. 依赖和前置条件

### 环境依赖
- Python 3.8+
- mypy >= 1.0
- bandit >= 1.7

### 代码依赖
- 现有 PyScan v1.0 代码库
- AST 解析器正常工作
- 上下文构建器正常工作

---

## 7. 下一阶段预览

Stage 1 完成后，Stage 2 将实现：
- CFG（控制流图）构建
- 基于 CFG 的简单可疑点检测（如未初始化变量、不可达代码）
- 将 CFG 信息融入 prompt

预计 Stage 2 耗时 3 周。
