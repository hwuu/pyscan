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
