"""Command line interface for pyscan."""
import argparse
import json
import logging
import sys
from pathlib import Path
from tqdm import tqdm

from pyscan.config import Config, ConfigError
from pyscan.scanner import Scanner
from pyscan.ast_parser import ASTParser
from pyscan.context_builder import ContextBuilder
from pyscan.bug_detector import BugDetector
from pyscan.reporter import Reporter


# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProgressManager:
    """管理扫描进度和断点续传。"""

    def __init__(self, progress_dir: Path):
        """
        初始化进度管理器。

        Args:
            progress_dir: 进度文件存储目录
        """
        self.progress_dir = progress_dir
        self.progress_file = progress_dir / "progress.json"
        self.reports_file = progress_dir / "reports.json"
        self.prompts_dir = progress_dir / "prompts"

        # 确保目录存在
        self.progress_dir.mkdir(parents=True, exist_ok=True)
        self.prompts_dir.mkdir(parents=True, exist_ok=True)

    def load_progress(self):
        """
        加载上次的进度。

        Returns:
            (completed_functions, reports): 已完成的函数列表和 bug 报告列表
        """
        if not self.progress_file.exists():
            return set(), []

        try:
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            completed = set(data.get('completed_functions', []))

            if self.reports_file.exists():
                with open(self.reports_file, 'r', encoding='utf-8') as f:
                    reports_data = json.load(f)
                # 重构报告对象（新格式：每个 bug 一个 report）
                from pyscan.bug_detector import BugReport
                reports = [
                    BugReport(
                        bug_id=r['bug_id'],
                        function_name=r['function_name'],
                        file_path=r['file_path'],
                        function_start_line=r['function_start_line'],
                        severity=r['severity'],
                        bug_type=r['type'],
                        description=r['description'],
                        location=r['location'],
                        start_line=r['start_line'],
                        end_line=r['end_line'],
                        start_col=r['start_col'],
                        end_col=r['end_col'],
                        suggestion=r['suggestion'],
                        callers=r.get('callers', []),
                        callees=r.get('callees', []),
                        inferred_callers=r.get('inferred_callers', [])
                    )
                    for r in reports_data
                ]
            else:
                reports = []

            logger.info(f"Loaded progress: {len(completed)} functions completed, {len(reports)} bugs found")
            return completed, reports

        except Exception as e:
            logger.warning(f"Failed to load progress: {e}")
            return set(), []

    def save_progress(self, completed_functions, reports):
        """
        保存当前进度。

        Args:
            completed_functions: 已完成的函数集合
            reports: Bug 报告列表（每个 bug 一个 report）
        """
        try:
            # 保存已完成函数列表
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'completed_functions': list(completed_functions)
                }, f, indent=2)

            # 保存报告（新格式：每个 bug 一个 report）
            reports_data = [
                {
                    'bug_id': r.bug_id,
                    'function_name': r.function_name,
                    'file_path': r.file_path,
                    'function_start_line': r.function_start_line,
                    'severity': r.severity,
                    'type': r.bug_type,
                    'description': r.description,
                    'location': r.location,
                    'start_line': r.start_line,
                    'end_line': r.end_line,
                    'start_col': r.start_col,
                    'end_col': r.end_col,
                    'suggestion': r.suggestion,
                    'callers': r.callers,
                    'callees': r.callees,
                    'inferred_callers': r.inferred_callers
                }
                for r in reports
            ]

            with open(self.reports_file, 'w', encoding='utf-8') as f:
                json.dump(reports_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Failed to save progress: {e}")

    def save_llm_interaction(self, bug_id: str, file_path: str, function_name: str, prompt: str, raw_response: str):
        """
        保存 LLM 交互到 .md 文件。

        Args:
            bug_id: Bug ID (如 BUG_0001)
            file_path: 源文件路径
            function_name: 函数名
            prompt: 发送给 LLM 的 prompt
            raw_response: LLM 的原始响应
        """
        try:
            # 生成文件名: file.py__function_name__BUG_0001.md
            file_basename = Path(file_path).name if file_path else "unknown"
            md_filename = f"{file_basename}__{function_name}__{bug_id}.md"
            md_path = self.prompts_dir / md_filename

            # 构建 markdown 内容
            content = f"""# Bug Detection: {function_name}

**File:** `{file_path}`
**Bug ID:** {bug_id}
**Timestamp:** {__import__('datetime').datetime.now().isoformat()}

---

## Prompt

{prompt}

---

## LLM Response

{raw_response}
"""

            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(content)

        except Exception as e:
            logger.error(f"Failed to save LLM interaction for {function_name}: {e}")


def extract_caller_snippet(caller_code: str, target_func_name: str, context_lines: int = 5) -> str:
    """
    提取调用者函数的签名和调用目标函数的代码片段。

    Args:
        caller_code: 调用者函数的完整代码
        target_func_name: 目标函数名（被调用的函数）
        context_lines: 调用行上下文行数（±N行）

    Returns:
        包含签名和调用上下文的代码片段，调用行用 >>>  标记
    """
    lines = caller_code.split('\n')
    if not lines:
        return caller_code

    # 提取函数签名（第一行，通常是 def xxx(...): ）
    signature = lines[0] if lines else ""

    # 查找包含目标函数调用的所有行号
    call_lines = []
    for i, line in enumerate(lines):
        # 简单检查：行中是否包含 target_func_name(
        if f"{target_func_name}(" in line:
            call_lines.append(i)

    if not call_lines:
        # 如果没找到调用行，返回签名
        return signature

    # 对于每个调用点，提取 ±context_lines 的代码
    snippets = [signature]

    for call_line_idx in call_lines:
        start = max(1, call_line_idx - context_lines)  # 跳过签名行
        end = min(len(lines), call_line_idx + context_lines + 1)

        # 添加上下文标记
        snippets.append(f"\n    # ... (call at line {call_line_idx + 1})")

        # 添加代码行，调用行前面加上 ">>> " 标记
        for i in range(start, end):
            if i == call_line_idx:
                snippets.append(f">>> {lines[i]}")
            else:
                snippets.append(lines[i])

    return '\n'.join(snippets)


def main():
    """Main entry point for pyscan CLI."""
    parser = argparse.ArgumentParser(
        description='PyScan - Python code bug detection tool using LLM'
    )

    parser.add_argument(
        'directory',
        type=str,
        help='Directory to scan for Python files'
    )

    parser.add_argument(
        '-c', '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        default='report.json',
        help='Output JSON file path (default: report.json)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # 1. 加载配置
        logger.info(f"Loading configuration from {args.config}")
        config = Config.from_file(args.config)

        # 2. 扫描代码文件
        logger.info(f"Scanning directory: {args.directory}")
        scanner = Scanner(exclude_patterns=config.scan_exclude_patterns)
        files = scanner.scan(args.directory)

        if not files:
            logger.warning("No Python files found!")
            return

        logger.info(f"Found {len(files)} Python files")

        # 3. 解析所有文件的 AST
        logger.info("Parsing Python files...")
        parser_ast = ASTParser()
        all_functions = []

        for file_path in tqdm(files, desc="Parsing files"):
            try:
                functions = parser_ast.parse_file(file_path)
                # 为每个函数记录文件路径
                for func in functions:
                    func.file_path = file_path
                all_functions.extend(functions)
            except Exception as e:
                logger.error(f"Failed to parse {file_path}: {e}")

        if not all_functions:
            logger.warning("No functions found!")
            return

        logger.info(f"Found {len(all_functions)} functions")

        # 4. 初始化进度管理器
        progress_dir = Path(args.directory) / ".pyscan"
        progress_manager = ProgressManager(progress_dir)

        # 加载之前的进度
        completed_functions, reports = progress_manager.load_progress()

        # 如果有之前的进度，先生成一次报告
        if reports:
            logger.info("Found previous progress, generating report from existing data...")
            reporter = Reporter(reports)
            reporter.to_json(args.output)
            logger.info(f"Existing report generated: {args.output}")

        # 4. 构建上下文并检测 bug
        logger.info("Building context and detecting bugs...")
        context_builder = ContextBuilder(
            all_functions,
            config=config,
            max_tokens=config.detector_context_token_limit,
            use_tiktoken=config.detector_use_tiktoken,
            enable_advanced_analysis=config.detector_enable_advanced_analysis
        )
        detector = BugDetector(config)

        # 生成函数唯一ID
        def get_function_id(func):
            return f"{getattr(func, 'file_path', '')}::{func.name}"

        # 过滤出需要检测的函数
        functions_to_detect = [
            f for f in all_functions
            if get_function_id(f) not in completed_functions
        ]

        if len(functions_to_detect) < len(all_functions):
            logger.info(
                f"Resuming from previous run: {len(completed_functions)} "
                f"functions already completed, {len(functions_to_detect)} remaining"
            )

        # Bug ID 计数器 (从已有的 reports 开始计数)
        bug_counter = len(reports) + 1

        for func in tqdm(functions_to_detect, desc="Detecting bugs"):
            func_id = get_function_id(func)

            try:
                context = context_builder.build_context(func)

                # 提取 callers 信息：文件路径 + 函数名 + 调用点周围代码
                callers = []
                callees = []

                # 从context中提取实际的函数调用关系
                for func_obj in all_functions:
                    if func.name in func_obj.calls:
                        # 提取调用点周围的代码（签名 + 调用行 ± 5）
                        caller_snippet = extract_caller_snippet(
                            func_obj.code,
                            func.name,
                            context_lines=5
                        )

                        callers.append({
                            'file_path': getattr(func_obj, 'file_path', ''),
                            'function_name': func_obj.name,
                            'code_snippet': caller_snippet
                        })

                for call_name in func.calls:
                    if call_name in [f.name for f in all_functions]:
                        callees.append(call_name)

                # 提取 inferred_callers（格式已经是 dict，包含 hint 和 code）
                inferred_callers = context.get("inferred_callers", [])

                result = detector.detect(
                    func,
                    context,
                    file_path=getattr(func, 'file_path', ''),
                    function_start_line=func.lineno,
                    callers=callers,
                    callees=callees,
                    inferred_callers=inferred_callers,
                    bug_id_start=bug_counter
                )

                if result is None:
                    # 检测失败,立即退出
                    error_msg = (
                        f"Bug detection failed for function '{func.name}' "
                        f"in {getattr(func, 'file_path', 'unknown')}. "
                        f"Aborting scan."
                    )
                    logger.error(error_msg)

                    # 保存当前进度和报告
                    progress_manager.save_progress(completed_functions, reports)
                    reporter = Reporter(reports)
                    reporter.to_json(args.output)

                    logger.info(
                        f"Progress saved to {progress_manager.progress_dir}. "
                        f"Run the command again to resume."
                    )
                    sys.exit(1)

                # 检测成功，提取结果（现在是 bug 列表）
                bug_reports = result["reports"]
                prompt = result["prompt"]
                raw_response = result["raw_response"]

                # 如果有 bug，保存 LLM 交互并添加到 reports
                if bug_reports:
                    # 为每个 bug 保存 LLM 交互
                    for bug_report in bug_reports:
                        progress_manager.save_llm_interaction(
                            bug_id=bug_report.bug_id,
                            file_path=getattr(func, 'file_path', ''),
                            function_name=func.name,
                            prompt=prompt,
                            raw_response=raw_response
                        )
                        reports.append(bug_report)
                        bug_counter += 1

                completed_functions.add(func_id)

                # 每完成一个函数就保存进度和更新报告
                progress_manager.save_progress(completed_functions, reports)
                reporter = Reporter(reports)
                reporter.to_json(args.output)

            except Exception as e:
                # 发生异常,立即退出
                error_msg = (
                    f"Error detecting bugs for function '{func.name}': {e}"
                )
                logger.error(error_msg, exc_info=True)

                # 保存当前进度和报告
                progress_manager.save_progress(completed_functions, reports)
                reporter = Reporter(reports)
                reporter.to_json(args.output)

                logger.info(
                    f"Progress saved to {progress_manager.progress_dir}. "
                    f"Run the command again to resume."
                )
                sys.exit(1)

        # 5. 生成报告
        logger.info("Generating report...")
        reporter = Reporter(reports)
        reporter.to_json(args.output)
        logger.info(f"Report generated: {args.output}")

        # 统计信息
        total_bugs = len(reports)
        affected_functions = len(set(r.function_name for r in reports))
        high_severity = sum(1 for r in reports if r.severity == "high")
        medium_severity = sum(1 for r in reports if r.severity == "medium")
        low_severity = sum(1 for r in reports if r.severity == "low")

        logger.info(f"\nScan completed!")
        logger.info(f"Total bugs found: {total_bugs}")
        logger.info(f"Affected functions: {affected_functions}")
        logger.info(f"Severity breakdown - High: {high_severity}, Medium: {medium_severity}, Low: {low_severity}")

    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\nScan interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
