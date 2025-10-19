# Phase 3 Step 2 实施计划

## 目标

**总目标**: 扩展已有 5 个类别，新增 15 bugs，从 50 → 65

**时间**: 2025-10-19 ~ 2025-10-21 (3 天)

---

## 新增 Bug 分配

### 类别 1: 资源管理 (+5 bugs) → 17 total

**当前**: 12 bugs
**目标**: 17 bugs

#### 网络泄露扩展 (已有 2, +2 = 4)

- [x] RM-NET-001: Socket 未关闭 ✅
- [x] RM-NET-002: HTTP 连接未关闭 ✅
- [ ] **RM-NET-003**: 数据库连接未关闭
  - 文件: `network_leak/positive/example2_database_leak.py`
  - 场景: SQLite/MySQL 连接未 close()
  - CWE: CWE-404
  - 严重性: High

- [ ] **RM-NET-004**: SMTP 连接未关闭
  - 文件: `network_leak/positive/example3_smtp_leak.py`
  - 场景: smtplib 连接未 quit()
  - CWE: CWE-404
  - 严重性: Medium

#### 同步原语泄露 (新子类别, +3)

- [ ] **RM-SYNC-001**: Lock 未释放
  - 子类别: `resource_management/lock_leak/`
  - 文件: `positive/example1_lock_leak.py`
  - 场景: Lock.acquire() 未配对 release()
  - CWE: CWE-667
  - 严重性: High

- [ ] **RM-SYNC-002**: Semaphore 未释放
  - 文件: `lock_leak/positive/example2_semaphore_leak.py`
  - 场景: Semaphore.acquire() 无 release()
  - CWE: CWE-667
  - 严重性: Medium

- [ ] **RM-SYNC-003**: Condition 变量未释放
  - 文件: `lock_leak/positive/example3_condition_leak.py`
  - 场景: Condition.wait() 未在 finally 中释放
  - CWE: CWE-667
  - 严重性: Medium

---

### 类别 2: 并发 (+5 bugs) → 13 total

**当前**: 8 bugs
**目标**: 13 bugs

#### 竞态条件扩展 (已有 6, +3 = 9)

- [ ] **CONC-RACE-007**: 单例模式竞态
  - 文件: `race_condition/positive/example4_singleton_race.py`
  - 场景: 双重检查锁定单例实现错误
  - CWE: CWE-362
  - 严重性: High

- [ ] **CONC-RACE-008**: 懒加载竞态
  - 文件: `race_condition/positive/example5_lazy_init_race.py`
  - 场景: 懒加载初始化无锁保护
  - CWE: CWE-362
  - 严重性: Medium

- [ ] **CONC-RACE-009**: 计数器竞态
  - 文件: `race_condition/positive/example6_counter_race.py`
  - 场景: 非原子操作的计数器递增
  - CWE: CWE-362
  - 严重性: Medium

#### 死锁风险扩展 (已有 1, +2 = 3)

- [x] CONC-DEAD-001: 嵌套锁顺序不一致 ✅
- [ ] **CONC-DEAD-002**: 锁内调用回调
  - 文件: `deadlock_risk/positive/example2_callback_deadlock.py`
  - 场景: 持有锁时调用用户回调函数
  - CWE: CWE-833
  - 严重性: High

- [ ] **CONC-DEAD-003**: 锁内等待异步结果
  - 文件: `deadlock_risk/positive/example3_wait_deadlock.py`
  - 场景: 持有锁时等待 Future.result()
  - CWE: CWE-833
  - 严重性: High

---

### 类别 3: 注入漏洞 (+4 bugs) → 14 total

**当前**: 10 bugs
**目标**: 14 bugs

#### 命令注入扩展 (已有 1, +2 = 3)

- [x] INJ-CMD-001: os.system 拼接用户输入 ✅
- [ ] **INJ-CMD-002**: subprocess shell=True
  - 文件: `command_injection/positive/example2_subprocess_shell.py`
  - 场景: subprocess.Popen(shell=True) 拼接
  - CWE: CWE-78
  - 严重性: Critical

- [ ] **INJ-CMD-003**: eval/exec 执行用户输入
  - 文件: `command_injection/positive/example3_eval_injection.py`
  - 场景: eval(user_input) 代码注入
  - CWE: CWE-94
  - 严重性: Critical

#### SQL 注入 (新子类别, +2)

- [ ] **INJ-SQL-001**: 字符串拼接 SQL
  - 子类别: `injection_flaws/sql_injection/`
  - 文件: `positive/example1_string_concat.py`
  - 场景: f"SELECT * FROM users WHERE id={user_id}"
  - CWE: CWE-89
  - 严重性: Critical

- [ ] **INJ-SQL-002**: format 格式化 SQL
  - 文件: `sql_injection/positive/example2_format_sql.py`
  - 场景: "SELECT * FROM {}".format(table_name)
  - CWE: CWE-89
  - 严重性: Critical

---

### 类别 4: 错误处理 (不扩展)

**当前**: 10 bugs
**保持**: 10 bugs

---

### 类别 5: 输入验证 (+1 bug) → 11 total

**当前**: 10 bugs
**目标**: 11 bugs

#### 路径遍历扩展 (已有 2, +1 = 3)

- [ ] **INPUT-PATH-003**: ZIP 路径遍历
  - 文件: `path_traversal/positive/example3_zip_traversal.py`
  - 场景: zipfile.extractall() 未验证路径
  - CWE: CWE-22
  - 严重性: High

---

## 实施顺序

### Day 1 (2025-10-19 下午)

**目标**: 完成资源管理 5 bugs

1. ✅ 制定详细计划
2. 实现 RM-NET-003 (数据库泄露)
3. 实现 RM-NET-004 (SMTP 泄露)
4. 创建 lock_leak 子目录
5. 实现 RM-SYNC-001~003 (锁泄露 3 bugs)

### Day 2 (2025-10-20)

**目标**: 完成并发 5 bugs + 注入 2 bugs

1. 实现 CONC-RACE-007~009 (竞态 3 bugs)
2. 实现 CONC-DEAD-002~003 (死锁 2 bugs)
3. 实现 INJ-CMD-002~003 (命令注入 2 bugs)

### Day 3 (2025-10-21)

**目标**: 完成注入 2 bugs + 输入验证 1 bug + 验证提交

1. 创建 sql_injection 子目录
2. 实现 INJ-SQL-001~002 (SQL 注入 2 bugs)
3. 实现 INPUT-PATH-003 (路径遍历)
4. 更新 ground_truth.json
5. 运行评估验证
6. Code review & 提交

---

## 验收标准

### Step 2 完成标准

- [ ] Bug 总数 = 65 (50 + 15)
- [ ] 新增子类别 = 2 (lock_leak, sql_injection)
- [ ] ground_truth.json 正确更新
- [ ] 所有新 bugs 通过 PyScan 检测
- [ ] 所有 bugs 有完整 metadata
- [ ] 代码已提交并推送

### 质量标准

- [ ] 每个 bug 有 positive/negative 样本对
- [ ] 详细的攻击场景说明
- [ ] 正确的 CWE 映射
- [ ] 合理的严重性和难度评级

---

**创建日期**: 2025-10-19
**状态**: 进行中 🚧
**负责人**: Claude Code
