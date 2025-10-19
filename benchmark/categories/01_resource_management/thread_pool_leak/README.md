# Thread Pool Leak - 线程池泄露

## Bug 描述

ThreadPoolExecutor 或 ProcessPoolExecutor 创建后未调用 `shutdown()` 或未使用 `with` 语句，导致线程资源泄露。

## 常见模式

### 1. 未使用 with 语句

```python
# Bad
executor = ThreadPoolExecutor(max_workers=4)
future = executor.submit(task)
# 缺少 executor.shutdown()
```

### 2. 循环内创建线程池

```python
# Bad
for item in items:
    executor = ThreadPoolExecutor(max_workers=2)
    executor.submit(process, item)
    # 每次循环创建新线程池但未关闭
```

### 3. 异常时未关闭

```python
# Bad
executor = ThreadPoolExecutor(max_workers=4)
try:
    executor.submit(risky_task)
except Exception:
    return  # executor 未关闭
```

## 正确做法

### 1. 使用 with 语句（推荐）

```python
# Good
with ThreadPoolExecutor(max_workers=4) as executor:
    future = executor.submit(task)
# 自动 shutdown()
```

### 2. 显式 shutdown

```python
# Good
executor = ThreadPoolExecutor(max_workers=4)
try:
    future = executor.submit(task)
    result = future.result()
finally:
    executor.shutdown(wait=True)
```

## 检测方法

### 静态分析

1. **检测 Executor 创建**：查找 ThreadPoolExecutor/ProcessPoolExecutor 实例化
2. **检查 with 语句**：判断是否在 with 上下文中使用
3. **追踪 shutdown 调用**：检查是否有对应的 shutdown() 调用

### 难度等级

- **Easy**: 单一函数内未关闭
- **Medium**: 异步函数、循环内创建
- **Hard**: 跨函数传递、作为类成员

## 相关 Bug

- BUG_0010: `run_in_thread_pool` 中 ThreadPoolExecutor 每次调用都创建但未关闭

## CWE 分类

- **CWE-404**: Improper Resource Shutdown or Release
- **CWE--772**: Missing Release of Resource after Effective Lifetime

## 参考资料

- [concurrent.futures — Launching parallel tasks](https://docs.python.org/3/library/concurrent.futures.html)
- [ThreadPoolExecutor](https://docs.python.org/3/library/concurrent.futures.html#threadpoolexecutor)
