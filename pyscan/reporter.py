"""Reporter module for generating bug detection reports."""
import json
from typing import List
from datetime import datetime
from pyscan.bug_detector import BugReport


class Reporter:
    """Reporter for bug detection results."""

    def __init__(self, reports: List[BugReport]):
        """
        Initialize reporter.

        Args:
            reports: List of bug reports (one per bug).
        """
        self.reports = reports

    def to_json(self, output_path: str) -> None:
        """
        Export reports to JSON file.

        Args:
            output_path: Path to output JSON file.
        """
        # 统计信息
        total_bugs = len(self.reports)
        unique_functions = len(set(r.function_name for r in self.reports))
        severity_counts = {
            "high": sum(1 for r in self.reports if r.severity == "high"),
            "medium": sum(1 for r in self.reports if r.severity == "medium"),
            "low": sum(1 for r in self.reports if r.severity == "low")
        }

        data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_bugs": total_bugs,
                "affected_functions": unique_functions,
                "severity_breakdown": severity_counts
            },
            "bugs": [
                {
                    "bug_id": r.bug_id,
                    "function_name": r.function_name,
                    "file_path": r.file_path,
                    "function_start_line": r.function_start_line,
                    "severity": r.severity,
                    "type": r.bug_type,
                    "description": r.description,
                    "location": r.location,
                    "start_line": r.start_line,
                    "end_line": r.end_line,
                    "start_col": r.start_col,
                    "end_col": r.end_col,
                    "suggestion": r.suggestion,
                    "callers": r.callers,
                    "callees": r.callees,
                    "inferred_callers": r.inferred_callers
                }
                for r in self.reports
            ]
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
