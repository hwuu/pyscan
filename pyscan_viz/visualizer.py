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

        # 如果需要嵌入源码，读取所有源文件
        source_files = {}
        if embed_source:
            source_files = self._load_source_files(report)

        # 生成 HTML
        html_content = self._build_html(report, source_files, embed_source)

        # 写入文件
        with open(output_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def _load_source_files(self, report: Dict[str, Any]) -> Dict[str, str]:
        """
        Load all source files mentioned in the report.

        Args:
            report: Report data dictionary.

        Returns:
            Dictionary mapping file paths to their contents.
        """
        source_files = {}
        file_paths = set()

        # 收集所有文件路径
        for func_report in report.get('reports', []):
            file_path = func_report.get('file_path')
            if file_path:
                file_paths.add(file_path)

        # 读取文件内容
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    source_files[file_path] = f.read()
            except Exception as e:
                # 如果无法读取文件，存储错误信息
                source_files[file_path] = f"// Error loading file: {e}"

        return source_files

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
        bugs_list = self._prepare_bugs_list(report)
        bugs_json = json.dumps(bugs_list, ensure_ascii=False)
        source_files_json = json.dumps(source_files, ensure_ascii=False) if embed_source else "{}"

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PyScan Bug Report - {report.get('timestamp', '')}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f5f5f5;
            color: #333;
        }}

        .container {{
            display: flex;
            flex-direction: column;
            height: 100vh;
        }}

        /* 顶部统计面板 */
        .stats-pane {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}

        .stats-pane h1 {{
            font-size: 20px;
            margin-bottom: 10px;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
        }}

        .stat-card {{
            background: rgba(255,255,255,0.1);
            padding: 10px 12px;
            border-radius: 6px;
            backdrop-filter: blur(10px);
        }}

        .stat-label {{
            font-size: 11px;
            opacity: 0.9;
            margin-bottom: 3px;
        }}

        .stat-value {{
            font-size: 22px;
            font-weight: bold;
        }}

        /* 主内容区域 */
        .main-content {{
            display: flex;
            flex: 1;
            overflow: hidden;
        }}

        /* 左侧 Bug 列表 */
        .bugs-pane {{
            width: 40%;
            background: white;
            border-right: 1px solid #e0e0e0;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
        }}

        .bugs-header {{
            padding: 15px 20px;
            background: #f9f9f9;
            border-bottom: 1px solid #e0e0e0;
            position: sticky;
            top: 0;
            z-index: 10;
        }}

        .bugs-header h2 {{
            font-size: 18px;
            margin-bottom: 10px;
        }}

        .filter-buttons {{
            display: flex;
            gap: 8px;
        }}

        .filter-btn {{
            padding: 6px 12px;
            border: 1px solid #ddd;
            background: white;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
            transition: all 0.2s;
        }}

        .filter-btn:hover {{
            background: #f5f5f5;
        }}

        .filter-btn.active {{
            background: #667eea;
            color: white;
            border-color: #667eea;
        }}

        .bugs-list {{
            flex: 1;
        }}

        .bug-item {{
            padding: 15px 20px;
            border-bottom: 1px solid #f0f0f0;
            cursor: pointer;
            transition: background 0.2s;
        }}

        .bug-item:hover {{
            background: #f9f9f9;
        }}

        .bug-item.selected {{
            background: #e8eaf6;
            border-left: 4px solid #667eea;
        }}

        .bug-id {{
            display: inline-block;
            font-family: 'Courier New', monospace;
            font-size: 11px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
            margin-right: 8px;
        }}

        .bug-severity {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
            margin-bottom: 5px;
        }}

        .bug-severity.high {{
            background: #ffebee;
            color: #c62828;
        }}

        .bug-severity.medium {{
            background: #fff3e0;
            color: #e65100;
        }}

        .bug-severity.low {{
            background: #e8f5e9;
            color: #2e7d32;
        }}

        .bug-type {{
            font-weight: 600;
            font-size: 14px;
            margin-bottom: 5px;
            color: #333;
        }}

        .bug-location {{
            font-size: 12px;
            color: #666;
            font-family: 'Courier New', monospace;
        }}

        /* 右侧代码面板 */
        .code-pane {{
            flex: 1;
            background: #1e1e1e;
            color: #d4d4d4;
            overflow-y: auto;
            padding: 20px;
        }}

        .code-header {{
            color: #9cdcfe;
            font-size: 14px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #3e3e3e;
        }}

        .code-content {{
            font-family: 'Courier New', Consolas, Monaco, monospace;
            font-size: 13px;
            line-height: 1.4;
        }}

        .code-line {{
            display: flex;
        }}

        .line-number {{
            color: #858585;
            padding-right: 20px;
            user-select: none;
            text-align: right;
            min-width: 50px;
        }}

        .line-content {{
            flex: 1;
        }}

        .code-line.highlighted {{
            background: rgba(255, 87, 51, 0.2);
            border-left: 3px solid #ff5733;
        }}

        .bug-details {{
            background: #252526;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 15px;
            border-left: 4px solid #ff5733;
        }}

        .bug-details h3 {{
            color: #ff5733;
            font-size: 14px;
            margin-bottom: 10px;
        }}

        .bug-details p {{
            margin-bottom: 8px;
            line-height: 1.5;
        }}

        .bug-details .label {{
            color: #9cdcfe;
            font-weight: 600;
        }}

        .empty-state {{
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
            color: #666;
            font-size: 14px;
        }}

        /* 滚动条样式 */
        ::-webkit-scrollbar {{
            width: 10px;
            height: 10px;
        }}

        ::-webkit-scrollbar-track {{
            background: #f1f1f1;
        }}

        ::-webkit-scrollbar-thumb {{
            background: #888;
            border-radius: 5px;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: #555;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- 顶部统计面板 -->
        <div class="stats-pane">
            <h1>🔍 PyScan Bug Report</h1>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Total Functions</div>
                    <div class="stat-value">{report.get('total_functions', 0)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Functions with Bugs</div>
                    <div class="stat-value">{report.get('functions_with_bugs', 0)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">High Severity</div>
                    <div class="stat-value">{self._count_bugs_by_severity(report, 'high')}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Medium Severity</div>
                    <div class="stat-value">{self._count_bugs_by_severity(report, 'medium')}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Low Severity</div>
                    <div class="stat-value">{self._count_bugs_by_severity(report, 'low')}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Scan Time</div>
                    <div class="stat-value" style="font-size: 12px; padding-top: 4px;">{report.get('timestamp', 'N/A')}</div>
                </div>
            </div>
        </div>

        <!-- 主内容区域 -->
        <div class="main-content">
            <!-- 左侧 Bug 列表 -->
            <div class="bugs-pane">
                <div class="bugs-header">
                    <h2>Detected Bugs</h2>
                    <div class="filter-buttons">
                        <button class="filter-btn active" data-filter="all">All</button>
                        <button class="filter-btn" data-filter="high">High</button>
                        <button class="filter-btn" data-filter="medium">Medium</button>
                        <button class="filter-btn" data-filter="low">Low</button>
                    </div>
                </div>
                <div class="bugs-list" id="bugsList">
                    <!-- Bug items will be inserted here by JavaScript -->
                </div>
            </div>

            <!-- 右侧代码面板 -->
            <div class="code-pane">
                <div class="empty-state">
                    👈 Select a bug from the list to view details
                </div>
            </div>
        </div>
    </div>

    <script>
        // Bug 数据
        const bugsData = {bugs_json};

        // 源码文件数据（如果嵌入模式）
        const sourceFiles = {source_files_json};
        const embedMode = {str(embed_source).lower()};

        let currentFilter = 'all';
        let selectedBugIndex = -1;

        // 初始化
        function init() {{
            renderBugsList();
            setupFilterButtons();

            // 处理 URL hash，自动定位到相应的 bug
            handleUrlHash();
        }}

        // 处理 URL hash
        function handleUrlHash() {{
            const hash = window.location.hash.slice(1); // 移除 # 号
            if (hash) {{
                // 查找匹配的 bug
                const filteredBugs = filterBugs(bugsData, currentFilter);
                const bugIndex = filteredBugs.findIndex(bug => bug.id === hash);

                if (bugIndex !== -1) {{
                    // 找到了，选择这个 bug
                    selectBug(bugIndex);
                }}
            }}
        }}

        // 监听 hash 变化
        window.addEventListener('hashchange', () => {{
            handleUrlHash();
        }});

        // 渲染 Bug 列表
        function renderBugsList() {{
            const bugsList = document.getElementById('bugsList');
            const filteredBugs = filterBugs(bugsData, currentFilter);

            if (filteredBugs.length === 0) {{
                bugsList.innerHTML = '<div class="empty-state">No bugs found</div>';
                return;
            }}

            bugsList.innerHTML = filteredBugs.map((bug, index) => `
                <div class="bug-item" onclick="selectBug(${{index}})" data-index="${{index}}" data-bug-id="${{bug.id}}" data-severity="${{bug.severity}}">
                    <div class="bug-id">${{bug.id}}</div>
                    <div class="bug-severity ${{bug.severity}}">${{bug.severity}}</div>
                    <div class="bug-type">${{bug.type}}</div>
                    <div class="bug-location">${{bug.file_path}}:${{bug.function_name}}</div>
                </div>
            `).join('');
        }}

        // 过滤 Bug
        function filterBugs(bugs, filter) {{
            if (filter === 'all') return bugs;
            return bugs.filter(bug => bug.severity === filter);
        }}

        // 设置过滤按钮
        function setupFilterButtons() {{
            document.querySelectorAll('.filter-btn').forEach(btn => {{
                btn.addEventListener('click', () => {{
                    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    currentFilter = btn.dataset.filter;
                    renderBugsList();

                    // 如果有选中的 bug，清除选中状态
                    selectedBugIndex = -1;
                    document.querySelector('.code-pane').innerHTML = '<div class="empty-state">👈 Select a bug from the list to view details</div>';
                }});
            }});
        }}

        // 选择 Bug
        function selectBug(index) {{
            selectedBugIndex = index;

            // 更新选中状态
            document.querySelectorAll('.bug-item').forEach(item => {{
                item.classList.remove('selected');
            }});

            const selectedItem = document.querySelector(`.bug-item[data-index="${{index}}"]`);
            if (selectedItem) {{
                selectedItem.classList.add('selected');
            }}

            // 显示 Bug 详情和代码
            const bug = filterBugs(bugsData, currentFilter)[index];

            // 更新 URL hash
            window.location.hash = bug.id;

            displayBugDetails(bug);
        }}

        // 显示 Bug 详情
        async function displayBugDetails(bug) {{
            const codePane = document.querySelector('.code-pane');

            codePane.innerHTML = '<div class="empty-state">Loading...</div>';

            let sourceCode;

            if (embedMode) {{
                // 嵌入模式：从 sourceFiles 对象获取源码
                sourceCode = sourceFiles[bug.file_path];
                if (!sourceCode) {{
                    sourceCode = `// Source file not found in embedded data: ${{bug.file_path}}`;
                }}
                displayCodeWithBug(bug, sourceCode);
            }} else {{
                // 动态加载模式：从文件系统读取
                try {{
                    const response = await fetch(`file:///${{bug.file_path}}`);

                    if (response.ok) {{
                        sourceCode = await response.text();
                    }} else {{
                        sourceCode = `// Unable to load source file: ${{bug.file_path}}\\n// Please ensure the file exists and is accessible.`;
                    }}

                    displayCodeWithBug(bug, sourceCode);

                }} catch (error) {{
                    // 文件加载失败，显示错误信息
                    codePane.innerHTML = `
                        <div class="bug-details">
                            <h3>${{bug.type}}</h3>
                            <p><span class="label">Severity:</span> ${{bug.severity}}</p>
                            <p><span class="label">Function:</span> ${{bug.function_name}}</p>
                            <p><span class="label">File:</span> ${{bug.file_path}}</p>
                            <p><span class="label">Location:</span> ${{bug.location}}</p>
                            <p><span class="label">Description:</span> ${{bug.description}}</p>
                            <p><span class="label">Suggestion:</span> ${{bug.suggestion}}</p>
                        </div>
                        <div class="code-header">⚠️ Unable to load source file</div>
                        <div style="color: #858585; padding: 20px;">
                            Source code cannot be displayed because the file could not be loaded.<br>
                            File path: ${{bug.file_path}}<br><br>
                            Please ensure:<br>
                            1. The file exists at the specified location<br>
                            2. You have permission to read the file<br>
                            3. The HTML file is opened from a local file system (file:// protocol)
                        </div>
                    `;
                }}
            }}
        }}

        // 显示带有 Bug 标记的代码
        function displayCodeWithBug(bug, sourceCode) {{
            const codePane = document.querySelector('.code-pane');
            const lines = sourceCode.split('\\n');

            // 构建 HTML
            let html = `
                <div class="bug-details">
                    <h3>${{bug.id}} - ${{bug.type}}</h3>
                    <p><span class="label">Severity:</span> ${{bug.severity}}</p>
                    <p><span class="label">Function:</span> ${{bug.function_name}}</p>
                    <p><span class="label">Location:</span> ${{bug.location}}</p>
                    <p><span class="label">Description:</span> ${{bug.description}}</p>
                    <p><span class="label">Suggestion:</span> ${{bug.suggestion}}</p>
                </div>
                <div class="code-header">${{bug.file_path}}</div>
                <div class="code-content">
            `;

            // 计算要高亮的行范围（考虑上下文）
            const contextLines = 5;
            const startLine = Math.max(0, bug.start_line - contextLines);
            const endLine = Math.min(lines.length, bug.end_line + contextLines);

            for (let i = startLine; i < endLine; i++) {{
                const lineNum = i + 1;
                const isHighlighted = lineNum >= bug.start_line && lineNum <= bug.end_line;
                const lineClass = isHighlighted ? 'code-line highlighted' : 'code-line';

                html += `<div class="${{lineClass}}"><div class="line-number">${{lineNum}}</div><div class="line-content">${{escapeHtml(lines[i])}}</div></div>`;
            }}

            html += '</div>';
            codePane.innerHTML = html;

            // 滚动到高亮行
            setTimeout(() => {{
                const highlightedLine = codePane.querySelector('.code-line.highlighted');
                if (highlightedLine) {{
                    highlightedLine.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                }}
            }}, 100);
        }}

        // HTML 转义（保留空格和缩进）
        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.textContent = text;
            // 将空格替换为 &nbsp; 以保留缩进
            return div.innerHTML.replace(/ /g, '&nbsp;');
        }}

        // 启动应用
        init();
    </script>
</body>
</html>
"""
        return html

    def _prepare_bugs_list(self, report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Prepare bugs list with sorting and absolute line numbers.

        Args:
            report: Report data dictionary.

        Returns:
            Sorted list of bugs.
        """
        bugs_list = []

        for func_report in report.get('reports', []):
            if not func_report.get('has_bug'):
                continue

            function_name = func_report['function_name']
            file_path = func_report['file_path']
            severity = func_report['severity']

            # 从 file_path 中提取文件相关信息
            # 注意：这里需要获取函数的绝对行号，但 JSON 中没有，所以我们用相对行号
            # 实际使用时，JavaScript 会动态加载文件

            # 获取函数起始行号，用于转换相对行号为绝对行号
            function_start_line = func_report.get('function_start_line', 0)

            for bug in func_report.get('bugs', []):
                # 转换相对行号为绝对行号
                # bug 的 start_line 是相对于函数定义行（函数定义行算作第1行）
                # 所以绝对行号 = function_start_line + relative_line - 1
                relative_start = bug.get('start_line', 0)
                relative_end = bug.get('end_line', 0)
                absolute_start = function_start_line + relative_start - 1 if relative_start > 0 else 0
                absolute_end = function_start_line + relative_end - 1 if relative_end > 0 else 0

                bugs_list.append({
                    'type': bug.get('type', 'Unknown'),
                    'description': bug.get('description', ''),
                    'location': bug.get('location', ''),
                    'suggestion': bug.get('suggestion', ''),
                    'severity': severity,
                    'function_name': function_name,
                    'file_path': file_path,
                    'start_line': absolute_start,
                    'end_line': absolute_end,
                    'start_col': bug.get('start_col', 0),
                    'end_col': bug.get('end_col', 0),
                })

        # 排序：按照 severity > file_path > start_line
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        bugs_list.sort(key=lambda x: (
            severity_order.get(x['severity'], 3),
            x['file_path'],
            x['start_line']
        ))

        # 添加 bug ID
        for i, bug in enumerate(bugs_list, 1):
            bug['id'] = f"BUG-{i:03d}"

        return bugs_list

    def _count_bugs_by_severity(self, report: Dict[str, Any], severity: str) -> int:
        """Count bugs by severity level."""
        count = 0
        for func_report in report.get('reports', []):
            if func_report.get('severity') == severity and func_report.get('has_bug'):
                count += len(func_report.get('bugs', []))
        return count
