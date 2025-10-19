# PyScan Benchmark 测试集

**版本**: v2.0  
**创建日期**: 2025-10-19  
**总 Bug 数**: 105  
**覆盖类别**: 8 大类，20 子类别

---

## 概述

本目录包含 PyScan 的 benchmark 测试集，用于评估 bug 检测的准确性（Precision 和 Recall）。

Benchmark v2.0 包含 **105 个精心标注的 Python bugs**，覆盖资源管理、并发安全、错误处理、安全漏洞等 8 大类别，旨在全面评估 PyScan 的检测能力。

---

## Bug 统计

### 按类别分布

| 类别 | Bug 数 | 占比 |
|------|--------|------|
| 资源管理 (resource_management) | 17 | 16.2% |
| 并发安全 (concurrency) | 17 | 16.2% |
| 注入漏洞 (injection_flaws) | 18 | 17.1% |
| 错误处理 (error_handling) | 15 | 14.3% |
| 数据流问题 (data_flow_issues) | 15 | 14.3% |
| 输入验证 (input_validation) | 10 | 9.5% |
| 类型安全 (type_safety) | 7 | 6.7% |
| API 使用 (api_usage) | 6 | 5.7% |
| **Total** | **105** | **100%** |

### 按严重级别分布

- Critical: 14 (13.3%)
- High: 58 (55.2%)
- Medium: 27 (25.7%)
- Low: 6 (5.7%)

### 按难度分布

- Easy: 36 (34.3%)
- Medium: 43 (41.0%)
- Hard: 26 (24.7%)

---

## 使用方法

### 1. 运行 PyScan 扫描

```bash
# 扫描所有类别
python -m pyscan benchmark/categories -o benchmark_report.json

# 扫描单个类别
python -m pyscan benchmark/categories/01_resource_management -o resource_report.json
```

### 2. 查看检测结果

```bash
# 统计检测到的 bugs
python -c "import json; r=json.load(open('benchmark_report.json')); print(f'Total bugs: {len(r[\"bugs\"])}')"
```

---

## 最新评估结果

**评估日期**: 2025-10-19

- **检测到**: 132 bugs
- **Ground Truth**: 105 bugs  
- **初步观察**: 存在一定误报，需详细匹配分析
- **详细报告**: 查看 [EVALUATION_SUMMARY.md](./EVALUATION_SUMMARY.md)

---

## 版本历史

### v2.0 (2025-10-19)
- ✅ 达成 105 bugs 目标
- ✅ 覆盖 8 大类别，20 子类别
- ✅ 完成首次完整 benchmark 评估

### v1.0 (2025-10-17)
- ✅ 初始版本，85 bugs

---

**最后更新**: 2025-10-19
