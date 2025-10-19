# Race Condition - 竞态条件

## Bug 描述

多个线程同时访问共享资源（全局变量、类成员等）而未进行同步，导致数据竞争和不确定行为。

## 常见模式

### 1. 全局变量未加锁

```python
# Bad
counter = 0

def increment():
    global counter
    counter += 1  # 竞态条件：读-修改-写不是原子操作
```

### 2. 类成员变量竞争

```python
# Bad
class Cache:
    def __init__(self):
        self.data = {}

    def set(self, key, value):
        self.data[key] = value  # 多线程访问未同步
```

### 3. 检查-使用时间窗口（TOCTOU）

```python
# Bad
if key in cache:
    # 另一线程可能在这里删除 key
    value = cache[key]  # KeyError 风险
```

## 正确做法

### 1. 使用锁保护

```python
# Good
import threading

counter = 0
counter_lock = threading.Lock()

def increment():
    global counter
    with counter_lock:
        counter += 1  # 线程安全
```

### 2. 使用线程安全数据结构

```python
# Good
from queue import Queue

task_queue = Queue()  # 内置线程安全

def add_task(task):
    task_queue.put(task)
```

### 3. 使用原子操作

```python
# Good
import threading

class AtomicCounter:
    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()

    def increment(self):
        with self.lock:
            self.value += 1
            return self.value
```

## 检测方法

### 静态分析

1. **检测全局变量写入**：查找对全局变量的赋值操作
2. **推断多线程调用**：通过 inferred_callers 判断函数是否可能被多线程调用
3. **检查同步机制**：判断是否有 `Lock`, `RLock`, `with lock:` 等保护

### 难度等级

- **Easy**: 明显的全局变量写入，无锁保护
- **Medium**: 类成员变量竞争，需分析调用上下文
- **Hard**: 复杂的 TOCTOU 问题，需数据流分析

## 相关 Bug

- BUG_0002: `init_logger_with_config` 使用 MultiProcessingRFHandler 未检查多进程安全
- BUG_0005: `start` 函数中 global_vars.DFA_DETECTOR 赋值和访问存在竞态条件

## CWE 分类

- **CWE-362**: Concurrent Execution using Shared Resource with Improper Synchronization ('Race Condition')
- **CWE-366**: Race Condition within a Thread
- **CWE-367**: Time-of-check Time-of-use (TOCTOU) Race Condition

## 参考资料

- [Python threading — Thread-based parallelism](https://docs.python.org/3/library/threading.html)
- [Python GIL and Thread Safety](https://realpython.com/python-gil/)
- [CWE-362: Race Condition](https://cwe.mitre.org/data/definitions/362.html)
