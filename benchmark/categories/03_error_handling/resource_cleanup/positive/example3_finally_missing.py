"""
Example 3: Missing finally block for cleanup

Bug: 缺少 finally 块导致资源未释放
Difficulty: Easy
"""


def acquire_and_use_lock(lock, data):
    """
    获取锁并使用（Bug: 缺少 finally 释放锁）

    Bug: 如果 process() 抛出异常，锁不会被释放，导致死锁
    """
    import threading

    lock.acquire()  # BUG: LOGIC-EXC-008
    try:
        result = process(data)
        return result
    except Exception as e:
        print(f"处理失败: {e}")
        return None
    # 缺少 finally: lock.release()


def process(data):
    """模拟处理函数"""
    if not data:
        raise ValueError("Empty data")
    return data.upper()


def manual_file_handling(filename):
    """
    手动文件处理（Bug: 异常时文件未关闭）

    Bug: 正常情况下文件会关闭，但异常时不会
    """
    f = open(filename, 'r')  # BUG: LOGIC-EXC-009
    try:
        data = f.read()
        result = process(data)
        f.close()  # 只在成功时关闭
        return result
    except ValueError:
        # 异常时文件未关闭
        return None


def set_flag_and_process(flag_holder, data):
    """
    设置标志并处理（Bug: 异常时标志未重置）

    Bug: processing 标志在异常时未重置为 False
    """
    flag_holder['processing'] = True  # BUG: LOGIC-EXC-010
    try:
        result = process(data)
        flag_holder['processing'] = False
        return result
    except Exception:
        # 异常时标志未重置，导致后续调用被阻塞
        print("处理失败")
        return None
