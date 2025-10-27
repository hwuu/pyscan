# PyScan - Python 代码深度 Bug 检测工具

PyScan 是一个基于大语言模型(LLM)的 Python 代码静态分析工具，**专注于发现传统静态工具无法检测的深层次问题**（业务逻辑错误、复杂数据流问题、并发问题等）。

## 核心理念

- **定位明确**：PyScan 不是静态工具的集合，而是深度 bug 检测的专家
- **智能增强**：集成 mypy/bandit 等工具为 LLM 提供上下文，引导其专注于深层次分析
- **报告纯净**：只输出 LLM 发现的深度 bug，不包含简单的类型错误或代码规范问题（这些可以直接用 mypy/pylint 等工具检查）

## 特性

### 核心能力
- ✅ **深度分析专家**: LLM 专注于发现静态工具找不到的深层次问题
  - 业务逻辑错误（边界条件、状态转换、隐式约束）
  - 复杂数据流问题（跨函数依赖、间接引用）
  - 资源管理问题（文件/连接/锁的正确释放）
  - 并发问题（竞态条件、死锁风险）
- ✅ **智能上下文增强**: 集成 mypy/bandit 为 LLM 提供静态分析事实，引导其专注方向
  - Layer 1 工具（mypy、bandit）的结果**不会**直接输出到报告
  - 而是作为"已知事实"融入 LLM prompt，减少重复分析

### 技术特性
- ✅ **AST 解析**: 深度解析 Python 代码结构,提取函数信息和调用关系
- ✅ **上下文增强**: 为每个函数构建包含调用者和被调用者的完整上下文
- ✅ **智能调用分析**: 精简的 caller 信息展示(调用点上下文 ± 5 行,带行号和高亮)
- ✅ **公共 API 识别**: 自动识别公共 API 并要求严格的参数验证
- ✅ **高级调用推断**: 支持装饰器和 Callable 类型注解的调用关系推断
- ✅ **LLM 驱动**: 利用大语言模型进行智能代码审查
- ✅ **精确定位**: 提供 bug 的准确代码位置(行号、列号)
- ✅ **Bug 级报告**: 每个 bug 独立记录,包含 caller/callee 信息
- ✅ **断点续传**: 支持从失败点恢复扫描,避免重复检测
- ✅ **强制重扫**: 支持 `--force` 参数从头开始扫描
- ✅ **快速失败**: 检测失败时立即退出并保存进度
- ✅ **交互式可视化**: 通过 pyscan_viz 生成交互式 HTML 报告,支持代码片段行号显示和调用点高亮
- ✅ **相对路径**: 报告中使用相对路径,便于移动和分享
- ✅ **灵活配置**: 通过 YAML 配置文件自定义扫描规则
- ✅ **Prompt 压缩**: 自动多级压缩策略,处理超长上下文

## 安装

```bash
pip install -r requirements.txt
```

## 配置

创建 `config.yaml` 配置文件:

```yaml
llm:
  base_url: "https://api.openai.com/v1"
  api_key: "your-api-key"
  model: "gpt-4"
  max_tokens: 8000
  temperature: 0.2

scan:
  exclude_patterns:
    - "test_*.py"
    - "*_test.py"
    - "config.py"
    - "settings.py"
    - "*/site-packages/*"
    - "*/venv/*"
    - "*/.venv/*"

detector:
  max_retries: 3
  concurrency: 1
  context_token_limit: 6000
  use_tiktoken: false  # 可选: 使用 tiktoken 精确计算 token (需安装 tiktoken)
  enable_advanced_analysis: true  # 启用装饰器和 Callable 类型注解的调用推断

public_api:
  # 公共 API 识别规则 (自动检测需要严格参数验证的函数)
  decorators:
    - "route"
    - "api_view"
    - "app.route"
    - "blueprint.route"
  file_patterns:
    - "*/api/*"
    - "*/views/*"
    - "*/endpoints/*"
  name_prefixes:
    - "api_"
    - "handle_"
    - "endpoint_"

# Layer 1 静态分析工具配置
# 作用：为 LLM 提供静态分析上下文，引导其专注于深层次问题
# 注意：Layer 1 的结果不会直接输出到报告
layer1:
  enable_mypy: true      # 启用 mypy 类型检查
  enable_bandit: true    # 启用 bandit 安全扫描

# Layer 4 交叉验证配置
# 建议：设置为 false（默认），让 PyScan 只输出 LLM 发现的深度 bug
layer4:
  enable_cross_validation: false  # 禁用交叉验证（推荐）
```

### 配置说明

#### 基础配置
- **llm.base_url**: LLM API 基础 URL
- **llm.api_key**: API 密钥
- **llm.model**: 使用的模型名称
- **llm.max_tokens**: LLM 单次请求最大 token 数
- **llm.temperature**: 温度参数 (0-2)，值越低结果越确定
- **scan.exclude_patterns**: 扫描时排除的文件模式
- **detector.max_retries**: 检测失败时的最大重试次数
- **detector.concurrency**: 并发检测数量（建议为 1 以避免 API 限流）
- **detector.context_token_limit**: 上下文 token 限制（必须小于 llm.max_tokens）
- **detector.use_tiktoken**: 是否使用 tiktoken 精确计算 token 数
  - `false` (默认): 使用简单估算 (1 token ≈ 4 字符)，无需额外依赖
  - `true`: 使用 tiktoken 精确计算，需要安装 tiktoken 包

#### Layer 1 配置（智能上下文增强）
- **layer1.enable_mypy**: 是否启用 mypy 类型检查（默认: true）
  - mypy 发现的类型错误会告知 LLM，引导其专注于业务逻辑问题
  - **重要**：mypy 的结果不会直接输出到报告
- **layer1.enable_bandit**: 是否启用 bandit 安全扫描（默认: true）
  - bandit 发现的安全问题会告知 LLM，引导其专注于深层次安全问题
  - **重要**：bandit 的结果不会直接输出到报告

#### Layer 4 配置（交叉验证）
- **layer4.enable_cross_validation**: 是否启用交叉验证（默认: false，推荐）
  - `false`（推荐）：PyScan 只输出 LLM 发现的深度 bug
  - `true`：会把 Layer 1 的结果转换成 bug 报告（与产品定位不符，不推荐）
```

## 使用方法

### 基本用法

扫描指定目录并生成 JSON 报告:

```bash
python -m pyscan /path/to/your/code
```

### 高级选项

```bash
# 指定配置文件
python -m pyscan /path/to/code -c config.yaml

# 指定输出 JSON 文件
python -m pyscan /path/to/code -o my_report.json

# 启用详细日志
python -m pyscan /path/to/code -v

# 强制从头开始扫描（删除已有进度）
python -m pyscan /path/to/code --force

# 断点续传: 如果上次扫描失败,再次运行会从失败点继续
python -m pyscan /path/to/code
```

### 生成可视化报告

使用 `pyscan_viz` 将 JSON 报告转换为交互式 HTML:

```bash
# 基本用法 (默认嵌入源码)
python -m pyscan_viz report.json

# 指定输出文件
python -m pyscan_viz report.json -o visualization.html

# 不嵌入源码,动态加载 (适合大型项目)
python -m pyscan_viz report.json --no-embed-source
```

## 工作原理

### PyScan 扫描流程

1. **代码扫描**: 递归扫描目标目录,收集所有 Python 文件
2. **AST 解析**: 解析每个文件的 AST,提取函数定义、参数、调用关系、代码位置等信息
3. **上下文构建**: 为每个函数构建包含调用者和被调用者代码的完整上下文
4. **Bug 检测**: 将函数和上下文发送给 LLM,分析潜在 bug,返回精确位置
5. **进度保存**: 每完成一个函数检测后立即保存进度到 `.pyscan/` 目录
6. **报告生成**: 汇总检测结果,生成 JSON 报告

### PyScan Viz 可视化

1. **加载报告**: 读取 pyscan 生成的 JSON 报告
2. **源码处理**: 根据选项嵌入源码或准备动态加载
3. **位置转换**: 将相对行号转换为绝对行号
4. **HTML 生成**: 生成包含统计、bug 列表、代码查看器的交互式网页
5. **导航支持**: 支持通过 URL hash 直接定位到特定 bug

## 检测的 Bug 类型

- 逻辑错误(边界条件、空值处理)
- 类型错误
- 资源泄漏
- 并发问题
- 异常处理缺失
- 性能问题

## 报告格式

### JSON 格式 (PyScan 输出)

新版本采用 **Bug 级别** 的报告格式，每个 bug 独立记录：

```json
{
  "timestamp": "2025-01-01T12:00:00",
  "summary": {
    "total_bugs": 15,
    "affected_functions": 12,
    "severity_breakdown": {
      "high": 3,
      "medium": 7,
      "low": 5
    }
  },
  "bugs": [
    {
      "bug_id": "BUG_0001",
      "function_name": "divide",
      "file_path": "/path/to/file.py",
      "function_start_line": 10,
      "severity": "high",
      "type": "ZeroDivisionError",
      "description": "除数可能为零（中文描述）",
      "location": "第13行",
      "start_line": 13,
      "end_line": 13,
      "start_col": 11,
      "end_col": 18,
      "suggestion": "添加除数检查",
      "callers": [
        {
          "file_path": "/path/to/caller.py",
          "function_name": "calculate",
          "code_snippet": "def calculate(a, b):\n    ...\n    result = divide(a, b)\n    ..."
        }
      ],
      "callees": ["helper_func"],
      "inferred_callers": [
        {
          "hint": "(推断): @decorator装饰器",
          "code": "def decorator(func):\n    return wrapper"
        }
      ]
    }
  ]
}
```

**关键字段说明**：
- `file_path`: 相对于扫描目录的相对路径（如 `src/utils.py`）
- `start_line`/`end_line`: Bug 在文件中的绝对行号（从1开始）
- `callers`: 调用者列表，每个包含：
  - `file_path`: 文件相对路径
  - `function_name`: 函数名
  - `start_line`/`end_line`: 函数在文件中的绝对行号
  - `code`: 完整函数代码（供 LLM 分析）
  - `highlight_lines`: 调用点行号列表（HTML 显示时高亮）
- `callees`: 被调用函数名列表
- `inferred_callers`: 推断的调用者（如装饰器、Callable 类型注解），结构同 `callers`

### 交互式 HTML (PyScan Viz 输出)

通过 `pyscan_viz` 生成的交互式网页报告,包含:

- **顶部统计面板**: 显示总 bug 数、影响函数数、按严重程度分类统计
- **左侧 Bug 列表**:
  - 按严重程度/函数/类型/行号排序
  - 支持多维度过滤（严重程度、函数、Bug 类型）
  - 显示 Bug ID、严重程度、类型和位置
- **右侧代码查看器**（基于 POI - Point of Interest 设计）:
  - **Current Function 区域**：显示 bug 所在位置
    - 只显示 **bug POI ± 5 行**代码（约 11 行）
    - 高亮显示 bug 所在行
    - 显示绝对行号
  - **Callers 区域**：显示调用当前函数的函数信息
    - 显示文件相对路径 + 函数名
    - 只显示 **调用点 ± 5 行**代码（约 11 行）
    - 高亮显示调用行
    - 显示绝对行号
  - **Inferred Callers 区域**：显示推断的调用者（装饰器、Callable 等）
    - 显示文件相对路径 + 函数名 + 推断提示
    - 只显示 **类型注解点 ± 5 行**代码（约 11 行）
    - 高亮显示类型注解行
    - 显示绝对行号
- **POI 设计优势**：
  - 精简展示，只显示关键代码上下文
  - 避免显示整个函数（可能几十上百行）
  - 快速定位问题，减少干扰信息
- **URL 导航**: 支持通过 `#BUG_0001` 等 hash 直接定位到特定 bug

## 项目结构

```
pyscan/
├── pyscan/                 # 核心扫描工具
│   ├── __init__.py
│   ├── __main__.py         # 程序入口
│   ├── cli.py              # 命令行接口(含进度管理)
│   ├── config.py           # 配置管理
│   ├── scanner.py          # 代码扫描
│   ├── ast_parser.py       # AST 解析
│   ├── context_builder.py  # 上下文构建
│   ├── bug_detector.py     # Bug 检测
│   └── reporter.py         # 报告生成(JSON)
├── pyscan_viz/             # 可视化工具
│   ├── __init__.py
│   ├── __main__.py         # 程序入口
│   ├── cli.py              # 命令行接口
│   └── visualizer.py       # HTML 生成器
├── tests/                  # 测试用例
├── config.yaml.example     # 配置示例
├── requirements.txt        # 依赖清单
└── README.md              # 本文档
```

## 运行测试

```bash
pytest tests/ -v
```

## 注意事项

1. **API 成本**: 每个函数都会调用一次 LLM API,大型项目可能产生较高费用
2. **Token 限制**: 确保 `context_token_limit` 小于 LLM 的 `max_tokens`
3. **检测速度**: 受限于 API 调用速度和并发设置,大型项目扫描可能较慢
4. **误报率**: LLM 可能产生误报或漏报,建议结合人工审查
5. **断点续传**: 进度文件保存在被扫描目录的 `.pyscan/` 子目录中,不会自动清理
6. **快速失败**: 任何检测失败都会立即终止扫描并保存进度,修复问题后可继续

## 使用示例

```bash
# 1. 首次扫描项目
python -m pyscan ./my_project -c config.yaml -o bugs.json

# 2. 如果扫描失败(如 API 限流),修复问题后继续
python -m pyscan ./my_project -c config.yaml -o bugs.json

# 3. 扫描完成后生成可视化报告
python -m pyscan_viz bugs.json -o bugs.html

# 4. 在浏览器中打开 bugs.html 查看交互式报告

# 5. 分享特定 bug 的 URL
# 例如: file:///path/to/bugs.html#BUG-003
```

## License

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request!
