# PyScan v2 Git Visualization 功能设计

**版本**: v1.2
**日期**: 2025-10-27
**状态**: 实现完成（v1.2）

---

## 1. 功能概述

### 目标
在 pyscan_viz 生成的 HTML 报告中，为每个 bug 添加 Git commit 信息，显示该 bug 所在代码最后一次修改的 commit 详情。

### 核心价值
- **快速定位责任人**：直接查看是谁最后修改了这段有问题的代码
- **时间追溯**：了解代码最后修改时间，判断是新引入的问题还是历史遗留
- **便捷跳转**：一键跳转到 GitHub/GitLab/Gitee 查看完整 commit 详情
- **辅助调试**：通过 commit message 了解代码修改意图
- **智能过滤**：按 commit 或时间范围过滤 bug，聚焦特定变更

### 核心功能
1. **Git Commit 信息展示**：在 Bug Details Pane 显示代码最后修改的 commit
2. **按 Commit 过滤**：在 Stats Pane 选择特定 commit，只显示该 commit 相关的 bug
3. **按时间范围过滤**：选择时间范围（1/7/15/30/90天），只显示最近修改的 bug
4. **按作者过滤**：选择特定作者，只显示该作者最后修改的代码相关的 bug

### 非目标
- ❌ 不显示 commit 完整历史（只显示最新一次修改）
- ❌ 不进行深度 commit 统计分析（如贡献者排名）
- ❌ 不支持多 commit 同时选择（单选即可）

---

## 2. 技术方案

### 2.1 核心技术选型

**使用 `git blame`** 精确定位每行代码的最后修改 commit。

**为什么选择 git blame？**
- ✅ 精确到行：能准确知道 bug 所在代码行的最后修改
- ✅ 信息丰富：提供 commit hash、作者、时间、message
- ✅ 性能可控：通过缓存优化，可接受的性能开销
- ✅ Git 原生：无需额外依赖

### 2.2 工作流程

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 用户运行 pyscan_viz report.json --git-enrich            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. 检测是否为 Git 仓库                                      │
│    - git rev-parse --is-inside-work-tree                    │
│    - 获取 remote URL                                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. 遍历所有 bugs                                            │
│    - 按文件分组（优化：同一文件只 blame 一次）             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. 对每个文件执行 git blame --line-porcelain               │
│    - 获取所有行的 commit 信息                               │
│    - 缓存到内存（避免重复 blame）                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. 为每个 bug 查找对应代码行的 blame 信息                  │
│    - Bug 涉及 start_line 到 end_line                        │
│    - 如果多行涉及不同 commit，选择最新的 commit            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. 生成 commit URL                                          │
│    - 解析 remote URL（GitHub/GitLab/Gitee/Bitbucket）      │
│    - 构建 commit 链接                                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. 将 git_info 添加到 bug 数据                             │
│    - hash, author, date, subject, url                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. 生成 HTML，在 Bug Details Pane 显示 commit 信息         │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 数据结构设计

### 3.1 BlameInfo 数据类

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class BlameInfo:
    """单行代码的 git blame 信息"""
    commit_hash: str        # 完整 commit hash
    author: str             # 作者名
    author_email: str       # 作者邮箱
    commit_date: datetime   # commit 时间
    subject: str            # commit message 第一行

    def is_newer_than(self, other: 'BlameInfo') -> bool:
        """比较两个 commit 的时间"""
        return self.commit_date > other.commit_date
```

### 3.2 Bug 数据结构扩展

**原始 Bug 数据**（来自 report.json）：
```json
{
  "bug_id": "BUG_0001",
  "file_path": "src/utils.py",
  "start_line": 42,
  "end_line": 45,
  "severity": "high",
  "description": "...",
  ...
}
```

**添加 git_info 后**：
```json
{
  "bug_id": "BUG_0001",
  "file_path": "src/utils.py",
  "start_line": 42,
  "end_line": 45,
  "severity": "high",
  "description": "...",
  "git_info": {
    "hash": "a1b2c3d4",           // 短 hash（8位）
    "hash_full": "a1b2c3d4...",  // 完整 hash
    "author": "John Doe",
    "email": "john@example.com",
    "date": "2025-10-20T14:30:00",
    "date_relative": "7 days ago",
    "subject": "Fix null pointer bug in utils",
    "url": "https://github.com/user/repo/commit/a1b2c3d4..."
  }
}
```

**如果无法获取 git 信息**：
```json
{
  "bug_id": "BUG_0001",
  ...,
  "git_info": null
}
```

### 3.3 Commit 列表数据结构

**用途**：用于 Stats Pane 的 commit 下拉列表和时间过滤。

在 HTML 生成时，需要从所有 bugs 中提取唯一的 commits，并按时间排序。

**数据结构**：
```javascript
// 在 template.html 的 Vue data 中
data: {
  // ... 现有数据

  // 所有唯一的 commits（从 bugs 中提取）
  allCommits: [
    {
      hash: "a1b2c3d4",
      hash_full: "a1b2c3d4e5f6...",
      subject: "Fix null pointer bug",
      author: "John Doe",
      date: "2025-10-20T14:30:00",
      date_relative: "7 days ago",
      bug_count: 5,  // 多少个 bug 关联到这个 commit
      url: "https://github.com/..."
    },
    {
      hash: "b2c3d4e5",
      subject: "Add validation",
      author: "Jane Smith",
      date: "2025-10-15T10:00:00",
      date_relative: "12 days ago",
      bug_count: 3,
      url: "https://github.com/..."
    },
    // ... 按时间从新到旧排序
  ],

  // 所有唯一的作者（从 bugs 中提取）
  allOwners: [
    {
      name: "John Doe",
      email: "john@example.com",
      bug_count: 25,  // 该作者修改的代码涉及多少个 bug
    },
    {
      name: "Jane Smith",
      email: "jane@example.com",
      bug_count: 18,
    },
    // ... 按 bug_count 从高到低排序
  ],

  // 过滤器状态
  filters: {
    selectedCommit: null,  // null 表示"全部"，否则是 commit hash
    timeRange: null,       // null 或 1/7/15/30/90（天数）
    selectedOwner: null,   // null 表示"全部"，否则是作者 email
    // ... 现有的过滤器（severity, function, type）
  }
}
```

**从 bugs 提取 commits 的逻辑**：
```python
# 在 pyscan_viz/visualizer.py 中
def extract_commits(bugs: List[Dict]) -> List[Dict]:
    """
    从 bugs 中提取唯一的 commits，并按时间排序。

    Returns:
        按时间从新到旧排序的 commit 列表
    """
    commit_map = {}  # {hash_full: commit_info}

    for bug in bugs:
        git_info = bug.get('git_info')
        if not git_info:
            continue

        hash_full = git_info['hash_full']

        if hash_full not in commit_map:
            commit_map[hash_full] = {
                'hash': git_info['hash'],
                'hash_full': hash_full,
                'subject': git_info['subject'],
                'author': git_info['author'],
                'date': git_info['date'],
                'date_relative': git_info['date_relative'],
                'url': git_info.get('url'),
                'bug_count': 0
            }

        commit_map[hash_full]['bug_count'] += 1

    # 按时间排序（从新到旧）
    commits = list(commit_map.values())
    commits.sort(key=lambda c: c['date'], reverse=True)

    return commits
```

**从 bugs 提取 owners 的逻辑**：
```python
# 在 pyscan_viz/visualizer.py 中
def extract_owners(bugs: List[Dict]) -> List[Dict]:
    """
    从 bugs 中提取唯一的作者，并按 bug 数量排序。

    Returns:
        按 bug_count 从高到低排序的作者列表
    """
    owner_map = {}  # {email: owner_info}

    for bug in bugs:
        git_info = bug.get('git_info')
        if not git_info:
            continue

        email = git_info['email']
        name = git_info['author']

        if email not in owner_map:
            owner_map[email] = {
                'name': name,
                'email': email,
                'bug_count': 0
            }

        owner_map[email]['bug_count'] += 1

    # 按 bug_count 排序（从高到低）
    owners = list(owner_map.values())
    owners.sort(key=lambda o: o['bug_count'], reverse=True)

    return owners
```

---

## 3.4 自定义 Git 平台配置

### 3.4.1 功能概述

从 v1.2 开始，pyscan_viz 支持自定义 Git 平台配置，允许用户为企业内部 Git 服务器（如 GitLab 企业版、自托管 GitHub Enterprise、Azure DevOps 等）配置自定义的检测和 URL 生成规则。

**核心能力**：
- ✅ 在 `config.yaml` 中定义自定义平台规则
- ✅ 使用正则表达式匹配仓库路径
- ✅ 使用字符串模板生成 commit URL
- ✅ 自定义平台覆盖内置平台（支持覆盖 GitHub/GitLab 等默认配置）
- ✅ 严格配置验证，提供清晰的错误提示

### 3.4.2 配置格式

在 `config.yaml` 中添加 `git` 配置段：

```yaml
# ... 现有的 llm、scan、detector 配置

git:
  platforms:
    # 企业 GitLab 实例
    - name: company-gitlab
      detect_pattern: gitlab.company.com
      repo_path_regex: '[:/]([^/:]+/[^/]+?)(?:\.git)?$'
      commit_url_template: 'https://gitlab.company.com/{repo_path}/-/commit/{hash}'

    # Azure DevOps
    - name: azure-devops
      detect_pattern: dev.azure.com
      repo_path_regex: 'dev\.azure\.com/([^/]+/[^/]+/_git/[^/]+)'
      commit_url_template: 'https://dev.azure.com/{repo_path}/commit/{hash}'

    # 覆盖内置 GitHub 配置（使用自定义 commit viewer）
    - name: github
      detect_pattern: github.com
      repo_path_regex: '[:/]([^/:]+/[^/]+?)(?:\.git)?$'
      commit_url_template: 'https://custom-github-viewer.com/{repo_path}/commits/{hash}'
```

### 3.4.3 配置字段说明

| 字段 | 必填 | 说明 | 示例 |
|-----|------|------|------|
| `name` | ✅ | 平台名称（唯一标识） | `company-gitlab` |
| `detect_pattern` | ✅ | 用于检测 remote URL 的字符串模式 | `gitlab.company.com` |
| `repo_path_regex` | ✅ | 从 remote URL 提取仓库路径的正则表达式，**必须包含至少一个捕获组 `(...)`** | `[:/]([^/:]+/[^/]+?)(?:\.git)?$` |
| `commit_url_template` | ✅ | Commit URL 模板，**必须包含 `{repo_path}` 和 `{hash}` 占位符** | `https://gitlab.company.com/{repo_path}/-/commit/{hash}` |

### 3.4.4 配置验证规则

GitAnalyzer 会在加载配置时进行严格验证：

**1. 字段完整性检查**：
- 所有必填字段不能为空

**2. 正则表达式验证**：
- `repo_path_regex` 必须是有效的正则表达式
- 必须包含**至少一个捕获组 `(...)`** 用于提取 `repo_path`

**3. URL 模板验证**：
- `commit_url_template` 必须同时包含 `{repo_path}` 和 `{hash}` 占位符

**4. 验证失败示例**：

```python
# ❌ 错误：缺少捕获组
repo_path_regex: '[:/][^/:]+/[^/]+?(?:\.git)?$'
# 错误信息: 'repo_path_regex' must contain at least one capture group (...) to extract repo_path

# ❌ 错误：缺少 {repo_path} 占位符
commit_url_template: 'https://gitlab.company.com/commit/{hash}'
# 错误信息: 'commit_url_template' must contain {repo_path} placeholder

# ❌ 错误：无效的正则表达式
repo_path_regex: '[:/]([^/:]+/[^/]+?(?:\.git)?$'  # 缺少右括号
# 错误信息: Invalid regex pattern in 'repo_path_regex': ...
```

### 3.4.5 平台检测优先级

为了确保更具体的模式优先匹配，GitAnalyzer 使用以下策略：

1. **按 `detect_pattern` 长度排序**（降序）
   - 更长的模式优先匹配
   - 例如：`gitlab.company.com` 优先于 `gitlab.com`

2. **自定义平台覆盖内置平台**
   - 如果自定义平台的 `name` 与内置平台相同（如 `github`、`gitlab`），则使用自定义配置

**示例**：

```python
# 配置
git:
  platforms:
    - name: company-gitlab
      detect_pattern: gitlab.company.com  # 长度: 19
      ...
    # 内置 gitlab 配置
    # detect_pattern: gitlab.com  # 长度: 10

# Remote URL: git@gitlab.company.com:team/project.git
# 匹配结果: company-gitlab (因为 'gitlab.company.com' 长度更长，优先匹配)
```

### 3.4.6 使用示例

**场景 1：企业 GitLab 实例**

```yaml
git:
  platforms:
    - name: company-gitlab
      detect_pattern: gitlab.company.com
      repo_path_regex: '[:/]([^/:]+/[^/]+?)(?:\.git)?$'
      commit_url_template: 'https://gitlab.company.com/{repo_path}/-/commit/{hash}'
```

测试：
```bash
# Remote URL: git@gitlab.company.com:backend/api-server.git
# 检测平台: company-gitlab
# 提取 repo_path: backend/api-server
# 生成 URL: https://gitlab.company.com/backend/api-server/-/commit/abc123def456
```

**场景 2：Azure DevOps**

```yaml
git:
  platforms:
    - name: azure-devops
      detect_pattern: dev.azure.com
      repo_path_regex: 'dev\.azure\.com/([^/]+/[^/]+/_git/[^/]+)'
      commit_url_template: 'https://dev.azure.com/{repo_path}/commit/{hash}'
```

测试：
```bash
# Remote URL: https://dev.azure.com/myorg/myproject/_git/myrepo
# 检测平台: azure-devops
# 提取 repo_path: myorg/myproject/_git/myrepo
# 生成 URL: https://dev.azure.com/myorg/myproject/_git/myrepo/commit/abc123def456
```

**场景 3：覆盖内置 GitHub 配置**

```yaml
git:
  platforms:
    # 使用自定义 GitHub commit viewer
    - name: github
      detect_pattern: github.com
      repo_path_regex: '[:/]([^/:]+/[^/]+?)(?:\.git)?$'
      commit_url_template: 'https://custom-github-viewer.com/{repo_path}/commits/{hash}'
```

测试：
```bash
# Remote URL: git@github.com:user/repo.git
# 检测平台: github
# 提取 repo_path: user/repo
# 生成 URL: https://custom-github-viewer.com/user/repo/commits/abc123def456
# (注意: 使用了自定义 URL 模板，而不是默认的 github.com/user/repo/commit/...)
```

### 3.4.7 配置加载流程

```
┌─────────────────────────────────────────────────────────┐
│ 1. pyscan_viz CLI 启动 (--git-enrich)                  │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 2. 检查 config.yaml 是否存在                            │
│    - 存在：尝试加载                                     │
│    - 不存在：跳过，使用内置平台                         │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 3. 解析 config.yaml                                     │
│    - 提取 git.platforms 配置                            │
│    - 对每个平台进行严格验证                             │
└────────────────┬────────────────────────────────────────┘
                 │
                 ├─ 验证失败 ──────────────────────┐
                 │                                  ▼
                 │                     ┌────────────────────┐
                 │                     │ 打印详细错误信息   │
                 │                     │ 退出程序 (exit 1)  │
                 │                     └────────────────────┘
                 │
                 ├─ 验证成功
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 4. 创建 GitAnalyzer(custom_platforms=...)              │
│    - 合并自定义平台和内置平台                           │
│    - 自定义平台覆盖同名内置平台                         │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 5. 检测 Git 平台                                        │
│    - 获取 remote URL                                    │
│    - 按 detect_pattern 长度排序（降序）                │
│    - 遍历匹配，返回第一个匹配的平台                     │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 6. 为每个 bug 生成 git_info                            │
│    - 使用平台的 repo_path_regex 解析 repo_path         │
│    - 使用平台的 commit_url_template 生成 URL           │
└─────────────────────────────────────────────────────────┘
```

### 3.4.8 错误处理

pyscan_viz 在遇到 Git 配置错误时采用**快速失败 (fail-fast)** 策略：

1. **配置验证失败 → 立即退出**
   ```bash
   $ python -m pyscan_viz report.json --git-enrich

   Error: Failed to load git config from config.yaml
          Git platform 'company-gitlab': 'repo_path_regex' must contain at least one capture group (...) to extract repo_path

   # Exit code: 1
   ```

2. **配置文件不存在 → 使用内置平台**
   ```bash
   $ python -m pyscan_viz report.json --git-enrich

   # 没有 config.yaml，使用内置 GitHub/GitLab/Gitee/Bitbucket 平台
   Enriching 10 bugs with git information...
   Git information added successfully
   ```

3. **不是 Git 仓库 → 跳过 Git 集成**
   ```bash
   $ python -m pyscan_viz report.json --git-enrich

   Warning: Not a git repository, skipping git integration
   [OK] Visualization generated: report.html
   ```

### 3.4.9 技术实现

**核心类**：
- `pyscan.config.GitPlatformConfig`：Git 平台配置的数据类，包含验证逻辑
- `pyscan_viz.git_analyzer.GitAnalyzer`：Git 分析器，支持动态平台配置

**关键方法**：
- `GitAnalyzer._merge_platforms()`：合并自定义和内置平台配置
- `GitAnalyzer._detect_platform()`：按长度排序后检测平台
- `GitPlatformConfig.__post_init__()`：配置验证逻辑

**测试覆盖**：
- ✅ 自定义平台检测（`tests/test_git_analyzer.py::test_custom_platform_detection`）
- ✅ 自定义平台覆盖内置平台（`tests/test_git_analyzer.py::test_custom_platform_override_builtin`）
- ✅ 自定义平台 URL 生成（`tests/test_git_analyzer.py::test_custom_platform_parse_repo_path`）
- ✅ 内置平台仍然工作（`tests/test_git_analyzer.py::test_builtin_platforms_still_work`）
- ✅ 配置验证（`tests/test_config.py`，包含 7 个 git 配置测试）

---

## 4. 核心实现

### 4.1 GitAnalyzer 类

**文件**: `pyscan_viz/git_analyzer.py`

```python
class GitAnalyzer:
    """Git 仓库分析器，用于获取代码的 git blame 信息"""

    def __init__(self, repo_path: str):
        """
        初始化 Git 分析器。

        Args:
            repo_path: 仓库根目录路径
        """
        self.repo_path = Path(repo_path).resolve()
        self.is_git_repo = self._check_git_repo()
        self.remote_url = self._get_remote_url() if self.is_git_repo else None
        self.platform = self._detect_platform()
        self.blame_cache: Dict[str, Dict[int, BlameInfo]] = {}

    def _check_git_repo(self) -> bool:
        """检查是否是 git 仓库"""
        # git rev-parse --is-inside-work-tree

    def _get_remote_url(self) -> Optional[str]:
        """获取 origin 的 remote URL"""
        # git remote get-url origin

    def _detect_platform(self) -> Optional[str]:
        """
        检测 Git 平台。

        Returns:
            'github' | 'gitlab' | 'gitee' | 'bitbucket' | None
        """
        # 根据 remote_url 判断

    def _parse_repo_path(self) -> Optional[str]:
        """
        从 remote URL 解析仓库路径。

        Examples:
            git@github.com:user/repo.git -> user/repo
            https://github.com/user/repo.git -> user/repo
        """
        # 正则表达式解析

    def _generate_commit_url(self, commit_hash: str) -> Optional[str]:
        """
        生成 commit URL。

        Supported platforms:
            - GitHub: https://github.com/{repo}/commit/{hash}
            - GitLab: https://gitlab.com/{repo}/-/commit/{hash}
            - Gitee:  https://gitee.com/{repo}/commit/{hash}
            - Bitbucket: https://bitbucket.org/{repo}/commits/{hash}
        """

    def blame_file(self, file_path: str) -> Dict[int, BlameInfo]:
        """
        获取文件所有行的 blame 信息（带缓存）。

        Args:
            file_path: 相对于仓库根目录的文件路径

        Returns:
            {line_num: BlameInfo} 字典，line_num 从 1 开始
        """
        # 1. 检查缓存
        # 2. 执行 git blame --line-porcelain <file>
        # 3. 解析输出
        # 4. 缓存并返回

    def _parse_blame_output(self, output: str) -> Dict[int, BlameInfo]:
        """
        解析 git blame --line-porcelain 的输出。

        Format:
            <commit_hash> <original_line> <final_line> <num_lines>
            author <author_name>
            author-mail <email>
            author-time <unix_timestamp>
            summary <commit_subject>
            ...
            \t<code_line>
        """

    def get_bug_blame_info(self, bug: Dict) -> Optional[BlameInfo]:
        """
        获取 bug 所在代码的 blame 信息。

        如果 bug 涉及多行（start_line != end_line），且这些行来自不同的 commit，
        则返回最新的那个 commit。

        Args:
            bug: Bug 字典，必须包含 file_path, start_line, end_line

        Returns:
            BlameInfo 或 None（如果无法获取）
        """
        # 1. 获取文件的 blame 信息
        # 2. 提取 bug 范围内所有行的 blame
        # 3. 选择最新的 commit（按 commit_date 排序）

    def enrich_bugs_with_git_info(self, bugs: List[Dict]) -> List[Dict]:
        """
        为所有 bug 添加 git_info 字段。

        Args:
            bugs: Bug 列表

        Returns:
            添加了 git_info 字段的 bug 列表
        """
        # 遍历 bugs，为每个添加 git_info

    def _format_relative_date(self, commit_date: datetime) -> str:
        """
        格式化为相对时间。

        Examples:
            - "5 minutes ago"
            - "2 hours ago"
            - "yesterday"
            - "3 days ago"
            - "2 weeks ago"
            - "1 month ago"
        """
```

### 4.2 Git Blame 输出解析

**命令**：
```bash
git blame --line-porcelain src/utils.py
```

**输出示例**：
```
a1b2c3d4e5f6... 1 1 1
author John Doe
author-mail <john@example.com>
author-time 1698000000
author-tz +0800
committer John Doe
committer-mail <john@example.com>
committer-time 1698000000
committer-tz +0800
summary Fix null pointer bug
previous b2c3d4e5f6a7... src/utils.py
filename src/utils.py
        def process_data(data):
b2c3d4e5f6a7... 2 2 1
author Jane Smith
author-mail <jane@example.com>
author-time 1697000000
...
```

**解析逻辑**：
1. 第一行：`<hash> <original_line> <final_line> <num_lines>`
   - `final_line` 是当前文件中的行号（1-based）
2. 后续行是 key-value 元数据
3. 以 `\t` 开头的是代码行（标志着当前 commit 信息结束）

### 4.3 Remote URL 解析

**支持的格式**：
```
SSH:
  git@github.com:user/repo.git
  git@gitlab.com:user/repo.git

HTTPS:
  https://github.com/user/repo.git
  https://gitlab.com/user/repo

Mixed:
  ssh://git@github.com/user/repo.git
```

**解析正则**：
```python
# 匹配 user/repo 部分
pattern = r'[:/]([^/:]+/[^/]+?)(?:\.git)?$'
match = re.search(pattern, remote_url)
if match:
    repo_path = match.group(1)  # "user/repo"
```

**Commit URL 模板**：
```python
url_templates = {
    'github': f'https://github.com/{repo_path}/commit/{hash}',
    'gitlab': f'https://gitlab.com/{repo_path}/-/commit/{hash}',
    'gitee': f'https://gitee.com/{repo_path}/commit/{hash}',
    'bitbucket': f'https://bitbucket.org/{repo_path}/commits/{hash}',
}
```

---

## 5. CLI 集成

### 5.1 新增命令行参数

**文件**: `pyscan_viz/cli.py`

```bash
python -m pyscan_viz report.json [options]

Options:
  -o, --output PATH        Output HTML file (default: report.html)
  --no-embed-source        Don't embed source code (dynamic load instead)
  --git-enrich            Add git blame info to all bugs
```

### 5.2 使用示例

```bash
# 不添加 git 信息（默认）
python -m pyscan_viz report.json -o bugs.html

# 添加 git 信息
python -m pyscan_viz report.json --git-enrich -o bugs_with_git.html
```

### 5.3 CLI 代码修改

```python
def main():
    parser = argparse.ArgumentParser(
        description='Generate interactive HTML visualization for PyScan reports'
    )

    parser.add_argument('report', help='Path to report.json')
    parser.add_argument('-o', '--output', default='report.html')
    parser.add_argument('--no-embed-source', action='store_true')
    parser.add_argument('--git-enrich', action='store_true',
                       help='Add git blame info to all bugs')

    args = parser.parse_args()

    # 加载报告
    with open(args.report) as f:
        report = json.load(f)

    bugs = report.get('bugs', [])
    scan_dir = Path(args.report).parent

    # Git 集成
    if args.git_enrich:
        from pyscan_viz.git_analyzer import GitAnalyzer

        git_analyzer = GitAnalyzer(scan_dir)

        if not git_analyzer.is_git_repo:
            print("Warning: Not a git repository, skipping git integration")
        else:
            print(f"Enriching {len(bugs)} bugs with git information...")
            bugs = git_analyzer.enrich_bugs_with_git_info(bugs)
            print(f"✓ Git information added")

    # 生成 HTML
    visualizer = Visualizer(bugs, scan_dir, embed_source=not args.no_embed_source)
    visualizer.generate(args.output)
    print(f"✓ HTML report generated: {args.output}")
```

---

## 6. HTML UI 设计

### 6.0 Stats Pane 过滤器（新增）

在顶部统计面板（Stats Pane）添加两个 Git 相关的过滤器。

#### 6.0.1 按 Commit 过滤

**UI 设计**：
```html
<div class="stats-pane">
    <!-- 现有内容：总 bug 数、严重程度统计等 -->

    <!-- 新增：Git 过滤器区域 -->
    <div class="git-filters" v-if="allCommits.length > 0">
        <div class="filter-group">
            <label for="commit-filter">📝 Filter by Commit:</label>
            <select id="commit-filter"
                    v-model="filters.selectedCommit"
                    @change="applyFilters"
                    class="commit-select">
                <option :value="null">全部 Commits ({{bugs.length}} bugs)</option>
                <option v-for="commit in allCommits"
                        :key="commit.hash_full"
                        :value="commit.hash_full">
                    {{commit.hash}} - {{commit.subject}} ({{commit.bug_count}} bugs) - {{commit.date_relative}}
                </option>
            </select>
        </div>

        <div class="filter-group">
            <label for="time-filter">⏰ Filter by Time Range:</label>
            <select id="time-filter"
                    v-model="filters.timeRange"
                    @change="applyFilters"
                    class="time-select">
                <option :value="null">全部时间</option>
                <option :value="1">最近 1 天</option>
                <option :value="7">最近 7 天</option>
                <option :value="15">最近 15 天</option>
                <option :value="30">最近 30 天</option>
                <option :value="90">最近 90 天</option>
            </select>
        </div>

        <div class="filter-group">
            <label for="owner-filter">👤 Filter by Owner:</label>
            <select id="owner-filter"
                    v-model="filters.selectedOwner"
                    @change="applyFilters"
                    class="owner-select">
                <option :value="null">全部作者 ({{bugs.length}} bugs)</option>
                <option v-for="owner in allOwners"
                        :key="owner.email"
                        :value="owner.email">
                    {{owner.name}} &lt;{{owner.email}}&gt; ({{owner.bug_count}} bugs)
                </option>
            </select>
        </div>

        <!-- 清除按钮 -->
        <button v-if="filters.selectedCommit || filters.timeRange || filters.selectedOwner"
                @click="clearGitFilters"
                class="clear-filters-btn">
            ✖ Clear Git Filters
        </button>
    </div>

    <!-- 过滤后的统计信息 -->
    <div class="filtered-stats" v-if="isGitFiltered">
        <span class="filter-indicator">
            🔍 Filtered: {{filteredBugs.length}} / {{bugs.length}} bugs
        </span>
    </div>
</div>
```

#### 6.0.2 过滤逻辑

**Vue computed 属性**：
```javascript
computed: {
    // 是否应用了 Git 过滤器
    isGitFiltered() {
        return this.filters.selectedCommit !== null ||
               this.filters.timeRange !== null ||
               this.filters.selectedOwner !== null;
    },

    // 应用 Git 过滤后的 bugs
    filteredBugsByGit() {
        let bugs = this.bugs;

        // 按 commit 过滤
        if (this.filters.selectedCommit) {
            bugs = bugs.filter(bug => {
                return bug.git_info &&
                       bug.git_info.hash_full === this.filters.selectedCommit;
            });
        }

        // 按时间范围过滤
        if (this.filters.timeRange) {
            const cutoffDate = new Date();
            cutoffDate.setDate(cutoffDate.getDate() - this.filters.timeRange);

            bugs = bugs.filter(bug => {
                if (!bug.git_info || !bug.git_info.date) {
                    return false;
                }
                const bugDate = new Date(bug.git_info.date);
                return bugDate >= cutoffDate;
            });
        }

        // 按作者过滤
        if (this.filters.selectedOwner) {
            bugs = bugs.filter(bug => {
                return bug.git_info &&
                       bug.git_info.email === this.filters.selectedOwner;
            });
        }

        return bugs;
    },

    // 最终的已过滤 bugs（组合所有过滤器）
    filteredBugs() {
        // 先应用 Git 过滤
        let bugs = this.filteredBugsByGit;

        // 再应用现有的过滤器（severity, function, type）
        if (this.filters.severity !== 'all') {
            bugs = bugs.filter(b => b.severity === this.filters.severity);
        }
        // ... 其他过滤器

        return bugs;
    }
}
```

#### 6.0.3 样式设计

```css
/* Git 过滤器区域 */
.git-filters {
    margin-top: 15px;
    padding: 15px;
    background: #f8f9fa;
    border-radius: 6px;
    border: 1px solid #dee2e6;
}

.filter-group {
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 10px;
}

.filter-group label {
    font-weight: 500;
    font-size: 14px;
    min-width: 150px;
    color: #495057;
}

.commit-select,
.time-select,
.owner-select {
    flex: 1;
    padding: 6px 12px;
    border: 1px solid #ced4da;
    border-radius: 4px;
    font-size: 13px;
    background: white;
    cursor: pointer;
}

.commit-select:focus,
.time-select:focus,
.owner-select:focus {
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 0 0.2rem rgba(0,123,255,0.25);
}

/* Commit 选项样式 */
.commit-select option {
    padding: 8px;
    font-family: monospace;
}

.clear-filters-btn {
    padding: 6px 12px;
    background: #6c757d;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 13px;
    transition: background 0.2s;
}

.clear-filters-btn:hover {
    background: #545b62;
}

/* 过滤状态指示 */
.filtered-stats {
    margin-top: 10px;
    padding: 8px 12px;
    background: #fff3cd;
    border: 1px solid #ffc107;
    border-radius: 4px;
}

.filter-indicator {
    font-size: 13px;
    color: #856404;
    font-weight: 500;
}
```

#### 6.0.4 UI 预览

```
┌────────────────────────────────────────────────────────────┐
│ Stats Pane                                                 │
├────────────────────────────────────────────────────────────┤
│ 📊 Total Bugs: 150    🔴 High: 30  🟡 Medium: 80  ⚪ Low: 40│
├────────────────────────────────────────────────────────────┤
│ Git Filters                                                │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ 📝 Filter by Commit:                                 │   │
│ │ [全部 Commits (150 bugs) ▼]                         │   │
│ │   - 全部 Commits (150 bugs)                         │   │
│ │   - a1b2c3d4 - Fix bug in auth (12 bugs) - 2 days   │   │
│ │   - b2c3d4e5 - Add validation (8 bugs) - 5 days     │   │
│ │   - c3d4e5f6 - Refactor utils (15 bugs) - 10 days   │   │
│ │   ...                                                │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                            │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ ⏰ Filter by Time Range:                             │   │
│ │ [全部时间 ▼]                                        │   │
│ │   - 全部时间                                        │   │
│ │   - 最近 1 天                                       │   │
│ │   - 最近 7 天                                       │   │
│ │   - 最近 15 天                                      │   │
│ │   - 最近 30 天                                      │   │
│ │   - 最近 90 天                                      │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                            │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ 👤 Filter by Owner:                                  │   │
│ │ [全部作者 (150 bugs) ▼]                            │   │
│ │   - 全部作者 (150 bugs)                            │   │
│ │   - John Doe <john@example.com> (45 bugs)           │   │
│ │   - Jane Smith <jane@example.com> (32 bugs)         │   │
│ │   - Bob Wilson <bob@example.com> (28 bugs)          │   │
│ │   ...                                                │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                            │
│ [✖ Clear Git Filters]                                     │
│                                                            │
│ 🔍 Filtered: 12 / 150 bugs                                │
└────────────────────────────────────────────────────────────┘
```

### 6.1 Bug Details Pane 布局

```html
<div class="bug-details" v-if="selectedBug">
    <!-- 现有内容：Bug ID, Severity, Type, Description, Location -->

    <!-- 新增：Git Commit 信息 -->
    <div class="git-info-section" v-if="selectedBug.git_info">
        <h4 class="section-title">
            <span class="icon">📝</span>
            Last Modified
        </h4>

        <div class="git-commit-card">
            <!-- Commit Hash + Date -->
            <div class="commit-header">
                <span class="commit-hash" :title="selectedBug.git_info.hash_full">
                    <code>{{selectedBug.git_info.hash}}</code>
                </span>
                <span class="commit-date">
                    {{selectedBug.git_info.date_relative}}
                </span>
            </div>

            <!-- Author -->
            <div class="commit-author">
                <span class="icon">👤</span>
                <span class="author-name">{{selectedBug.git_info.author}}</span>
                <span class="author-email" :title="selectedBug.git_info.email">
                    &lt;{{selectedBug.git_info.email}}&gt;
                </span>
            </div>

            <!-- Commit Message -->
            <div class="commit-subject">
                {{selectedBug.git_info.subject}}
            </div>

            <!-- Link to Git Platform -->
            <a v-if="selectedBug.git_info.url"
               :href="selectedBug.git_info.url"
               target="_blank"
               class="commit-link">
                <span class="icon">🔗</span>
                View commit on {{gitPlatform}}
                <span class="external-icon">↗</span>
            </a>
        </div>
    </div>

    <!-- 如果没有 git 信息 -->
    <div class="git-info-section" v-else>
        <p class="no-git-info">
            <span class="icon">ℹ️</span>
            Git information not available
        </p>
    </div>

    <!-- 现有内容：Suggestion, Callers, etc. -->
</div>
```

### 6.2 样式设计

```css
/* Git 信息区域 */
.git-info-section {
    margin-top: 20px;
    padding: 15px;
    background: #f8f9fa;
    border-radius: 8px;
    border-left: 4px solid #007bff;
}

.section-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 12px;
    color: #333;
}

.git-commit-card {
    background: white;
    padding: 15px;
    border-radius: 6px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

/* Commit Header */
.commit-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.commit-hash {
    font-family: 'Monaco', 'Menlo', monospace;
    background: #f1f3f5;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 13px;
    color: #495057;
    cursor: help;
}

.commit-date {
    font-size: 13px;
    color: #6c757d;
}

/* Author */
.commit-author {
    margin-bottom: 10px;
    font-size: 14px;
}

.author-name {
    font-weight: 500;
    color: #333;
}

.author-email {
    font-size: 12px;
    color: #6c757d;
    margin-left: 5px;
}

/* Commit Subject */
.commit-subject {
    margin-bottom: 12px;
    padding: 10px;
    background: #f8f9fa;
    border-radius: 4px;
    font-size: 14px;
    line-height: 1.5;
    color: #333;
    font-style: italic;
}

/* Commit Link */
.commit-link {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 8px 12px;
    background: #007bff;
    color: white;
    text-decoration: none;
    border-radius: 4px;
    font-size: 13px;
    transition: background 0.2s;
}

.commit-link:hover {
    background: #0056b3;
}

.external-icon {
    font-size: 12px;
}

/* No Git Info */
.no-git-info {
    font-size: 13px;
    color: #6c757d;
    text-align: center;
    padding: 10px;
}
```

### 6.3 UI 预览

```
┌──────────────────────────────────────────────────────────┐
│ Bug Details                                              │
├──────────────────────────────────────────────────────────┤
│ Bug ID: BUG_0042                                         │
│ Severity: 🔴 High                                        │
│ Type: NullPointerError                                   │
│ ...                                                      │
├──────────────────────────────────────────────────────────┤
│ 📝 Last Modified                                         │
│ ┌────────────────────────────────────────────────────┐   │
│ │ a1b2c3d4              7 days ago                   │   │
│ │                                                    │   │
│ │ 👤 John Doe <john@example.com>                    │   │
│ │                                                    │   │
│ │ "Fix null pointer bug in data processing module"  │   │
│ │                                                    │   │
│ │ [🔗 View commit on GitHub ↗]                      │   │
│ └────────────────────────────────────────────────────┘   │
├──────────────────────────────────────────────────────────┤
│ Suggestion: Add null check before accessing data...     │
│ ...                                                      │
└──────────────────────────────────────────────────────────┘
```

---

## 7. 性能优化

### 7.1 文件级缓存

**问题**：同一文件的多个 bug 会重复执行 git blame。

**解决**：
- 每个文件只 blame 一次
- 结果缓存在 `self.blame_cache: Dict[str, Dict[int, BlameInfo]]`
- 后续查询直接从缓存读取

**效果**：
- 假设 100 个 bugs 分布在 30 个文件
- 无缓存：100 次 git blame
- 有缓存：30 次 git blame

### 7.2 进度提示

```python
from tqdm import tqdm

def enrich_bugs_with_git_info(self, bugs: List[Dict]) -> List[Dict]:
    # 按文件分组
    bugs_by_file = {}
    for bug in bugs:
        file_path = bug.get('file_path')
        if file_path:
            bugs_by_file.setdefault(file_path, []).append(bug)

    # 显示进度
    enriched_bugs = []
    with tqdm(total=len(bugs), desc="Adding git info") as pbar:
        for file_path, file_bugs in bugs_by_file.items():
            # 一次性 blame 整个文件
            self.blame_file(file_path)

            # 为该文件的所有 bugs 添加信息
            for bug in file_bugs:
                blame_info = self.get_bug_blame_info(bug)
                # ...
                enriched_bugs.append(bug_with_git)
                pbar.update(1)

    return enriched_bugs
```

### 7.3 超时保护

```python
def blame_file(self, file_path: str) -> Dict[int, BlameInfo]:
    try:
        result = subprocess.run(
            ['git', 'blame', '--line-porcelain', str(absolute_path)],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True,
            timeout=30  # 30 秒超时
        )
        # ...
    except subprocess.TimeoutExpired:
        logger.warning(f"Git blame timeout for {file_path}")
        return {}
    except Exception as e:
        logger.warning(f"Git blame failed for {file_path}: {e}")
        return {}
```

### 7.4 持久化缓存（可选）

**目的**：避免重复扫描时重新 blame。

**实现**：
```python
# 保存到 .pyscan/git_blame_cache.json
{
  "version": "1.0",
  "generated_at": "2025-10-27T14:00:00",
  "files": {
    "src/utils.py": {
      "1": {
        "hash": "a1b2c3d4...",
        "author": "John Doe",
        "email": "john@example.com",
        "date": "2025-10-20T14:30:00",
        "subject": "Fix null pointer bug"
      },
      "2": {...},
      ...
    }
  }
}
```

**缓存失效策略**：
- 检测文件的 mtime（修改时间）
- 如果文件被修改，重新 blame

### 7.5 性能预估

| 场景 | Bug 数量 | 涉及文件 | 首次耗时 | 使用缓存 |
|------|---------|---------|---------|---------|
| 小型项目 | 50 | 15 | 3-5秒 | 瞬时 |
| 中型项目 | 200 | 60 | 10-20秒 | 瞬时 |
| 大型项目 | 1000 | 300 | 60-120秒 | 瞬时 |

---

## 8. 错误处理

### 8.1 Git 不可用

```python
if not self.is_git_repo:
    print("Warning: Not a git repository, skipping git integration")
    return bugs  # 原样返回
```

### 8.2 文件不存在

```python
absolute_path = self.repo_path / file_path
if not absolute_path.exists():
    logger.warning(f"File not found: {file_path}")
    return {}
```

### 8.3 Git Blame 失败

```python
try:
    result = subprocess.run(...)
except subprocess.CalledProcessError as e:
    logger.warning(f"Git blame failed for {file_path}: {e.stderr}")
    return {}
```

### 8.4 无法解析 Remote URL

```python
if not self.remote_url:
    logger.info("No remote URL found, commit links will not be generated")
    # 继续处理，只是不生成 URL
```

### 8.5 优雅降级

**原则**：Git 功能失败不应影响核心功能。

```python
# 即使 git 集成失败，仍然生成 HTML
bugs_with_git = bugs  # 默认不变

if args.git_enrich:
    try:
        git_analyzer = GitAnalyzer(scan_dir)
        if git_analyzer.is_git_repo:
            bugs_with_git = git_analyzer.enrich_bugs_with_git_info(bugs)
    except Exception as e:
        print(f"Warning: Git integration failed: {e}")
        # 继续使用原始 bugs

visualizer = Visualizer(bugs_with_git, ...)
```

---

## 9. 实施步骤

### Phase 1: 核心功能（P0）

#### Step 1: 创建 GitAnalyzer 基础类
- [ ] 创建 `pyscan_viz/git_analyzer.py`
- [ ] 实现 `_check_git_repo()`
- [ ] 实现 `_get_remote_url()`
- [ ] 编写单元测试

**验收标准**：
- 能正确检测 git 仓库
- 能获取 remote URL

#### Step 2: 实现 Git Blame 解析
- [ ] 实现 `blame_file()` 方法
- [ ] 实现 `_parse_blame_output()` 方法
- [ ] 添加缓存机制
- [ ] 编写解析测试（使用 fixture）

**验收标准**：
- 能正确解析 git blame 输出
- 缓存工作正常

#### Step 3: 实现 Bug 关联
- [ ] 实现 `get_bug_blame_info()` 方法
- [ ] 处理多行 bug 的情况（选择最新 commit）
- [ ] 实现 `enrich_bugs_with_git_info()` 方法
- [ ] 添加进度提示

**验收标准**：
- 能为每个 bug 找到对应的 commit
- 多行 bug 正确选择最新 commit

#### Step 4: 实现 URL 生成
- [ ] 实现 `_detect_platform()` 方法
- [ ] 实现 `_parse_repo_path()` 方法（正则解析）
- [ ] 实现 `_generate_commit_url()` 方法
- [ ] 支持 GitHub、GitLab、Gitee、Bitbucket
- [ ] 编写 URL 生成测试

**验收标准**：
- 支持常见的 SSH 和 HTTPS 格式
- 能正确生成 4 大平台的 URL

#### Step 5: CLI 集成
- [ ] 修改 `pyscan_viz/cli.py`
- [ ] 添加 `--git-enrich` 参数
- [ ] 集成 GitAnalyzer
- [ ] 添加错误处理和日志

**验收标准**：
- 命令行参数正常工作
- 优雅降级（git 失败不影响 HTML 生成）

#### Step 6: HTML UI 实现（Bug Details Pane）
- [ ] 修改 `template.html`
- [ ] 添加 Bug Details Pane 中的 Git 信息展示区域
- [ ] 实现 CSS 样式
- [ ] 测试不同浏览器兼容性

**验收标准**：
- Git 信息正确显示在 Bug Details
- UI 美观，与现有风格一致
- 链接可点击跳转

#### Step 6.5: 实现 Git 过滤功能
- [ ] 在 `visualizer.py` 中实现 `extract_commits()` 方法
- [ ] 在 `visualizer.py` 中实现 `extract_owners()` 方法
- [ ] 在 `template.html` 的 Vue data 中添加 `allCommits` 和 `allOwners`
- [ ] 在 Stats Pane 添加三个过滤器：
  - [ ] Commit 下拉列表（按时间排序）
  - [ ] 时间范围选择器
  - [ ] 作者下拉列表（按 bug 数量排序）
- [ ] 实现 Vue computed 属性：`filteredBugsByGit`
- [ ] 更新现有的 `filteredBugs` 逻辑，整合 Git 过滤
- [ ] 添加"Clear Git Filters"按钮
- [ ] 添加过滤状态指示器
- [ ] 实现 CSS 样式

**验收标准**：
- 三个过滤器正常工作
- 可以单独使用或组合使用
- 过滤结果准确
- Clear 按钮正常工作
- 过滤状态清晰显示

#### Step 7: 端到端测试
- [ ] 准备测试仓库（包含多个 commit）
- [ ] 运行完整流程：pyscan → pyscan_viz --git-enrich
- [ ] 验证 HTML 中的 git 信息
- [ ] 测试各种边界情况

**验收标准**：
- 完整流程无错误
- Git 信息准确显示

### Phase 2: 优化增强（P1）

#### Step 8: 性能优化
- [ ] 实现持久化缓存（.pyscan/git_blame_cache.json）
- [ ] 添加缓存失效策略（基于文件 mtime）
- [ ] 优化大文件处理

#### Step 9: 错误处理完善
- [ ] 添加详细的错误日志
- [ ] 改进超时处理
- [ ] 添加重试机制（可选）

#### Step 10: 文档和示例
- [ ] 更新 README.md
- [ ] 添加使用示例
- [ ] 编写故障排查指南

---

## 10. 测试策略

### 10.1 单元测试

**测试文件**：`tests/test_git_analyzer.py`

```python
class TestGitAnalyzer:
    def test_check_git_repo_valid(self):
        """测试检测有效的 git 仓库"""

    def test_check_git_repo_invalid(self):
        """测试检测非 git 目录"""

    def test_parse_remote_url_ssh(self):
        """测试解析 SSH 格式的 remote URL"""

    def test_parse_remote_url_https(self):
        """测试解析 HTTPS 格式的 remote URL"""

    def test_detect_platform_github(self):
        """测试检测 GitHub"""

    def test_generate_commit_url_github(self):
        """测试生成 GitHub commit URL"""

    def test_parse_blame_output(self):
        """测试解析 git blame 输出（使用 fixture）"""

    def test_get_bug_blame_info_single_line(self):
        """测试单行 bug 的 blame 信息"""

    def test_get_bug_blame_info_multi_line_same_commit(self):
        """测试多行 bug，相同 commit"""

    def test_get_bug_blame_info_multi_line_different_commits(self):
        """测试多行 bug，不同 commit，应返回最新的"""

    def test_enrich_bugs_with_git_info(self):
        """测试批量添加 git 信息"""
```

### 10.2 集成测试

**测试文件**：`tests/test_e2e_gitviz.py`

```python
class TestGitVizE2E:
    def test_full_workflow_with_git(self):
        """测试完整流程：pyscan → pyscan_viz --git-enrich"""
        # 1. 创建测试仓库
        # 2. 创建测试文件并 commit
        # 3. 运行 pyscan
        # 4. 运行 pyscan_viz --git-enrich
        # 5. 验证生成的 HTML

    def test_no_git_repo_graceful_degradation(self):
        """测试非 git 仓库时的优雅降级"""
```

### 10.3 测试用例覆盖

| 测试场景 | 覆盖 |
|---------|-----|
| Git 仓库检测 | ✅ |
| Remote URL 解析（SSH/HTTPS） | ✅ |
| 平台检测（GitHub/GitLab/Gitee/Bitbucket） | ✅ |
| Commit URL 生成 | ✅ |
| Git Blame 输出解析 | ✅ |
| 单行 Bug blame | ✅ |
| 多行 Bug，相同 commit | ✅ |
| 多行 Bug，不同 commit（选择最新） | ✅ |
| 文件不存在 | ✅ |
| Git blame 失败 | ✅ |
| 非 git 仓库 | ✅ |
| 无 remote URL | ✅ |
| 缓存机制 | ✅ |

---

## 11. 使用示例

### 示例 1: 基本使用

```bash
# Step 1: 扫描代码
python -m pyscan /path/to/project -c config.yaml -o report.json

# Step 2: 生成带 git 信息的 HTML
python -m pyscan_viz report.json --git-enrich -o bugs_with_git.html

# Step 3: 在浏览器打开
open bugs_with_git.html
```

### 示例 2: 不使用 Git 功能

```bash
# 默认不添加 git 信息
python -m pyscan_viz report.json -o bugs.html
```

### 示例 3: 查看 Git 信息

在生成的 HTML 中：
1. 点击任意 bug
2. 在 Bug Details Pane 查看 "Last Modified" 区域
3. 点击 "View commit on GitHub" 跳转到完整 commit

---

## 12. 风险和缓解

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| Git blame 性能差 | 用户等待时间长 | 中 | 文件级缓存、进度提示、持久化缓存 |
| 大文件 blame 超时 | 部分 bug 无 git 信息 | 低 | 30秒超时、优雅降级 |
| Remote URL 格式不支持 | 无法生成链接 | 低 | 扩展支持列表、提供警告 |
| Git 不可用 | 功能无法使用 | 低 | 优雅降级、清晰错误提示 |
| 文件路径不匹配 | 找不到文件 | 中 | 统一使用相对路径、路径规范化 |

---

## 13. 未来扩展

### v2.1 可能的增强

- [ ] 显示 commit diff 摘要
- [ ] 支持更多 Git 平台（自托管 GitLab、企业 GitHub）
- [ ] 添加作者统计（哪个作者引入的 bug 最多）
- [ ] 支持显示多个相关 commit（不仅是最新的）
- [ ] 集成 CI/CD，自动生成带 git 信息的报告
- [ ] 支持 git blame 的行级高亮（在代码显示区域）

### v2.2 高级功能

- [ ] Git 历史分析：追踪 bug 代码的演变历史
- [ ] 热力图：显示哪些文件/作者的 bug 最多
- [ ] PR 关联：如果 commit 关联了 PR，显示 PR 信息

---

## 14. 总结

### 核心价值

本功能通过 Git blame 为每个 bug 添加代码最后修改的 commit 信息，并提供强大的过滤功能，帮助开发者：
- 🎯 快速定位责任人
- ⏰ 了解代码修改时间
- 🔗 一键跳转到完整 commit
- 🐛 更高效地调试和修复 bug
- 🔍 按 commit/时间/作者过滤 bug，聚焦特定变更

### 技术亮点

- ✅ **精确**：行级别的 git blame
- ✅ **高效**：文件级缓存，避免重复操作
- ✅ **可靠**：优雅降级，不影响核心功能
- ✅ **易用**：一个参数即可启用
- ✅ **美观**：与现有 UI 风格一致
- ✅ **灵活**：三种过滤方式可单独或组合使用

### 实施建议

建议采用**渐进式开发**：
1. 先实现 MVP（Phase 1），验证功能可行性
   - GitAnalyzer 核心功能
   - Bug Details Pane 的 git 信息展示
   - Stats Pane 的三个过滤器
2. 收集用户反馈
3. 再进行性能优化和功能增强（Phase 2）

**预估工作量**：3-4 天开发 + 1 天测试

---

**文档版本**: v1.2
**最后更新**: 2025-10-27
**作者**: Claude + User

**变更历史**：
- v1.0 (2025-10-27): 初始版本，包含 Git blame 和 Bug Details 展示
- v1.1 (2025-10-27): 添加三种过滤功能（按 commit/时间/作者）
- v1.2 (2025-10-27): 添加自定义 Git 平台配置功能（企业 Git 服务器支持）
