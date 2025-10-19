# PyScan v2.0 Benchmark 设计提案

## 文档信息

- **版本**: v2.0
- **日期**: 2025-10-19
- **作者**: Claude & hwuu
- **状态**: 设计提案

---

## 1. Benchmark 的目标与重要性

### 1.1 为什么需要 Benchmark？

**问题**: PyScan v1.0 缺少客观的评估标准
- 无法量化检测准确率（Precision）
- 无法衡量召回率（Recall）
- 难以对比不同版本的改进效果
- 缺乏与其他工具的对比基准

**Benchmark 的价值**:
```
Benchmark = 标准化的 Bug 样本集 + 自动化评估系统
```

1. **量化评估**: Precision, Recall, F1 Score
2. **版本对比**: Stage 1 vs Stage 2 vs Stage 3
3. **工具对比**: PyScan vs Bandit vs Pylint
4. **回归测试**: 确保新版本不降低检测能力
5. **持续改进**: 基于数据驱动的优化

### 1.2 设计目标

| 目标 | 指标 | 说明 |
|------|------|------|
| **真实性** | 100% 来源于真实项目 | 所有 bug 样本基于真实代码或常见反模式 |
| **多样性** | 8 大类，30+ 子类 | 覆盖 Python 常见 bug 类型 |
| **可扩展** | 模块化设计 | 易于添加新类别和样本 |
| **自动化** | 一键评估 | 从扫描到评估全自动 |
| **可追溯** | 关联已知 Bug | 每个样本关联真实项目 Bug ID |

---

## 2. Bug 类型分类体系

### 2.1 分类原则

基于 **CWE 分类体系** + **检测技术层级** 的科学分类方法：

#### 分类维度

**维度 1: CWE 顶层类别** (按影响域分类)
- 参考 CWE-1000 (Research Concepts) 和 CWE-699 (Development Concepts)
- 聚焦于可通过静态分析检测的类别

**维度 2: 检测技术层级** (按检测难度分类)
```
Layer 0 (Parser):     语法解析错误 - Python parser
Layer 1 (Basic Static): 基础静态检查 - mypy, flake8, bandit, pylint
Layer 2 (Deep Static):  深度静态分析 - CFG, DFG, Taint Analysis, Astroid
Layer 3 (LLM/Semantic): 语义推理 - 业务逻辑、复杂上下文
```

#### 核心设计原则

1. **可检测性优先**: 只收录可通过自动化工具检测的 bug 类型
2. **CWE 映射**: 每个 bug 类型映射到标准 CWE ID
3. **严重性分级**: Critical > High > Medium > Low
4. **去重与聚焦**:
   - 排除 Layer 0 (由 Python parser/flake8 覆盖)
   - 排除 Layer 1 低优先级 (字符串格式化、代码风格等)
   - 聚焦 Layer 2/3 的高价值 bug

### 2.2 完整 Bug 分类清单

本分类体系基于 **CWE 标准** + **Python 特性** + **检测技术能力**，共计 **105 个 Bug 类型**，分为 **8 个核心类别**。

#### 类别 1: 资源生命周期管理 (Resource Lifecycle)

**CWE 映射**: CWE-404 (资源未释放), CWE-772 (缺少资源释放)
**检测层**: Layer 2 (Astroid + DFG)
**优先级**: P0 (Critical) / P1 (High)

##### 类别 1-1: 文件资源泄露 (12 bugs)

| Bug ID | Bug 类型 | 示例 | CWE | 严重性 | 检测层 |
|--------|---------|------|-----|--------|--------|
| RM-FILE-001 | 文件未关闭 | `f = open(...); return` | CWE-404 | High | Layer 2 |
| RM-FILE-002 | 异常路径泄露 | `try: f=open() except: return` | CWE-755 | High | Layer 2 |
| RM-FILE-003 | 多路径未全关闭 | `if x: f.close() # else 分支未关闭` | CWE-404 | High | Layer 2 |
| RM-FILE-004 | 链式调用泄露 | `open().read()` | CWE-404 | Medium | Layer 2 |
| RM-FILE-005 | 嵌套调用泄露 | `process(open())` | CWE-404 | Medium | Layer 2 |
| RM-FILE-006 | 条件创建泄露 | `if cond: f=open(); use(f)` | CWE-404 | High | Layer 2/3 |
| RM-FILE-007 | 循环内泄露 | `for x in lst: open(x)` | CWE-404 | High | Layer 2 |
| RM-FILE-008 | 赋值后未用 | `f = open(); f = None` | CWE-404 | Medium | Layer 2 |
| RM-FILE-009 | 返回前未关 | `f=open(); if x: return` | CWE-404 | High | Layer 2 |
| RM-FILE-010 | finally 缺失 | `f=open(); try: use(f)` 无 finally | CWE-404 | High | Layer 2 |
| RM-FILE-011 | with 嵌套错误 | `with open() as f: with open()` 内层泄露 | CWE-404 | Medium | Layer 2 |
| RM-FILE-012 | close 条件错误 | `if success: f.close()` 失败时泄露 | CWE-404 | High | Layer 2 |

##### 类别 1-2: 线程池与执行器泄露 (6 bugs)

| Bug ID | Bug 类型 | 示例 | CWE | 严重性 | 检测层 |
|--------|---------|------|-----|--------|--------|
| RM-POOL-001 | ThreadPoolExecutor 未 shutdown | `executor = TPE(); submit()` | CWE-772 | High | Layer 2 |
| RM-POOL-002 | ProcessPoolExecutor 未 shutdown | `executor = PPE(); map()` | CWE-772 | High | Layer 2 |
| RM-POOL-003 | 异常路径未 shutdown | `executor=TPE(); try: submit()` | CWE-772 | High | Layer 2 |
| RM-POOL-004 | 异步函数泄露 | `await run_in_executor(TPE())` | CWE-772 | High | Layer 2/3 |
| RM-POOL-005 | 循环创建未释放 | `for x in lst: TPE().submit()` | CWE-772 | Critical | Layer 2 |
| RM-POOL-006 | 条件创建泄露 | `if cond: e=TPE(); e.submit()` | CWE-772 | High | Layer 2 |

##### 类别 1-3: 网络与连接泄露 (8 bugs)

| Bug ID | Bug 类型 | 示例 | CWE | 严重性 | 检测层 |
|--------|---------|------|-----|--------|--------|
| RM-NET-001 | Socket 未关闭 | `s = socket(); s.connect()` | CWE-404 | High | Layer 2 |
| RM-NET-002 | HTTP 连接未关闭 | `conn = http.client.HTTPConnection()` | CWE-404 | High | Layer 2 |
| RM-NET-003 | requests.Session 未关闭 | `s = Session(); s.get()` | CWE-404 | Medium | Layer 2 |
| RM-NET-004 | 数据库连接泄露 | `conn = connect(); cursor()` | CWE-404 | High | Layer 2 |
| RM-NET-005 | 数据库游标泄露 | `cursor = conn.cursor(); execute()` | CWE-404 | Medium | Layer 2 |
| RM-NET-006 | SMTP 连接泄露 | `smtp = smtplib.SMTP(); send()` | CWE-404 | Medium | Layer 2 |
| RM-NET-007 | FTP 连接泄露 | `ftp = ftplib.FTP(); login()` | CWE-404 | Medium | Layer 2 |
| RM-NET-008 | Redis 连接泄露 | `r = redis.Redis(); get()` | CWE-404 | Medium | Layer 2 |

##### 类别 1-4: 同步原语泄露 (4 bugs)

| Bug ID | Bug 类型 | 示例 | CWE | 严重性 | 检测层 |
|--------|---------|------|-----|--------|--------|
| RM-SYNC-001 | 锁未释放 | `lock.acquire(); return` | CWE-667 | Critical | Layer 2 |
| RM-SYNC-002 | 信号量未释放 | `sem.acquire(); raise` | CWE-667 | High | Layer 2 |
| RM-SYNC-003 | RLock 未配对 | `rlock.acquire(); if x: return` | CWE-667 | Critical | Layer 2 |
| RM-SYNC-004 | Condition 未释放 | `cv.acquire(); wait()` 无 release | CWE-667 | High | Layer 2 |

**小计**: 30 bugs

---

#### 类别 2: 并发与线程安全 (Concurrency & Thread Safety)

**CWE 映射**: CWE-362 (竞态条件), CWE-833 (死锁), CWE-667 (锁定不当)
**检测层**: Layer 2/3 (CFG + Data Flow + LLM)
**优先级**: P0 (Critical) / P1 (High)

##### 类别 2-1: 竞态条件 (Race Condition) - 10 bugs

| Bug ID | Bug 类型 | 示例 | CWE | 严重性 | 检测层 |
|--------|---------|------|-----|--------|--------|
| CONC-RACE-001 | 全局变量写入竞态 | `global_var += 1` | CWE-362 | High | Layer 2 |
| CONC-RACE-002 | 全局字典竞态 | `global_dict[k] = v` | CWE-362 | High | Layer 2 |
| CONC-RACE-003 | 全局列表竞态 | `global_list.append(x)` | CWE-362 | High | Layer 2 |
| CONC-RACE-004 | 类成员变量竞态 | `self.count += 1` (共享实例) | CWE-362 | High | Layer 2/3 |
| CONC-RACE-005 | 类变量竞态 | `MyClass.shared_var += 1` | CWE-362 | High | Layer 2 |
| CONC-RACE-006 | 复合操作竞态 | `if x > 0: x -= 1` | CWE-362 | High | Layer 2/3 |
| CONC-RACE-007 | check-then-act | `if key in dict: use(dict[key])` | CWE-362 | High | Layer 3 |
| CONC-RACE-008 | 单例模式竞态 | `if not instance: instance = Class()` | CWE-362 | High | Layer 2/3 |
| CONC-RACE-009 | 懒加载竞态 | `if not _cache: _cache = load()` | CWE-362 | High | Layer 2/3 |
| CONC-RACE-010 | 文件读写竞态 | 多线程写同一文件无锁 | CWE-362 | Medium | Layer 2 |

##### 类别 2-2: 死锁风险 (Deadlock Risk) - 6 bugs

| Bug ID | Bug 类型 | 示例 | CWE | 严重性 | 检测层 |
|--------|---------|------|-----|--------|--------|
| CONC-DEAD-001 | 嵌套锁顺序不一致 | `lock1.acquire(); lock2.acquire()` | CWE-833 | Critical | Layer 3 |
| CONC-DEAD-002 | 回调中获取锁 | `with lock: callback()` callback 获取同一锁 | CWE-833 | Critical | Layer 3 |
| CONC-DEAD-003 | 锁内等待锁 | `with lock1: lock2.acquire()` | CWE-833 | Critical | Layer 3 |
| CONC-DEAD-004 | 循环等待 | A 等 B，B 等 C，C 等 A | CWE-833 | Critical | Layer 3 |
| CONC-DEAD-005 | 条件变量死锁 | `cv.wait()` 无对应 `notify()` | CWE-833 | High | Layer 3 |
| CONC-DEAD-006 | Join 死锁 | 线程 join 自己或循环 join | CWE-833 | High | Layer 2 |

##### 类别 2-3: 异步与协程问题 (Async/Await) - 8 bugs

| Bug ID | Bug 类型 | 示例 | CWE | 严重性 | 检测层 |
|--------|---------|------|-----|--------|--------|
| CONC-ASYNC-001 | 忘记 await | `async_func()` 未 await | CWE-1088 | High | Layer 1/2 |
| CONC-ASYNC-002 | 同步函数中 await | `def f(): await x` | CWE-1088 | High | Layer 1 |
| CONC-ASYNC-003 | 异步中阻塞调用 | `async def f(): time.sleep()` | CWE-1088 | Medium | Layer 2/3 |
| CONC-ASYNC-004 | Event loop 嵌套 | `asyncio.run()` 嵌套调用 | CWE-1088 | High | Layer 2/3 |
| CONC-ASYNC-005 | Task 未 await | `asyncio.create_task()` 未等待 | CWE-1088 | Medium | Layer 2 |
| CONC-ASYNC-006 | Task 未取消 | 长期 Task 无 cancel() | CWE-772 | Medium | Layer 3 |
| CONC-ASYNC-007 | async context 泄露 | `async with` 实现错误 | CWE-404 | High | Layer 2 |
| CONC-ASYNC-008 | gather 异常未处理 | `await gather()` 部分失败 | CWE-755 | Medium | Layer 2/3 |

**小计**: 24 bugs

---

#### 类别 3: 错误与异常处理 (Error & Exception Handling)

**CWE 映射**: CWE-755 (异常处理不当), CWE-396 (异常捕获过宽), CWE-703 (检查后未处理)
**检测层**: Layer 1/2 (pylint + CFG)
**优先级**: P1 (High) / P2 (Medium)

##### 类别 3-1: 异常捕获问题 (10 bugs)

| Bug ID | Bug 类型 | 示例 | CWE | 严重性 | 检测层 |
|--------|---------|------|-----|--------|--------|
| EXC-CATCH-001 | 捕获过宽异常 | `except Exception:` | CWE-396 | Medium | Layer 1 |
| EXC-CATCH-002 | 裸 except | `except:` | CWE-396 | Medium | Layer 1 |
| EXC-CATCH-003 | 错误异常类型 | `except ValueError:` 应为 `TypeError` | CWE-396 | Medium | Layer 2/3 |
| EXC-CATCH-004 | 异常处理不完整 | 只捕获 ValueError，未处理 IOError | CWE-755 | Medium | Layer 2 |
| EXC-CATCH-005 | except 仅 pass | `except: pass` 吞异常 | CWE-391 | Medium | Layer 1 |
| EXC-CATCH-006 | 捕获后未记录 | `except: return None` 无日志 | CWE-778 | Low | Layer 1 |
| EXC-CATCH-007 | 捕获 BaseException | `except BaseException:` | CWE-396 | High | Layer 1 |
| EXC-CATCH-008 | 多余的 except | 前面已捕获父类 | CWE-561 | Low | Layer 1 |
| EXC-CATCH-009 | except 顺序错误 | 子类在父类之后 | CWE-561 | Medium | Layer 1 |
| EXC-CATCH-010 | 空 try 块 | `try: pass except:` | CWE-561 | Low | Layer 1 |

##### 类别 3-2: 资源清理问题 (6 bugs)

| Bug ID | Bug 类型 | 示例 | CWE | 严重性 | 检测层 |
|--------|---------|------|-----|--------|--------|
| EXC-CLEAN-001 | 异常时资源未释放 | `f=open(); may_raise()` | CWE-755 | High | Layer 2 |
| EXC-CLEAN-002 | 缺少 finally 块 | `lock.acquire(); try: ...` 无 finally | CWE-755 | High | Layer 2 |
| EXC-CLEAN-003 | finally 中抛异常 | `finally: raise` 覆盖原异常 | CWE-755 | Medium | Layer 2 |
| EXC-CLEAN-004 | 双重异常 | `except: raise` + `finally: raise` | CWE-755 | Medium | Layer 2 |
| EXC-CLEAN-005 | 清理失败 | `finally: f.close()` 但 f 可能未定义 | CWE-755 | Medium | Layer 2 |
| EXC-CLEAN-006 | 状态未重置 | 异常时 flag 未重置 | CWE-755 | Medium | Layer 2/3 |

**小计**: 16 bugs

---

#### 类别 4: 输入验证与数据校验 (Input Validation)

**CWE 映射**: CWE-20 (输入验证不当)
**检测层**: Layer 2/3 (Taint + LLM)
**优先级**: P1 (High) / P2 (Medium)

##### 类别 4-1: API 输入验证 (10 bugs)

| Bug ID | Bug 类型 | 示例 | CWE | 严重性 | 检测层 |
|--------|---------|------|-----|--------|--------|
| VAL-INPUT-001 | 缺少 None 检查 | `def f(x): return x.attr` | CWE-476 | High | Layer 2/3 |
| VAL-INPUT-002 | 缺少类型检查 | `def f(x): return x + 1` x 可能非数字 | CWE-20 | Medium | Layer 2/3 |
| VAL-INPUT-003 | 缺少范围验证 | `def f(limit): query(limit)` limit 可能负数 | CWE-20 | Medium | Layer 2/3 |
| VAL-INPUT-004 | 缺少长度验证 | `def f(name): save(name)` name 可能超长 | CWE-20 | Low | Layer 3 |
| VAL-INPUT-005 | 缺少白名单 | `def set_config(key, val)` key 无限制 | CWE-20 | High | Layer 3 |
| VAL-INPUT-006 | 缺少格式验证 | `def f(email)` 未验证 email 格式 | CWE-20 | Medium | Layer 3 |
| VAL-INPUT-007 | 缺少权限检查 | `def delete(user, file)` 未检查权限 | CWE-285 | Critical | Layer 3 |
| VAL-INPUT-008 | 缺少边界检查 | `def f(idx, lst): return lst[idx]` | CWE-129 | High | Layer 2 |
| VAL-INPUT-009 | 缺少空值检查 | `def f(lst): return lst[0]` lst 可能为空 | CWE-476 | High | Layer 2/3 |
| VAL-INPUT-010 | 缺少唯一性检查 | `def create(id)` 未检查 id 冲突 | CWE-20 | Medium | Layer 3 |

**小计**: 10 bugs

---

#### 类别 5: 注入漏洞 (Injection Flaws)

**CWE 映射**: CWE-78 (命令注入), CWE-89 (SQL 注入), CWE-22 (路径遍历), CWE-94 (代码注入)
**检测层**: Layer 1/2 (bandit + Taint Analysis)
**优先级**: P0 (Critical)

##### 类别 5-1: 路径遍历 (Path Traversal) - 9 bugs

| Bug ID | Bug 类型 | 示例 | CWE | 严重性 | 检测层 |
|--------|---------|------|-----|--------|--------|
| INJ-PATH-001 | 路径拼接未验证 | `open(base + user_input)` | CWE-22 | High | Layer 2 |
| INJ-PATH-002 | 路径规范化缺失 | `if path.startswith(base)` 未 resolve | CWE-22 | High | Layer 2 |
| INJ-PATH-003 | 符号链接未检查 | 未用 `realpath()` | CWE-59 | High | Layer 2 |
| INJ-PATH-004 | TOCTOU 漏洞 | `if exists(p): open(p)` | CWE-367 | High | Layer 2/3 |
| INJ-PATH-005 | Zip Slip | `tar.extractall()` 未验证成员路径 | CWE-22 | High | Layer 2 |
| INJ-PATH-006 | 文件名注入 | `open(f"{dir}/{filename}")` | CWE-22 | High | Layer 2 |
| INJ-PATH-007 | 相对路径未解析 | `../../../etc/passwd` 未阻止 | CWE-22 | High | Layer 2 |
| INJ-PATH-008 | 路径穿越 | `os.path.join` 与 `../` 组合 | CWE-22 | High | Layer 2 |
| INJ-PATH-009 | 临时文件路径 | 可预测的 temp 文件名 | CWE-377 | Medium | Layer 1 |

##### 类别 5-2: 命令注入 (Command Injection) - 6 bugs

| Bug ID | Bug 类型 | 示例 | CWE | 严重性 | 检测层 |
|--------|---------|------|-----|--------|--------|
| INJ-CMD-001 | os.system 拼接 | `os.system('cmd ' + input)` | CWE-78 | Critical | Layer 1/2 |
| INJ-CMD-002 | subprocess shell=True | `subprocess.run(cmd, shell=True)` | CWE-78 | Critical | Layer 1/2 |
| INJ-CMD-003 | os.popen 注入 | `os.popen('ls ' + dir)` | CWE-78 | Critical | Layer 1 |
| INJ-CMD-004 | eval 用户输入 | `eval(user_input)` | CWE-95 | Critical | Layer 1 |
| INJ-CMD-005 | exec 注入 | `exec(code)` code 来自外部 | CWE-94 | Critical | Layer 1 |
| INJ-CMD-006 | compile 注入 | `compile(source, ...)` | CWE-94 | Critical | Layer 1 |

##### 类别 5-3: SQL 注入 (SQL Injection) - 5 bugs

| Bug ID | Bug 类型 | 示例 | CWE | 严重性 | 检测层 |
|--------|---------|------|-----|--------|--------|
| INJ-SQL-001 | 字符串拼接 SQL | `f"SELECT * WHERE id={id}"` | CWE-89 | Critical | Layer 1/2 |
| INJ-SQL-002 | % 格式化 SQL | `"SELECT * WHERE id=%s" % id` | CWE-89 | Critical | Layer 1/2 |
| INJ-SQL-003 | execute 拼接 | `cursor.execute("..."+val)` | CWE-89 | Critical | Layer 1/2 |
| INJ-SQL-004 | ORM raw 注入 | `Model.objects.raw(query+val)` | CWE-89 | Critical | Layer 2 |
| INJ-SQL-005 | 动态表名注入 | `f"SELECT * FROM {table}"` | CWE-89 | High | Layer 2 |

**小计**: 20 bugs

---

#### 类别 6: 数据流问题 (Data Flow Issues)

**CWE 映射**: CWE-457 (未初始化变量), CWE-476 (空指针), CWE-561 (死代码)
**检测层**: Layer 2 (DFG + CFG)
**优先级**: P1 (High) / P2 (Medium)

##### 类别 6-1: 变量初始化 (6 bugs)

| Bug ID | Bug 类型 | 示例 | CWE | 严重性 | 检测层 |
|--------|---------|------|-----|--------|--------|
| DATA-INIT-001 | 条件分支未初始化 | `if x: v=1; return v` | CWE-457 | High | Layer 2 |
| DATA-INIT-002 | 循环外未初始化 | `for x in lst: v=x; return v` | CWE-457 | Medium | Layer 2 |
| DATA-INIT-003 | 异常分支未初始化 | `try: v=1 except: pass; use(v)` | CWE-457 | High | Layer 2 |
| DATA-INIT-004 | 提前引用 | `print(x); x=1` | CWE-457 | High | Layer 1 |
| DATA-INIT-005 | 全局声明未初始化 | `global x; x+=1` x 可能未定义 | CWE-457 | Medium | Layer 2 |
| DATA-INIT-006 | 类变量未初始化 | `self.x += 1` 但 `__init__` 未设置 | CWE-457 | Medium | Layer 2 |

##### 类别 6-2: None 解引用 (5 bugs)

| Bug ID | Bug 类型 | 示例 | CWE | 严重性 | 检测层 |
|--------|---------|------|-----|--------|--------|
| DATA-NULL-001 | Optional 未检查 | `x: Optional[int]; x+1` | CWE-476 | High | Layer 1/2 |
| DATA-NULL-002 | 函数返回 None | `x = dict.get(k); x.attr` | CWE-476 | High | Layer 2/3 |
| DATA-NULL-003 | 空列表索引 | `lst = []; lst[0]` | CWE-476 | High | Layer 2 |
| DATA-NULL-004 | 空字典键 | `d = {}; d['key']` | CWE-476 | High | Layer 2 |
| DATA-NULL-005 | find 返回 -1 | `s.find(x); s[idx]` idx 可能 -1 | CWE-476 | Medium | Layer 2/3 |

##### 类别 6-3: 控制流问题 (4 bugs)

| Bug ID | Bug 类型 | 示例 | CWE | 严重性 | 检测层 |
|--------|---------|------|-----|--------|--------|
| DATA-FLOW-001 | 不可达代码 | `return; x=1` | CWE-561 | Low | Layer 1 |
| DATA-FLOW-002 | 恒真/恒假条件 | `if 1==2:` | CWE-570 | Low | Layer 1/2 |
| DATA-FLOW-003 | 无限循环 | `while True:` 无 break | CWE-835 | Medium | Layer 3 |
| DATA-FLOW-004 | 递归无终止条件 | `def f(): f()` | CWE-674 | High | Layer 2/3 |

**小计**: 15 bugs

---

#### 类别 7: 类型安全 (Type Safety)

**CWE 映射**: CWE-704 (类型错误), CWE-843 (类型混淆)
**检测层**: Layer 1 (mypy) / Layer 2
**优先级**: P2 (Medium)

##### 类别 7-1: 类型不匹配 (6 bugs)

| Bug ID | Bug 类型 | 示例 | CWE | 严重性 | 检测层 |
|--------|---------|------|-----|--------|--------|
| TYPE-MIS-001 | 参数类型不匹配 | `def f(x: int): ...; f("str")` | CWE-704 | High | Layer 1 |
| TYPE-MIS-002 | 返回类型不匹配 | `def f() -> int: return "str"` | CWE-704 | High | Layer 1 |
| TYPE-MIS-003 | 容器类型错误 | `List[int] = [1, "2"]` | CWE-704 | High | Layer 1 |
| TYPE-MIS-004 | Union 未收窄 | `x: int|str; x+1` | CWE-704 | Medium | Layer 1/2 |
| TYPE-MIS-005 | Any 滥用 | 过度使用 Any 逃避检查 | CWE-704 | Low | Layer 1 |
| TYPE-MIS-006 | 类型转换错误 | `int("1.5")` | CWE-704 | Medium | Layer 2 |

##### 类别 7-2: API 契约违反 (4 bugs)

| Bug ID | Bug 类型 | 示例 | CWE | 严重性 | 检测层 |
|--------|---------|------|-----|--------|--------|
| TYPE-API-001 | 可变默认参数 | `def f(x=[])` | CWE-474 | High | Layer 1 |
| TYPE-API-002 | 继承签名不一致 | 子类重写参数数量不同 | CWE-573 | High | Layer 1 |
| TYPE-API-003 | 抽象方法未实现 | ABC 子类未实现抽象方法 | CWE-573 | High | Layer 1/2 |
| TYPE-API-004 | 返回类型不一致 | 成功返回 dict，失败返回 None | CWE-252 | Medium | Layer 1/2 |

**小计**: 10 bugs

---

#### 类别 8: API 使用与设计 (API Usage & Design)

**CWE 映射**: CWE-252 (未检查返回值), CWE-573 (调用错误)
**检测层**: Layer 1/2/3
**优先级**: P2 (Medium) / P3 (Low)

##### 类别 8-1: 废弃 API (4 bugs)

| Bug ID | Bug 类型 | 示例 | CWE | 严重性 | 检测层 |
|--------|---------|------|-----|--------|--------|
| API-DEP-001 | os.popen | 应使用 subprocess | CWE-477 | Low | Layer 1 |
| API-DEP-002 | platform.dist | 已废弃 | CWE-477 | Low | Layer 1 |
| API-DEP-003 | imp 模块 | 应使用 importlib | CWE-477 | Low | Layer 1 |
| API-DEP-004 | collections ABC | 应从 collections.abc 导入 | CWE-477 | Low | Layer 1 |

##### 类别 8-2: 危险 API (6 bugs)

| Bug ID | Bug 类型 | 示例 | CWE | 严重性 | 检测层 |
|--------|---------|------|-----|--------|--------|
| API-DANGER-001 | pickle.loads 不可信数据 | `pickle.loads(user_data)` | CWE-502 | Critical | Layer 1 |
| API-DANGER-002 | yaml.load 不安全 | 应使用 safe_load | CWE-502 | High | Layer 1 |
| API-DANGER-003 | random 用于安全 | 应使用 secrets | CWE-330 | Medium | Layer 1 |
| API-DANGER-004 | assert 用于验证 | assert 可被禁用 | CWE-703 | Medium | Layer 1 |
| API-DANGER-005 | tempfile 固定名称 | 应使用 mkstemp | CWE-377 | Medium | Layer 1 |
| API-DANGER-006 | MD5/SHA1 密码 | 应使用 bcrypt/argon2 | CWE-327 | High | Layer 1 |

**小计**: 10 bugs

---

### 2.3 统计总结

#### 按类别统计

| 类别 | Bug 数量 | 占比 | 主要检测层 |
|------|---------|------|-----------|
| 1. 资源管理 | 30 | 28.6% | Layer 2 |
| 2. 并发与同步 | 24 | 22.9% | Layer 2/3 |
| 3. 错误处理 | 16 | 15.2% | Layer 1/2 |
| 4. 输入验证 | 10 | 9.5% | Layer 2/3 |
| 5. 注入漏洞 | 20 | 19.0% | Layer 1/2 |
| 6. 数据流问题 | 15 | 14.3% | Layer 2 |
| 7. 类型安全 | 10 | 9.5% | Layer 1 |
| 8. API 使用 | 10 | 9.5% | Layer 1 |
| **总计** | **105** | **100%** | |

#### 按检测层统计

| 检测层 | Bug 数量 | 占比 |
|--------|---------|------|
| Layer 1 | 25 | 23.8% |
| Layer 2 | 50 | 47.6% |
| Layer 2/3 | 25 | 23.8% |
| Layer 3 | 5 | 4.8% |
| **总计** | **105** | **100%** |

#### 按严重性统计

| 严重性 | Bug 数量 | 占比 |
|--------|---------|------|
| Critical | 15 | 14.3% |
| High | 50 | 47.6% |
| Medium | 35 | 33.3% |
| Low | 5 | 4.8% |
| **总计** | **105** | **100%** |

#### 按 CWE 顶层类别统计

| CWE 类别 | Bug 数量 | 说明 |
|---------|---------|------|
| CWE-404/772 (资源管理) | 30 | 资源未释放、生命周期问题 |
| CWE-362/667/833 (并发) | 24 | 竞态、死锁、同步问题 |
| CWE-22/78/89/94 (注入) | 20 | 路径、命令、SQL、代码注入 |
| CWE-755/396 (异常处理) | 16 | 异常捕获、资源清理 |
| CWE-457/476/561 (数据流) | 15 | 未初始化、空指针、死代码 |
| CWE-20/285 (输入验证) | 10 | 输入校验、权限检查 |
| CWE-704/843 (类型安全) | 10 | 类型错误、类型混淆 |
| CWE-252/573/477 (API) | 10 | 返回值、废弃 API、危险 API |
| **总计** | **105** | |

---

## 3. 分阶段实施计划

### 3.1 总体路线图

基于 Section 2 的 105 个 Bug 类型,分 4 个阶段逐步构建 Benchmark:

```
Phase 1: 基础架构搭建 (0 bugs)
    ↓
Phase 2: 核心 8 类别样本收集 (50+ bugs)
    - 资源管理(12)、并发(10)、错误处理(8)、输入验证(5)、注入漏洞(10)、数据流(5)
    ↓
Phase 3: 扩展到 80+ 样本 (80+ bugs)
    - 补齐 8 大类别的高优先级 bug
    ↓
Phase 4: 扩展到 150+ 样本 (150+ bugs)
    - 真实项目样本 + 难度梯度优化
```

**覆盖计划**:
- **Phase 2**: 50+ bugs (47.6% of 105)
- **Phase 3**: 80+ bugs (76.2% of 105)
- **Phase 4**: 100+ bugs from新8类别 (95%+ of 105) + 50+ 真实项目样本

---

### 3.2 Phase 1: 基础架构搭建

**预计时间**: 已完成
**目标**: 建立 Benchmark 基础设施

**已完成内容**:
- 目录结构设计（categories/positive/negative）
- 元数据格式定义（metadata.yaml）
- Ground truth 自动生成（build_ground_truth.py）
- 评估脚本实现（evaluation/evaluate.py）
- 文档系统（README, SUMMARY, PROGRESS）

---

### 3.3 Phase 2: 核心 8 类别样本收集 (50+ bugs)

**预计时间**: 1-2 天
**目标**: 基于新的 8 类别分类,收集 50+ 高优先级 bug 样本

**实施内容** (对应 Section 2.2 的 Bug ID):

#### 类别 1: 资源管理 (12 bugs)
- **RM-FILE-001~007**: 文件泄露 (7 bugs)
  - 文件未关闭、异常路径泄露、多路径未全关闭、链式调用泄露等
- **RM-POOL-001~003**: 线程池泄露 (3 bugs)
  - ThreadPoolExecutor/ProcessPoolExecutor 未 shutdown
- **RM-NET-001~002**: 网络泄露 (2 bugs)
  - Socket 未关闭、HTTP 连接泄露

#### 类别 2: 并发与同步 (10 bugs)
- **CONC-RACE-001~006**: 竞态条件 (6 bugs)
  - 全局变量竞态、复合操作竞态、check-then-act 等
- **CONC-DEAD-001~002**: 死锁风险 (2 bugs)
  - 嵌套锁顺序不一致、锁内等待锁
- **CONC-ASYNC-001~002**: 异步问题 (2 bugs)
  - 忘记 await、同步函数中 await

#### 类别 3: 错误处理 (8 bugs)
- **EXC-CATCH-001~005**: 异常捕获 (5 bugs)
  - 捕获过宽异常、裸 except、except 仅 pass 等
- **EXC-CLEAN-001~003**: 资源清理 (3 bugs)
  - 异常时资源未释放、缺少 finally、finally 中抛异常

#### 类别 4: 输入验证 (5 bugs)
- **VAL-INPUT-001~005**: API 输入验证 (5 bugs)
  - 缺少 None 检查、类型检查、范围验证、边界检查等

#### 类别 5: 注入漏洞 (10 bugs)
- **INJ-PATH-001~005**: 路径遍历 (5 bugs)
  - 路径拼接未验证、规范化缺失、Zip Slip 等
- **INJ-CMD-001~003**: 命令注入 (3 bugs)
  - os.system 拼接、subprocess shell=True、eval 用户输入
- **INJ-SQL-001~002**: SQL 注入 (2 bugs)
  - 字符串拼接 SQL、% 格式化 SQL

#### 类别 6: 数据流问题 (5 bugs)
- **DATA-INIT-001~002**: 变量初始化 (2 bugs)
  - 条件分支未初始化、循环外未初始化
- **DATA-NULL-001~002**: None 解引用 (2 bugs)
  - Optional 未检查、函数返回 None
- **DATA-FLOW-004**: 递归无终止条件 (1 bug)

#### 类别 7: 类型安全 (预留,Phase 3 实现)

#### 类别 8: API 使用 (预留,Phase 3 实现)

**预期成果**:
- 50+ bug 样本 (覆盖 6/8 大类别)
- 所有 bug 与 Section 2.2 的 ID 精确对应
- Positive 文件 30+，Negative 文件 20+
- ground_truth.json 包含完整的 CWE 和检测层信息

**验收标准**:
- 50+ bug 样本
- 所有 bug ID 与 Section 2.2 对应
- Precision ≥ 65%, Recall ≥ 55%

---

### 3.4 Phase 3: 扩展到 80+ 样本

**预计时间**: 3-5 天
**目标**: 补齐 8 大类别,覆盖所有高优先级 Bug

**实施内容** (对应 Section 2.2 的 Bug ID):

#### 补齐类别 1-6 的剩余 bugs (约 20 bugs)
- **RM-NET-003~008**: 更多网络泄露 (6 bugs)
  - requests.Session、数据库连接、SMTP、FTP 等
- **RM-SYNC-001~004**: 同步原语泄露 (4 bugs)
  - 锁未释放、信号量未释放、RLock 未配对等
- **CONC-RACE-007~010**: 更多竞态 (4 bugs)
  - 单例模式竞态、懒加载竞态、文件读写竞态等
- **CONC-DEAD-003~006**: 更多死锁 (4 bugs)
  - 回调中获取锁、循环等待、Join 死锁等
- **CONC-ASYNC-003~008**: 更多异步问题 (6 bugs)
  - 异步中阻塞调用、Event loop 嵌套、Task 未 await 等

#### 新增类别 7: 类型安全 (10 bugs)
- **TYPE-MIS-001~006**: 类型不匹配 (6 bugs)
  - 参数类型不匹配、返回类型不匹配、Union 未收窄等
- **TYPE-API-001~004**: API 契约违反 (4 bugs)
  - 可变默认参数、继承签名不一致、抽象方法未实现等

#### 新增类别 8: API 使用 (10 bugs)
- **API-DEP-001~004**: 废弃 API (4 bugs)
  - os.popen、platform.dist、imp 模块等
- **API-DANGER-001~006**: 危险 API (6 bugs)
  - pickle.loads 不可信数据、yaml.load、random 用于安全等

**预期成果**:
- 80+ bug 样本 (覆盖 8/8 大类别)
- 所有高优先级 (Critical/High) bug 覆盖

**验收标准**:
- 80+ bug 样本
- 8 大类别全覆盖
- Precision ≥ 70%, Recall ≥ 60%

---

### 3.5 Phase 4: 扩展到 150+ 样本

**预计时间**: 2-3 周
**目标**: 从真实项目提取样本,建立全面的 Benchmark

**数据来源**:

1. **开源项目 Bug 提取**
   - 从 GitHub Issues 中提取真实 bug
   - 分析 CVE 数据库
   - 参考 Pylint/Bandit 检测到的问题

2. **难度梯度优化**
   - Easy: 30-40%（明显错误）
   - Medium: 40-50%（需要分析）
   - Hard: 20-30%（复杂场景）

3. **Negative 样本扩充**
   - 增加到 Positive 的 80%
   - 减少 False Positive

4. **补齐 Section 2.2 的剩余 bugs**
   - 补充类别 1-8 的 Medium 优先级 bugs
   - 增加复杂场景和边界情况

**预期成果**:
- 150+ bug 样本
- 105 个 bug 类型 95%+ 覆盖
- 从真实项目提取 50%+
- Negative 样本达到 120+

**验收标准**:
- 150+ bug 样本
- 50%+ 来自真实项目
- Negative 样本 ≥ 120
- 难度分布符合目标
- Precision ≥ 75%, Recall ≥ 65%

---

## 4. 评估指标与目标

### 4.1 关键指标定义

| 指标 | 公式 | 说明 | 目标 |
|------|------|------|------|
| **Precision** | TP / (TP + FP) | 检测结果中真实 bug 的比例 | ≥ 75% |
| **Recall** | TP / (TP + FN) | 真实 bug 中被检测到的比例 | ≥ 65% |
| **F1 Score** | 2 × P × R / (P + R) | 综合指标 | ≥ 0.70 |
| **FPR** | FP / (FP + TN) | 误报率（在 negative 样本上） | ≤ 15% |

### 4.2 分阶段目标

| Phase | Bug 样本数 | 类别覆盖 | Precision | Recall | F1 Score |
|-------|-----------|---------|-----------|--------|----------|
| Phase 1 | 0 (基础设施) | - | - | - | - |
| Phase 2 | 50+ | 6/8 (75%) | ≥ 65% | ≥ 55% | ≥ 0.60 |
| Phase 3 | 80+ | 8/8 (100%) | ≥ 70% | ≥ 60% | ≥ 0.65 |
| Phase 4 | 150+ | 8/8 + 真实项目 | ≥ 75% | ≥ 65% | ≥ 0.70 |

### 4.3 按类别目标

| 类别 | Phase 2 | Phase 3 目标 | Phase 4 目标 |
|------|---------|-------------|-------------|
| 1. 资源管理 | 12 | 25 | 35 |
| 2. 并发与同步 | 10 | 20 | 30 |
| 3. 错误处理 | 8 | 12 | 20 |
| 4. 输入验证 | 5 | 8 | 12 |
| 5. 注入漏洞 | 10 | 15 | 25 |
| 6. 数据流问题 | 5 | 10 | 15 |
| 7. 类型安全 | 0 | 8 | 12 |
| 8. API 使用 | 0 | 8 | 11 |
| **总计** | **50** | **106** | **160** |

---

## 5. 技术实现细节

### 5.1 Bug 标注格式

每个 bug 包含以下元数据:

```yaml
bugs:
  - id: "RM-FILE-001"                    # 唯一 ID (对应 Section 2.2)
    category: "resource_management"     # 大类别
    subcategory: "file_leak"            # 子类别
    severity: "high"                    # 严重程度: critical/high/medium/low
    type: "ResourceLeakRisk"            # Bug 类型
    file: "example1.py"                 # 文件名
    function: "read_config"             # 函数名
    location:                           # 精确位置
      start_line: 10
      end_line: 10
      start_col: 4
      end_col: 31
    description: "文件句柄未关闭"       # 描述
    root_cause: "未使用 with 语句"      # 根因
    cwe_id: "CWE-404"                   # CWE 分类
    difficulty: "easy"                  # 难度: easy/medium/hard
    related_bugs: ["BUG_0001"]          # 关联的真实 Bug
    detection_layer: "Layer 2"          # 检测层
```

### 5.2 目录结构

```
benchmark/
├── categories/
│   ├── 01_resource_management/
│   │   ├── file_leak/
│   │   │   ├── positive/          # 包含 bug 的样本
│   │   │   │   ├── example1.py
│   │   │   │   ├── example2.py
│   │   │   │   └── metadata.yaml  # Bug 标注
│   │   │   └── negative/          # 正确的代码
│   │   │       ├── example1.py
│   │   │       └── example2.py
│   │   ├── thread_pool_leak/
│   │   │   ├── positive/
│   │   │   └── negative/
│   │   ├── network_leak/
│   │   └── sync_primitive_leak/
│   ├── 02_concurrency/
│   │   ├── race_condition/
│   │   ├── deadlock_risk/
│   │   └── async_await_misuse/
│   ├── 03_error_handling/
│   │   ├── exception_catching/
│   │   └── resource_cleanup/
│   ├── 04_input_validation/
│   │   └── api_input_validation/
│   ├── 05_injection_flaws/
│   │   ├── path_traversal/
│   │   ├── command_injection/
│   │   └── sql_injection/
│   ├── 06_data_flow/
│   │   ├── uninitialized_variable/
│   │   ├── none_dereference/
│   │   └── control_flow/
│   ├── 07_type_safety/
│   │   ├── type_mismatch/
│   │   └── api_contract_violation/
│   └── 08_api_usage/
│       ├── deprecated_api/
│       └── dangerous_api/
├── ground_truth.json              # 自动生成
├── build_ground_truth.py
├── evaluation/
│   └── evaluate.py
├── README.md
├── SUMMARY.md
└── PROGRESS.md
```

### 5.3 自动化流程

```bash
# 1. 添加新 bug 样本
# 编辑 positive/example.py 和 metadata.yaml

# 2. 重新生成 ground truth
cd benchmark
python build_ground_truth.py

# 3. 运行 PyScan 扫描
python -m pyscan benchmark/categories -o report.json

# 4. 评估结果
python benchmark/evaluation/evaluate.py \
    --ground-truth benchmark/ground_truth.json \
    --report report.json \
    --output evaluation.json

# 5. 查看结果
cat evaluation.json | jq .
```

---

## 6. 风险与缓解

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| **样本质量不高** | 中 | 高 | Code review，参考真实项目 |
| **标注不准确** | 中 | 高 | 多人 review，自动化检查 |
| **覆盖不全面** | 低 | 中 | 参考 CWE/OWASP，社区反馈 |
| **维护成本高** | 中 | 中 | 自动化工具，文档完善 |
| **与真实场景脱节** | 中 | 高 | 从真实项目提取样本 |

---

## 7. 成功标准

### Phase 1
- 能够自动生成 ground_truth.json
- 能够评估 PyScan 扫描结果
- 计算 Precision, Recall, F1 Score

### Phase 2
- 50+ bug 样本
- 6/8 大类别覆盖
- 所有 bug 与 Section 2.2 的 ID 对应
- 自动化评估流程
- 完整文档
- Precision ≥ 65%, Recall ≥ 55%, F1 Score ≥ 0.60

### Phase 3
- 80+ bug 样本
- 8/8 大类别覆盖
- Precision ≥ 70%
- Recall ≥ 60%
- F1 Score ≥ 0.65

### Phase 4
- 150+ bug 样本
- 50%+ 来自真实项目
- Precision ≥ 75%
- Recall ≥ 65%
- F1 Score ≥ 0.70

---

## 8. 下一步行动

### 短期（1-2 周）
1. 启动 Phase 2: 基于新 8 类别收集 50+ bug 样本
2. 运行 PyScan 评估 Phase 2 benchmark
3. 分析结果，识别短板
4. 调整 bug 样本和标注

### 中期（1-2 月）
1. 完成 Phase 3 扩展 (80+ bugs)
2. 评估并优化检测规则
3. 对比其他工具（Bandit, Pylint）
4. 发布 Benchmark v0.3

### 长期（3-6 月）
1. 从真实项目提取样本
2. 完成 Phase 4 扩展 (150+ bugs)
3. 发布 Benchmark v1.0
4. 社区贡献指南

---

**文档版本历史**:
- v2.0 (2025-10-19): 基于新的 8 类别 105 bugs 分类更新全文
- v1.0 (2025-10-19): 初始版本

---

**参考资源**:
- CWE 分类: https://cwe.mitre.org/
- OWASP Top 10: https://owasp.org/Top10/
- Python 常见错误: https://docs.python.org/3/tutorial/errors.html
- 详细 Bug 清单: 参见本文档 Section 2.2
