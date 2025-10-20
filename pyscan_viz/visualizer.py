"""Visualizer for converting JSON reports to interactive HTML."""
import json
from pathlib import Path
from typing import Dict, List, Any


class Visualizer:
    """Generate interactive HTML visualization from JSON report."""

    def generate_html(self, report_json_path: str, output_html_path: str, embed_source: bool = True):
        """
        Generate interactive HTML from JSON report.

        Args:
            report_json_path: Path to JSON report file.
            output_html_path: Path to output HTML file.
            embed_source: If True, embed source code in HTML. If False, load dynamically.
        """
        # 加载 JSON 报告
        with open(report_json_path, 'r', encoding='utf-8') as f:
            report = json.load(f)

        # 获取 report.json 所在的目录，用于解析相对路径
        report_dir = Path(report_json_path).parent.absolute()

        # 如果需要嵌入源码，读取所有源文件
        source_files = {}
        if embed_source:
            source_files = self._load_source_files(report, report_dir)

        # 生成 HTML
        html_content = self._build_html(report, source_files, embed_source)

        # 写入文件
        with open(output_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def _load_source_files(self, report: Dict[str, Any], report_dir: Path) -> Dict[str, str]:
        """
        Load all source files mentioned in the report.

        Args:
            report: Report data dictionary.
            report_dir: Directory where the report.json is located (used to resolve relative paths).

        Returns:
            Dictionary mapping file paths to their contents.
        """
        source_files = {}
        file_paths = set()

        # 收集所有文件路径（新格式：从 bugs 列表 + callers + inferred_callers）
        for bug in report.get('bugs', []):
            # Bug所在文件
            file_path = bug.get('file_path')
            if file_path:
                file_paths.add(file_path)

            # Callers 的文件
            for caller in bug.get('callers', []):
                caller_file = caller.get('file_path')
                if caller_file:
                    file_paths.add(caller_file)

            # Inferred callers 的文件
            for inferred in bug.get('inferred_callers', []):
                inferred_file = inferred.get('file_path')
                if inferred_file:
                    file_paths.add(inferred_file)

        # 获取扫描目录（如果report中有的话）
        scan_directory = report.get('scan_directory', '')
        if scan_directory:
            # 使用 scan_directory 作为基准目录
            base_dir = Path(scan_directory)
        else:
            # 兼容旧格式：使用 report.json 所在目录
            base_dir = report_dir

        # 读取文件内容
        for file_path in file_paths:
            try:
                # 将相对路径转换为绝对路径（基于 base_dir）
                absolute_path = base_dir / file_path
                with open(absolute_path, 'r', encoding='utf-8') as f:
                    source_files[file_path] = f.read()
            except Exception as e:
                # 如果无法读取文件，存储错误信息
                source_files[file_path] = f"// Error loading file: {e}"

        return source_files

    def _extract_snippet_from_poi(
        self,
        file_content: str,
        start_line: int,
        end_line: int,
        context_lines: int = 5
    ) -> Dict[str, Any]:
        """
        Extract code snippet from POI with context lines.

        Args:
            file_content: Full file content as string.
            start_line: POI start line (1-based, absolute).
            end_line: POI end line (1-based, absolute).
            context_lines: Number of context lines before and after POI (default: 5).

        Returns:
            Dictionary with:
                - snippet: Code snippet as string
                - snippet_start_line: Absolute line number where snippet starts (1-based)
                - poi_start_line: Relative line number of POI start within snippet (1-based)
                - poi_end_line: Relative line number of POI end within snippet (1-based)
        """
        lines = file_content.split('\n')
        total_lines = len(lines)

        # 计算 snippet 的范围 (1-based to 0-based conversion)
        snippet_start = max(1, start_line - context_lines)
        snippet_end = min(total_lines, end_line + context_lines)

        # 提取 snippet (转换为 0-based index)
        snippet_lines = lines[snippet_start - 1:snippet_end]
        snippet = '\n'.join(snippet_lines)

        # 计算 POI 在 snippet 中的相对位置 (1-based)
        poi_start_relative = start_line - snippet_start + 1
        poi_end_relative = end_line - snippet_start + 1

        return {
            'snippet': snippet,
            'snippet_start_line': snippet_start,
            'poi_start_line': poi_start_relative,
            'poi_end_line': poi_end_relative
        }

    def _build_html(self, report: Dict[str, Any], source_files: Dict[str, str], embed_source: bool) -> str:
        """
        Build HTML content from report data.

        Args:
            report: Report data dictionary.
            source_files: Dictionary of source file contents (empty if not embedding).
            embed_source: Whether source code is embedded.

        Returns:
            Complete HTML content.
        """
        # 准备数据
        bugs_list = self._prepare_bugs_list(report, source_files, embed_source)
        bugs_json = json.dumps(bugs_list, ensure_ascii=False)
        source_files_json = json.dumps(source_files, ensure_ascii=False) if embed_source else "{}"

        # 加载 HTML 模板
        template_path = Path(__file__).parent / 'template.html'
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()

        # 替换模板中的变量
        html = template.format(
            timestamp=report.get('timestamp', ''),
            bugs_json=bugs_json,
            source_files_json=source_files_json,
            embed_source=str(embed_source).lower()
        )

        return html

    def _prepare_bugs_list(
        self,
        report: Dict[str, Any],
        source_files: Dict[str, str],
        embed_source: bool
    ) -> List[Dict[str, Any]]:
        """
        Prepare bugs list with POI data and optional code snippets.

        Args:
            report: Report data dictionary (new format).
            source_files: Dictionary of source file contents (for embedMode).
            embed_source: If True, extract and embed code snippets.

        Returns:
            Sorted list of bugs with POI information and optional snippets.
        """
        bugs_list = []

        # 新格式：直接从 bugs 列表获取
        for bug in report.get('bugs', []):
            function_name = bug.get('function_name', 'Unknown')
            file_path = bug.get('file_path', '')
            severity = bug.get('severity', 'low')

            # Function POI (从扁平结构读取)
            function_start_line = bug.get('function_start_line', 0)
            function_end_line = bug.get('function_end_line', function_start_line)
            function_start_col = bug.get('function_start_col', 0)
            function_end_col = bug.get('function_end_col', 0)

            # Bug POI (相对于函数)
            bug_relative_start = bug.get('start_line', 0)
            bug_relative_end = bug.get('end_line', 0)
            bug_start_col = bug.get('start_col', 0)
            bug_end_col = bug.get('end_col', 0)

            # 准备 bug 数据（转换为嵌套 POI 结构供 JS 使用）
            bug_data = {
                'id': bug.get('bug_id', 'BUG-000'),
                'type': bug.get('type', 'Unknown'),
                'description': bug.get('description', ''),
                'location': bug.get('location', ''),
                'suggestion': bug.get('suggestion', ''),
                'severity': severity,
                'function_name': function_name,
                'file_path': file_path,
                # Function POI
                'function_poi': {
                    'start_line': function_start_line,
                    'end_line': function_end_line,
                    'start_col': function_start_col,
                    'end_col': function_end_col
                },
                # Bug POI (relative to function)
                'bug_poi': {
                    'start_line': bug_relative_start,
                    'end_line': bug_relative_end,
                    'start_col': bug_start_col,
                    'end_col': bug_end_col
                },
                # Layer 4 证据链
                'confidence': bug.get('confidence', 1.0),
                'evidence': bug.get('evidence', {}),
                'callers': bug.get('callers', []),
                'callees': bug.get('callees', []),
                'inferred_callers': bug.get('inferred_callers', [])
            }

            # 如果 embedMode，提取 code snippets
            if embed_source and file_path in source_files:
                file_content = source_files[file_path]

                # 提取 function snippet（基于 bug POI 而不是整个 function）
                # 计算 bug 在整个文件中的绝对行号
                if bug_relative_start > 0:
                    bug_absolute_start = function_start_line + bug_relative_start - 1
                    bug_absolute_end = function_start_line + bug_relative_end - 1
                else:
                    # 如果没有 bug POI，使用函数起始行
                    bug_absolute_start = function_start_line
                    bug_absolute_end = function_start_line

                function_snippet_data = self._extract_snippet_from_poi(
                    file_content,
                    bug_absolute_start,
                    bug_absolute_end,
                    context_lines=5
                )
                bug_data['function_snippet'] = function_snippet_data

                # 提取 callers snippets (基于 call_lines 而不是整个函数)
                for caller in bug_data['callers']:
                    caller_file = caller.get('file_path', '')
                    if caller_file in source_files:
                        caller_content = source_files[caller_file]
                        call_lines = caller.get('call_lines', [])

                        # 使用 call_lines 来确定 snippet 范围
                        if call_lines:
                            # 使用第一个和最后一个调用行作为 POI
                            poi_start = min(call_lines)
                            poi_end = max(call_lines)
                        else:
                            # 如果没有 call_lines，使用函数的 start_line
                            poi_start = caller.get('start_line', 1)
                            poi_end = poi_start

                        caller_snippet = self._extract_snippet_from_poi(
                            caller_content,
                            poi_start,
                            poi_end,
                            context_lines=5
                        )
                        caller['snippet'] = caller_snippet

                # 提取 inferred callers snippets (基于 inference_lines 而不是整个函数)
                for inferred in bug_data['inferred_callers']:
                    inferred_file = inferred.get('file_path', '')
                    if inferred_file in source_files:
                        inferred_content = source_files[inferred_file]
                        inference_lines = inferred.get('inference_lines', [])

                        # 使用 inference_lines 来确定 snippet 范围
                        if inference_lines:
                            # 使用第一个和最后一个推断行作为 POI
                            poi_start = min(inference_lines)
                            poi_end = max(inference_lines)
                        else:
                            # 如果没有 inference_lines，使用函数的 start_line
                            poi_start = inferred.get('start_line', 1)
                            poi_end = poi_start

                        inferred_snippet = self._extract_snippet_from_poi(
                            inferred_content,
                            poi_start,
                            poi_end,
                            context_lines=5
                        )
                        inferred['snippet'] = inferred_snippet

            bugs_list.append(bug_data)

        # 排序：按照 severity > file_path > function_start_line
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        bugs_list.sort(key=lambda x: (
            severity_order.get(x['severity'], 3),
            x['file_path'],
            x['function_poi']['start_line']
        ))

        return bugs_list

    def _count_bugs_by_severity(self, report: Dict[str, Any], severity: str) -> int:
        """Count bugs by severity level."""
        return sum(1 for bug in report.get('bugs', []) if bug.get('severity') == severity)
