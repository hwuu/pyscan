# Benchmark 扩展进展

## 当前状态

**日期**: 2025-10-19
**总 Bug 数**: 45
**已完成类别**: 5/5 (100%) ✅

## 统计信息

### 按类别

| 类别 | Bug 数 | Positive 文件 | Negative 文件 | 状态 |
|------|--------|--------------|--------------|------|
| 09_resource_and_context | 10 | 5 | 3 | ✅ 完成 |
| - file_leak | 7 | 3 | 2 | ✅ |
| - thread_pool_leak | 3 | 2 | 1 | ✅ |
| 13_concurrency | 6 | 2 | 1 | ✅ 完成 |
| - race_condition | 6 | 2 | 1 | ✅ |
| 05_logic_and_control_flow | 10 | 3 | 1 | ✅ 完成 |
| - exception_logic_error | 10 | 3 | 1 | ✅ |
| 10_security | 9 | 2 | 1 | ✅ 完成 |
| - path_traversal | 9 | 2 | 1 | ✅ |
| 21_api_design | 10 | 2 | 1 | ✅ 完成 |
| - public_api_no_validation | 10 | 2 | 1 | ✅ |
| **总计** | **45** | **14** | **7** | **100%** ✅ |

### 按严重程度

- **High**: 31 (68.9%)
- **Medium**: 13 (28.9%)
- **Low**: 1 (2.2%)

### 按难度

- **Easy**: 11 (24.4%)
- **Medium**: 23 (51.1%)
- **Hard**: 4 (8.9%)
- **High**: 7 (15.6%)

## 已实现的 Bug 类型

### 1. 资源管理错误 (10 bugs)

#### File Leak (7 bugs)
- ✅ RM-FL-001: 简单文件未关闭
- ✅ RM-FL-002: 日志文件未关闭
- ✅ RM-FL-003: 异常路径下未关闭
- ✅ RM-FL-004: 多个 return 路径
- ✅ RM-FL-005: 直接使用未保存引用
- ✅ RM-FL-006: 链式调用
- ✅ RM-FL-007: 嵌套调用

#### Thread Pool Leak (3 bugs)
- ✅ RM-TPL-001: ThreadPoolExecutor 未 shutdown
- ✅ RM-TPL-002: 单任务线程池未关闭
- ✅ RM-TPL-003: 异步函数泄露（**BUG_0010 类型**）

### 2. 并发问题 (6 bugs)

#### Race Condition (6 bugs)
- ✅ CONC-RC-001: 全局变量 counter 竞态
- ✅ CONC-RC-002: 全局字典竞态
- ✅ CONC-RC-003: 复合操作竞态
- ✅ CONC-RC-004: 全局对象成员竞态（**BUG_0005 类型**）
- ✅ CONC-RC-005: 嵌套属性字典竞态
- ✅ CONC-RC-006: 实例变量竞态

### 3. 逻辑控制流 (10 bugs)

#### Exception Logic Error (10 bugs)
- ✅ LOGIC-EXC-001: 文件异常时未关闭
- ✅ LOGIC-EXC-002: 网络响应和文件异常未关闭
- ✅ LOGIC-EXC-003: 数据库连接异常未关闭
- ✅ LOGIC-EXC-004: 捕获过于宽泛的 Exception
- ✅ LOGIC-EXC-005: 捕获错误的异常类型
- ✅ LOGIC-EXC-006: 异常处理不完整
- ✅ LOGIC-EXC-007: 裸 except 掩盖所有异常
- ✅ LOGIC-EXC-008: 锁缺少 finally 释放
- ✅ LOGIC-EXC-009: 文件正常关闭但异常未关闭
- ✅ LOGIC-EXC-010: 标志异常时未重置

### 4. 安全漏洞 (9 bugs)

#### Path Traversal (9 bugs)
- ✅ SEC-PT-001: 用户输入直接拼接路径
- ✅ SEC-PT-002: file_id 直接拼接路径
- ✅ SEC-PT-003: 路径检查不足
- ✅ SEC-PT-004: 文件名未验证
- ✅ SEC-PT-005: 模板名称未验证
- ✅ SEC-PT-006: TOCTOU 漏洞（**BUG_0014 类型**）
- ✅ SEC-PT-007: 符号链接未检查
- ✅ SEC-PT-008: Zip Slip 漏洞
- ✅ SEC-PT-009: 检查后删除前 TOCTOU

### 5. API 设计 (10 bugs)

#### Public API No Validation (10 bugs)
- ✅ API-VAL-001: 缺少参数校验（**BUG_0012 类型**）
- ✅ API-VAL-002: 缺少配置键白名单
- ✅ API-VAL-003: 缺少角色验证
- ✅ API-VAL-004: 缺少范围验证
- ✅ API-VAL-005: 缺少路径验证
- ✅ API-RET-001: 返回类型不一致（**BUG_0013 类型**）
- ✅ API-RET-002: 空列表返回 int 非空返回 float
- ✅ API-RET-003: 找到返回 list 未找到返回 bool
- ✅ API-RET-004: 成功返回 dict 失败返回 str
- ✅ API-RET-005: 返回类型取决于 default 参数

## 覆盖的已知 Bug

当前 benchmark 已覆盖报告中的以下 bug:

| Bug ID | 类别 | Benchmark 对应 |
|--------|------|---------------|
| BUG_0001 | 资源管理 | RM-FL-001~007 (file_leak) |
| BUG_0010 | 资源管理 | RM-TPL-003 (thread_pool_leak) |
| BUG_0011 | 资源管理 | RM-FL-005~007 (file_leak) |
| BUG_0002 | 并发 | CONC-RC-004~006 (race_condition) |
| BUG_0005 | 并发 | CONC-RC-004 (race_condition) |
| BUG_0007 | 逻辑控制流 | LOGIC-EXC-001~003 (exception_logic_error) |
| BUG_0008 | 逻辑控制流 | LOGIC-EXC-004~007 (exception_logic_error) |
| BUG_0009 | 逻辑控制流 | LOGIC-EXC-008~010 (exception_logic_error) |
| BUG_0012 | API 设计 | API-VAL-001~005 (public_api_no_validation) |
| BUG_0013 | API 设计 | API-RET-001~005 (public_api_no_validation) |
| BUG_0014 | 安全漏洞 | SEC-PT-001~009 (path_traversal) |

**覆盖率**: 11/15 (73.3%)

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

## 文件清单

```
benchmarks/
├── categories/
│   ├── 05_logic_and_control_flow/
│   │   └── exception_logic_error/
│   │       ├── positive/      # 3 files, 10 bugs
│   │       └── negative/      # 1 file
│   ├── 09_resource_and_context/
│   │   ├── file_leak/
│   │   │   ├── positive/      # 3 files, 7 bugs
│   │   │   └── negative/      # 2 files
│   │   └── thread_pool_leak/
│   │       ├── positive/      # 2 files, 3 bugs
│   │       └── negative/      # 1 file
│   ├── 10_security/
│   │   └── path_traversal/
│   │       ├── positive/      # 2 files, 9 bugs
│   │       └── negative/      # 1 file
│   ├── 13_concurrency/
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
└── PROGRESS.md (本文件)
```

## 优化建议（后续）

### 优先级 2 (可选)
- [ ] 增加更多 Hard 难度样本（当前仅 4 个）
- [ ] 添加更多 negative 样本（提高当前 7 个）
- [ ] 从真实项目提取样本
- [ ] 覆盖剩余 4 个已知 Bug (BUG_0003, 0004, 0006, 0015)

### 未覆盖的已知 Bug
| Bug ID | 原因 | 建议 |
|--------|------|------|
| BUG_0003 | 需要特定类型的并发场景 | 后续添加 deadlock_risk 子类别 |
| BUG_0004 | 需要异步代码示例 | 后续添加 async_await_misuse 子类别 |
| BUG_0006 | 需要特定的 API 使用场景 | 后续添加 deprecated_api_usage 子类别 |
| BUG_0015 | 需要更复杂的资源管理场景 | 后续扩展 resource_and_context 类别 |

---

**更新日期**: 2025-10-19
**状态**: Stage 2 Benchmark 扩展完成 ✅
**下一步**: 运行 PyScan 评估，对比 Stage 1 vs Stage 2 性能
