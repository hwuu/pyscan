"""
Deadlock Risk - Callback and Wait Examples
演示锁内调用回调和锁内等待导致的死锁
"""

import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor

# Bug CONC-DEAD-002: 锁内调用回调导致死锁
class EventManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.callbacks = []
    
    def register_callback(self, callback):
        with self.lock:
            self.callbacks.append(callback)
    
    def trigger_event(self, data):
        """Bug: 持有锁时调用用户回调，可能死锁"""
        with self.lock:  # Bug: 获取锁
            for callback in self.callbacks:
                # Bug: 持有锁时调用未知代码，callback 可能尝试获取同一个锁
                callback(data)

# Bug CONC-DEAD-003: 锁内等待异步结果导致死锁  
class DataProcessor:
    def __init__(self):
        self.lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    def process_data(self, data):
        """Bug: 持有锁时等待 Future 结果"""
        with self.lock:  # Bug: 获取锁
            # 提交异步任务
            future = self.executor.submit(self._process_async, data)
            # Bug: 持有锁等待结果，如果 _process_async 需要同一个锁则死锁
            result = future.result()  
            return result
    
    def _process_async(self, data):
        # 如果这里尝试获取 self.lock，将导致死锁
        time.sleep(0.1)
        return data * 2

if __name__ == "__main__":
    print("Deadlock risk examples created")
