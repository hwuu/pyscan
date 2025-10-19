"""
Correct Lock/Semaphore/Condition Usage Examples
演示正确的同步原语使用，避免资源泄露
"""

import threading
import time

shared_counter = 0
counter_lock = threading.Lock()
semaphore = threading.Semaphore(3)
condition = threading.Condition()


# 正确示例 1: 使用 with 语句管理 Lock
def increment_counter_safe(value):
    """正确: with 语句自动释放锁"""
    global shared_counter
    with counter_lock:
        temp = shared_counter
        time.sleep(0.001)
        shared_counter = temp + value


# 正确示例 2: try/finally 释放锁
def increment_try_finally(value):
    """正确: try/finally 确保锁被释放"""
    global shared_counter
    counter_lock.acquire()
    try:
        shared_counter += value
    finally:
        counter_lock.release()


# 正确示例 3: Semaphore with 语句
def limited_resource_access_safe(resource_id):
    """正确: with 语句管理 semaphore"""
    with semaphore:
        print(f"Accessing resource {resource_id}")
        time.sleep(0.1)


# 正确示例 4: Condition with 语句
def producer_safe(item):
    """正确: with 语句管理 condition"""
    with condition:
        print(f"Producing {item}")
        condition.notify()


def consumer_safe():
    """正确: with 语句管理 condition"""
    with condition:
        condition.wait(timeout=1.0)
        print("Consumed item")


if __name__ == "__main__":
    print("✅ All locks are properly managed with context managers!")
