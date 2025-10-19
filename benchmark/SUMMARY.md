# PyScan Benchmark 测试集总结

## 概述

**版本**: 0.2
**创建日期**: 2025-10-19
**最后更新**: 2025-10-19
**总 Bug 数**: 45
**状态**: Stage 2 扩展完成 ✅

## 目标

Benchmark 测试集用于评估 PyScan 的检测能力，通过标准化的 bug 样本衡量：
- **Precision（精确率）**: 检测结果中真实 bug 的比例
- **Recall（召回率）**: 真实 bug 中被检测到的比例
- **F1 Score**: Precision 和 Recall 的调和平均

## 统计信息

### 按类别分布

| 类别 | Bug 数 | 占比 | 状态 |
|------|--------|------|------|
| 资源管理 (Resource Management) | 10 | 22.2% | ✅ |
| 并发问题 (Concurrency) | 6 | 13.3% | ✅ |
| 逻辑控制流 (Logic & Control Flow) | 10 | 22.2% | ✅ |
| 安全漏洞 (Security) | 9 | 20.0% | ✅ |
| API 设计 (API Design) | 10 | 22.2% | ✅ |
| **总计** | **45** | **100%** | **✅** |

### 按严重程度分布

| 严重程度 | Bug 数 | 占比 |
|---------|--------|------|
| High | 31 | 68.9% |
| Medium | 13 | 28.9% |
| Low | 1 | 2.2% |

### 按难度分布

| 难度 | Bug 数 | 占比 |
|------|--------|------|
| Easy | 11 | 24.4% |
| Medium | 23 | 51.1% |
| Hard | 4 | 8.9% |
| High | 7 | 15.6% |

## Bug 样本详情

### 1. 资源管理 (10 bugs)

| ID | 子类别 | 描述 | 严重程度 | 难度 |
|----|--------|------|---------|------|
| RM-FL-001~007 | file_leak | 文件未关闭、异常路径泄露 | High | Easy/Medium |
| RM-TPL-001~003 | thread_pool_leak | 线程池未关闭 | High | Medium |

**关键模式**:
- 资源创建后未在所有路径释放
- 异常路径下资源泄露
- 缺少 finally 块或 with 语句

### 2. 并发问题 (6 bugs)

| ID | 子类别 | 描述 | 严重程度 | 难度 |
|----|--------|------|---------|------|
| CONC-RC-001~006 | race_condition | 全局变量竞态、无锁访问 | High | Easy/Medium |

**关键模式**:
- 全局变量写入未加锁
- 复合操作非原子
- 实例变量多线程共享未同步

### 3. 逻辑控制流 (10 bugs)

| ID | 子类别 | 描述 | 严重程度 | 难度 |
|----|--------|------|---------|------|
| LOGIC-EXC-001~003 | exception_logic_error | 异常时资源未释放 | High | Medium |
| LOGIC-EXC-004~007 | exception_logic_error | 异常类型错误/过宽 | Medium/High | Easy/Medium |
| LOGIC-EXC-008~010 | exception_logic_error | 缺少 finally 块 | High/Medium | Easy/Medium |

**关键模式**:
- 异常捕获后未清理资源
- 捕获过于宽泛的 Exception
- 裸 except 掩盖系统异常
- 缺少 finally 块释放锁/状态

### 4. 安全漏洞 (9 bugs)

| ID | 子类别 | 描述 | 严重程度 | 难度 |
|----|--------|------|---------|------|
| SEC-PT-001~005 | path_traversal | 路径拼接未验证 | High | High |
| SEC-PT-006~009 | path_traversal | TOCTOU、符号链接、Zip Slip | High/Medium | Hard |

**关键模式**:
- 用户输入直接拼接路径
- 缺少路径规范化和验证
- TOCTOU 漏洞（检查后使用前）
- 符号链接未检测
- 压缩包路径未验证

### 5. API 设计 (10 bugs)

| ID | 子类别 | 描述 | 严重程度 | 难度 |
|----|--------|------|---------|------|
| API-VAL-001~005 | public_api_no_validation | 缺少参数校验 | High/Medium | Medium |
| API-RET-001~005 | public_api_no_validation | 返回类型不一致 | Medium/Low | Easy/Medium |

**关键模式**:
- 公共 API 缺少输入验证
- 缺少白名单限制
- 缺少范围验证
- 返回类型不一致（dict/None/异常混合）
- 成功/失败路径返回不同类型

## 覆盖的已知 Bug

Benchmark 覆盖了以下真实项目中发现的 bug 类型：

| Bug ID | 描述 | Benchmark 对应 | 覆盖度 |
|--------|------|---------------|-------|
| BUG_0001 | 文件未关闭 | RM-FL-001~007 | ✅ |
| BUG_0002 | 全局变量竞态 | CONC-RC-004~006 | ✅ |
| BUG_0005 | 类成员竞态 | CONC-RC-004 | ✅ |
| BUG_0007 | 异常时资源未释放 | LOGIC-EXC-001~003 | ✅ |
| BUG_0008 | 异常类型错误 | LOGIC-EXC-004~007 | ✅ |
| BUG_0009 | 缺少 finally | LOGIC-EXC-008~010 | ✅ |
| BUG_0010 | 线程池泄露 | RM-TPL-003 | ✅ |
| BUG_0011 | 资源引用泄露 | RM-FL-005~007 | ✅ |
| BUG_0012 | API 缺少验证 | API-VAL-001~005 | ✅ |
| BUG_0013 | 返回类型不一致 | API-RET-001~005 | ✅ |
| BUG_0014 | 路径遍历 | SEC-PT-001~009 | ✅ |

**总覆盖率**: 11/15 (73.3%)

## 使用方法

### 1. 生成 Ground Truth

```bash
cd benchmarks
python build_ground_truth.py
```

输出: `ground_truth.json` (45 个标注的 bug)

### 2. 运行 PyScan 扫描

```bash
python -m pyscan benchmarks/categories -o scan_report.json
```

### 3. 评估结果

```bash
python benchmarks/evaluation/evaluate.py \
    --ground-truth benchmarks/ground_truth.json \
    --report scan_report.json \
    --output evaluation_result.json
```

输出指标:
- **Precision**: 精确率
- **Recall**: 召回率
- **F1 Score**: 综合指标
- **误报 (False Positives)**: 错误检测
- **漏报 (False Negatives)**: 未检测到的真实 bug

## 文件结构

```
benchmarks/
├── categories/                  # Bug 样本分类
│   ├── 05_logic_and_control_flow/
│   │   └── exception_logic_error/
│   │       ├── positive/       # 包含 bug 的样本
│   │       │   ├── example1_resource_cleanup.py
│   │       │   ├── example2_exception_type.py
│   │       │   ├── example3_finally_missing.py
│   │       │   └── metadata.yaml  # Bug 标注
│   │       └── negative/       # 正确的代码
│   │           └── example1_correct_handling.py
│   ├── 09_resource_and_context/
│   │   ├── file_leak/
│   │   └── thread_pool_leak/
│   ├── 10_security/
│   │   └── path_traversal/
│   ├── 13_concurrency/
│   │   └── race_condition/
│   └── 21_api_design/
│       └── public_api_no_validation/
├── ground_truth.json           # 自动生成的标注文件
├── build_ground_truth.py       # 生成工具
├── evaluation/
│   └── evaluate.py             # 评估脚本
├── README.md                   # 详细文档
├── SUMMARY.md                  # 本文件
└── PROGRESS.md                 # 进展跟踪
```

## Bug 标注格式

每个 positive 目录下的 `metadata.yaml` 文件包含 bug 标注：

```yaml
bugs:
  - id: "RM-FL-001"
    category: "resource_management"
    subcategory: "file_leak"
    severity: "high"
    type: "ResourceLeakRisk"
    file: "example1_simple_leak.py"
    function: "read_config"
    location:
      start_line: 10
      end_line: 10
      start_col: 4
      end_col: 31
    description: "文件句柄未关闭，缺少 close() 调用"
    root_cause: "未使用 with 语句或 finally 块"
    cwe_id: "CWE-404"
    difficulty: "easy"
    related_bugs: ["BUG_0001"]
```

## 设计原则

### 1. 真实性
- 所有 bug 样本来源于真实项目或常见反模式
- 避免人为构造的不切实际场景

### 2. 多样性
- 覆盖 5 大类别、10+ 子类别
- 包含不同严重程度和难度
- 包含 positive（有 bug）和 negative（正确）样本

### 3. 可扩展性
- 标准化的目录结构
- YAML 格式标注，易于添加新样本
- 自动化构建和评估流程

### 4. 可追溯性
- 每个 bug 关联真实项目中的 Bug ID
- 详细的 root_cause 和 description
- CWE 分类标准

## 评估指标

### Precision (精确率)
```
Precision = TP / (TP + FP)
```
检测结果中真实 bug 的比例（越高越好）

### Recall (召回率)
```
Recall = TP / (TP + FN)
```
真实 bug 中被检测到的比例（越高越好）

### F1 Score
```
F1 = 2 * (Precision * Recall) / (Precision + Recall)
```
综合指标，平衡精确率和召回率

### Bug 匹配规则

检测的 bug 与 ground truth 匹配标准：
1. **文件路径匹配** (40%): 相同文件或包含关系
2. **函数名匹配** (40%): 完全相同
3. **行号接近** (20%): 差异 ≤ 5 行

相似度 ≥ 0.7 视为匹配成功。

## 预期性能目标

| 指标 | Stage 1 (仅 Layer 1) | Stage 2 目标 (Layer 1+2) |
|------|---------------------|------------------------|
| Precision | ~60% | 80%+ |
| Recall | ~40% | 70%+ |
| F1 Score | ~0.48 | 0.75+ |

## 改进路线图

### ✅ 已完成 (v0.2)
- [x] 基础架构搭建
- [x] 5 大类别完整覆盖
- [x] 45 个 bug 样本（超过 30+ 目标）
- [x] 11/15 已知 bug 覆盖 (73.3%)
- [x] 自动化评估脚本

### 后续优化
- [ ] 增加 Hard 难度样本（目前仅 4 个）
- [ ] 扩展 negative 样本（提高当前 7 个）
- [ ] 覆盖剩余 4 个已知 bug (BUG_0003, 0004, 0006, 0015)
- [ ] 添加更多子类别:
  - deadlock_risk (死锁风险)
  - async_await_misuse (async/await 误用)
  - deprecated_api_usage (废弃 API)
- [ ] 从真实开源项目提取样本

## 贡献指南

### 添加新 Bug 样本

1. 在相应类别下创建 positive 和 negative 示例
2. 在 `positive/metadata.yaml` 中添加标注
3. 运行 `python build_ground_truth.py` 重新生成
4. 更新 PROGRESS.md

### Bug 样本要求

- **真实性**: 基于真实项目或常见反模式
- **完整性**: 包含完整的函数上下文
- **注释清晰**: 标注 bug 位置和原因
- **可复现**: 提供触发条件说明

## 版本历史

- **v0.1 (2025-10-19)**:
  - 初始版本
  - 10 个 bug 样本（file_leak + thread_pool_leak）
  - 完整评估系统

- **v0.2 (2025-10-19)**:
  - 扩展到 45 个 bug 样本
  - 新增 3 个类别（逻辑控制流、安全漏洞、API 设计）
  - 覆盖 11/15 已知 bug (73.3%)
  - Stage 2 扩展完成 ✅

## 许可证

MIT License

---

**创建者**: Claude & hwuu
**项目**: PyScan v2.0
**最后更新**: 2025-10-19
**状态**: Stage 2 Benchmark 扩展完成 ✅
