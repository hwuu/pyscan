"""
Race Condition Extended Examples - Singleton, Lazy Init, Counter
"""

import threading
import time

# Bug CONC-RACE-007: 单例模式竞态
class Singleton:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:  # Bug: 双重检查不正确
            time.sleep(0.001)  # 模拟初始化延迟
            cls._instance = super().__new__(cls)
        return cls._instance

# Bug CONC-RACE-008: 懒加载竞态
class LazyResource:
    _resource = None
    
    @classmethod
    def get_resource(cls):
        if cls._resource is None:  # Bug: 无锁保护
            cls._resource = {"initialized": True}
        return cls._resource

# Bug CONC-RACE-009: 计数器竞态  
counter = 0

def increment_counter():
    global counter
    temp = counter  # Bug: 非原子操作
    time.sleep(0.0001)
    counter = temp + 1
