"""
Correct Lock Ordering to Prevent Deadlock
演示正确的锁顺序管理,避免死锁
"""

import threading
import time


# 共享资源
account_locks = {
    'A': threading.Lock(),
    'B': threading.Lock(),
    'C': threading.Lock()
}

balances = {
    'A': 1000,
    'B': 2000,
    'C': 3000
}


# 正确示例 1: 固定锁顺序避免死锁
def transfer_funds_correct(from_account, to_account, amount):
    """
    正确: 总是按字母顺序获取锁

    关键策略:
    1. 确定全局锁顺序(如按账户名排序)
    2. 所有线程按相同顺序获取锁
    3. 避免循环等待条件

    优点:
    - 完全消除死锁可能性
    - 逻辑简单,易于维护
    """
    print(f"[{threading.current_thread().name}] Transferring {amount} from {from_account} to {to_account}")

    # 关键: 按字母顺序获取锁,确保所有线程的锁顺序一致
    first_account = min(from_account, to_account)
    second_account = max(from_account, to_account)

    first_lock = account_locks[first_account]
    second_lock = account_locks[second_account]

    # 总是先获取字母序较小的锁
    first_lock.acquire()
    print(f"[{threading.current_thread().name}] Acquired lock for {first_account}")

    second_lock.acquire()
    print(f"[{threading.current_thread().name}] Acquired lock for {second_account}")

    try:
        if balances[from_account] >= amount:
            balances[from_account] -= amount
            balances[to_account] += amount
            print(f"[{threading.current_thread().name}] Transfer successful")
        else:
            print(f"[{threading.current_thread().name}] Insufficient funds")
    finally:
        second_lock.release()
        first_lock.release()


# 正确示例 2: 使用 context manager 确保锁顺序
class OrderedLockManager:
    """
    正确: 封装锁顺序逻辑的上下文管理器

    优点:
    1. 自动管理锁的获取和释放
    2. 代码更简洁,不易出错
    3. 可重用
    """
    def __init__(self, *lock_ids):
        self.lock_ids = sorted(lock_ids)  # 排序确保顺序
        self.locks = [account_locks[lid] for lid in self.lock_ids]

    def __enter__(self):
        for lock in self.locks:
            lock.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for lock in reversed(self.locks):  # 逆序释放
            lock.release()


def transfer_with_manager(from_account, to_account, amount):
    """
    正确: 使用 OrderedLockManager 管理锁
    """
    with OrderedLockManager(from_account, to_account):
        if balances[from_account] >= amount:
            balances[from_account] -= amount
            balances[to_account] += amount
            print(f"Transfer {amount} from {from_account} to {to_account} successful")
        else:
            print(f"Transfer failed: insufficient funds in {from_account}")


# 正确示例 3: 使用单一全局锁
global_lock = threading.Lock()

def transfer_with_global_lock(from_account, to_account, amount):
    """
    正确: 使用单一全局锁保护所有操作

    优点:
    1. 完全避免死锁
    2. 实现简单

    缺点:
    - 并发性能较低(所有转账串行化)
    - 适用于低并发场景
    """
    with global_lock:
        if balances[from_account] >= amount:
            balances[from_account] -= amount
            balances[to_account] += amount
            return True
        return False


# 正确示例 4: 使用 try-lock 模式避免死锁
def transfer_with_trylock(from_account, to_account, amount, timeout=1.0):
    """
    正确: 使用 try-lock 模式,失败时回退

    策略:
    1. 尝试获取锁,设置超时
    2. 如果失败,释放已获取的锁,稍后重试
    3. 避免无限等待

    优点:
    - 即使锁顺序不一致,也能避免永久死锁
    - 提供更好的用户体验(超时返回)
    """
    from_lock = account_locks[from_account]
    to_lock = account_locks[to_account]

    # 尝试获取第一个锁
    if not from_lock.acquire(timeout=timeout):
        return False, "Failed to acquire source account lock"

    try:
        # 尝试获取第二个锁
        if not to_lock.acquire(timeout=timeout):
            return False, "Failed to acquire target account lock"

        try:
            if balances[from_account] >= amount:
                balances[from_account] -= amount
                balances[to_account] += amount
                return True, "Transfer successful"
            else:
                return False, "Insufficient funds"
        finally:
            to_lock.release()
    finally:
        from_lock.release()


def demonstrate_no_deadlock():
    """
    演示正确的锁管理,不会发生死锁
    """
    print("=== Demonstrating Deadlock-Free Transfer ===")

    # 场景 1: 双向转账,使用固定锁顺序
    t1 = threading.Thread(
        target=transfer_funds_correct,
        args=('A', 'B', 100),
        name="Transfer-A-to-B"
    )
    t2 = threading.Thread(
        target=transfer_funds_correct,
        args=('B', 'A', 50),
        name="Transfer-B-to-A"
    )

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    print("\n✅ All transfers completed successfully, no deadlock!")
    print(f"Final balances: {balances}")


def demonstrate_lock_manager():
    """
    演示使用 context manager
    """
    print("\n=== Using Lock Manager ===")
    t1 = threading.Thread(target=transfer_with_manager, args=('A', 'C', 200))
    t2 = threading.Thread(target=transfer_with_manager, args=('C', 'A', 100))

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    print(f"Final balances: {balances}")


if __name__ == "__main__":
    demonstrate_no_deadlock()
    demonstrate_lock_manager()
