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

        # 收集所有文件路径（新格式：从 bugs 列表）
        for bug in report.get('bugs', []):
            file_path = bug.get('file_path')
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
        }}

        .filter-section {{
            margin-bottom: 0;
        }}

        .filter-label {{
            font-size: 12px;
            font-weight: 600;
            color: rgba(255,255,255,0.9);
            margin-bottom: 6px;
        }}

        .filter-buttons {{
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
        }}

        .filter-btn {{
            padding: 5px 10px;
            border: 1px solid rgba(255,255,255,0.3);
            background: rgba(255,255,255,0.1);
            color: white;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 4px;
        }}

        .filter-btn:hover {{
            background: rgba(255,255,255,0.2);
        }}

        .filter-btn.active {{
            background: rgba(255,255,255,0.3);
            color: white;
            border-color: rgba(255,255,255,0.5);
        }}

        .filter-count {{
            background: rgba(0,0,0,0.2);
            padding: 2px 6px;
            border-radius: 10px;
            font-size: 11px;
            font-weight: bold;
        }}

        .filter-btn.active .filter-count {{
            background: rgba(0,0,0,0.3);
        }}

        .sort-buttons {{
            display: flex;
            gap: 8px;
        }}

        .sort-btn {{
            padding: 5px 10px;
            border: 1px solid rgba(255,255,255,0.3);
            background: rgba(255,255,255,0.1);
            color: white;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.2s;
        }}

        .sort-btn:hover {{
            background: rgba(255,255,255,0.2);
        }}

        .sort-btn.active {{
            background: rgba(255,255,255,0.3);
            color: white;
            border-color: rgba(255,255,255,0.5);
        }}

        select.filter-select {{
            padding: 5px 10px;
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 4px;
            font-size: 12px;
            background: rgba(255,255,255,0.1);
            color: white;
            cursor: pointer;
            outline: none;
        }}

        select.filter-select option {{
            background: #667eea;
            color: white;
        }}

        select.filter-select:focus {{
            border-color: rgba(255,255,255,0.5);
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

        /* Caller 展示样式 */
        .caller-section {{
            margin-top: 20px;
            border-top: 2px solid #3e3e3e;
            padding-top: 15px;
        }}

        .caller-header {{
            color: #4ec9b0;
            font-size: 14px;
            font-weight: bold;
            margin-bottom: 10px;
            padding: 8px 12px;
            background: #2d2d2d;
            border-left: 4px solid #4ec9b0;
        }}

        .caller-item {{
            margin-bottom: 15px;
            background: #252526;
            border-radius: 4px;
            padding: 12px;
            border-left: 3px solid #569cd6;
        }}

        .caller-label {{
            color: #569cd6;
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 8px;
        }}

        .caller-hint {{
            color: #ce9178;
            font-size: 12px;
            font-style: italic;
            margin-bottom: 8px;
        }}

        .caller-code {{
            font-family: 'Courier New', Consolas, Monaco, monospace;
            font-size: 12px;
            line-height: 1.6;
            color: #d4d4d4;
            background: #1e1e1e;
            padding: 10px;
            border-radius: 3px;
            overflow-x: auto;
            white-space: pre-wrap;
        }}

        .caller-code .call-line {{
            background: rgba(255, 215, 0, 0.15);
            border-left: 3px solid #ffd700;
            padding-left: 8px;
            margin-left: -8px;
            display: block;
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
        <!-- 顶部过滤/排序面板 -->
        <div class="stats-pane">
            <h1>🔍 PyScan Bug Report</h1>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px;">
                <!-- Severity 筛选 -->
                <div class="filter-section">
                    <div class="filter-label">Severity</div>
                    <div class="filter-buttons" id="severityFilters">
                        <!-- 动态生成 -->
                    </div>
                </div>

                <!-- Function 筛选 -->
                <div class="filter-section">
                    <div class="filter-label">Function</div>
                    <select class="filter-select" id="functionFilter">
                        <option value="all">All Functions</option>
                        <!-- 动态生成 -->
                    </select>
                </div>

                <!-- Bug Type 筛选 -->
                <div class="filter-section">
                    <div class="filter-label">Bug Type</div>
                    <select class="filter-select" id="typeFilter">
                        <option value="all">All Types</option>
                        <!-- 动态生成 -->
                    </select>
                </div>

                <!-- 排序 -->
                <div class="filter-section">
                    <div class="filter-label">Sort By</div>
                    <div class="sort-buttons">
                        <button class="sort-btn active" data-sort="severity">Severity</button>
                        <button class="sort-btn" data-sort="function">Function</button>
                        <button class="sort-btn" data-sort="type">Type</button>
                        <button class="sort-btn" data-sort="line">Line</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- 主内容区域 -->
        <div class="main-content">
            <!-- 左侧 Bug 列表 -->
            <div class="bugs-pane">
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

        let currentFilters = {{
            severity: 'all',
            function: 'all',
            type: 'all'
        }};
        let currentSort = 'severity';
        let selectedBugIndex = -1;

        // 初始化
        function init() {{
            generateFilterOptions();
            setupFilterControls();
            renderBugsList();

            // 处理 URL hash，自动定位到相应的 bug
            handleUrlHash();
        }}

        // 生成筛选选项和统计
        function generateFilterOptions() {{
            // 统计每个维度的数量
            const stats = {{
                severity: {{}},
                function: {{}},
                type: {{}}
            }};

            bugsData.forEach(bug => {{
                // Severity
                stats.severity[bug.severity] = (stats.severity[bug.severity] || 0) + 1;

                // Function
                stats.function[bug.function_name] = (stats.function[bug.function_name] || 0) + 1;

                // Type
                stats.type[bug.type] = (stats.type[bug.type] || 0) + 1;
            }});

            // 生成 Severity 按钮
            const severityContainer = document.getElementById('severityFilters');
            const severities = [
                {{ value: 'all', label: 'All', count: bugsData.length }},
                {{ value: 'high', label: 'High', count: stats.severity.high || 0 }},
                {{ value: 'medium', label: 'Medium', count: stats.severity.medium || 0 }},
                {{ value: 'low', label: 'Low', count: stats.severity.low || 0 }}
            ];

            severityContainer.innerHTML = severities.map(s => `
                <button class="filter-btn ${{s.value === 'all' ? 'active' : ''}}" data-filter="${{s.value}}">
                    <span>${{s.label}}</span>
                    <span class="filter-count">${{s.count}}</span>
                </button>
            `).join('');

            // 生成 Function 选项
            const functionSelect = document.getElementById('functionFilter');
            const functions = Object.keys(stats.function).sort();
            functionSelect.innerHTML = `
                <option value="all">All Functions (${{bugsData.length}})</option>
                ${{functions.map(fn => `
                    <option value="${{fn}}">${{fn}} (${{stats.function[fn]}})</option>
                `).join('')}}
            `;

            // 生成 Type 选项
            const typeSelect = document.getElementById('typeFilter');
            const types = Object.keys(stats.type).sort();
            typeSelect.innerHTML = `
                <option value="all">All Types (${{bugsData.length}})</option>
                ${{types.map(t => `
                    <option value="${{t}}">${{t}} (${{stats.type[t]}})</option>
                `).join('')}}
            `;
        }}

        // 设置筛选控件
        function setupFilterControls() {{
            // Severity 按钮
            document.getElementById('severityFilters').addEventListener('click', (e) => {{
                const btn = e.target.closest('.filter-btn');
                if (!btn) return;

                document.querySelectorAll('#severityFilters .filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentFilters.severity = btn.dataset.filter;
                renderBugsList();
            }});

            // Function 下拉框
            document.getElementById('functionFilter').addEventListener('change', (e) => {{
                currentFilters.function = e.target.value;
                renderBugsList();
            }});

            // Type 下拉框
            document.getElementById('typeFilter').addEventListener('change', (e) => {{
                currentFilters.type = e.target.value;
                renderBugsList();
            }});

            // Sort 按钮
            document.querySelectorAll('.sort-btn').forEach(btn => {{
                btn.addEventListener('click', () => {{
                    document.querySelectorAll('.sort-btn').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    currentSort = btn.dataset.sort;
                    renderBugsList();
                }});
            }});
        }}

        // 处理 URL hash
        function handleUrlHash() {{
            const hash = window.location.hash.slice(1); // 移除 # 号
            if (hash) {{
                // 查找匹配的 bug
                const filteredBugs = filterAndSortBugs();
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
            const filteredBugs = filterAndSortBugs();

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

            // 如果有选中的 bug，清除选中状态
            selectedBugIndex = -1;
            document.querySelector('.code-pane').innerHTML = '<div class="empty-state">👈 Select a bug from the list to view details</div>';
        }}

        // 筛选和排序 Bug
        function filterAndSortBugs() {{
            let filtered = bugsData;

            // 应用筛选
            if (currentFilters.severity !== 'all') {{
                filtered = filtered.filter(bug => bug.severity === currentFilters.severity);
            }}

            if (currentFilters.function !== 'all') {{
                filtered = filtered.filter(bug => bug.function_name === currentFilters.function);
            }}

            if (currentFilters.type !== 'all') {{
                filtered = filtered.filter(bug => bug.type === currentFilters.type);
            }}

            // 应用排序
            const sortFunctions = {{
                severity: (a, b) => {{
                    const order = {{ high: 0, medium: 1, low: 2 }};
                    return (order[a.severity] || 3) - (order[b.severity] || 3);
                }},
                function: (a, b) => a.function_name.localeCompare(b.function_name),
                type: (a, b) => a.type.localeCompare(b.type),
                line: (a, b) => {{
                    if (a.file_path !== b.file_path) {{
                        return a.file_path.localeCompare(b.file_path);
                    }}
                    return a.start_line - b.start_line;
                }}
            }};

            if (sortFunctions[currentSort]) {{
                filtered.sort(sortFunctions[currentSort]);
            }}

            return filtered;
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
            const filteredBugs = filterAndSortBugs();
            const bug = filteredBugs[index];

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
                <div class="code-header">📄 Current Function - ${{bug.file_path}}</div>
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

            // 添加 Callers 部分
            if (bug.callers && bug.callers.length > 0) {{
                html += '<div class="caller-section">';
                html += '<div class="caller-header">📞 Callers (Functions that call this function)</div>';

                for (let i = 0; i < bug.callers.length; i++) {{
                    const caller = bug.callers[i];
                    const filePath = caller.file_path || 'Unknown';
                    const functionName = caller.function_name || 'Unknown';
                    const codeSnippet = caller.code_snippet || '';

                    html += `
                        <div class="caller-item">
                            <div class="caller-label">Caller ${{i + 1}}: ${{functionName}} @ ${{filePath}}</div>
                            <div class="caller-code">${{formatCallerCode(codeSnippet)}}</div>
                        </div>
                    `;
                }}

                html += '</div>';
            }}

            // 添加 Inferred Callers 部分
            if (bug.inferred_callers && bug.inferred_callers.length > 0) {{
                html += '<div class="caller-section">';
                html += '<div class="caller-header">🔍 Inferred Callers (Potential callers detected by analysis)</div>';

                for (let i = 0; i < bug.inferred_callers.length; i++) {{
                    const inferredCaller = bug.inferred_callers[i];
                    const hint = inferredCaller.hint || '';
                    const filePath = inferredCaller.file_path || 'Unknown';
                    const functionName = inferredCaller.function_name || 'Unknown';
                    const code = inferredCaller.code || '';

                    html += `
                        <div class="caller-item">
                            <div class="caller-hint">${{escapeHtml(hint)}}</div>
                            <div class="caller-label">${{functionName}} @ ${{filePath}}</div>
                            <div class="caller-code">${{formatCallerCode(code)}}</div>
                        </div>
                    `;
                }}

                html += '</div>';
            }}

            codePane.innerHTML = html;

            // 滚动到顶部
            codePane.scrollTop = 0;
        }}

        // HTML 转义（保留空格和缩进）
        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.textContent = text;
            // 将空格替换为 &nbsp; 以保留缩进
            return div.innerHTML.replace(/ /g, '&nbsp;');
        }}

        // 格式化 caller code，高亮调用行（以 ">>> " 开头）
        function formatCallerCode(code) {{
            const lines = code.split('\\n');
            const formattedLines = lines.map(line => {{
                if (line.startsWith('>>> ')) {{
                    // 移除 ">>> " 标记，并添加高亮类
                    const cleanLine = line.substring(4);
                    return `<span class="call-line">${{escapeHtml(cleanLine)}}</span>`;
                }} else {{
                    return escapeHtml(line);
                }}
            }});
            return formattedLines.join('\\n');
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
            report: Report data dictionary (new format).

        Returns:
            Sorted list of bugs with caller information.
        """
        bugs_list = []

        # 新格式：直接从 bugs 列表获取
        for bug in report.get('bugs', []):
            function_name = bug.get('function_name', 'Unknown')
            file_path = bug.get('file_path', '')
            severity = bug.get('severity', 'low')
            function_start_line = bug.get('function_start_line', 0)

            # 转换相对行号为绝对行号
            relative_start = bug.get('start_line', 0)
            relative_end = bug.get('end_line', 0)
            absolute_start = function_start_line + relative_start - 1 if relative_start > 0 else 0
            absolute_end = function_start_line + relative_end - 1 if relative_end > 0 else 0

            bugs_list.append({
                'id': bug.get('bug_id', 'BUG-000'),
                'type': bug.get('type', 'Unknown'),
                'description': bug.get('description', ''),
                'location': bug.get('location', ''),
                'suggestion': bug.get('suggestion', ''),
                'severity': severity,
                'function_name': function_name,
                'file_path': file_path,
                'function_start_line': function_start_line,
                'start_line': absolute_start,
                'end_line': absolute_end,
                'start_col': bug.get('start_col', 0),
                'end_col': bug.get('end_col', 0),
                'callers': bug.get('callers', []),  # List[Dict] with file_path, function_name, code_snippet
                'callees': bug.get('callees', []),
                'inferred_callers': bug.get('inferred_callers', [])  # List[Dict] with hint, code
            })

        # 排序：按照 severity > file_path > start_line
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        bugs_list.sort(key=lambda x: (
            severity_order.get(x['severity'], 3),
            x['file_path'],
            x['start_line']
        ))

        return bugs_list

    def _count_bugs_by_severity(self, report: Dict[str, Any], severity: str) -> int:
        """Count bugs by severity level."""
        return sum(1 for bug in report.get('bugs', []) if bug.get('severity') == severity)
