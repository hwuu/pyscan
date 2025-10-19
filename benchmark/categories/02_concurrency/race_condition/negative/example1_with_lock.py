"""
Negative Example: Correct thread-safe implementation

正确做法：使用锁保护共享资源
"""

import threading

# 全局变量 + 锁
counter = 0
counter_lock = threading.Lock()

cache_data = {}
cache_lock = threading.Lock()


def increment_counter_safe():
    """正确：使用锁保护全局变量"""
    global counter
    with counter_lock:
        counter += 1  # 线程安全


def update_cache_safe(key, value):
    """正确：使用锁保护字典操作"""
    global cache_data
    with cache_lock:
        cache_data[key] = value


def get_and_increment_safe():
    """正确：原子复合操作"""
    global counter
    with counter_lock:
        old_value = counter
        counter = old_value + 1
        return old_value  # 整个操作在锁内，线程安全


class ThreadSafeCounter:
    """正确：线程安全计数器"""

    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()

    def increment(self):
        with self.lock:
            self.value += 1
            return self.value


class GlobalStateSafe:
    """正确：带锁的全局状态"""

    def __init__(self):
        self.detector = None
        self.config = {}
        self.lock = threading.RLock()  # 可重入锁

    def set_detector(self, detector_instance):
        with self.lock:
            self.detector = detector_instance

    def update_config(self, key, value):
        with self.lock:
            self.config[key] = value
