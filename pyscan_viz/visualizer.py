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

        select.filter-select {{
            width: 100%;
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
            padding: 10px 12px;
            border-radius: 4px;
            margin-bottom: 10px;
            border-left: 4px solid #ff5733;
        }}

        .bug-details h3 {{
            color: #ff5733;
            font-size: 14px;
            margin: 0 0 8px 0;
        }}

        .bug-details p {{
            margin: 0 0 4px 0;
            line-height: 1.4;
            font-size: 13px;
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

            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top: 15px;">
                <!-- Severity 筛选 -->
                <div class="filter-section">
                    <div class="filter-label">Severity</div>
                    <select class="filter-select" id="severityFilter">
                        <option value="all">All Severities</option>
                        <!-- 动态生成 -->
                    </select>
                </div>

                <!-- File Path 筛选 -->
                <div class="filter-section">
                    <div class="filter-label">File Path</div>
                    <select class="filter-select" id="pathFilter">
                        <option value="all">All Paths</option>
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
            path: 'all',
            type: 'all'
        }};
        let selectedBugIndex = -1;

        // 初始化
        function init() {{
            generateFilterOptions();
            setupFilterControls();
            renderBugsList();

            // 处理 URL hash，自动定位到相应的 bug
            handleUrlHash();
        }}

        // 生成筛选选项和统计（联动：根据当前筛选条件更新可用选项）
        function generateFilterOptions() {{
            // 获取当前筛选后的 bugs（用于计算联动后的统计）
            const currentBugs = getFilteredBugs();

            // 统计每个维度的数量
            const stats = {{
                severity: {{}},
                path: {{}},
                type: {{}}
            }};

            currentBugs.forEach(bug => {{
                stats.severity[bug.severity] = (stats.severity[bug.severity] || 0) + 1;
                stats.path[bug.file_path] = (stats.path[bug.file_path] || 0) + 1;
                stats.type[bug.type] = (stats.type[bug.type] || 0) + 1;
            }});

            // 生成 Severity 下拉选项（按数量从大到小排序）
            const severitySelect = document.getElementById('severityFilter');
            const currentSeverity = currentFilters.severity;
            const severities = [
                {{ value: 'high', label: 'High', count: stats.severity.high || 0 }},
                {{ value: 'medium', label: 'Medium', count: stats.severity.medium || 0 }},
                {{ value: 'low', label: 'Low', count: stats.severity.low || 0 }}
            ].sort((a, b) => b.count - a.count);  // 按数量降序

            severitySelect.innerHTML = `
                <option value="all" ${{currentSeverity === 'all' ? 'selected' : ''}}>All Severities (${{currentBugs.length}})</option>
                ${{severities.map(s => `
                    <option value="${{s.value}}" ${{s.value === currentSeverity ? 'selected' : ''}}>${{s.label}} (${{s.count}})</option>
                `).join('')}}
            `;

            // 生成 Path 选项（按数量从大到小排序）
            const pathSelect = document.getElementById('pathFilter');
            const currentPath = currentFilters.path;
            const paths = Object.entries(stats.path)
                .sort((a, b) => b[1] - a[1])  // 按数量降序
                .map(([path, count]) => ({{ path, count }}));
            pathSelect.innerHTML = `
                <option value="all" ${{currentPath === 'all' ? 'selected' : ''}}>All Paths (${{currentBugs.length}})</option>
                ${{paths.map(p => `
                    <option value="${{p.path}}" ${{p.path === currentPath ? 'selected' : ''}}>${{p.path}} (${{p.count}})</option>
                `).join('')}}
            `;

            // 生成 Type 选项（按数量从大到小排序）
            const typeSelect = document.getElementById('typeFilter');
            const currentType = currentFilters.type;
            const types = Object.entries(stats.type)
                .sort((a, b) => b[1] - a[1])  // 按数量降序
                .map(([type, count]) => ({{ type, count }}));
            typeSelect.innerHTML = `
                <option value="all" ${{currentType === 'all' ? 'selected' : ''}}>All Types (${{currentBugs.length}})</option>
                ${{types.map(t => `
                    <option value="${{t.type}}" ${{t.type === currentType ? 'selected' : ''}}>${{t.type}} (${{t.count}})</option>
                `).join('')}}
            `;
        }}

        // 获取当前筛选条件下的 bugs（用于联动计算，不包括当前正在修改的筛选器）
        function getFilteredBugs() {{
            let filtered = bugsData;

            // 应用筛选
            if (currentFilters.severity !== 'all') {{
                filtered = filtered.filter(bug => bug.severity === currentFilters.severity);
            }}

            if (currentFilters.path !== 'all') {{
                filtered = filtered.filter(bug => bug.file_path === currentFilters.path);
            }}

            if (currentFilters.type !== 'all') {{
                filtered = filtered.filter(bug => bug.type === currentFilters.type);
            }}

            return filtered;
        }}

        // 设置筛选控件
        function setupFilterControls() {{
            // Severity 下拉框
            document.getElementById('severityFilter').addEventListener('change', (e) => {{
                currentFilters.severity = e.target.value;
                updateFiltersAndRender();
            }});

            // Path 下拉框
            document.getElementById('pathFilter').addEventListener('change', (e) => {{
                currentFilters.path = e.target.value;
                updateFiltersAndRender();
            }});

            // Type 下拉框
            document.getElementById('typeFilter').addEventListener('change', (e) => {{
                currentFilters.type = e.target.value;
                updateFiltersAndRender();
            }});
        }}

        // 更新筛选器选项并重新渲染列表（联动）
        function updateFiltersAndRender() {{
            generateFilterOptions();  // 重新生成选项（联动更新）
            renderBugsList();          // 渲染 bug 列表
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

            if (currentFilters.path !== 'all') {{
                filtered = filtered.filter(bug => bug.file_path === currentFilters.path);
            }}

            if (currentFilters.type !== 'all') {{
                filtered = filtered.filter(bug => bug.type === currentFilters.type);
            }}

            // 按 bug id 升序排序
            filtered.sort((a, b) => {{
                // 提取 bug id 中的数字进行比较
                const aNum = parseInt(a.id.replace(/\D/g, '')) || 0;
                const bNum = parseInt(b.id.replace(/\D/g, '')) || 0;
                return aNum - bNum;
            }});

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
                            <h3>${{bug.id}} - ${{bug.type}} [${{bug.severity.toUpperCase()}}]</h3>
                            <p>${{bug.description}}</p>
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

        // 显示带有 Bug 标记的代码（使用 POI）
        function displayCodeWithBug(bug, sourceCode) {{
            const codePane = document.querySelector('.code-pane');

            // 构建 HTML
            let html = `
                <div class="bug-details">
                    <h3>${{bug.id}} - ${{bug.type}} [${{bug.severity.toUpperCase()}}]</h3>
                    <p>${{bug.description}}</p>
                    <p><span class="label">Suggestion:</span> ${{bug.suggestion}}</p>
                </div>
                <div class="code-header">${{bug.function_name}} @ ${{bug.file_path}}</div>
                <div class="code-content">
            `;

            // embedMode: 使用预先提取的 snippet
            if (bug.function_snippet) {{
                const snippet = bug.function_snippet;
                const snippetLines = snippet.snippet.split('\\n');
                const snippetStartLine = snippet.snippet_start_line;
                const bugPoiStart = snippet.poi_start_line;
                const bugPoiEnd = snippet.poi_end_line;

                // 计算 bug 在 snippet 中的绝对位置（用于高亮 bug POI）
                const bugRelativeStart = bug.bug_poi.start_line;
                const bugRelativeEnd = bug.bug_poi.end_line;

                // bug 在整个文件中的绝对行号
                const bugAbsoluteStart = bug.function_poi.start_line + bugRelativeStart - 1;
                const bugAbsoluteEnd = bug.function_poi.start_line + bugRelativeEnd - 1;

                for (let i = 0; i < snippetLines.length; i++) {{
                    const lineNum = snippetStartLine + i;
                    // 高亮 bug POI 行
                    const isBugLine = bugRelativeStart > 0 && lineNum >= bugAbsoluteStart && lineNum <= bugAbsoluteEnd;
                    const lineClass = isBugLine ? 'code-line highlighted' : 'code-line';

                    html += `<div class="${{lineClass}}"><div class="line-number">${{lineNum}}</div><div class="line-content">${{escapeHtml(snippetLines[i])}}</div></div>`;
                }}
            }} else {{
                // 非 embedMode: 从 sourceCode 动态提取 bug POI snippet
                const lines = sourceCode.split('\\n');
                const functionStartLine = bug.function_poi.start_line;

                // 计算 bug 在整个文件中的绝对行号
                const bugRelativeStart = bug.bug_poi.start_line;
                const bugRelativeEnd = bug.bug_poi.end_line;

                let bugAbsoluteStart, bugAbsoluteEnd;
                if (bugRelativeStart > 0) {{
                    bugAbsoluteStart = functionStartLine + bugRelativeStart - 1;
                    bugAbsoluteEnd = functionStartLine + bugRelativeEnd - 1;
                }} else {{
                    // 如果没有 bug POI，使用函数起始行
                    bugAbsoluteStart = functionStartLine;
                    bugAbsoluteEnd = functionStartLine;
                }}

                // 提取 bug POI ± 5 行
                const contextLines = 5;
                const snippetStart = Math.max(1, bugAbsoluteStart - contextLines);
                const snippetEnd = Math.min(lines.length, bugAbsoluteEnd + contextLines);

                for (let i = snippetStart - 1; i < snippetEnd; i++) {{
                    const lineNum = i + 1;
                    const isBugLine = bugRelativeStart > 0 && lineNum >= bugAbsoluteStart && lineNum <= bugAbsoluteEnd;
                    const lineClass = isBugLine ? 'code-line highlighted' : 'code-line';

                    html += `<div class="${{lineClass}}"><div class="line-number">${{lineNum}}</div><div class="line-content">${{escapeHtml(lines[i])}}</div></div>`;
                }}
            }}

            html += '</div>';

            // 添加 Callers 部分（使用 POI）
            if (bug.callers && bug.callers.length > 0) {{
                html += '<div class="caller-section">';
                html += '<div class="caller-header">📞 Callers (Functions that call this function)</div>';

                for (let i = 0; i < bug.callers.length; i++) {{
                    const caller = bug.callers[i];
                    const filePath = caller.file_path || 'Unknown';
                    const functionName = caller.function_name || 'Unknown';
                    const callLines = caller.call_lines || [];

                    html += `
                        <div class="caller-item">
                            <div class="caller-label">[${{i + 1}}/${{bug.callers.length}}] ${{functionName}} @ ${{filePath}}</div>
                            <div class="code-content">
                    `;

                    // embedMode: 使用预先提取的 snippet
                    if (caller.snippet) {{
                        const snippet = caller.snippet;
                        const snippetLines = snippet.snippet.split('\\n');
                        const snippetStartLine = snippet.snippet_start_line;

                        for (let j = 0; j < snippetLines.length; j++) {{
                            const lineNum = snippetStartLine + j;
                            const isHighlighted = callLines.includes(lineNum);
                            const lineClass = isHighlighted ? 'code-line highlighted' : 'code-line';
                            html += `<div class="${{lineClass}}"><div class="line-number">${{lineNum}}</div><div class="line-content">${{escapeHtml(snippetLines[j])}}</div></div>`;
                        }}
                    }} else {{
                        // 非 embedMode: 从 sourceFiles 动态提取 caller POI snippet
                        const callerSourceCode = sourceFiles[filePath];
                        if (callerSourceCode) {{
                            const lines = callerSourceCode.split('\\n');

                            // 使用 callLines 来确定 snippet 范围（而不是整个函数）
                            let poiStart, poiEnd;
                            if (callLines && callLines.length > 0) {{
                                poiStart = Math.min(...callLines);
                                poiEnd = Math.max(...callLines);
                            }} else {{
                                poiStart = caller.start_line || 1;
                                poiEnd = poiStart;
                            }}

                            // 提取 POI ± 5 行
                            const contextLines = 5;
                            const snippetStart = Math.max(1, poiStart - contextLines);
                            const snippetEnd = Math.min(lines.length, poiEnd + contextLines);

                            for (let j = snippetStart - 1; j < snippetEnd; j++) {{
                                const lineNum = j + 1;
                                const isHighlighted = callLines.includes(lineNum);
                                const lineClass = isHighlighted ? 'code-line highlighted' : 'code-line';
                                html += `<div class="${{lineClass}}"><div class="line-number">${{lineNum}}</div><div class="line-content">${{escapeHtml(lines[j])}}</div></div>`;
                            }}
                        }} else {{
                            html += `<div class="code-line"><div class="line-content">Source file not available</div></div>`;
                        }}
                    }}

                    html += `
                            </div>
                        </div>
                    `;
                }}

                html += '</div>';
            }}

            // 添加 Inferred Callers 部分（使用 POI）
            if (bug.inferred_callers && bug.inferred_callers.length > 0) {{
                html += '<div class="caller-section">';
                html += '<div class="caller-header">🔍 Inferred Callers (Potential callers detected by analysis)</div>';

                for (let i = 0; i < bug.inferred_callers.length; i++) {{
                    const inferredCaller = bug.inferred_callers[i];
                    const hint = inferredCaller.hint || '';
                    const filePath = inferredCaller.file_path || 'Unknown';
                    const functionName = inferredCaller.function_name || 'Unknown';
                    const inferenceLines = inferredCaller.inference_lines || [];

                    html += `
                        <div class="caller-item">
                            <div class="caller-hint">${{escapeHtml(hint)}}</div>
                            <div class="caller-label">[${{i + 1}}/${{bug.inferred_callers.length}}] ${{functionName}} @ ${{filePath}}</div>
                            <div class="code-content">
                    `;

                    // embedMode: 使用预先提取的 snippet
                    if (inferredCaller.snippet) {{
                        const snippet = inferredCaller.snippet;
                        const snippetLines = snippet.snippet.split('\\n');
                        const snippetStartLine = snippet.snippet_start_line;

                        for (let j = 0; j < snippetLines.length; j++) {{
                            const lineNum = snippetStartLine + j;
                            const isHighlighted = inferenceLines.includes(lineNum);
                            const lineClass = isHighlighted ? 'code-line highlighted' : 'code-line';
                            html += `<div class="${{lineClass}}"><div class="line-number">${{lineNum}}</div><div class="line-content">${{escapeHtml(snippetLines[j])}}</div></div>`;
                        }}
                    }} else {{
                        // 非 embedMode: 从 sourceFiles 动态提取 inferred caller POI snippet
                        const inferredSourceCode = sourceFiles[filePath];
                        if (inferredSourceCode) {{
                            const lines = inferredSourceCode.split('\\n');

                            // 使用 inferenceLines 来确定 snippet 范围（而不是整个函数）
                            let poiStart, poiEnd;
                            if (inferenceLines && inferenceLines.length > 0) {{
                                poiStart = Math.min(...inferenceLines);
                                poiEnd = Math.max(...inferenceLines);
                            }} else {{
                                poiStart = inferredCaller.start_line || 1;
                                poiEnd = poiStart;
                            }}

                            // 提取 POI ± 5 行
                            const contextLines = 5;
                            const snippetStart = Math.max(1, poiStart - contextLines);
                            const snippetEnd = Math.min(lines.length, poiEnd + contextLines);

                            for (let j = snippetStart - 1; j < snippetEnd; j++) {{
                                const lineNum = j + 1;
                                const isHighlighted = inferenceLines.includes(lineNum);
                                const lineClass = isHighlighted ? 'code-line highlighted' : 'code-line';
                                html += `<div class="${{lineClass}}"><div class="line-number">${{lineNum}}</div><div class="line-content">${{escapeHtml(lines[j])}}</div></div>`;
                            }}
                        }} else {{
                            html += `<div class="code-line"><div class="line-content">Source file not available</div></div>`;
                        }}
                    }}

                    html += `
                            </div>
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
