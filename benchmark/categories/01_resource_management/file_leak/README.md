# File Leak - 文件泄露

## Bug 描述

文件句柄未正确关闭，导致资源泄露。长期运行的程序可能耗尽系统文件描述符。

## 常见模式

### 1. 未使用 with 语句

```python
# Bad
f = open("data.txt", "r")
content = f.read()
# 缺少 f.close()
```

### 2. 异常路径下未关闭

```python
# Bad
f = open("data.txt", "r")
try:
    process(f.read())
except Exception:
    return  # f 未关闭
f.close()
```

### 3. 多个 return 路径

```python
# Bad
def read_data():
    f = open("data.txt", "r")
    if condition:
        return f.read()  # f 未关闭
    data = f.read()
    f.close()
    return data
```

## 正确做法

### 1. 使用 with 语句（推荐）

```python
# Good
with open("data.txt", "r") as f:
    content = f.read()
# 自动关闭
```

### 2. try-finally 显式关闭

```python
# Good
f = open("data.txt", "r")
try:
    content = f.read()
finally:
    f.close()
```

## 检测方法

### 静态分析

1. **检测 open() 调用**：查找未在 with 语句中的 open() 调用
2. **追踪变量**：检查赋值后是否有对应的 .close() 调用
3. **分析控制流**：检查所有路径是否都释放资源

### 难度等级

- **Easy**: 单一路径未关闭
- **Medium**: 异常路径未关闭
- **Hard**: 复杂控制流、多个 return 路径

## 相关 Bug

- BUG_0001: `init_logger_with_config` 返回的 logging_handler 未关闭
- BUG_0011: `async_write_file` 中文件未使用 with 语句

## CWE 分类

- **CWE-404**: Improper Resource Shutdown or Release
- **CWE-772**: Missing Release of Resource after Effective Lifetime

## 参考资料

- [Python Context Managers](https://docs.python.org/3/reference/datamodel.html#context-managers)
- [PEP 343 – The "with" Statement](https://peps.python.org/pep-0343/)
