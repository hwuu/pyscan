"""Bug detector module using LLM."""
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from openai import OpenAI
from pyscan.config import Config
from pyscan.ast_parser import FunctionInfo
from pyscan.layer1.base import StaticFacts


logger = logging.getLogger(__name__)


@dataclass
class BugReport:
    """Bug detection report for a single bug."""

    bug_id: str  # Bug ID (e.g., BUG_0001)
    function_name: str
    file_path: str
    function_start_line: int  # 函数在文件中的起始行号
    function_end_line: int  # 函数在文件中的结束行号
    function_start_col: int = 0  # 函数起始列
    function_end_col: int = 0  # 函数结束列
    severity: str = ""  # high, medium, low
    bug_type: str = ""  # Bug 类型
    description: str = ""  # Bug 描述（中文）
    location: str = ""  # 位置描述
    start_line: int = 0  # Bug 起始行（相对于函数）
    end_line: int = 0  # Bug 结束行（相对于函数）
    start_col: int = 0  # Bug 起始列
    end_col: int = 0  # Bug 结束列
    suggestion: str = ""  # 修复建议
    callers: List[Dict[str, Any]] = field(default_factory=list)  # Caller POIs
    callees: List[str] = field(default_factory=list)  # 被调用函数名列表
    inferred_callers: List[Dict[str, Any]] = field(default_factory=list)  # Inferred Caller POIs


class BugDetector:
    """Bug detector using LLM."""

    SYSTEM_PROMPT = """你是一个 Python 代码审查专家。你的任务是分析函数代码，识别真正的逻辑错误和 bug。

**重要限制：**
1. 不要报告 pylint、flake8、mypy 等静态检查工具能发现的问题
2. 不要报告代码风格、命名规范等问题
3. 不要过度建议防御性编程（如到处检查 None、验证参数类型等）
4. 信任函数的类型注解（type hints）和调用链中的验证
5. 只报告明确的、会导致程序错误的逻辑缺陷
6. **假定所有调用者（callers）和被调用函数（callees）都是正确的、无 bug 的**
7. **尽量少标记为 high 严重程度，只有在确实会导致严重后果时才使用 high**
8. **bug 的 description 字段必须用中文描述**

**参数验证要求（根据函数类型）：**
- 如果函数是**公共 API/接口**（会被外部或不可信代码调用），必须检查是否缺少以下验证：
  * 参数类型验证（是否检查了参数类型是否符合预期）
  * 空值检查（None 值的处理）
  * 必需字段存在性检查（对于字典/对象参数）
  * 边界值检查（数值范围、字符串长度等）
  * 如果缺少这些验证，应报告为 bug
- 如果函数是**内部函数**（仅被项目内部代码调用），则：
  * 信任调用者已做必要的验证
  * 不要报告缺少参数验证的问题
  * 除非存在明确的逻辑错误会导致崩溃

**应该检测的问题：**
- 明确的逻辑错误（算法错误、条件判断错误、边界条件处理错误）
- 资源管理问题（文件、连接未正确关闭，且不是简单的 with 语句缺失）
- 并发安全问题（竞态条件、死锁风险）
- 数据一致性问题
- 安全漏洞（SQL 注入、路径遍历等）
- 公共 API 缺少必要的参数验证（仅当函数类型为"公共 API"时）

**不应该报告的问题：**
- 缺少类型注解
- 缺少 docstring
- 变量命名不规范
- 内部函数缺少参数验证（调用者已验证）
- 性能优化建议（除非有明显的性能问题）
- 代码重复

请以 JSON 格式返回分析结果，格式如下：
{
  "has_bug": true/false,
  "severity": "high/medium/low",
  "bugs": [
    {
      "type": "bug类型",
      "description": "问题描述",
      "location": "具体位置描述",
      "start_line": 相对行号（相对于函数起始行，从1开始），
      "end_line": 结束行号（相对于函数起始行），
      "start_col": 起始列号（从0开始，如果无法确定设为0），
      "end_col": 结束列号（如果无法确定设为0），
      "suggestion": "修复建议"
    }
  ]
}

注意：
- start_line/end_line 是相对于当前函数的第一行代码的行号，从1开始计数
- 例如，如果 bug 在函数的第3行，start_line 应该是 3
- start_col/end_col 是该行内的字符偏移量，从0开始
- 如果无法精确定位列号，可以设置为 0

如果没有发现**真正的 bug**，返回 {"has_bug": false, "severity": "low", "bugs": []}
"""

    SYSTEM_PROMPT_WITH_STATIC_ANALYSIS = """你是一个 Python 代码审查专家。静态分析工具（mypy、bandit）已经发现了一些基础问题（见用户消息中的"静态分析结果"部分）。

你的任务是发现**静态工具无法检测的深层次问题**，请专注于：

**应该检测的问题：**
1. **业务逻辑错误**：算法错误、边界条件处理错误、状态转换错误、隐式约束违反
2. **复杂数据流问题**：跨函数的数据依赖、间接引用、数据一致性问题
3. **资源管理**：文件/连接/锁的正确释放（非简单的 with 语句缺失）
4. **并发问题**：竞态条件、死锁风险
5. **安全漏洞**：SQL 注入、路径遍历等（静态工具未发现的）
6. **公共 API 参数验证**：仅当函数类型为"公共 API"且缺少必要验证时

**重要限制：**
1. **不要重复报告**静态工具已发现的问题（类型错误、基础安全问题等）
2. 对于静态工具已发现的问题，可以补充说明其影响，但不要作为单独的 bug 报告
3. 不要报告代码风格、命名规范、缺少 docstring 等问题
4. 不要过度建议防御性编程（如到处检查 None、验证参数类型等）
5. 信任函数的类型注解（type hints）和调用链中的验证
6. **假定所有调用者（callers）和被调用函数（callees）都是正确的、无 bug 的**
7. **尽量少标记为 high 严重程度，只有在确实会导致严重后果时才使用 high**
8. **bug 的 description 字段必须用中文描述**

**参数验证要求（根据函数类型）：**
- 如果函数是**公共 API/接口**（会被外部或不可信代码调用），检查是否缺少必要验证
- 如果函数是**内部函数**（仅被项目内部代码调用），信任调用者已做验证

请以 JSON 格式返回分析结果，格式如下：
{
  "has_bug": true/false,
  "severity": "high/medium/low",
  "bugs": [
    {
      "type": "bug类型",
      "description": "问题描述",
      "location": "具体位置描述",
      "start_line": 相对行号（相对于函数起始行，从1开始），
      "end_line": 结束行号（相对于函数起始行），
      "start_col": 起始列号（从0开始，如果无法确定设为0），
      "end_col": 结束列号（如果无法确定设为0），
      "suggestion": "修复建议"
    }
  ]
}

注意：
- start_line/end_line 是相对于当前函数的第一行代码的行号，从1开始计数
- 如果没有发现**真正的深层次 bug**，返回 {"has_bug": false, "severity": "low", "bugs": []}
"""

    def __init__(self, config: Config):
        """
        Initialize bug detector.

        Args:
            config: Configuration object.
        """
        self.config = config
        self.client = OpenAI(
            base_url=config.llm_base_url,
            api_key=config.llm_api_key
        )

    def detect(
        self,
        function: FunctionInfo,
        context: Dict[str, Any],
        file_path: str = "",
        function_start_line: int = 0,
        callers: List[Dict[str, Any]] = None,
        callees: List[str] = None,
        inferred_callers: List[Dict[str, str]] = None,
        bug_id_start: int = 1,
        static_facts: Optional[StaticFacts] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Detect bugs in a function.

        Args:
            function: Function to analyze.
            context: Function context (callers, callees).
            file_path: Path to the file containing the function.
            function_start_line: Starting line number of function.
            callers: List of caller info dicts (file_path, function_name, code_snippet).
            callees: List of callee function names.
            inferred_callers: List of inferred caller dicts with hints and code.
            bug_id_start: Starting bug ID number.
            static_facts: Static analysis results from Layer 1 (optional).

        Returns:
            Dictionary containing:
                - reports: List of BugReport (one per bug found, empty if no bugs)
                - prompt: The full prompt sent to LLM
                - raw_response: The raw response from LLM
            None if failed after retries.
        """
        prompt = self._build_prompt(function, context, static_facts)

        # 根据是否有静态分析结果选择不同的 system prompt
        system_prompt = (
            self.SYSTEM_PROMPT_WITH_STATIC_ANALYSIS
            if static_facts is not None
            else self.SYSTEM_PROMPT
        )

        for attempt in range(self.config.detector_max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.config.llm_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.config.llm_temperature,
                    max_tokens=self.config.llm_max_tokens
                )

                content = response.choices[0].message.content
                result = self._parse_response(content)

                # 将每个 bug 转换为独立的 BugReport
                reports = []
                if result["has_bug"] and result["bugs"]:
                    for idx, bug in enumerate(result["bugs"]):
                        bug_id = f"BUG_{bug_id_start + idx:04d}"
                        report = BugReport(
                            bug_id=bug_id,
                            function_name=function.name,
                            file_path=file_path,
                            function_start_line=function_start_line,
                            function_end_line=function.end_lineno,
                            function_start_col=function.col_offset,
                            function_end_col=function.end_col_offset,
                            severity=bug.get("severity", result.get("severity", "low")),
                            bug_type=bug.get("type", "Unknown"),
                            description=bug.get("description", ""),
                            location=bug.get("location", ""),
                            start_line=bug.get("start_line", 0),
                            end_line=bug.get("end_line", 0),
                            start_col=bug.get("start_col", 0),
                            end_col=bug.get("end_col", 0),
                            suggestion=bug.get("suggestion", ""),
                            callers=callers or [],
                            callees=callees or [],
                            inferred_callers=inferred_callers or []
                        )
                        reports.append(report)

                return {
                    "reports": reports,
                    "prompt": prompt,
                    "raw_response": content
                }

            except Exception as e:
                logger.warning(
                    f"Attempt {attempt + 1}/{self.config.detector_max_retries} "
                    f"failed for function {function.name}: {e}"
                )

                if attempt < self.config.detector_max_retries - 1:
                    # 等待后重试
                    time.sleep(1)
                else:
                    logger.error(
                        f"Failed to detect bugs for {function.name} "
                        f"after {self.config.detector_max_retries} attempts"
                    )
                    return None

        return None

    def _build_prompt(
        self,
        function: FunctionInfo,
        context: Dict[str, Any],
        static_facts: Optional[StaticFacts] = None
    ) -> str:
        """
        Build prompt for LLM.

        Args:
            function: Function to analyze.
            context: Function context.
            static_facts: Static analysis results from Layer 1 (optional).

        Returns:
            Formatted prompt.
        """
        parts = []

        parts.append("请分析以下函数是否存在潜在 bug：\n\n")

        # 添加函数类型说明
        is_public_api = context.get("is_public_api", False)
        function_type = "公共 API/接口" if is_public_api else "内部函数"
        parts.append(f"**当前函数类型:** {function_type}\n")
        if is_public_api:
            parts.append("（此函数会被外部或不可信代码调用，需要严格的参数验证）\n\n")
        else:
            parts.append("（此函数仅被项目内部代码调用，可以信任调用者已做验证）\n\n")

        parts.append("### 当前函数\n")
        parts.append("```python\n")
        # 添加行号以帮助 LLM 定位
        code_lines = context["current_function"].split('\n')
        for i, line in enumerate(code_lines, 1):
            parts.append(f"{i:3d} | {line}\n")
        parts.append("```\n\n")

        # 添加静态分析结果（如果有）
        if static_facts is not None:
            parts.append(self._build_static_facts_section(static_facts))

        if context.get("callers"):
            parts.append("### 调用者函数\n")
            for i, caller in enumerate(context["callers"], 1):
                parts.append(f"调用者 {i}:\n```python\n")
                parts.append(caller)
                parts.append("\n```\n\n")

        # callees 已移除 - 假定被调用函数无 bug，不需要在 prompt 中展示

        # 添加推断的调用者
        if context.get("inferred_callers"):
            parts.append("### 调用者函数(推断)\n")
            for i, inferred in enumerate(context["inferred_callers"], 1):
                parts.append(f"调用者 {i} {inferred['hint']}:\n```python\n")
                parts.append(inferred['code'])
                parts.append("\n```\n\n")

        # 推断的 callees 已移除 - 不需要在 prompt 中展示

        parts.append(
            "请返回 JSON 格式的分析结果，只返回 JSON，不要其他说明文字。"
        )

        return "".join(parts)

    def _build_static_facts_section(self, facts: StaticFacts) -> str:
        """
        Build static analysis facts section for prompt.

        Args:
            facts: Static analysis results from Layer 1.

        Returns:
            Formatted section string.
        """
        parts = []
        parts.append("### 静态分析结果\n\n")

        has_issues = False

        # 类型检查问题
        if facts.type_issues:
            has_issues = True
            parts.append("**类型检查（Mypy）：**\n")
            for issue in facts.type_issues:
                parts.append(
                    f"- 行 {issue.line}: [{issue.severity.upper()}] {issue.message}"
                )
                if issue.code:
                    parts.append(f" [{issue.code}]")
                parts.append("\n")
            parts.append("\n")

        # 安全扫描问题
        if facts.security_issues:
            has_issues = True
            parts.append("**安全扫描（Bandit）：**\n")
            for issue in facts.security_issues:
                parts.append(
                    f"- 行 {issue.line}: [{issue.severity.upper()}] {issue.message}"
                )
                if issue.code:
                    parts.append(f" [{issue.code}]")
                parts.append("\n")
            parts.append("\n")

        # 元信息
        parts.append("**元信息：**\n")
        parts.append(f"- 有类型注解: {'是' if facts.has_type_annotations else '否'}\n")
        if facts.complexity_score > 0:
            parts.append(f"- 复杂度评分: {facts.complexity_score}\n")
        parts.append("\n")

        # 如果没有发现问题，说明一下
        if not has_issues:
            parts.append("*静态工具未发现明显的类型错误或安全问题。*\n\n")

        return "".join(parts)

    def _parse_response(self, content: str) -> Dict[str, Any]:
        """
        Parse LLM response.

        Args:
            content: Response content.

        Returns:
            Parsed result dictionary.

        Raises:
            ValueError: If response cannot be parsed.
        """
        # 尝试提取 JSON（可能包含在 markdown 代码块中）
        content = content.strip()

        # 移除可能的 markdown 代码块标记
        if content.startswith("```"):
            lines = content.split('\n')
            # 移除第一行和最后一行
            if lines[0].startswith("```") and lines[-1].strip() == "```":
                content = '\n'.join(lines[1:-1])
            # 如果只是开头有 ```json
            elif lines[0].startswith("```json"):
                content = '\n'.join(lines[1:])
                if content.endswith("```"):
                    content = content[:-3]

        try:
            result = json.loads(content.strip())

            # 验证必需字段
            if "has_bug" not in result:
                raise ValueError("Missing 'has_bug' field")
            if "severity" not in result:
                result["severity"] = "low"
            if "bugs" not in result:
                result["bugs"] = []

            # 验证和补充 bug 位置信息
            for bug in result["bugs"]:
                if "start_line" not in bug:
                    bug["start_line"] = 0
                if "end_line" not in bug:
                    bug["end_line"] = 0
                if "start_col" not in bug:
                    bug["start_col"] = 0
                if "end_col" not in bug:
                    bug["end_col"] = 0

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {content}")
            raise ValueError(f"Invalid JSON response: {e}")
