# PyScan v2.0 实施追踪

本目录用于追踪 PyScan v2.0 的渐进式实施过程。

## 实施策略

采用**渐进式增强**策略，在 v1.0 基础上逐步添加新能力。

## Stage 划分

- **Stage 1**: Layer 1 集成（工具集成：mypy + bandit）
- **Stage 2**: Layer 2 基础（CFG 构建 + 简单可疑点检测）
- **Stage 3**: Layer 4 验证（交叉验证 + 置信度评分）
- **Stage 4**: Layer 2 完善（污点分析）
- **Stage 5**: Layer 2 高级（符号执行）
- **Stage 6**: 优化调优

## 文档规范

每个 Stage 包含两个文档：

- `stageN_plan.md`: 该阶段的详细执行计划
  - 目标
  - 技术方案
  - 实现步骤
  - 验收标准
  - 风险点

- `stageN_result.md`: 该阶段的执行结果
  - 完成情况
  - 测试结果
  - 遇到的问题和解决方案
  - 未完成的 TODO
  - 下一阶段建议

## 当前进度

- [x] Stage 0: 设计文档完成 (`pyscan_v2_design_proposal.md`)
- [ ] Stage 1: Layer 1 集成（进行中）
- [ ] Stage 2: Layer 2 基础
- [ ] Stage 3: Layer 4 验证
- [ ] Stage 4: Layer 2 完善
- [ ] Stage 5: Layer 2 高级
- [ ] Stage 6: 优化调优
