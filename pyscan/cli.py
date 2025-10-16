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

        # 确保目录存在
        self.progress_dir.mkdir(parents=True, exist_ok=True)

    def load_progress(self):
        """
        加载上次的进度。

        Returns:
            (completed_functions, reports): 已完成的函数列表和报告列表
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
                # 重构报告对象
                from pyscan.bug_detector import BugReport
                reports = [
                    BugReport(
                        function_name=r['function_name'],
                        file_path=r['file_path'],
                        has_bug=r['has_bug'],
                        severity=r['severity'],
                        bugs=r['bugs'],
                        function_start_line=r.get('function_start_line', 0)
                    )
                    for r in reports_data
                ]
            else:
                reports = []

            logger.info(f"Loaded progress: {len(completed)} functions completed")
            return completed, reports

        except Exception as e:
            logger.warning(f"Failed to load progress: {e}")
            return set(), []

    def save_progress(self, completed_functions, reports):
        """
        保存当前进度。

        Args:
            completed_functions: 已完成的函数集合
            reports: 报告列表
        """
        try:
            # 保存已完成函数列表
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'completed_functions': list(completed_functions)
                }, f, indent=2)

            # 保存报告
            reports_data = [
                {
                    'function_name': r.function_name,
                    'file_path': r.file_path,
                    'has_bug': r.has_bug,
                    'severity': r.severity,
                    'bugs': r.bugs,
                    'function_start_line': r.function_start_line
                }
                for r in reports
            ]

            with open(self.reports_file, 'w', encoding='utf-8') as f:
                json.dump(reports_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Failed to save progress: {e}")

    def clear_progress(self):
        """清除进度文件。"""
        if self.progress_file.exists():
            self.progress_file.unlink()
        if self.reports_file.exists():
            self.reports_file.unlink()


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

        # 4. 构建上下文并检测 bug
        logger.info("Building context and detecting bugs...")
        context_builder = ContextBuilder(
            all_functions,
            max_tokens=config.detector_context_token_limit
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

        for func in tqdm(functions_to_detect, desc="Detecting bugs"):
            func_id = get_function_id(func)

            try:
                context = context_builder.build_context(func)
                report = detector.detect(
                    func,
                    context,
                    file_path=getattr(func, 'file_path', ''),
                    function_start_line=func.lineno
                )

                if report is None:
                    # 改进1: 检测失败,立即退出
                    error_msg = (
                        f"Bug detection failed for function '{func.name}' "
                        f"in {getattr(func, 'file_path', 'unknown')}. "
                        f"Aborting scan."
                    )
                    logger.error(error_msg)

                    # 保存当前进度
                    progress_manager.save_progress(completed_functions, reports)

                    logger.info(
                        f"Progress saved to {progress_manager.progress_dir}. "
                        f"Run the command again to resume."
                    )
                    sys.exit(1)

                # 检测成功
                reports.append(report)
                completed_functions.add(func_id)

                # 改进2: 每完成一个函数就保存进度
                progress_manager.save_progress(completed_functions, reports)

            except Exception as e:
                # 改进1: 发生异常,立即退出
                error_msg = (
                    f"Error detecting bugs for function '{func.name}': {e}"
                )
                logger.error(error_msg, exc_info=True)

                # 保存当前进度
                progress_manager.save_progress(completed_functions, reports)

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
        total = len(reports)
        with_bugs = sum(1 for r in reports if r.has_bug)

        logger.info(f"\nScan completed!")
        logger.info(f"Total functions: {total}")
        logger.info(f"Functions with bugs: {with_bugs}")

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
