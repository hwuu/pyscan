"""
Lock/Semaphore/Condition Leak Examples
演示同步原语未释放导致的资源泄露和死锁
"""

import threading
import time


# 共享资源
shared_counter = 0
counter_lock = threading.Lock()
semaphore = threading.Semaphore(3)
condition = threading.Condition()


# Bug RM-SYNC-001: Lock 未释放
def increment_counter_unsafe(value):
    """
    Bug: Lock.acquire() 未配对 release()

    问题:
    - 获取锁后未释放
    - 其他线程永久阻塞
    - 导致死锁

    影响: Critical
    - 程序挂起
    - 其他线程无法访问资源

    CWE: CWE-667 (Improper Locking)
    """
    global shared_counter

    # Bug: acquire 后未 release
    counter_lock.acquire()

    # 模拟一些操作
    temp = shared_counter
    time.sleep(0.001)
    shared_counter = temp + value

    # Bug: 缺少 counter_lock.release()
    # 其他线程将永久等待这个锁


def conditional_lock_leak(condition_met):
    """
    Bug: 条件分支中锁未释放

    场景:
    - 某些分支释放锁
    - 其他分支泄露锁
    """
    global shared_counter

    counter_lock.acquire()

    if condition_met:
        shared_counter += 1
        counter_lock.release()  # 只在这个分支释放
        return True
    else:
        # Bug: 这个分支未释放锁
        return False


def exception_lock_leak(value):
    """
    Bug: 异常情况下锁未释放

    场景:
    - 正常路径释放锁
    - 异常路径泄露锁
    """
    global shared_counter

    counter_lock.acquire()

    # Bug: 如果这里抛出异常，锁不会被释放
    if value < 0:
        raise ValueError("Value must be non-negative")

    shared_counter += value
    counter_lock.release()


# Bug RM-SYNC-002: Semaphore 未释放
def limited_resource_access_unsafe(resource_id):
    """
    Bug: Semaphore.acquire() 无对应 release()

    问题:
    - 信号量获取后未释放
    - 可用资源计数递减
    - 最终耗尽所有资源

    影响:
    - 新请求永久阻塞
    - 资源利用率下降

    CWE: CWE-667 (Improper Locking)
    """
    # Bug: acquire 后未 release
    semaphore.acquire()
    print(f"Accessing resource {resource_id}")

    # 模拟资源使用
    time.sleep(0.1)

    # Bug: 缺少 semaphore.release()
    # 信号量计数不会恢复


def semaphore_exception_leak():
    """
    Bug: 异常时信号量未释放
    """
    semaphore.acquire()

    try:
        # Bug: 如果这里抛出异常，信号量不会释放
        result = 10 / 0
        return result
    except ZeroDivisionError:
        print("Math error occurred")
        # Bug: 异常处理中未释放信号量
        return None


def semaphore_early_return_leak(should_process):
    """
    Bug: 提前返回时信号量未释放
    """
    semaphore.acquire()

    if not should_process:
        # Bug: 提前返回，信号量未释放
        return None

    # 正常处理
    result = "processed"
    semaphore.release()
    return result


# Bug RM-SYNC-003: Condition 变量未释放
def producer_condition_leak(item):
    """
    Bug: Condition.wait() 未在 finally 中释放

    问题:
    - Condition 内部使用锁
    - 未正确释放导致死锁

    CWE: CWE-667 (Improper Locking)
    """
    # Bug: acquire 后未 release
    condition.acquire()

    # 模拟生产数据
    print(f"Producing {item}")

    # 通知消费者
    condition.notify()

    # Bug: 缺少 condition.release()


def consumer_condition_leak():
    """
    Bug: wait() 后未释放 condition
    """
    condition.acquire()

    # Bug: wait 可能永久阻塞，且之后未 release
    condition.wait(timeout=1.0)

    print("Consumed item")

    # Bug: 缺少 condition.release()


def condition_exception_leak():
    """
    Bug: 异常时 condition 未释放
    """
    condition.acquire()

    try:
        # Bug: 异常时 condition 不会被释放
        raise RuntimeError("Something went wrong")
    except RuntimeError:
        print("Error handled")
        # Bug: 异常处理中未释放


# 混合错误：多个锁同时泄露
def multiple_locks_leak():
    """
    Bug: 多个锁都未释放

    场景:
    - 获取多个锁
    - 都未释放
    - 死锁风险极高
    """
    lock1 = threading.Lock()
    lock2 = threading.Lock()

    # Bug: 两个锁都未释放
    lock1.acquire()
    lock2.acquire()

    print("Critical section")

    # Bug: 缺少 lock1.release() 和 lock2.release()


if __name__ == "__main__":
    print("=== Demonstrating Lock/Semaphore/Condition Leaks ===")
    print("\n!!! WARNING: These examples contain REAL deadlock bugs !!!")
    print("!!! Running these will cause threads to hang !!!\n")

    # 示例 1: Lock 泄露（会导致死锁）
    print("1. Lock leak (COMMENTED OUT - would cause deadlock):")
    print("   thread = threading.Thread(target=increment_counter_unsafe, args=(1,))")
    print("   thread.start()")
    # thread = threading.Thread(target=increment_counter_unsafe, args=(1,))
    # thread.start()
    # thread.join()
    # 第二个线程将永久阻塞：
    # thread2 = threading.Thread(target=increment_counter_unsafe, args=(2,))
    # thread2.start()  # 这个线程会永久等待

    # 示例 2: Semaphore 泄露
    print("\n2. Semaphore leak (COMMENTED OUT):")
    print("   for i in range(5):")
    print("       limited_resource_access_unsafe(i)")
    # 前3次成功，第4次开始永久阻塞

    # 示例 3: Condition 泄露
    print("\n3. Condition leak (COMMENTED OUT):")
    print("   producer_condition_leak('item1')")
    # 后续任何使用 condition 的代码都会阻塞

    print("\nAll dangerous calls are commented out for safety.")
