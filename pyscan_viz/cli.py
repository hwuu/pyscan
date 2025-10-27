"""Command line interface for pyscan_viz."""
import argparse
import sys
import json
from pathlib import Path
from pyscan_viz.visualizer import Visualizer


def main():
    """Main entry point for pyscan_viz CLI."""
    parser = argparse.ArgumentParser(
        description='PyScan Visualizer - Convert pyscan JSON reports to interactive HTML'
    )

    parser.add_argument(
        'report_json',
        type=str,
        help='Path to pyscan JSON report file'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='Output HTML file path (default: <report_json>.html)'
    )

    parser.add_argument(
        '--embed-source',
        action='store_true',
        default=True,
        help='Embed source code in HTML (default: True)'
    )

    parser.add_argument(
        '--no-embed-source',
        dest='embed_source',
        action='store_false',
        help='Do not embed source code, load dynamically instead'
    )

    parser.add_argument(
        '--git-enrich',
        action='store_true',
        default=True,
        help='Add git blame information to all bugs (default: True)'
    )

    parser.add_argument(
        '--no-git-enrich',
        dest='git_enrich',
        action='store_false',
        help='Do not add git blame information'
    )

    parser.add_argument(
        '-c', '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )

    args = parser.parse_args()

    # 检查输入文件是否存在
    report_path = Path(args.report_json)
    if not report_path.exists():
        print(f"Error: Report file not found: {args.report_json}", file=sys.stderr)
        sys.exit(1)

    # 确定输出文件名
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = report_path.with_suffix('.html')

    try:
        # 读取报告
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)

        # Git 集成
        enriched_report = None
        if args.git_enrich:
            from pyscan_viz.git_analyzer import GitAnalyzer
            from pyscan.config import Config, ConfigError

            # 获取扫描目录（用于 git repo 检测）
            scan_dir = report.get('scan_directory')
            if scan_dir:
                git_repo_path = scan_dir
            else:
                # 兼容旧格式：使用 report.json 所在目录
                git_repo_path = str(report_path.parent)

            # 尝试加载 git 平台配置（如果存在）
            custom_platforms = None
            config_path = Path(args.config)
            if config_path.exists():
                try:
                    config = Config.from_file(str(config_path))
                    custom_platforms = config.git_platforms
                    if custom_platforms:
                        print(f"Loaded {len(custom_platforms)} custom git platform(s) from {config_path}")
                except ConfigError as e:
                    print(f"Error: Failed to load git config from {config_path}", file=sys.stderr)
                    print(f"       {e}", file=sys.stderr)
                    sys.exit(1)
                except Exception as e:
                    print(f"Error: Unexpected error loading config from {config_path}", file=sys.stderr)
                    print(f"       {e}", file=sys.stderr)
                    sys.exit(1)

            # 初始化 GitAnalyzer
            git_analyzer = GitAnalyzer(git_repo_path, custom_platforms=custom_platforms)

            if not git_analyzer.is_git_repo:
                print("Warning: Not a git repository, skipping git integration", file=sys.stderr)
            else:
                bugs = report.get('bugs', [])
                print(f"Enriching {len(bugs)} bugs with git information...")
                enriched_bugs = git_analyzer.enrich_bugs_with_git_info(bugs)

                # 更新 report
                enriched_report = report.copy()
                enriched_report['bugs'] = enriched_bugs
                print("Git information added successfully")

        # 生成可视化 HTML
        visualizer = Visualizer()
        visualizer.generate_html(
            str(report_path),
            str(output_path),
            embed_source=args.embed_source,
            report=enriched_report  # 传入 enriched report（如果有）
        )

        embed_mode = "embedded" if args.embed_source else "dynamic"
        git_mode = " (with git info)" if args.git_enrich and enriched_report else ""
        print(f"[OK] Visualization generated: {output_path}")
        print(f"     Source code mode: {embed_mode}{git_mode}")
        print(f"     Open the HTML file in a web browser to view the report.")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
