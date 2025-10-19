# PyScan Benchmark 测试集

## 概述

本目录包含 PyScan 的 benchmark 测试集，用于评估 bug 检测的准确性（precision 和 recall）。

## 目录结构

```
benchmarks/
├── README.md                   # 本文件
├── metadata.yaml               # Benchmark 元数据
├── categories/                 # 按 bug 类型分类
│   ├── 09_resource_and_context/
│   ├── 13_concurrency/
│   ├── 05_logic_and_control_flow/
│   ├── 10_security/
│   └── 21_api_design/
├── ground_truth.json           # 所有 bug 的标准答案
└── evaluation/                 # 评估工具
    └── evaluate.py             # 评估脚本
```

## Bug 类别

### P0 优先级（已实现）

1. **09_resource_and_context**: 资源管理错误
   - file_leak: 文件泄露
   - thread_pool_leak: 线程池泄露
   - socket_leak: Socket 泄露
   - db_connection_leak: 数据库连接泄露
   - context_manager_error: 上下文管理器错误

2. **13_concurrency**: 并发与线程安全
   - race_condition: 竞态条件
   - lock_mismatch: 锁获取释放不配对
   - deadlock_risk: 死锁风险

3. **05_logic_and_control_flow**: 逻辑与控制流
   - constant_condition: 恒真/恒假条件
   - exception_logic_error: 异常逻辑缺陷

4. **10_security**: 安全漏洞
   - command_injection: 命令注入
   - path_traversal: 路径遍历

5. **21_api_design**: API 设计与使用
   - public_api_no_validation: 公共 API 缺少参数验证
   - return_type_inconsistent: 返回值类型不一致

## 样本结构

每个 bug 子类型目录包含：

```
<bug_type>/
├── README.md           # Bug 类型说明文档
├── positive/           # 包含 bug 的代码样本
│   ├── example1.py
│   ├── example2.py
│   └── metadata.yaml   # Bug 标注信息
└── negative/           # 不包含 bug 的代码样本
    ├── example1.py
    ├── example2.py
    └── metadata.yaml
```

## Bug 标注格式

每个 `metadata.yaml` 包含：

```yaml
bugs:
  - id: "RM-FL-001"                    # 唯一标识符
    category: "resource_management"     # 大类
    subcategory: "file_leak"            # 子类
    severity: "high"                    # 严重程度
    type: "ResourceLeakRisk"            # Bug 类型
    file: "example1.py"                 # 文件名
    function: "read_config"             # 函数名
    location:
      start_line: 4                     # Bug 起始行
      end_line: 4                       # Bug 结束行
      start_col: 4                      # Bug 起始列
      end_col: 28                       # Bug 结束列
    description: "文件句柄未关闭"         # 描述
    root_cause: "未使用 with 语句"       # 根因
    cwe_id: "CWE-404"                   # CWE 编号
    difficulty: "easy"                  # 难度（easy/medium/hard）
```

## 评估指标

运行评估脚本后，将生成以下指标：

- **Precision (精确率)**: TP / (TP + FP)
- **Recall (召回率)**: TP / (TP + FN)
- **F1 Score**: 2 * Precision * Recall / (Precision + Recall)
- **按类别统计**: 每个 bug 类别的独立评估
- **按难度统计**: 简单/中等/困难样本的检测率

## 使用方法

### 1. 运行 PyScan 扫描 benchmark

```bash
python -m pyscan benchmarks/categories -o benchmark_report.json
```

### 2. 评估结果

```bash
python benchmarks/evaluation/evaluate.py \
    --ground-truth benchmarks/ground_truth.json \
    --report benchmark_report.json \
    --output evaluation_report.json
```

### 3. 查看报告

评估报告包含：
- 总体指标
- 按类别分析
- False Positive 详情
- False Negative 详情

## 贡献新样本

欢迎贡献新的 bug 样本！请遵循以下步骤：

1. 在对应类别目录下创建新文件
2. 添加 bug 标注到 metadata.yaml
3. 确保代码可执行且 bug 真实存在
4. 运行 `python benchmarks/evaluation/validate.py` 验证格式

## 版本历史

- v0.1 (2025-10-19): 初始版本，包含 P0 优先级类别（~50 个样本）
