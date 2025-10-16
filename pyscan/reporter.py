"""Reporter module for generating bug detection reports."""
import json
from pathlib import Path
from typing import List
from datetime import datetime
from jinja2 import Template
from pyscan.bug_detector import BugReport


class Reporter:
    """Reporter for bug detection results."""

    def __init__(self, reports: List[BugReport]):
        """
        Initialize reporter.

        Args:
            reports: List of bug reports.
        """
        self.reports = reports

    def to_json(self, output_path: str) -> None:
        """
        Export reports to JSON file.

        Args:
            output_path: Path to output JSON file.
        """
        data = {
            "timestamp": datetime.now().isoformat(),
            "total_functions": len(self.reports),
            "functions_with_bugs": sum(1 for r in self.reports if r.has_bug),
            "reports": [
                {
                    "function_name": r.function_name,
                    "file_path": r.file_path,
                    "has_bug": r.has_bug,
                    "severity": r.severity,
                    "bugs": r.bugs,
                    "function_start_line": r.function_start_line
                }
                for r in self.reports
            ]
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def to_markdown(self, output_path: str) -> None:
        """
        Export reports to Markdown file.

        Args:
            output_path: Path to output Markdown file.
        """
        lines = []

        lines.append("# Bug Detection Report\n")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # 统计信息
        total = len(self.reports)
        with_bugs = sum(1 for r in self.reports if r.has_bug)
        high_severity = sum(
            1 for r in self.reports if r.has_bug and r.severity == "high"
        )
        medium_severity = sum(
            1 for r in self.reports if r.has_bug and r.severity == "medium"
        )
        low_severity = sum(
            1 for r in self.reports if r.has_bug and r.severity == "low"
        )

        lines.append("## 统计信息\n\n")
        lines.append(f"- 总函数数: {total}\n")
        lines.append(f"- 有潜在问题的函数: {with_bugs}\n")
        lines.append(f"- 高严重性: {high_severity}\n")
        lines.append(f"- 中严重性: {medium_severity}\n")
        lines.append(f"- 低严重性: {low_severity}\n\n")

        # 详细报告
        lines.append("## 详细报告\n\n")

        for report in self.reports:
            if not report.has_bug:
                continue

            lines.append(f"### {report.function_name}\n\n")
            lines.append(f"**文件**: `{report.file_path}`\n\n")
            lines.append(f"**严重性**: {report.severity}\n\n")

            if report.bugs:
                lines.append("**发现的问题**:\n\n")
                for i, bug in enumerate(report.bugs, 1):
                    lines.append(f"{i}. **{bug.get('type', 'Unknown')}**\n")
                    lines.append(f"   - 描述: {bug.get('description', 'N/A')}\n")
                    lines.append(f"   - 位置: {bug.get('location', 'N/A')}\n")
                    lines.append(
                        f"   - 建议: {bug.get('suggestion', 'N/A')}\n\n"
                    )

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(''.join(lines))

    def to_html(self, output_path: str) -> None:
        """
        Export reports to HTML file.

        Args:
            output_path: Path to output HTML file.
        """
        template_str = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bug Detection Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }
        .stats {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stats ul {
            list-style: none;
            padding: 0;
        }
        .stats li {
            padding: 5px 0;
        }
        .report-item {
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .severity-high {
            border-left: 5px solid #dc3545;
        }
        .severity-medium {
            border-left: 5px solid #ffc107;
        }
        .severity-low {
            border-left: 5px solid #28a745;
        }
        .bug-item {
            background: #f8f9fa;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }
        .bug-type {
            font-weight: bold;
            color: #007bff;
        }
        code {
            background: #e9ecef;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
    </style>
</head>
<body>
    <h1>Bug Detection Report</h1>
    <p><strong>生成时间</strong>: {{ timestamp }}</p>

    <div class="stats">
        <h2>统计信息</h2>
        <ul>
            <li>总函数数: <strong>{{ total }}</strong></li>
            <li>有潜在问题的函数: <strong>{{ with_bugs }}</strong></li>
            <li>高严重性: <strong style="color: #dc3545;">{{ high_severity }}</strong></li>
            <li>中严重性: <strong style="color: #ffc107;">{{ medium_severity }}</strong></li>
            <li>低严重性: <strong style="color: #28a745;">{{ low_severity }}</strong></li>
        </ul>
    </div>

    <h2>详细报告</h2>
    {% for report in bug_reports %}
    <div class="report-item severity-{{ report.severity }}">
        <h3>{{ report.function_name }}</h3>
        <p><strong>文件</strong>: <code>{{ report.file_path }}</code></p>
        <p><strong>严重性</strong>: {{ report.severity }}</p>

        {% if report.bugs %}
        <h4>发现的问题:</h4>
        {% for bug in report.bugs %}
        <div class="bug-item">
            <div class="bug-type">{{ bug.type }}</div>
            <p><strong>描述</strong>: {{ bug.description }}</p>
            <p><strong>位置</strong>: {{ bug.location }}</p>
            <p><strong>建议</strong>: {{ bug.suggestion }}</p>
        </div>
        {% endfor %}
        {% endif %}
    </div>
    {% endfor %}
</body>
</html>
"""

        template = Template(template_str)

        bug_reports = [r for r in self.reports if r.has_bug]

        html_content = template.render(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            total=len(self.reports),
            with_bugs=len(bug_reports),
            high_severity=sum(1 for r in bug_reports if r.severity == "high"),
            medium_severity=sum(
                1 for r in bug_reports if r.severity == "medium"
            ),
            low_severity=sum(1 for r in bug_reports if r.severity == "low"),
            bug_reports=bug_reports
        )

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
