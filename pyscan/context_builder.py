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
                # 找出调用目标函数的行号（相对于 func 的行号，1-based）
                highlight_lines = []
                lines = func.code.split('\n')
                for i, line in enumerate(lines, 1):
                    if f"{function.name}(" in line:
                        highlight_lines.append(i)

                context["callers"].append({
                    "code": func.code,
                    "highlight_lines": highlight_lines  # 调用点的相对行号（1-based）
                })

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

                # 装饰器的 highlight_lines 是函数定义行（第1行）
                highlight_lines = [1]

                context["inferred_callers"].append({
                    "file_path": getattr(decorator_func, 'file_path', ''),
                    "function_name": decorator_func.name,
                    "code": decorator_func.code,
                    "start_line": decorator_func.lineno,
                    "end_line": decorator_func.end_lineno,
                    "start_col": decorator_func.col_offset,
                    "end_col": decorator_func.end_col_offset,
                    "highlight_lines": highlight_lines,  # 装饰器定义行
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

                            # 查找参数定义的行号（相对行号）
                            highlight_lines = []
                            lines = func.code.split('\n')
                            for i, line in enumerate(lines, 1):
                                if arg_name in line and (":" in line or "def " in line):
                                    highlight_lines.append(i)
                            if not highlight_lines:
                                highlight_lines = [1]  # 默认高亮函数签名

                            context["inferred_callers"].append({
                                "file_path": getattr(func, 'file_path', ''),
                                "function_name": func.name,
                                "code": func.code,
                                "start_line": func.lineno,
                                "end_line": func.end_lineno,
                                "start_col": func.col_offset,
                                "end_col": func.end_col_offset,
                                "arg_name": arg_name,  # 保存参数名用于高亮
                                "arg_type": arg_type,  # 保存参数类型用于高亮
                                "highlight_lines": highlight_lines,  # 参数定义行
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

    def _extract_snippet_with_context(
        self, code: str, highlight_lines: List[int], context_lines: int = 10
    ) -> str:
        """
        提取函数签名和调用点周围的代码片段。

        Args:
            code: 完整函数代码
            highlight_lines: 需要高亮的行号列表（1-based，相对于函数）
            context_lines: 调用点前后保留的行数

        Returns:
            压缩后的代码片段（包含函数签名 + 调用点上下文）
        """
        lines = code.split('\n')
        if not lines:
            return code

        # 1. 提取函数签名（第1行到第一个不以空白字符开头的行，或找到 ): 结束）
        signature_lines = []
        for i, line in enumerate(lines):
            signature_lines.append(line)
            # 检查是否是函数签名结束（找到 ): 或者单独的 ):）
            stripped = line.strip()
            if stripped.endswith('):') or stripped == '):':
                break
            # 如果已经超过10行还没找到结束，就只保留第一行
            if i >= 10:
                signature_lines = [lines[0]]
                break

        signature = '\n'.join(signature_lines)

        # 2. 提取每个 highlight_line 周围的上下文
        ranges = []
        for hl in highlight_lines:
            start = max(1, hl - context_lines)
            end = min(len(lines), hl + context_lines)
            ranges.append((start, end))

        # 3. 合并重叠的范围
        if ranges:
            ranges.sort()
            merged = [ranges[0]]
            for start, end in ranges[1:]:
                last_start, last_end = merged[-1]
                if start <= last_end + 1:  # 重叠或相邻
                    merged[-1] = (last_start, max(last_end, end))
                else:
                    merged.append((start, end))
        else:
            merged = []

        # 4. 构建代码片段
        parts = [signature]

        for start, end in merged:
            # 如果范围不是从签名开始，添加省略标记
            if start > len(signature_lines) + 1:
                parts.append("    ...")

            # 添加代码行
            for i in range(start - 1, end):
                if i >= len(lines):
                    break
                # 跳过已经在签名中的行
                if i < len(signature_lines):
                    continue
                parts.append(lines[i])

        return '\n'.join(parts)

    def _fit_context_to_token_limit(
        self, context: Dict[str, Any], function: FunctionInfo
    ) -> Dict[str, Any]:
        """
        Fit context to token limit using 8-level compression strategy.

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

        # Level 1: inferred_callers 只保留函数签名和调用点 ±10 行
        logger.info(f"Applying compression level 1 for function {function.name}")
        compressed_context = {
            "current_function": context["current_function"],
            "callers": context.get("callers", []),
            "is_public_api": is_public_api,
            "inferred_callers": []
        }

        for inferred in context.get("inferred_callers", []):
            if isinstance(inferred, dict) and "code" in inferred:
                snippet = self._extract_snippet_with_context(
                    inferred["code"],
                    inferred.get("highlight_lines", [1]),
                    context_lines=10
                )
                compressed_context["inferred_callers"].append({
                    **inferred,
                    "code": snippet
                })
            else:
                compressed_context["inferred_callers"].append(inferred)

        context_text = self._build_context_text(compressed_context)
        current_tokens = self._count_tokens(context_text)

        if current_tokens <= self.max_tokens:
            return compressed_context

        # Level 2: inferred_callers 只保留函数签名和调用点 ±5 行
        logger.info(f"Applying compression level 2 for function {function.name}")
        compressed_context["inferred_callers"] = []
        for inferred in context.get("inferred_callers", []):
            if isinstance(inferred, dict) and "code" in inferred:
                snippet = self._extract_snippet_with_context(
                    inferred["code"],
                    inferred.get("highlight_lines", [1]),
                    context_lines=5
                )
                compressed_context["inferred_callers"].append({
                    **inferred,
                    "code": snippet
                })
            else:
                compressed_context["inferred_callers"].append(inferred)

        context_text = self._build_context_text(compressed_context)
        current_tokens = self._count_tokens(context_text)

        if current_tokens <= self.max_tokens:
            return compressed_context

        # Level 3: 限制 inferred_callers 数量（默认3）
        logger.info(f"Applying compression level 3 for function {function.name}")
        max_inferred = self.config.detector_max_inferred if self.config else 3
        compressed_context["inferred_callers"] = compressed_context["inferred_callers"][:max_inferred]

        context_text = self._build_context_text(compressed_context)
        current_tokens = self._count_tokens(context_text)

        if current_tokens <= self.max_tokens:
            return compressed_context

        # Level 4: 删除所有 inferred_callers
        logger.info(f"Applying compression level 4 for function {function.name}")
        compressed_context["inferred_callers"] = []

        context_text = self._build_context_text(compressed_context)
        current_tokens = self._count_tokens(context_text)

        if current_tokens <= self.max_tokens:
            return compressed_context

        # Level 5: callers 只保留函数签名和调用点 ±10 行
        logger.info(f"Applying compression level 5 for function {function.name}")
        compressed_context["callers"] = []
        for caller in context.get("callers", []):
            if isinstance(caller, dict) and "code" in caller:
                snippet = self._extract_snippet_with_context(
                    caller["code"],
                    caller.get("highlight_lines", [1]),
                    context_lines=10
                )
                compressed_context["callers"].append({
                    **caller,
                    "code": snippet
                })
            else:
                # 兼容旧格式（纯字符串）
                compressed_context["callers"].append(caller)

        context_text = self._build_context_text(compressed_context)
        current_tokens = self._count_tokens(context_text)

        if current_tokens <= self.max_tokens:
            return compressed_context

        # Level 6: callers 只保留函数签名和调用点 ±5 行
        logger.info(f"Applying compression level 6 for function {function.name}")
        compressed_context["callers"] = []
        for caller in context.get("callers", []):
            if isinstance(caller, dict) and "code" in caller:
                snippet = self._extract_snippet_with_context(
                    caller["code"],
                    caller.get("highlight_lines", [1]),
                    context_lines=5
                )
                compressed_context["callers"].append({
                    **caller,
                    "code": snippet
                })
            else:
                compressed_context["callers"].append(caller)

        context_text = self._build_context_text(compressed_context)
        current_tokens = self._count_tokens(context_text)

        if current_tokens <= self.max_tokens:
            return compressed_context

        # Level 7: 限制 caller 数量（默认3）
        logger.info(f"Applying compression level 7 for function {function.name}")
        max_callers = self.config.detector_max_callers if self.config else 3
        compressed_context["callers"] = compressed_context["callers"][:max_callers]

        context_text = self._build_context_text(compressed_context)
        current_tokens = self._count_tokens(context_text)

        if current_tokens <= self.max_tokens:
            return compressed_context

        # Level 8: 删除所有 callers（最小化）
        logger.warning(
            f"Applying compression level 8 (minimal) for function {function.name}"
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
                # 处理新格式（字典）和旧格式（字符串）
                if isinstance(caller, dict):
                    parts.append(caller.get('code', ''))
                else:
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
