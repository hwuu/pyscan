# PyScan Benchmark 下一步计划

**文档版本**: v1.0
**日期**: 2025-10-19
**当前状态**: Phase 2 已完成 ✅
**下一阶段**: Phase 3 规划与启动

---

## 1. 当前状态总结

### 1.1 Phase 2 完成情况 ✅

**统计数据**:
- **Bug 样本数**: 45 bugs (目标 50+, 完成度 90%)
- **大类别覆盖**: 5/8 (62.5%)
- **已知 Bug 覆盖**: 11/15 (73.3%)
- **Positive 文件**: 14
- **Negative 文件**: 7

**已完成的 5 个类别**:
1. **01_resource_management**: 10 bugs (file_leak: 7, thread_pool_leak: 3)
2. **02_concurrency**: 6 bugs (race_condition: 6)
3. **03_error_handling**: 10 bugs (exception_catching: 4, resource_cleanup: 6)
4. **04_input_validation**: 10 bugs (api_input_validation: 10)
5. **05_injection_flaws**: 9 bugs (path_traversal: 9)

**待完成的 3 个类别**:
- **06_data_flow**: 0 bugs (目录已创建)
- **07_type_safety**: 0 bugs (目录已创建)
- **08_api_usage**: 0 bugs (目录已创建)

### 1.2 Gap Analysis (差距分析)

#### Phase 2 目标 vs 实际

| 指标 | 设计目标 | 实际完成 | 差距 | 原因 |
|------|---------|---------|------|------|
| Bug 总数 | 50+ | 45 | -5 | 部分子类别未实现 |
| 类别 1 (资源管理) | 12 | 10 | -2 | 缺少 RM-NET-001~002 |
| 类别 2 (并发) | 10 | 6 | -4 | 缺少 CONC-DEAD, CONC-ASYNC |
| 类别 3 (错误处理) | 8 | 10 | +2 | 超额完成 ✅ |
| 类别 4 (输入验证) | 5 | 10 | +5 | 超额完成 ✅ |
| 类别 5 (注入漏洞) | 10 | 9 | -1 | 缺少 INJ-CMD, INJ-SQL |
| 类别 6 (数据流) | 5 | 0 | -5 | 未启动 |
| 类别 7 (类型安全) | 0 (Phase 3) | 0 | 0 | 按计划 |
| 类别 8 (API 使用) | 0 (Phase 3) | 0 | 0 | 按计划 |

#### 未覆盖的已知 Bug

| Bug ID | 原因 | 对应类别/子类别 |
|--------|------|----------------|
| BUG_0003 | 需要死锁场景 | 02_concurrency/deadlock_risk |
| BUG_0004 | 需要异步场景 | 02_concurrency/async_await_misuse |
| BUG_0006 | 需要废弃 API | 08_api_usage/deprecated_api |
| BUG_0015 | 需要复杂资源管理 | 01_resource_management/network_leak |

---

## 2. Phase 3 目标与范围

### 2.1 核心目标

**主要目标**:
- ✅ 补齐 Phase 2 缺失的 5 bugs (达到 50+)
- ✅ 扩展到 80+ bugs
- ✅ 覆盖全部 8 个类别
- ✅ 覆盖全部 15 个已知 Bug

**次要目标**:
- 提升 Precision ≥ 70%
- 提升 Recall ≥ 60%
- 增加 Negative 样本到 15+

### 2.2 实施范围

#### 第一优先级: 补齐 Phase 2 缺口 (5 bugs)

**目标**: 达到 Phase 2 原定的 50 bugs

1. **类别 1 - 资源管理** (+2 bugs)
   - RM-NET-001: Socket 未关闭
   - RM-NET-002: HTTP 连接未关闭

2. **类别 2 - 并发** (+2 bugs)
   - CONC-DEAD-001: 嵌套锁顺序不一致 (对应 BUG_0003)
   - CONC-ASYNC-001: 忘记 await (对应 BUG_0004)

3. **类别 5 - 注入漏洞** (+1 bug)
   - INJ-CMD-001: os.system 拼接 (高危)

#### 第二优先级: 扩展已有类别 (15 bugs)

**目标**: 补充高优先级 bugs,达到 65 bugs

1. **类别 1 - 资源管理** (+5 bugs)
   - RM-NET-003~006: 数据库、Session、SMTP 等 (4 bugs)
   - RM-SYNC-001: 锁未释放 (1 bug)

2. **类别 2 - 并发** (+6 bugs)
   - CONC-RACE-007~009: 单例竞态、懒加载竞态等 (3 bugs)
   - CONC-DEAD-002~003: 回调锁、锁内等待 (2 bugs)
   - CONC-ASYNC-002~003: 异步阻塞、Event loop (1 bug)

3. **类别 5 - 注入漏洞** (+4 bugs)
   - INJ-CMD-002~003: subprocess shell=True, eval (2 bugs)
   - INJ-SQL-001~002: 字符串拼接 SQL (2 bugs)

#### 第三优先级: 新增 3 个类别 (20 bugs)

**目标**: 覆盖 8/8 类别,达到 85 bugs

1. **类别 6 - 数据流问题** (5 bugs)
   - DATA-INIT-001~002: 条件分支未初始化、循环外未初始化 (2 bugs)
   - DATA-NULL-001~002: Optional 未检查、函数返回 None (2 bugs)
   - DATA-FLOW-004: 递归无终止条件 (1 bug)

2. **类别 7 - 类型安全** (8 bugs)
   - TYPE-MIS-001~003: 参数/返回类型不匹配 (3 bugs)
   - TYPE-API-001~002: 可变默认参数、继承签名不一致 (2 bugs)
   - TYPE-MIS-004~006: 容器类型、Union 未收窄等 (3 bugs)

3. **类别 8 - API 使用** (7 bugs)
   - API-DEP-001~002: os.popen, platform.dist (2 bugs, 对应 BUG_0006)
   - API-DANGER-001~005: pickle, yaml, random 等 (5 bugs)

---

## 3. 分步实施计划

### 3.1 Step 1: 补齐 Phase 2 缺口 (1-2 天)

**目标**: 45 → 50 bugs

**任务清单**:
- [ ] RM-NET-001~002: 网络泄露 (2 bugs)
  - 子类别: `01_resource_management/network_leak/`
  - 文件: positive/example1_socket_leak.py, example2_http_leak.py
  - 难度: Medium

- [ ] CONC-DEAD-001: 死锁风险 (1 bug)
  - 子类别: `02_concurrency/deadlock_risk/`
  - 文件: positive/example1_nested_locks.py
  - 难度: High
  - 关联: BUG_0003

- [ ] CONC-ASYNC-001: 异步问题 (1 bug)
  - 子类别: `02_concurrency/async_await_misuse/`
  - 文件: positive/example1_missing_await.py
  - 难度: Easy
  - 关联: BUG_0004

- [ ] INJ-CMD-001: 命令注入 (1 bug)
  - 子类别: `05_injection_flaws/command_injection/`
  - 文件: positive/example1_os_system.py
  - 难度: Critical

**验收标准**:
- Bug 总数 = 50
- 覆盖 BUG_0003, BUG_0004
- ground_truth.json 更新

### 3.2 Step 2: 扩展已有类别 (2-3 天)

**目标**: 50 → 65 bugs

**任务优先级**:

**P0 (Critical, 3 bugs)**:
- INJ-CMD-002~003: subprocess shell=True, eval 用户输入
- INJ-SQL-001: 字符串拼接 SQL

**P1 (High, 7 bugs)**:
- RM-NET-003~004: 数据库连接、requests.Session
- RM-SYNC-001: 锁未释放
- CONC-RACE-007: 单例模式竞态
- CONC-DEAD-002: 回调中获取锁
- CONC-ASYNC-002: 异步中阻塞调用

**P2 (Medium, 5 bugs)**:
- RM-NET-005~006: SMTP, FTP 连接
- CONC-RACE-008~009: 懒加载竞态、文件读写竞态
- INJ-SQL-002: % 格式化 SQL

**实施顺序**:
1. 先完成 P0 (Critical) - 1 天
2. 再完成 P1 (High) - 1-2 天
3. 最后 P2 (Medium) - 半天

### 3.3 Step 3: 新增 3 个类别 (3-4 天)

**目标**: 65 → 85 bugs

**任务分配**:

**第 1 天: 类别 6 - 数据流问题 (5 bugs)**
- 子类别 1: `06_data_flow/uninitialized_variable/`
  - DATA-INIT-001~002 (2 bugs)
- 子类别 2: `06_data_flow/none_dereference/`
  - DATA-NULL-001~002 (2 bugs)
- 子类别 3: `06_data_flow/control_flow/`
  - DATA-FLOW-004 (1 bug)

**第 2-3 天: 类别 7 - 类型安全 (8 bugs)**
- 子类别 1: `07_type_safety/type_mismatch/`
  - TYPE-MIS-001~006 (6 bugs)
- 子类别 2: `07_type_safety/api_contract_violation/`
  - TYPE-API-001~002 (2 bugs)

**第 4 天: 类别 8 - API 使用 (7 bugs)**
- 子类别 1: `08_api_usage/deprecated_api/`
  - API-DEP-001~002 (2 bugs, 对应 BUG_0006)
- 子类别 2: `08_api_usage/dangerous_api/`
  - API-DANGER-001~005 (5 bugs)

### 3.4 Step 4: 评估与优化 (1 天)

**目标**: 验证质量,达到验收标准

**任务清单**:
- [ ] 运行 PyScan 扫描 benchmark
- [ ] 生成评估报告
- [ ] 分析 Precision/Recall
- [ ] 优化 bug 样本 (针对 FP/FN)
- [ ] 增加 Negative 样本 (目标 15+)
- [ ] 更新文档

**验收标准**:
- Bug 总数 ≥ 80
- 8 大类别全覆盖
- Precision ≥ 70%
- Recall ≥ 60%
- 覆盖全部 15 个已知 Bug

---

## 4. 资源与时间估算

### 4.1 总体时间估算

| 步骤 | 任务 | Bug 数 | 预计时间 |
|------|------|--------|---------|
| Step 1 | 补齐 Phase 2 | 5 | 1-2 天 |
| Step 2 | 扩展已有类别 | 15 | 2-3 天 |
| Step 3 | 新增 3 个类别 | 20 | 3-4 天 |
| Step 4 | 评估与优化 | - | 1 天 |
| **总计** | **Phase 3 完成** | **40** | **7-10 天** |

### 4.2 里程碑与检查点

**Week 1 (Day 1-3)**:
- ✅ Milestone 1: 达到 50 bugs (补齐 Phase 2)
- ✅ Checkpoint: 覆盖 BUG_0003, BUG_0004

**Week 2 (Day 4-7)**:
- ✅ Milestone 2: 达到 65 bugs (扩展已有类别)
- ✅ Checkpoint: 所有 Critical/High bugs 完成

**Week 3 (Day 8-10)**:
- ✅ Milestone 3: 达到 85 bugs (新增 3 个类别)
- ✅ Checkpoint: 8/8 类别全覆盖,15/15 已知 Bug 覆盖

**Week 3 (Day 11)**:
- ✅ Final Milestone: Phase 3 完成
- ✅ 评估报告发布
- ✅ 启动 Phase 4 规划

---

## 5. 风险与缓解

### 5.1 主要风险

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| **样本质量不足** | 中 | 高 | Code review,参考真实项目 |
| **时间超期** | 中 | 中 | 优先 P0/P1,灵活调整范围 |
| **检测率低** | 中 | 高 | 先评估,再优化样本 |
| **Negative 样本不足** | 高 | 中 | 每个子类别至少 1 个 negative |
| **已知 Bug 难覆盖** | 低 | 高 | 针对性设计样本 |

### 5.2 质量控制

**每个 Bug 样本必须包含**:
- ✅ 完整的 metadata.yaml (id, category, severity, CWE, etc.)
- ✅ 清晰的代码示例 (真实场景)
- ✅ 明确的 bug 位置 (start_line, end_line)
- ✅ 至少 1 个 negative 对照样本

**Code Review Checklist**:
- [ ] Bug 示例是否真实可复现?
- [ ] 元数据是否完整准确?
- [ ] CWE 映射是否正确?
- [ ] 难度评级是否合理?
- [ ] Negative 样本是否足够?

---

## 6. 成功标准

### 6.1 Phase 3 验收标准

**定量指标**:
- ✅ Bug 样本数 ≥ 80
- ✅ 大类别覆盖 = 8/8 (100%)
- ✅ 已知 Bug 覆盖 = 15/15 (100%)
- ✅ Precision ≥ 70%
- ✅ Recall ≥ 60%
- ✅ F1 Score ≥ 0.65
- ✅ Negative 样本 ≥ 15

**定性指标**:
- ✅ 所有 bug 有 CWE 映射
- ✅ 所有子类别有 README
- ✅ ground_truth.json 正确生成
- ✅ 文档完整 (SUMMARY, PROGRESS)

### 6.2 Phase 4 准备

**Phase 3 完成后立即启动**:
- [ ] 分析 Phase 3 评估结果
- [ ] 识别检测短板
- [ ] 制定 Phase 4 详细计划
- [ ] 准备真实项目 bug 提取工具

---

## 7. 下一步行动 (Next Actions)

### 7.1 立即行动 (本周)

**Day 1-2: 启动 Step 1**
1. [ ] 创建 `v2_benchmark_impl_tracking/phase3_progress.md`
2. [ ] 创建子类别目录:
   - `01_resource_management/network_leak/`
   - `02_concurrency/deadlock_risk/`
   - `02_concurrency/async_await_misuse/`
   - `05_injection_flaws/command_injection/`
3. [ ] 实现 5 个 bug 样本 (RM-NET-001~002, CONC-DEAD-001, CONC-ASYNC-001, INJ-CMD-001)
4. [ ] 更新 ground_truth.json
5. [ ] 运行初步评估

**Day 3: Review & Commit**
6. [ ] Code review
7. [ ] 提交 Step 1 完成的代码
8. [ ] 更新 phase3_progress.md

### 7.2 本月目标

**Week 2-3: 完成 Step 2-3**
- [ ] 扩展已有类别到 65 bugs
- [ ] 新增 3 个类别到 85 bugs
- [ ] 全覆盖 15 个已知 Bug

**Week 4: 评估与优化**
- [ ] 完整评估 Phase 3
- [ ] 发布 Benchmark v0.3
- [ ] 启动 Phase 4 规划

---

## 8. 附录

### 8.1 参考资源

- **设计文档**: `v2_benchmark_design_proposal.md`
- **进度跟踪**: `v2_benchmark_impl_tracking/phase2_progress.md`
- **Bug 清单**: `v2_benchmark_design_proposal.md` Section 2.2
- **CWE 标准**: https://cwe.mitre.org/
- **已知 Bug 列表**: `known_bugs_report.md` (如果有)

### 8.2 关键决策

**决策 1**: Phase 3 是否包含所有 105 bugs?
- ❌ 否,Phase 3 目标 80-85 bugs (高优先级)
- ✅ Phase 4 覆盖剩余 20-25 bugs (中低优先级)

**决策 2**: 是否从真实项目提取样本?
- ❌ Phase 3 不强制要求
- ✅ Phase 4 重点从真实项目提取 (50%+)

**决策 3**: Negative 样本比例?
- Phase 2: ~15% (7/45)
- Phase 3 目标: ~18% (15/85)
- Phase 4 目标: ~40% (60/150)

---

**文档版本**: v1.0
**创建日期**: 2025-10-19
**下次更新**: Phase 3 启动时
**维护者**: Claude & hwuu

---

**批准与确认**:
- [ ] 技术方案已确认
- [ ] 时间估算已确认
- [ ] 资源分配已确认
- [ ] 风险已识别
- [ ] 准备启动 Phase 3 ✅
