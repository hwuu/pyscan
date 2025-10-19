"""Reporter module for generating bug detection reports."""
import json
from typing import List
from datetime import datetime
from pyscan.bug_detector import BugReport


class Reporter:
    """Reporter for bug detection results."""

    def __init__(self, reports: List[BugReport], scan_directory: str = ""):
        """
        Initialize reporter.

        Args:
            reports: List of bug reports (one per bug).
            scan_directory: Absolute path to scanned directory.
        """
        self.reports = reports
        self.scan_directory = scan_directory

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
            "scan_directory": self.scan_directory,
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
                    "function_end_line": r.function_end_line,
                    "function_start_col": r.function_start_col,
                    "function_end_col": r.function_end_col,
                    "severity": r.severity,
                    "type": r.bug_type,
                    "description": r.description,
                    "location": r.location,
                    "start_line": r.start_line,
                    "end_line": r.end_line,
                    "start_col": r.start_col,
                    "end_col": r.end_col,
                    "suggestion": r.suggestion,
                    "callers": [
                        {
                            "file_path": c.get("file_path", ""),
                            "function_name": c.get("function_name", ""),
                            "start_line": c.get("start_line", 0),
                            "end_line": c.get("end_line", 0),
                            "start_col": c.get("start_col", 0),
                            "end_col": c.get("end_col", 0),
                            "call_lines": c.get("highlight_lines", [])
                        }
                        for c in r.callers
                    ],
                    "callees": r.callees,
                    "inferred_callers": [
                        {
                            "hint": ic.get("hint", ""),
                            "file_path": ic.get("file_path", ""),
                            "function_name": ic.get("function_name", ""),
                            "start_line": ic.get("start_line", 0),
                            "end_line": ic.get("end_line", 0),
                            "start_col": ic.get("start_col", 0),
                            "end_col": ic.get("end_col", 0),
                            "inference_lines": ic.get("highlight_lines", [])
                        }
                        for ic in r.inferred_callers
                    ]
                }
                for r in self.reports
            ]
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
