"""Context builder module for constructing function analysis context."""
from typing import List, Dict, Any
from pyscan.ast_parser import FunctionInfo
import tiktoken


class ContextBuilder:
    """Builder for constructing function analysis context."""

    def __init__(
        self, functions: List[FunctionInfo], max_tokens: int = 6000
    ):
        """
        Initialize context builder.

        Args:
            functions: List of all functions in the codebase.
            max_tokens: Maximum tokens for context.
        """
        self.functions = functions
        self.max_tokens = max_tokens
        self.function_map = {f.name: f for f in functions}

        # Initialize tokenizer
        try:
            self.tokenizer = tiktoken.encoding_for_model("gpt-4")
        except Exception:
            # Fallback to cl100k_base encoding
            self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def build_context(self, function: FunctionInfo) -> Dict[str, Any]:
        """
        Build context for a function.

        Args:
            function: Function to build context for.

        Returns:
            Dictionary containing current function, callers, and callees.
        """
        context = {
            "current_function": function.code,
            "callers": [],
            "callees": []
        }

        # 查找调用者（哪些函数调用了当前函数）
        for func in self.functions:
            if function.name in func.calls:
                context["callers"].append(func.code)

        # 查找被调用者（当前函数调用了哪些函数）
        for call_name in function.calls:
            if call_name in self.function_map:
                callee = self.function_map[call_name]
                context["callees"].append(callee.code)

        # 检查 token 限制并进行压缩
        context = self._fit_context_to_token_limit(context, function)

        return context

    def _fit_context_to_token_limit(
        self, context: Dict[str, Any], function: FunctionInfo
    ) -> Dict[str, Any]:
        """
        Fit context to token limit by truncating or summarizing.

        Args:
            context: Original context.
            function: Current function.

        Returns:
            Adjusted context within token limit.
        """
        context_text = self._build_context_text(context)
        current_tokens = self._count_tokens(context_text)

        if current_tokens <= self.max_tokens:
            return context

        # 超过限制，开始压缩
        # 策略1: 保留当前函数完整代码，callers/callees 转为签名
        compressed_context = {
            "current_function": context["current_function"],
            "callers": [
                self._extract_signature(code) for code in context["callers"]
            ],
            "callees": [
                self._extract_signature(code) for code in context["callees"]
            ]
        }

        context_text = self._build_context_text(compressed_context)
        current_tokens = self._count_tokens(context_text)

        if current_tokens <= self.max_tokens:
            return compressed_context

        # 策略2: 限制 callers 和 callees 数量
        max_callers = 3
        max_callees = 3

        compressed_context["callers"] = compressed_context["callers"][
            :max_callers
        ]
        compressed_context["callees"] = compressed_context["callees"][
            :max_callees
        ]

        return compressed_context

    def _build_context_text(self, context: Dict[str, Any]) -> str:
        """
        Build context text from context dictionary.

        Args:
            context: Context dictionary.

        Returns:
            Formatted context text.
        """
        parts = []

        parts.append("当前函数:\n")
        parts.append(context["current_function"])
        parts.append("\n\n")

        if context["callers"]:
            parts.append("调用者函数:\n")
            for caller in context["callers"]:
                parts.append(caller)
                parts.append("\n")
            parts.append("\n")

        if context["callees"]:
            parts.append("被调用函数:\n")
            for callee in context["callees"]:
                parts.append(callee)
                parts.append("\n")

        return "".join(parts)

    def _count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Text to count tokens for.

        Returns:
            Number of tokens.
        """
        try:
            return len(self.tokenizer.encode(text))
        except Exception:
            # Fallback: rough estimate (1 token ≈ 4 characters)
            return len(text) // 4

    def _extract_signature(self, code: str) -> str:
        """
        Extract function signature from code.

        Args:
            code: Function code.

        Returns:
            Function signature (first line + docstring if available).
        """
        lines = code.strip().split('\n')
        if not lines:
            return code

        # 提取第一行（函数定义）
        signature = lines[0]

        # 尝试提取 docstring
        if len(lines) > 1:
            for line in lines[1:4]:  # 查看前几行
                stripped = line.strip()
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    signature += "\n    " + stripped
                    break

        return signature
