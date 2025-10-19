# Phase 3 Gap Analysis: 已实现 vs 设计规划

**分析日期**: 2025-10-19
**基准文档**: v2_benchmark_design_proposal.md (Section 2.2)
**当前状态**: Phase 3 Step 2 完成 (65 bugs)

---

## 执行摘要

| 维度 | 设计规划 | 已实现 | 差距 | 完成度 |
|------|---------|--------|------|--------|
| **总 Bug 数** | 105 | 65 | 40 | **61.9%** |
| **大类别数** | 8 | 5 | 3 | **62.5%** |
| **子类别数** | 26 | 13 | 13 | **50.0%** |

**核心差距**:
- ✅ 类别 1-5: 基础安全类别已覆盖 (62.5%)
- ❌ 类别 6-8: 高级分析类别尚未实现 (0%)

---

## 详细对比分析

### 类别 1: 资源生命周期管理 (Resource Lifecycle)

**规划**: 30 bugs (4 个子类别)
**已实现**: 17 bugs (4 个子类别)
**完成度**: 56.7% ✅

| 子类别 | 规划 Bug ID 范围 | 规划数量 | 已实现 Bug ID | 已实现数量 | 差距 | 完成度 |
|-------|----------------|---------|-------------|-----------|-----|--------|
| **1-1: 文件资源泄露** | RM-FILE-001~012 | 12 | RM-FILE-001~007 | 7 | -5 | 58.3% |
| **1-2: 线程池泄露** | RM-POOL-001~006 | 6 | M-TPL-001~003 | 3 | -3 | 50.0% |
| **1-3: 网络连接泄露** | RM-NET-001~008 | 8 | RM-NET-001~004 | 4 | -4 | 50.0% |
| **1-4: 同步原语泄露** | RM-SYNC-001~004 | 4 | RM-SYNC-001~003 | 3 | -1 | 75.0% |

**缺失的 bugs**:

<details>
<summary>文件泄露 (5个)</summary>

- RM-FILE-008: 赋值后未用 (`f = open(); f = None`)
- RM-FILE-009: 返回前未关 (`f=open(); if x: return`)
- RM-FILE-010: finally 缺失
- RM-FILE-011: with 嵌套错误
- RM-FILE-012: close 条件错误

</details>

<details>
<summary>线程池泄露 (3个)</summary>

- RM-POOL-002: ProcessPoolExecutor 未 shutdown
- RM-POOL-005: 循环创建未释放
- RM-POOL-006: 条件创建泄露

</details>

<details>
<summary>网络连接泄露 (4个)</summary>

- RM-NET-003: requests.Session 未关闭 (设计规划版本)
- RM-NET-005: 数据库游标泄露
- RM-NET-007: FTP 连接泄露
- RM-NET-008: Redis 连接泄露

</details>

<details>
<summary>同步原语泄露 (1个)</summary>

- RM-SYNC-004: Condition 未释放 (注意: 当前 RM-SYNC-003 可能对应此项)

</details>

---

### 类别 2: 并发与线程安全 (Concurrency & Thread Safety)

**规划**: 24 bugs (3 个子类别)
**已实现**: 7 bugs (3 个子类别)
**完成度**: 29.2% ⚠️

| 子类别 | 规划 Bug ID 范围 | 规划数量 | 已实现 Bug ID | 已实现数量 | 差距 | 完成度 |
|-------|----------------|---------|-------------|-----------|-----|--------|
| **2-1: 竞态条件** | CONC-RACE-001~010 | 10 | CONC-RACE-007~009 | 3 | -7 | 30.0% |
| **2-2: 死锁风险** | CONC-DEAD-001~006 | 6 | CONC-DEAD-001~003 | 3 | -3 | 50.0% |
| **2-3: 异步协程问题** | CONC-ASYNC-001~008 | 8 | CONC-ASYNC-001 | 1 | -7 | 12.5% |

**缺失的 bugs**:

<details>
<summary>竞态条件 (7个)</summary>

- CONC-RACE-001: 全局变量写入竞态
- CONC-RACE-002: 全局字典竞态
- CONC-RACE-003: 全局列表竞态
- CONC-RACE-004: 类成员变量竞态
- CONC-RACE-005: 类变量竞态
- CONC-RACE-006: 复合操作竞态
- CONC-RACE-010: 文件读写竞态

</details>

<details>
<summary>死锁风险 (3个)</summary>

- CONC-DEAD-004: 循环等待
- CONC-DEAD-005: 条件变量死锁
- CONC-DEAD-006: Join 死锁

</details>

<details>
<summary>异步协程问题 (7个)</summary>

- CONC-ASYNC-002: 同步函数中 await
- CONC-ASYNC-003: 异步中阻塞调用
- CONC-ASYNC-004: Event loop 嵌套
- CONC-ASYNC-005: Task 未 await
- CONC-ASYNC-006: Task 未取消
- CONC-ASYNC-007: async context 泄露
- CONC-ASYNC-008: gather 异常未处理

</details>

---

### 类别 3: 错误与异常处理 (Error & Exception Handling)

**规划**: 16 bugs (2 个子类别)
**已实现**: 10 bugs (2 个子类别)
**完成度**: 62.5% ✅

| 子类别 | 规划 Bug ID 范围 | 规划数量 | 已实现 Bug ID | 已实现数量 | 差距 | 完成度 |
|-------|----------------|---------|-------------|-----------|-----|--------|
| **3-1: 异常捕获问题** | EXC-CATCH-001~010 | 10 | EXC-CATCH-001~004 | 4 | -6 | 40.0% |
| **3-2: 资源清理问题** | EXC-CLEAN-001~006 | 6 | EXC-CLEAN-001~006 | 6 | 0 | 100% ✅ |

**缺失的 bugs**:

<details>
<summary>异常捕获问题 (6个)</summary>

- EXC-CATCH-005: except 仅 pass
- EXC-CATCH-006: 捕获后未记录
- EXC-CATCH-007: 捕获 BaseException
- EXC-CATCH-008: 多余的 except
- EXC-CATCH-009: except 顺序错误
- EXC-CATCH-010: 空 try 块

</details>

---

### 类别 4: 输入验证与数据校验 (Input Validation)

**规划**: 10 bugs (1 个子类别)
**已实现**: 10 bugs (1 个子类别)
**完成度**: 100% ✅ (但 Bug ID 不匹配)

| 子类别 | 规划 Bug ID 范围 | 规划数量 | 已实现 Bug ID | 已实现数量 | 完成度 |
|-------|----------------|---------|-------------|-----------|--------|
| **4-1: API 输入验证** | VAL-INPUT-001~010 | 10 | PI-VAL-001~005, VAL-INPUT-006~010 | 10 | 100% ✅ |

**说明**:
- 已实现的 bugs 与规划的功能对应，但 Bug ID 命名不一致
- PI-VAL-001~005 应重命名为 VAL-INPUT-001~005 以符合设计规范

---

### 类别 5: 注入漏洞 (Injection Flaws)

**规划**: 20 bugs (3 个子类别)
**已实现**: 15 bugs (3 个子类别)
**完成度**: 75.0% ✅

| 子类别 | 规划 Bug ID 范围 | 规划数量 | 已实现 Bug ID | 已实现数量 | 差距 | 完成度 |
|-------|----------------|---------|-------------|-----------|-----|--------|
| **5-1: 路径遍历** | INJ-PATH-001~009 | 9 | EC-PT-001~009, INPUT-PATH-003 | 10 | +1 | 111% ✅ |
| **5-2: 命令注入** | INJ-CMD-001~006 | 6 | INJ-CMD-001~003 | 3 | -3 | 50.0% |
| **5-3: SQL 注入** | INJ-SQL-001~005 | 5 | INJ-SQL-001~002 | 2 | -3 | 40.0% |

**缺失的 bugs**:

<details>
<summary>命令注入 (3个)</summary>

- INJ-CMD-004: os.popen 注入
- INJ-CMD-005: exec 注入
- INJ-CMD-006: compile 注入

</details>

<details>
<summary>SQL 注入 (3个)</summary>

- INJ-SQL-003: execute 拼接
- INJ-SQL-004: ORM raw 注入
- INJ-SQL-005: 动态表名注入

</details>

**说明**:
- 路径遍历实际实现了 10 个 bugs (超出规划 1 个)
- Bug ID 不一致: EC-PT-* 应重命名为 INJ-PATH-*

---

### 类别 6: 数据流问题 (Data Flow Issues) ❌

**规划**: 15 bugs (3 个子类别)
**已实现**: 0 bugs
**完成度**: 0% ❌

| 子类别 | 规划 Bug ID 范围 | 规划数量 | 状态 |
|-------|----------------|---------|------|
| **6-1: 变量初始化** | DATA-INIT-001~006 | 6 | ❌ 未实现 |
| **6-2: None 解引用** | DATA-NULL-001~005 | 5 | ❌ 未实现 |
| **6-3: 控制流问题** | DATA-FLOW-001~004 | 4 | ❌ 未实现 |

**说明**: 这是 Phase 3 Step 3 的核心任务之一

---

### 类别 7: 类型安全 (Type Safety) ❌

**规划**: 10 bugs (2 个子类别)
**已实现**: 0 bugs
**完成度**: 0% ❌

| 子类别 | 规划 Bug ID 范围 | 规划数量 | 状态 |
|-------|----------------|---------|------|
| **7-1: 类型不匹配** | TYPE-MIS-001~006 | 6 | ❌ 未实现 |
| **7-2: API 契约违反** | TYPE-API-001~004 | 4 | ❌ 未实现 |

**说明**: 这是 Phase 3 Step 3 的核心任务之一

---

### 类别 8: API 使用与设计 (API Usage & Design) ❌

**规划**: 10 bugs (2 个子类别)
**已实现**: 0 bugs
**完成度**: 0% ❌

| 子类别 | 规划 Bug ID 范围 | 规划数量 | 状态 |
|-------|----------------|---------|------|
| **8-1: 废弃 API** | API-DEP-001~004 | 4 | ❌ 未实现 |
| **8-2: 危险 API** | API-DANGER-001~006 | 6 | ❌ 未实现 |

**说明**:
- API-DEP-001~002 在 Phase 3 进度文档中提到但未实现
- 对应已知 BUG_0006 (废弃 API 使用)
- 这是 Phase 3 Step 3 的核心任务之一

---

## Phase 3 Step 3 任务清单

### 目标: 65 → 85 bugs (+20 bugs)

根据差距分析，Step 3 需要完成以下任务:

#### 任务分配 (20 bugs)

| 类别 | 子类别 | 新增数量 | 优先级 | 难度 |
|------|--------|---------|--------|------|
| **类别 6** | 变量初始化 | 6 | P1 | Medium |
| **类别 6** | None 解引用 | 5 | P1 | Medium |
| **类别 6** | 控制流问题 | 4 | P2 | Easy |
| **类别 7** | 类型不匹配 | 3 | P2 | Easy |
| **类别 8** | 废弃 API | 2 | P3 | Easy |
| **总计** | - | **20** | - | - |

**说明**:
- 类型安全类别保留 7 个 bugs (TYPE-MIS-004~006, TYPE-API-001~004) 用于 Phase 4
- API 危险类别保留 6 个 bugs (API-DANGER-001~006) 用于 Phase 4

---

## Bug ID 规范化任务

在进入 Step 3 之前，建议规范化以下 Bug ID 以符合设计文档:

| 当前 Bug ID | 应改为 | 数量 | 文件位置 |
|------------|--------|------|---------|
| PI-VAL-* | VAL-INPUT-* | 5 | api_input_validation/positive/metadata.yaml |
| EC-PT-* | INJ-PATH-* | 9 | path_traversal/positive/metadata.yaml |
| M-TPL-* | RM-POOL-* | 3 | thread_pool_leak/positive/metadata.yaml |

**影响**: 需要同步更新 ground_truth.json

---

## 剩余差距 (Phase 4+)

完成 Phase 3 Step 3 后，剩余 **20 bugs** 需在后续阶段完成:

| 类别 | 子类别 | 数量 | 备注 |
|------|--------|------|------|
| 类别 1 | 文件泄露 (补充) | 5 | 高级文件泄露场景 |
| 类别 1 | 线程池泄露 (补充) | 3 | ProcessPoolExecutor, 循环/条件泄露 |
| 类别 1 | 网络泄露 (补充) | 4 | Redis, FTP, Session, Cursor |
| 类别 1 | 同步原语 (补充) | 1 | Condition 高级场景 |
| 类别 2 | 竞态条件 (补充) | 7 | 全局变量、字典、列表竞态 |
| 类别 2 | 死锁 (补充) | 3 | 循环等待、Join 死锁 |
| 类别 2 | 异步 (补充) | 7 | Event loop, Task 管理 |
| 类别 3 | 异常捕获 (补充) | 6 | 高级异常处理模式 |
| 类别 5 | 命令注入 (补充) | 3 | os.popen, exec, compile |
| 类别 5 | SQL 注入 (补充) | 3 | ORM, 动态表名 |
| 类别 7 | 类型安全 (补充) | 7 | Union 收窄、API 契约 |
| 类别 8 | 危险 API | 6 | pickle, yaml, random, assert |

---

## 检测能力评估

### 当前检测层分布 (65 bugs)

| 检测层 | 规划占比 | 预估已实现 | 完成度 |
|--------|---------|-----------|--------|
| Layer 1 | 23.8% (25 bugs) | ~10 bugs | 40% |
| Layer 2 | 47.6% (50 bugs) | ~45 bugs | 90% |
| Layer 2/3 | 23.8% (25 bugs) | ~8 bugs | 32% |
| Layer 3 | 4.8% (5 bugs) | ~2 bugs | 40% |

**观察**:
- Layer 2 (DFG + CFG) 检测能力已得到充分验证 (45 bugs)
- Layer 1 (静态规则) 和 Layer 3 (语义推理) 覆盖不足
- Phase 3 Step 3 应重点补充 Layer 1 易检测 bugs (类别 6-8)

---

## 总结与建议

### ✅ 已完成的成就

1. **核心安全类别完整**: 类别 1-5 覆盖 62.5%
2. **关键漏洞覆盖**: 注入漏洞、并发问题、资源泄露等高危类别已有基础覆盖
3. **质量验证**: 65 个 bugs 均通过 PyScan 检测验证

### ⚠️ 当前差距

1. **数量差距**: 距离 105 bugs 目标还差 40 个 (38.1%)
2. **类别缺失**: 3 个高级分析类别 (数据流、类型、API) 完全未实现
3. **子类别不均**: 并发类别仅完成 29.2%，是五大类别中最低的

### 🎯 Phase 3 Step 3 建议

**目标**: 65 → 85 bugs (+20 bugs)

**实施策略**:
1. **优先级**: 类别 6 (数据流) > 类别 7 (类型) > 类别 8 (API)
2. **难度**: 先易后难，从 Layer 1 bugs 开始
3. **验证**: 每个子类别完成后立即运行 PyScan 检测
4. **质量**: 保持 positive + negative 样本配对

**工作量预估**:
- 类别 6: 15 bugs (6 + 5 + 4) → 2-3 天
- 类别 7: 3 bugs → 0.5 天
- 类别 8: 2 bugs → 0.5 天
- **总计**: 3-4 天完成 Step 3

---

**创建日期**: 2025-10-19
**最后更新**: 2025-10-19 23:05
**下一步**: 开始 Phase 3 Step 3 实施
