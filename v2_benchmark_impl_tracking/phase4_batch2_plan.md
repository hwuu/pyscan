# Phase 4 Batch 2 实施计划

**创建时间**: 2025-10-19 23:35
**当前状态**: 92 bugs → 目标 105 bugs
**本批次目标**: 新增 13 bugs

---

## 执行摘要

| 维度 | 数值 |
|------|------|
| 当前 bugs | 92 |
| 目标 bugs | 105 |
| 本批次新增 | 13 |
| 预估工期 | 2-3 天 |

---

## Batch 2 Bug 清单 (13 bugs)

基于检测价值和实现难度，选择以下 13 个 bugs：

### 🔥 优先级 P0: 异步并发 (4 bugs)

**原因**: 异步编程是现代 Python 的核心，bugs 检测价值高

| Bug ID | 描述 | 难度 | CWE |
|--------|------|------|-----|
| CONC-ASYNC-002 | 同步函数中使用 await | Easy | CWE-662 |
| CONC-ASYNC-003 | 异步中调用阻塞函数 | Easy | CWE-662 |
| CONC-ASYNC-004 | Event loop 嵌套运行 | Medium | CWE-662 |
| CONC-ASYNC-005 | Task 创建后未 await | Medium | CWE-772 |

**文件**: `benchmark/categories/02_concurrency/async_await_misuse/positive/`
- 扩展 `example1_async_misuse.py`
- 更新 `metadata.yaml`

---

### 🔒 优先级 P1: 类型安全 - API 契约 (4 bugs)

**原因**: API 设计问题导致运行时错误，检测价值高

| Bug ID | 描述 | 难度 | CWE |
|--------|------|------|-----|
| TYPE-API-001 | 可变默认参数 | Easy | CWE-1174 |
| TYPE-API-002 | 继承方法签名不一致 | Medium | CWE-685 |
| TYPE-API-003 | 抽象方法未实现 | Easy | CWE-477 |
| TYPE-API-004 | 返回类型不一致 | Medium | CWE-704 |

**文件**: 新建 `benchmark/categories/07_type_safety/api_contract/positive/`
- `example1_api_contract.py`
- `metadata.yaml`

---

### ⚠️ 优先级 P2: 错误处理扩展 (3 bugs)

**原因**: 补充异常处理的边界场景

| Bug ID | 描述 | 难度 | CWE |
|--------|------|------|-----|
| EXC-CATCH-007 | 捕获 BaseException | Medium | CWE-396 |
| EXC-CATCH-008 | 多余的 except 分支 | Easy | CWE-561 |
| EXC-CATCH-009 | except 顺序错误 | Medium | CWE-484 |

**文件**: 扩展 `benchmark/categories/03_error_handling/exception_catching/positive/example2_exception_type.py`

---

### 💾 优先级 P3: 危险 API 扩展 (2 bugs)

**原因**: 补充安全相关的危险 API 使用

| Bug ID | 描述 | 难度 | CWE |
|--------|------|------|-----|
| API-DANGER-003 | random 用于安全场景 | Easy | CWE-330 |
| API-DANGER-004 | assert 用于数据验证 | Easy | CWE-617 |

**文件**: 扩展 `benchmark/categories/08_api_usage/dangerous_api/positive/example1_pickle_yaml.py`
或新建 `example2_security_api.py`

---

## 实施步骤

### Step 1: 异步并发 (CONC-ASYNC-002~005)
1. 扩展 `async_await_misuse/positive/example1_async_misuse.py`
2. 添加 4 个新函数示例
3. 更新 `metadata.yaml`

### Step 2: 类型安全 (TYPE-API-001~004)
1. 创建新子类别 `type_safety/api_contract/positive/`
2. 编写 `example1_api_contract.py`
3. 创建 `metadata.yaml`

### Step 3: 错误处理 (EXC-CATCH-007~009)
1. 扩展 `exception_catching/positive/example2_exception_type.py`
2. 添加 3 个新函数
3. 更新 `metadata.yaml`

### Step 4: 危险 API (API-DANGER-003~004)
1. 创建 `dangerous_api/positive/example2_security_api.py`
2. 创建 `metadata.yaml`

### Step 5: 验证与提交
1. 重新生成 `ground_truth.json`
2. 运行 PyScan 验证
3. 清理测试文件
4. Git commit

---

## 预期结果

- ✅ 新增 13 bugs (92 → 105)
- ✅ 达成 v2 benchmark 设计目标
- ✅ 覆盖 4 个重要类别的深度扩展
- ✅ 检测层级: Layer 1 (6个), Layer 2 (5个), Layer 3 (2个)

---

## 里程碑

- [ ] Step 1: CONC-ASYNC (4 bugs)
- [ ] Step 2: TYPE-API (4 bugs)
- [ ] Step 3: EXC-CATCH (3 bugs)
- [ ] Step 4: API-DANGER (2 bugs)
- [ ] Step 5: 验证与提交
- [ ] 🎉 **Phase 4 完成**: 105 bugs 达成！

---

**状态**: 规划完成，待执行
**下一步**: 开始 Step 1 - 异步并发 bugs 实现
