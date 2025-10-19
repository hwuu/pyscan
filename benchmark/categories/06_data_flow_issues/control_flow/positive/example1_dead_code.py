"""
Control Flow Issues
演示不可达代码、恒真/恒假条件、无限循环等问题
"""

# Bug DATA-FLOW-001: 不可达代码
def process_data(data):
    """
    Bug: return 后的代码不可达

    风险:
    - 清理代码不会执行
    - 日志不会记录
    """
    if data is None:
        return None

    result = transform_data(data)
    return result

    # Bug: 以下代码永远不会执行
    log_processing(data)
    cleanup_temp_files()


# Bug DATA-FLOW-002: 恒真/恒假条件
def validate_age(age: int) -> bool:
    """
    Bug: 条件恒为假，代码不会执行

    风险:
    - 逻辑错误，判断无效
    """
    if age < 0:
        return False

    # Bug: 恒假条件 (1 == 2 永远为 False)
    if 1 == 2:
        return False

    # Bug: 恒真条件
    if True:
        pass  # 多余的条件

    return age >= 18


# Bug DATA-FLOW-003: 无限循环
def wait_for_signal():
    """
    Bug: while True 无 break，无限循环

    风险:
    - 函数永远不会返回
    - 占用 CPU 资源
    """
    while True:
        signal = check_signal()
        if signal:
            process_signal(signal)
        # Bug: 缺少 break 语句，无限循环


# Bug DATA-FLOW-004: 递归无终止条件
def process_recursive(n):
    """
    Bug: 递归函数缺少基本情况

    风险:
    - 递归无限深入
    - 最终 RecursionError
    """
    print(f"Processing {n}")
    result = compute(n)

    # Bug: 缺少终止条件，无限递归
    return process_recursive(n - 1) + result


# Helper functions
def transform_data(data):
    return data.upper() if isinstance(data, str) else data


def log_processing(data):
    print(f"Processed: {data}")


def cleanup_temp_files():
    print("Cleaning up temp files")


def check_signal():
    """模拟信号检查，总是返回 False"""
    return None


def process_signal(signal):
    print(f"Processing signal: {signal}")


def compute(n):
    return n * 2


if __name__ == "__main__":
    print("Control flow bugs (DANGEROUS)")

    # Bug DATA-FLOW-001: 不可达代码
    process_data("test")

    # Bug DATA-FLOW-002: 恒假条件
    print(validate_age(20))

    # Bug DATA-FLOW-003: 无限循环 (注释掉避免卡住)
    # wait_for_signal()

    # Bug DATA-FLOW-004: 无限递归 (注释掉避免栈溢出)
    # process_recursive(10)
