# Benchmark Phase 2 实施进展

## 概述

**阶段**: Phase 2
**状态**: 已完成 ✅
**日期**: 2025-10-19
**目标**: 扩展到 5 大类，达到 45+ bug 样本

---

## 完成情况

### 总体统计

| 指标 | 目标 | 实际 | 完成度 |
|------|------|------|--------|
| Bug 样本数 | 30+ | 45 | 150% ✅ |
| 大类别数 | 5 | 5 | 100% ✅ |
| 已知 Bug 覆盖 | - | 11/15 (73.3%) | - |
| Positive 文件 | - | 14 | - |
| Negative 文件 | - | 7 | - |

### 按类别统计

| 类别 | Bug 数 | Positive 文件 | Negative 文件 | 状态 |
|------|--------|--------------|--------------|------|
| 资源管理 (Resource Lifecycle) | 10 | 5 | 3 | ✅ |
| - file_leak | 7 | 3 | 2 | ✅ |
| - thread_pool_leak | 3 | 2 | 1 | ✅ |
| 并发与线程安全 (Concurrency & Thread Safety) | 6 | 2 | 1 | ✅ |
| - race_condition | 6 | 2 | 1 | ✅ |
| 错误与异常处理 (Error & Exception Handling) | 10 | 3 | 1 | ✅ |
| - exception_catching / resource_cleanup | 10 | 3 | 1 | ✅ |
| 注入漏洞 (Injection Flaws) | 9 | 2 | 1 | ✅ |
| - path_traversal | 9 | 2 | 1 | ✅ |
| 输入验证与数据校验 (Input Validation) | 10 | 2 | 1 | ✅ |
| - api_input_validation | 10 | 2 | 1 | ✅ |
| **总计** | **45** | **14** | **7** | **100%** |

### 按严重程度统计

| 严重程度 | Bug 数 | 占比 |
|---------|--------|------|
| High | 31 | 68.9% |
| Medium | 13 | 28.9% |
| Low | 1 | 2.2% |

### 按难度统计

| 难度 | Bug 数 | 占比 |
|------|--------|------|
| Easy | 11 | 24.4% |
| Medium | 23 | 51.1% |
| Hard | 4 | 8.9% |
| High | 7 | 15.6% |

---

## 已实现的 Bug 类型详情

### 1. 资源管理错误 (10 bugs) ✅

#### File Leak (7 bugs)
- ✅ RM-FILE-001: 简单文件未关闭
  - 文件: `01_resource_management/file_leak/positive/example1_simple_leak.py`
  - 函数: `read_config`
  - 难度: Easy

- ✅ RM-FILE-002: 日志文件未关闭
  - 文件: `01_resource_management/file_leak/positive/example1_simple_leak.py`
  - 函数: `write_log`
  - 难度: Easy

- ✅ RM-FILE-003: 异常路径下未关闭
  - 文件: `01_resource_management/file_leak/positive/example2_exception_path.py`
  - 函数: `process_data_file`
  - 难度: Medium

- ✅ RM-FILE-004: 多个 return 路径
  - 文件: `01_resource_management/file_leak/positive/example2_exception_path.py`
  - 函数: `load_config_with_fallback`
  - 难度: Medium

- ✅ RM-FILE-005: 直接使用未保存引用
  - 文件: `01_resource_management/file_leak/positive/example3_direct_use.py`
  - 函数: `quick_write`
  - 难度: Medium

- ✅ RM-FILE-006: 链式调用
  - 文件: `01_resource_management/file_leak/positive/example3_direct_use.py`
  - 函数: `chain_operations`
  - 难度: Medium

- ✅ RM-FILE-007: 嵌套调用
  - 文件: `01_resource_management/file_leak/positive/example3_direct_use.py`
  - 函数: `nested_open`
  - 难度: Medium

#### Thread Pool Leak (3 bugs)
- ✅ RM-POOL-001: ThreadPoolExecutor 未 shutdown
  - 文件: `01_resource_management/thread_pool_leak/positive/example1_no_shutdown.py`
  - 函数: `run_tasks_simple`
  - 难度: Easy

- ✅ RM-POOL-002: 单任务线程池未关闭
  - 文件: `01_resource_management/thread_pool_leak/positive/example1_no_shutdown.py`
  - 函数: `run_single_task`
  - 难度: Easy

- ✅ RM-POOL-003: 异步函数泄露（**BUG_0010 类型**）
  - 文件: `01_resource_management/thread_pool_leak/positive/example2_async_leak.py`
  - 函数: `run_in_thread_pool`
  - 难度: Medium
  - 关联: BUG_0010

---

### 2. 并发问题 (6 bugs) ✅

#### Race Condition (6 bugs)
- ✅ CONC-RACE-001: 全局变量 counter 竞态
  - 文件: `02_concurrency/race_condition/positive/example1_global_var.py`
  - 函数: `increment_counter`
  - 难度: Easy

- ✅ CONC-RACE-002: 全局字典竞态
  - 文件: `02_concurrency/race_condition/positive/example1_global_var.py`
  - 函数: `update_cache`
  - 难度: Easy

- ✅ CONC-RACE-003: 复合操作竞态
  - 文件: `02_concurrency/race_condition/positive/example1_global_var.py`
  - 函数: `get_and_increment`
  - 难度: Medium

- ✅ CONC-RACE-004: 全局对象成员竞态（**BUG_0005 类型**）
  - 文件: `02_concurrency/race_condition/positive/example2_class_member.py`
  - 函数: `initialize_detector`
  - 难度: Medium
  - 关联: BUG_0005

- ✅ CONC-RACE-005: 嵌套属性字典竞态
  - 文件: `02_concurrency/race_condition/positive/example2_class_member.py`
  - 函数: `update_config`
  - 难度: Medium

- ✅ CONC-RACE-006: 实例变量竞态
  - 文件: `02_concurrency/race_condition/positive/example2_class_member.py`
  - 函数: `handle_request`
  - 难度: Medium

---

### 3. 逻辑控制流 (10 bugs) ✅

#### Exception Catching / Resource Cleanup (10 bugs)
- ✅ EXC-CLEAN-001: 文件异常时未关闭
  - 文件: `03_error_handling/resource_cleanup/positive/example1_resource_cleanup.py`
  - 函数: `read_and_process_file`
  - 难度: Medium
  - 关联: BUG_0007

- ✅ EXC-CLEAN-002: 网络响应和文件异常未关闭
  - 文件: `03_error_handling/resource_cleanup/positive/example1_resource_cleanup.py`
  - 函数: `download_and_save`
  - 难度: Medium
  - 关联: BUG_0007

- ✅ EXC-CLEAN-003: 数据库连接异常未关闭
  - 文件: `03_error_handling/resource_cleanup/positive/example1_resource_cleanup.py`
  - 函数: `connect_and_query`
  - 难度: Medium
  - 关联: BUG_0007

- ✅ EXC-CATCH-001: 捕获过于宽泛的 Exception
  - 文件: `03_error_handling/exception_catching/positive/example2_exception_type.py`
  - 函数: `parse_config`
  - 难度: Medium
  - 关联: BUG_0008

- ✅ EXC-CATCH-002: 捕获错误的异常类型
  - 文件: `03_error_handling/exception_catching/positive/example2_exception_type.py`
  - 函数: `divide_numbers`
  - 难度: Easy
  - 关联: BUG_0008

- ✅ EXC-CATCH-003: 异常处理不完整
  - 文件: `03_error_handling/exception_catching/positive/example2_exception_type.py`
  - 函数: `read_integer_from_file`
  - 难度: Medium
  - 关联: BUG_0008

- ✅ EXC-CATCH-004: 裸 except 掩盖所有异常
  - 文件: `03_error_handling/exception_catching/positive/example2_exception_type.py`
  - 函数: `process_user_input`
  - 难度: Easy
  - 关联: BUG_0008

- ✅ EXC-CLEAN-004: 锁缺少 finally 释放
  - 文件: `03_error_handling/resource_cleanup/positive/example3_finally_missing.py`
  - 函数: `acquire_and_use_lock`
  - 难度: Medium
  - 关联: BUG_0009

- ✅ EXC-CLEAN-005: 文件正常关闭但异常未关闭
  - 文件: `03_error_handling/resource_cleanup/positive/example3_finally_missing.py`
  - 函数: `manual_file_handling`
  - 难度: Easy
  - 关联: BUG_0009

- ✅ EXC-CLEAN-006: 标志异常时未重置
  - 文件: `03_error_handling/resource_cleanup/positive/example3_finally_missing.py`
  - 函数: `set_flag_and_process`
  - 难度: Medium
  - 关联: BUG_0009

---

### 4. 安全漏洞 (9 bugs) ✅

#### Path Traversal (9 bugs)
- ✅ INJ-PATH-001: 用户输入直接拼接路径
  - 文件: `05_injection_flaws/path_traversal/positive/example1_path_injection.py`
  - 函数: `read_user_file`
  - 难度: High
  - 关联: BUG_0014

- ✅ INJ-PATH-002: file_id 直接拼接路径
  - 文件: `05_injection_flaws/path_traversal/positive/example1_path_injection.py`
  - 函数: `download_file`
  - 难度: High
  - 关联: BUG_0014

- ✅ INJ-PATH-003: 路径检查不足
  - 文件: `05_injection_flaws/path_traversal/positive/example1_path_injection.py`
  - 函数: `serve_static_file`
  - 难度: High
  - 关联: BUG_0014

- ✅ INJ-PATH-004: 文件名未验证
  - 文件: `05_injection_flaws/path_traversal/positive/example1_path_injection.py`
  - 函数: `delete_user_upload`
  - 难度: Medium
  - 关联: BUG_0014

- ✅ INJ-PATH-005: 模板名称未验证
  - 文件: `05_injection_flaws/path_traversal/positive/example1_path_injection.py`
  - 函数: `load_template`
  - 难度: High
  - 关联: BUG_0014

- ✅ INJ-PATH-006: TOCTOU 漏洞
  - 文件: `05_injection_flaws/path_traversal/positive/example2_symlink_attack.py`
  - 函数: `safe_write_to_user_dir`
  - 难度: Hard
  - 关联: BUG_0014

- ✅ INJ-PATH-007: 符号链接未检查
  - 文件: `05_injection_flaws/path_traversal/positive/example2_symlink_attack.py`
  - 函数: `read_config_file`
  - 难度: Hard
  - 关联: BUG_0014

- ✅ INJ-PATH-008: Zip Slip 漏洞
  - 文件: `05_injection_flaws/path_traversal/positive/example2_symlink_attack.py`
  - 函数: `extract_archive_to_user_space`
  - 难度: Hard
  - 关联: BUG_0014

- ✅ INJ-PATH-009: 检查后删除前 TOCTOU
  - 文件: `05_injection_flaws/path_traversal/positive/example2_symlink_attack.py`
  - 函数: `check_and_delete_temp_file`
  - 难度: Hard

---

### 5. API 设计 (10 bugs) ✅

#### API Input Validation (10 bugs)
- ✅ VAL-INPUT-001: 缺少参数校验
  - 文件: `04_input_validation/api_input_validation/positive/example1_missing_validation.py`
  - 函数: `create_user`
  - 难度: Medium
  - 关联: BUG_0012

- ✅ VAL-INPUT-002: 缺少配置键白名单
  - 文件: `04_input_validation/api_input_validation/positive/example1_missing_validation.py`
  - 函数: `update_config`
  - 难度: High
  - 关联: BUG_0012

- ✅ VAL-INPUT-003: 缺少角色验证
  - 文件: `04_input_validation/api_input_validation/positive/example1_missing_validation.py`
  - 函数: `set_user_role`
  - 难度: High
  - 关联: BUG_0012, BUG_0013

- ✅ VAL-INPUT-004: 缺少范围验证
  - 文件: `04_input_validation/api_input_validation/positive/example1_missing_validation.py`
  - 函数: `search_users`
  - 难度: Medium
  - 关联: BUG_0012

- ✅ VAL-INPUT-005: 缺少路径验证
  - 文件: `04_input_validation/api_input_validation/positive/example1_missing_validation.py`
  - 函数: `delete_file`
  - 难度: High
  - 关联: BUG_0012

- ✅ VAL-INPUT-006: 返回类型不一致
  - 文件: `04_input_validation/api_input_validation/positive/example2_inconsistent_return.py`
  - 函数: `get_user_by_id`
  - 难度: Medium
  - 关联: BUG_0013

- ✅ VAL-INPUT-007: 空列表返回 int 非空返回 float
  - 文件: `04_input_validation/api_input_validation/positive/example2_inconsistent_return.py`
  - 函数: `calculate_average`
  - 难度: Easy
  - 关联: BUG_0013

- ✅ VAL-INPUT-008: 找到返回 list 未找到返回 bool
  - 文件: `04_input_validation/api_input_validation/positive/example2_inconsistent_return.py`
  - 函数: `find_items`
  - 难度: Easy
  - 关联: BUG_0013

- ✅ VAL-INPUT-009: 成功返回 dict 失败返回 str
  - 文件: `04_input_validation/api_input_validation/positive/example2_inconsistent_return.py`
  - 函数: `parse_json_response`
  - 难度: Medium
  - 关联: BUG_0013

- ✅ VAL-INPUT-010: 返回类型取决于 default 参数
  - 文件: `04_input_validation/api_input_validation/positive/example2_inconsistent_return.py`
  - 函数: `get_config_value`
  - 难度: Medium
  - 关联: BUG_0013

---

## 覆盖的已知 Bug

当前 benchmark 已覆盖报告中的以下 bug:

| Bug ID | 类别 | Benchmark 对应 | 覆盖状态 |
|--------|------|---------------|---------|
| BUG_0001 | 资源管理 | RM-FILE-001~007 (file_leak) | ✅ |
| BUG_0002 | 并发 | CONC-RACE-004~006 (race_condition) | ✅ |
| BUG_0005 | 并发 | CONC-RACE-004 (race_condition) | ✅ |
| BUG_0007 | 逻辑控制流 | EXC-CLEAN-001~003 (exception_logic_error) | ✅ |
| BUG_0008 | 逻辑控制流 | EXC-CATCH-001~007 (exception_logic_error) | ✅ |
| BUG_0009 | 逻辑控制流 | EXC-CLEAN-004~010 (exception_logic_error) | ✅ |
| BUG_0010 | 资源管理 | RM-POOL-003 (thread_pool_leak) | ✅ |
| BUG_0011 | 资源管理 | RM-FILE-005~007 (file_leak) | ✅ |
| BUG_0012 | API 设计 | VAL-INPUT-001~005 (public_api_no_validation) | ✅ |
| BUG_0013 | API 设计 | VAL-INPUT-006~005 (public_api_no_validation) | ✅ |
| BUG_0014 | 安全漏洞 | INJ-PATH-001~009 (path_traversal) | ✅ |
| BUG_0003 | 并发 | - | ❌ Phase 3 计划 |
| BUG_0004 | 异步 | - | ❌ Phase 3 计划 |
| BUG_0006 | API 设计 | - | ❌ Phase 3 计划 |
| BUG_0015 | 资源管理 | - | ❌ Phase 3 计划 |

**覆盖率**: 11/15 (73.3%)

---

## 验收标准达成情况

| 标准 | 目标 | 实际 | 状态 |
|------|------|------|------|
| Bug 样本数 | 30+ | 45 | ✅ 超额完成 (150%) |
| 大类别覆盖 | 5 | 5 | ✅ 100% |
| 已知 Bug 覆盖 | - | 11/15 (73.3%) | ✅ |
| ground_truth.json | 正确生成 | 正确生成 | ✅ |
| 文档完整性 | SUMMARY, PROGRESS | 完整 | ✅ |

---

## 里程碑达成 ✅

### ✅ 目标 1: 30+ 样本
- **实际**: 45 bugs
- **状态**: 超额完成 (150%)

### ✅ 目标 2: 5 个类别全覆盖
- **实际**: 5/5 (100%)
- **状态**: 完成

### ✅ 目标 3: 覆盖主要已知 Bug
- **实际**: 11/15 (73.3%)
- **状态**: 大部分完成

---

## 文件清单

```
benchmarks/
├── categories/
│   ├── 05_logic_and_control_flow/
│   │   └── exception_logic_error/
│   │       ├── positive/      # 3 files, 10 bugs
│   │       └── negative/      # 1 file
│   ├── 01_resource_management/
│   │   ├── file_leak/
│   │   │   ├── positive/      # 3 files, 7 bugs
│   │   │   └── negative/      # 2 files
│   │   └── thread_pool_leak/
│   │       ├── positive/      # 2 files, 3 bugs
│   │       └── negative/      # 1 file
│   ├── 05_injection_flaws/
│   │   └── path_traversal/
│   │       ├── positive/      # 2 files, 9 bugs
│   │       └── negative/      # 1 file
│   ├── 02_concurrency/
│   │   └── race_condition/
│   │       ├── positive/      # 2 files, 6 bugs
│   │       └── negative/      # 1 file
│   └── 21_api_design/
│       └── public_api_no_validation/
│           ├── positive/      # 2 files, 10 bugs
│           └── negative/      # 1 file
├── ground_truth.json          # 45 bugs
├── build_ground_truth.py
├── evaluation/
│   └── evaluate.py
├── README.md
├── SUMMARY.md
└── PROGRESS.md
```

---

## 下一步计划

### 未覆盖的已知 Bug
| Bug ID | 原因 | 建议 |
|--------|------|------|
| BUG_0003 | 需要特定类型的并发场景 | Phase 3 添加 deadlock_risk 子类别 |
| BUG_0004 | 需要异步代码示例 | Phase 3 添加 async_await_misuse 子类别 |
| BUG_0006 | 需要特定的 API 使用场景 | Phase 3 添加 deprecated_api_usage 子类别 |
| BUG_0015 | 需要更复杂的资源管理场景 | Phase 3 扩展 resource_and_context 类别 |

### Phase 3 优先任务
1. **并发问题 - deadlock_risk** (4 bugs) - 对应 BUG_0003
2. **异步/协程 - async_await_misuse** (6 bugs) - 对应 BUG_0004
3. **API 设计 - deprecated_api_usage** (4 bugs) - 对应 BUG_0006
4. **资源管理 - complex_resource_leak** (5 bugs) - 对应 BUG_0015

---

**更新日期**: 2025-10-19
**状态**: Phase 2 完成 ✅
**下一步**: 启动 Phase 3 规划，目标 80+ bug 样本，覆盖所有 15 个已知 Bug
