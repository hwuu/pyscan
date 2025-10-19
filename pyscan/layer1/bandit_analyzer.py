"""
Bandit 安全扫描器集成
"""

import subprocess
import json
from typing import List, Dict
import logging

from .base import StaticAnalyzer, StaticIssue

logger = logging.getLogger(__name__)


class BanditAnalyzer(StaticAnalyzer):
    """Bandit 安全扫描器"""

    def __init__(self):
        self.cache: Dict[str, List[StaticIssue]] = {}  # 缓存文件级别的分析结果
        self._available = None  # 懒加载检查

    def get_name(self) -> str:
        """返回分析器名称"""
        return "bandit"

    def is_available(self) -> bool:
        """检查 bandit 是否可用"""
        if self._available is not None:
            return self._available

        try:
            # 检查 bandit 是否安装
            result = subprocess.run(
                ['bandit', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            self._available = result.returncode == 0
            if self._available:
                logger.debug(f"Bandit found: {result.stdout.strip()}")
            else:
                logger.warning("Bandit not available (non-zero return code)")
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning(f"Bandit not available: {e}")
            self._available = False

        return self._available

    def analyze_file(self, file_path: str) -> List[StaticIssue]:
        """
        运行 bandit 分析文件

        Args:
            file_path: 文件路径

        Returns:
            问题列表
        """
        # 检查缓存
        if file_path in self.cache:
            logger.debug(f"Using cached bandit results for {file_path}")
            return self.cache[file_path]

        # 检查工具是否可用
        if not self.is_available():
            logger.debug("Bandit not available, skipping analysis")
            return []

        try:
            # 运行 bandit
            # -f json: JSON 格式输出
            # -q: 安静模式，不显示进度
            result = subprocess.run(
                ['bandit', '-f', 'json', '-q', file_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            # 注意：bandit 发现问题时 returncode 为 1，这是正常的
            issues = self._parse_output(result.stdout, file_path)
            self.cache[file_path] = issues

            logger.debug(f"Bandit found {len(issues)} issues in {file_path}")
            return issues

        except subprocess.TimeoutExpired:
            logger.warning(f"Bandit analysis timeout for {file_path}")
            return []
        except Exception as e:
            logger.warning(f"Bandit analysis failed for {file_path}: {e}")
            return []

    def analyze_function(self, file_path: str, func_name: str,
                        start_line: int, end_line: int) -> List[StaticIssue]:
        """
        获取特定函数范围内的问题

        Args:
            file_path: 文件路径
            func_name: 函数名
            start_line: 函数起始行号
            end_line: 函数结束行号

        Returns:
            函数范围内的问题列表
        """
        all_issues = self.analyze_file(file_path)
        return [
            issue for issue in all_issues
            if start_line <= issue.line <= end_line
        ]

    def _parse_output(self, output: str, file_path: str) -> List[StaticIssue]:
        """
        解析 bandit JSON 输出

        Bandit JSON 格式：
        {
            "results": [
                {
                    "code": "...",
                    "col_offset": 0,
                    "end_col_offset": 16,
                    "filename": "test.py",
                    "issue_confidence": "HIGH",
                    "issue_severity": "MEDIUM",
                    "issue_text": "Use of exec detected.",
                    "line_number": 5,
                    "line_range": [5],
                    "more_info": "...",
                    "test_id": "B102",
                    "test_name": "exec_used"
                }
            ],
            "metrics": {...}
        }

        Args:
            output: bandit JSON 输出
            file_path: 文件路径

        Returns:
            问题列表
        """
        issues = []

        try:
            if not output.strip():
                return issues

            data = json.loads(output)
            results = data.get('results', [])

            # Severity 映射
            severity_map = {
                'HIGH': 'high',
                'MEDIUM': 'medium',
                'LOW': 'low'
            }

            for result in results:
                # 使用 issue_severity，而非 issue_confidence
                severity = severity_map.get(
                    result.get('issue_severity', 'MEDIUM'),
                    'medium'
                )

                issues.append(StaticIssue(
                    tool='bandit',
                    type='security',
                    severity=severity,
                    message=result.get('issue_text', ''),
                    file_path=file_path,
                    line=result.get('line_number', 0),
                    column=result.get('col_offset'),
                    code=result.get('test_id')
                ))

        except json.JSONDecodeError as e:
            logger.debug(f"Failed to parse bandit JSON output: {e}")
        except Exception as e:
            logger.debug(f"Failed to parse bandit output: {e}")

        return issues
