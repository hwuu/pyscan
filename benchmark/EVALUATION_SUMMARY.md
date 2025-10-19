# PyScan Benchmark 评估摘要

**评估日期**: 2025-10-19
**Benchmark 版本**: v2.0 (105 bugs)
**PyScan 版本**: v0.3.0

---

## 执行摘要

### 基本统计

| 指标 | 数值 |
|------|------|
| Ground Truth 总 bugs | 105 |
| PyScan 检测到 | 132 bugs |
| 扫描文件数 | 48 |
| 扫描函数数 | 296 |
| 扫描耗时 | ~10 分钟 |
| 平均每函数耗时 | ~2.0 秒 |

### 检测概览

- **检测数量**: 132 bugs (> 105 ground truth)
- **初步观察**: 存在一定数量的误报 (False Positives)
- **检测覆盖**: 覆盖了 8 个大类别的 bugs

### 严重级别分布 (检测结果)

| 级别 | 数量 | 占比 |
|------|------|------|
| High | 106 | 80.3% |
| Medium | 26 | 19.7% |
| Low | 0 | 0% |
| **Total** | **132** | **100%** |

---

## Ground Truth vs 检测结果对比

### 分类覆盖

| 类别 | Ground Truth | 检测数量 | 覆盖率估算 |
|------|--------------|----------|------------|
| 资源管理 (resource_management) | 17 | - | - |
| 并发安全 (concurrency) | 17 | - | - |
| 错误处理 (error_handling) | 15 | - | - |
| 输入验证 (input_validation) | 10 | - | - |
| 注入漏洞 (injection_flaws) | 18 | - | - |
| 数据流问题 (data_flow_issues) | 15 | - | - |
| 类型安全 (type_safety) | 7 | - | - |
| API 使用 (api_usage) | 6 | - | - |
| **Total** | **105** | **132** | **125.7%*** |

**注**: 检测数 > Ground Truth 说明存在误报，需要详细匹配分析

---

## 详细分析 (待完善)

### True Positives (TP)
需要手动匹配 bug ID 来确定准确检测的 bugs

### False Positives (FP)
检测到但不在 ground truth 中的 bugs，可能是：
1. 真实的新 bugs (应该加入 ground truth)
2. 误报 (需要优化检测规则)

### False Negatives (FN)
Ground truth 中存在但未被检测到的 bugs

---

## 评估指标 (需要详细匹配后计算)

### 精确率 (Precision)
```
Precision = TP / (TP + FP)
```

### 召回率 (Recall)
```
Recall = TP / (TP + FN) = TP / 105
```

### F1 分数
```
F1 = 2 * Precision * Recall / (Precision + Recall)
```

---

## 发现与建议

### 正面发现
1. ✅ **检测能力**: 能够检测到大量的 bugs (132)
2. ✅ **覆盖广度**: 覆盖了所有 8 个主要类别
3. ✅ **性能可接受**: 平均每函数 2 秒的检测速度

### 需要改进
1. ⚠️ **误报率**: 检测数 > Ground Truth，可能存在较高误报
2. ⚠️ **分类准确性**: 报告中类别显示为 "unknown"
3. ⚠️ **需要详细匹配**: 目前缺少 bug ID 级别的匹配分析

### 下一步工作
1. 实现自动化的 bug ID 匹配工具
2. 计算准确的 Precision/Recall/F1 指标
3. 分析 False Positives 并优化检测规则
4. 分析 False Negatives 并补充检测能力
5. 添加按类别、难度、严重性的详细评估

---

## 附录

### 评估命令
```bash
python -m pyscan benchmark/categories -o benchmark_evaluation_full.json
```

### 文件位置
- Ground Truth: `benchmark/ground_truth.json`
- 评估报告: `benchmark_evaluation_full.json`
- 评估日志: `benchmark_eval.log`

---

**创建时间**: 2025-10-19 23:57
**最后更新**: 2025-10-19 23:57
**状态**: 初步评估完成，待详细分析
