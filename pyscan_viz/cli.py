"""Command line interface for pyscan_viz."""
import argparse
import sys
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
        # 生成可视化 HTML
        visualizer = Visualizer()
        visualizer.generate_html(
            str(report_path),
            str(output_path),
            embed_source=args.embed_source
        )

        embed_mode = "embedded" if args.embed_source else "dynamic"
        print(f"[OK] Visualization generated: {output_path}")
        print(f"     Source code mode: {embed_mode}")
        print(f"     Open the HTML file in a web browser to view the report.")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
