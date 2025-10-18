"""Context builder module for constructing function analysis context."""
from typing import List, Dict, Any
from pyscan.ast_parser import FunctionInfo
from pyscan.config import Config
import tiktoken
import fnmatch
import logging

logger = logging.getLogger(__name__)


class ContextBuilder:
    """Builder for constructing function analysis context."""

    def __init__(
        self, functions: List[FunctionInfo], config: Config = None, max_tokens: int = 6000, use_tiktoken: bool = False, enable_advanced_analysis: bool = True
    ):
        """
        Initialize context builder.

        Args:
            functions: List of all functions in the codebase.
            config: Configuration object (optional).
            max_tokens: Maximum tokens for context.
            use_tiktoken: If True, use tiktoken for accurate token counting.
                         If False, use simple character-based estimation (1 token ≈ 4 chars).
            enable_advanced_analysis: If True, enable decorator and callable type inference.
        """
        self.functions = functions
        self.config = config
        self.max_tokens = max_tokens
        self.function_map = {f.name: f for f in functions}
        self.use_tiktoken = use_tiktoken
        self.enable_advanced_analysis = enable_advanced_analysis
        self.tokenizer = None

        # Initialize tokenizer if requested
        if self.use_tiktoken:
            try:
                self.tokenizer = tiktoken.encoding_for_model("gpt-4")
            except Exception:
                # Fallback to cl100k_base encoding
                self.tokenizer = tiktoken.get_encoding("cl100k_base")

        # Build decorator map (decorator_name -> list of decorated functions)
        self.decorator_map: Dict[str, List[FunctionInfo]] = {}
        if self.enable_advanced_analysis:
            self._build_decorator_map()

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
            "callees": [],
            "inferred_callers": [],  # 推断的调用者
            "inferred_callees": []   # 推断的被调用者
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

        # 高级分析：推断调用关系
        if self.enable_advanced_analysis:
            self._infer_decorator_calls(function, context)
            self._infer_callable_calls(function, context)

        # 判断是否为公共 API
        context["is_public_api"] = self.is_public_api(function, context)

        # 检查 token 限制并进行压缩
        context = self._fit_context_to_token_limit(context, function)

        return context

    def is_public_api(self, function: FunctionInfo, context: Dict[str, Any] = None) -> bool:
        """
        判断函数是否是公共 API/接口。

        规则:
        1. 有 API 相关的装饰器
        2. 文件路径匹配 API 模式
        3. 函数名符合 API 命名约定
        4. 没有内部调用者（可能被外部调用）

        Args:
            function: Function to check.
            context: Context dictionary (optional, used for caller check).

        Returns:
            True if function is likely a public API.
        """
        if not self.config:
            # 没有配置，默认为内部函数
            return False

        # 规则1: 检查装饰器
        for decorator in function.decorators:
            decorator_lower = decorator.lower()
            for indicator in self.config.detector_public_api_decorators:
                if indicator.lower() in decorator_lower:
                    return True

        # 规则2: 检查文件路径
        file_path = getattr(function, 'file_path', '')
        if file_path:
            for pattern in self.config.detector_public_api_file_patterns:
                if fnmatch.fnmatch(file_path, pattern):
                    return True

        # 规则3: 检查函数名
        for prefix in self.config.detector_public_api_name_prefixes:
            if function.name.startswith(prefix):
                return True

        # 规则4: 检查是否为非私有的顶层函数且没有内部调用者
        if not function.name.startswith('_'):
            # 获取内部调用者数量
            if context and len(context.get("callers", [])) == 0:
                # 没有内部调用者，但有推断的调用者（如装饰器），可能是公共API
                if context.get("inferred_callers"):
                    return True

        return False

    def _build_decorator_map(self):
        """Build map of decorators to decorated functions."""
        for func in self.functions:
            for decorator in func.decorators:
                if decorator not in self.decorator_map:
                    self.decorator_map[decorator] = []
                self.decorator_map[decorator].append(func)

    def _infer_decorator_calls(self, function: FunctionInfo, context: Dict[str, Any]):
        """
        Infer call relationships based on decorators.

        Args:
            function: Current function.
            context: Context dictionary to update.
        """
        # 情况1: 如果当前函数是装饰器，找出所有被它装饰的函数
        if function.name in self.decorator_map:
            for decorated_func in self.decorator_map[function.name]:
                hint = f"(推断): @{function.name}装饰的函数"
                context["inferred_callees"].append({
                    "code": decorated_func.code,
                    "hint": hint
                })

        # 情况2: 如果当前函数被装饰，找出装饰器函数
        for decorator in function.decorators:
            if decorator in self.function_map:
                decorator_func = self.function_map[decorator]
                hint = f"(推断): @{decorator}装饰器"
                context["inferred_callers"].append({
                    "code": decorator_func.code,
                    "hint": hint
                })

    def _infer_callable_calls(self, function: FunctionInfo, context: Dict[str, Any]):
        """
        Infer call relationships based on Callable type annotations.

        Args:
            function: Current function.
            context: Context dictionary to update.
        """
        # 情况1: 当前函数有 Callable 类型参数，找出签名匹配的函数
        for arg_name, arg_type in function.arg_types.items():
            if "Callable" in arg_type or "callable" in arg_type.lower():
                # 提取参数数量（宽松匹配）
                expected_arg_count = self._extract_callable_arg_count(arg_type)

                # 查找签名匹配的函数
                for func in self.functions:
                    if func.name != function.name:  # 排除自己
                        if expected_arg_count is None or len(func.args) == expected_arg_count:
                            hint = f"(推断): 可能作为参数 '{arg_name}: {arg_type}' 传入"
                            context["inferred_callees"].append({
                                "code": func.code,
                                "hint": hint
                            })
                            break  # 只添加一个示例

        # 情况2: 其他函数有 Callable 参数可能调用当前函数
        current_arg_count = len(function.args)
        for func in self.functions:
            if func.name != function.name:
                for arg_name, arg_type in func.arg_types.items():
                    if "Callable" in arg_type or "callable" in arg_type.lower():
                        expected_arg_count = self._extract_callable_arg_count(arg_type)
                        if expected_arg_count is None or current_arg_count == expected_arg_count:
                            hint = f"(推断): 可能被作为参数 '{arg_name}: {arg_type}' 传入 {func.name}"
                            context["inferred_callers"].append({
                                "code": func.code,
                                "hint": hint
                            })
                            break  # 每个函数只添加一个推断
                    if context["inferred_callers"]:
                        break

    def _extract_callable_arg_count(self, type_annotation: str) -> int:
        """
        Extract argument count from Callable type annotation.

        Args:
            type_annotation: Type annotation string.

        Returns:
            Number of arguments, or None if cannot determine.
        """
        # 尝试解析 Callable[[arg1, arg2, ...], return_type] 格式
        if "Callable[[" in type_annotation:
            try:
                start = type_annotation.index("[[") + 2
                end = type_annotation.index("]", start)
                args_part = type_annotation[start:end]
                if args_part.strip():
                    # 统计逗号数量 + 1
                    return args_part.count(",") + 1
                else:
                    return 0
            except (ValueError, IndexError):
                pass

        # 无法确定，返回 None（宽松匹配）
        return None

    def _prioritize_callers(
        self, callers: List[str], is_public_api: bool
    ) -> List[str]:
        """
        Prioritize callers by relevance.

        Args:
            callers: List of caller code strings.
            is_public_api: Whether current function is public API.

        Returns:
            Sorted list of callers (most important first).
        """
        # 计算每个 caller 的优先级分数
        caller_scores = []

        for caller_code in callers:
            score = 0

            # 规则1: 公共 API 的 caller 更重要 (+10)
            if is_public_api and any(
                indicator in caller_code.lower()
                for indicator in ['@route', '@api_view', '@endpoint', '@get', '@post']
            ):
                score += 10

            # 规则2: 代码较短的 caller 更容易理解 (+5 for <10 lines)
            line_count = len(caller_code.split('\n'))
            if line_count < 10:
                score += 5
            elif line_count < 20:
                score += 3

            # 规则3: 包含错误处理的 caller 更重要 (+3)
            if 'try:' in caller_code or 'except' in caller_code:
                score += 3

            caller_scores.append((score, caller_code))

        # 按分数降序排序
        caller_scores.sort(key=lambda x: x[0], reverse=True)

        return [code for score, code in caller_scores]

    def _fit_context_to_token_limit(
        self, context: Dict[str, Any], function: FunctionInfo
    ) -> Dict[str, Any]:
        """
        Fit context to token limit using multi-level compression strategy.

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

        is_public_api = context.get("is_public_api", False)

        # Level 1: 将 callers 转为签名，移除 callees（已在 build_context 中移除）
        logger.info(f"Applying compression level 1 for function {function.name}")
        compressed_context = {
            "current_function": context["current_function"],
            "callers": [
                self._extract_signature(code) for code in context.get("callers", [])
            ],
            "is_public_api": is_public_api,
            "inferred_callers": context.get("inferred_callers", [])
        }

        context_text = self._build_context_text(compressed_context)
        current_tokens = self._count_tokens(context_text)

        if current_tokens <= self.max_tokens:
            return compressed_context

        # Level 2: 限制 callers 数量 + 优先级排序
        logger.info(f"Applying compression level 2 for function {function.name}")
        max_callers = self.config.detector_max_callers if self.config else 3

        # 优先级排序
        callers = self._prioritize_callers(
            context.get("callers", []),
            is_public_api
        )
        compressed_context["callers"] = [
            self._extract_signature(code) for code in callers[:max_callers]
        ]

        context_text = self._build_context_text(compressed_context)
        current_tokens = self._count_tokens(context_text)

        if current_tokens <= self.max_tokens:
            return compressed_context

        # Level 3: 限制推断的 callers 数量
        logger.info(f"Applying compression level 3 for function {function.name}")
        max_inferred = self.config.detector_max_inferred if self.config else 2
        compressed_context["inferred_callers"] = compressed_context.get(
            "inferred_callers", []
        )[:max_inferred]

        context_text = self._build_context_text(compressed_context)
        current_tokens = self._count_tokens(context_text)

        if current_tokens <= self.max_tokens:
            return compressed_context

        # Level 4: 移除所有推断的 callers
        logger.info(f"Applying compression level 4 for function {function.name}")
        compressed_context["inferred_callers"] = []

        context_text = self._build_context_text(compressed_context)
        current_tokens = self._count_tokens(context_text)

        if current_tokens <= self.max_tokens:
            return compressed_context

        # Level 5: 只保留 1-2 个最重要的 callers
        logger.info(f"Applying compression level 5 for function {function.name}")
        compressed_context["callers"] = compressed_context["callers"][:2]

        context_text = self._build_context_text(compressed_context)
        current_tokens = self._count_tokens(context_text)

        if current_tokens <= self.max_tokens:
            return compressed_context

        # Level 6: 最小化 - 只保留当前函数
        logger.warning(
            f"Applying compression level 6 (minimal) for function {function.name}"
        )
        compressed_context = {
            "current_function": context["current_function"],
            "callers": [],
            "is_public_api": is_public_api,
            "inferred_callers": []
        }

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

        if context.get("callers"):
            parts.append("调用者函数:\n")
            for caller in context["callers"]:
                parts.append(caller)
                parts.append("\n")
            parts.append("\n")

        if context.get("inferred_callers"):
            parts.append("推断的调用者函数:\n")
            for inferred in context["inferred_callers"]:
                if isinstance(inferred, dict):
                    parts.append(f"{inferred.get('hint', '')}:\n")
                    parts.append(inferred.get('code', ''))
                else:
                    parts.append(str(inferred))
                parts.append("\n")
            parts.append("\n")

        # callees 已移除 - 不包含在上下文中

        return "".join(parts)

    def _count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Text to count tokens for.

        Returns:
            Number of tokens.
        """
        if self.use_tiktoken and self.tokenizer is not None:
            try:
                return len(self.tokenizer.encode(text))
            except Exception:
                # Fallback to simple estimation if tiktoken fails
                return len(text) // 4
        else:
            # Simple estimation: 1 token ≈ 4 characters
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
