"""Bug detector module using LLM."""
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from openai import OpenAI
from pyscan.config import Config
from pyscan.ast_parser import FunctionInfo


logger = logging.getLogger(__name__)


@dataclass
class BugReport:
    """Bug detection report for a function."""

    function_name: str
    file_path: str
    has_bug: bool
    severity: str  # high, medium, low
    bugs: List[Dict[str, str]] = field(default_factory=list)
    function_start_line: int = 0  # 函数在文件中的起始行号


class BugDetector:
    """Bug detector using LLM."""

    SYSTEM_PROMPT = """你是一个 Python 代码审查专家。你的任务是分析函数代码，识别潜在的 bug。

请仔细分析提供的函数代码及其上下文（调用者和被调用者），查找以下类型的问题：
- 逻辑错误（如边界条件、空值处理）
- 类型错误
- 资源泄漏
- 并发问题
- 异常处理缺失
- 性能问题

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

如果没有发现问题，返回 {"has_bug": false, "severity": "low", "bugs": []}
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
        function_start_line: int = 0
    ) -> Optional[BugReport]:
        """
        Detect bugs in a function.

        Args:
            function: Function to analyze.
            context: Function context (callers, callees).
            file_path: Path to the file containing the function.

        Returns:
            BugReport if successful, None if failed after retries.
        """
        prompt = self._build_prompt(function, context)

        for attempt in range(self.config.detector_max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.config.llm_model,
                    messages=[
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.config.llm_temperature,
                    max_tokens=self.config.llm_max_tokens
                )

                content = response.choices[0].message.content
                result = self._parse_response(content)

                return BugReport(
                    function_name=function.name,
                    file_path=file_path,
                    has_bug=result["has_bug"],
                    severity=result["severity"],
                    bugs=result["bugs"],
                    function_start_line=function_start_line
                )

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
        self, function: FunctionInfo, context: Dict[str, Any]
    ) -> str:
        """
        Build prompt for LLM.

        Args:
            function: Function to analyze.
            context: Function context.

        Returns:
            Formatted prompt.
        """
        parts = []

        parts.append("请分析以下函数是否存在潜在 bug：\n\n")

        parts.append("### 当前函数\n")
        parts.append("```python\n")
        # 添加行号以帮助 LLM 定位
        code_lines = context["current_function"].split('\n')
        for i, line in enumerate(code_lines, 1):
            parts.append(f"{i:3d} | {line}\n")
        parts.append("```\n\n")

        if context.get("callers"):
            parts.append("### 调用者函数\n")
            for i, caller in enumerate(context["callers"], 1):
                parts.append(f"调用者 {i}:\n```python\n")
                parts.append(caller)
                parts.append("\n```\n\n")

        if context.get("callees"):
            parts.append("### 被调用函数\n")
            for i, callee in enumerate(context["callees"], 1):
                parts.append(f"被调用函数 {i}:\n```python\n")
                parts.append(callee)
                parts.append("\n```\n\n")

        parts.append(
            "请返回 JSON 格式的分析结果，只返回 JSON，不要其他说明文字。"
        )

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
