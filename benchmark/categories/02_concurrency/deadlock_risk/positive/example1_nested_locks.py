"""
Deadlock Risk Examples - Nested Lock Ordering
演示嵌套锁顺序不一致导致的死锁风险
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


# Bug CONC-DEAD-001: 嵌套锁顺序不一致导致死锁
def transfer_funds(from_account, to_account, amount):
    """
    Bug: 两个线程以不同顺序获取锁,导致死锁

    场景:
    - Thread 1: transfer_funds('A', 'B', 100)  # 先锁 A,后锁 B
    - Thread 2: transfer_funds('B', 'A', 50)   # 先锁 B,后锁 A

    死锁发生:
    1. Thread 1 获取 lock_A,等待 lock_B
    2. Thread 2 获取 lock_B,等待 lock_A
    3. 两个线程互相等待,永久阻塞

    影响: Critical - 系统完全挂起
    CWE: CWE-833 (Deadlock)
    """
    print(f"[{threading.current_thread().name}] Transferring {amount} from {from_account} to {to_account}")

    from_lock = account_locks[from_account]
    to_lock = account_locks[to_account]

    # Bug: 锁的获取顺序取决于参数,可能导致死锁
    from_lock.acquire()
    print(f"[{threading.current_thread().name}] Acquired lock for {from_account}")
    time.sleep(0.01)  # 模拟处理时间,增加死锁概率

    to_lock.acquire()  # Bug: 可能在此处死锁
    print(f"[{threading.current_thread().name}] Acquired lock for {to_account}")

    try:
        if balances[from_account] >= amount:
            balances[from_account] -= amount
            balances[to_account] += amount
            print(f"[{threading.current_thread().name}] Transfer successful")
        else:
            print(f"[{threading.current_thread().name}] Insufficient funds")
    finally:
        to_lock.release()
        from_lock.release()


def circular_dependency_example():
    """
    Bug: 循环依赖导致死锁

    场景:
    - Thread 1: A → B → C
    - Thread 2: C → A
    - Thread 3: B → C → A

    形成循环等待,导致死锁
    """
    def worker_1():
        with account_locks['A']:
            time.sleep(0.01)
            with account_locks['B']:  # Bug: 可能死锁
                time.sleep(0.01)
                with account_locks['C']:
                    print("Worker 1 completed")

    def worker_2():
        with account_locks['C']:
            time.sleep(0.01)
            with account_locks['A']:  # Bug: 循环依赖
                print("Worker 2 completed")

    def worker_3():
        with account_locks['B']:
            time.sleep(0.01)
            with account_locks['C']:
                time.sleep(0.01)
                with account_locks['A']:  # Bug: 循环依赖
                    print("Worker 3 completed")

    t1 = threading.Thread(target=worker_1, name="Worker-1")
    t2 = threading.Thread(target=worker_2, name="Worker-2")
    t3 = threading.Thread(target=worker_3, name="Worker-3")

    t1.start()
    t2.start()
    t3.start()

    t1.join(timeout=2)
    t2.join(timeout=2)
    t3.join(timeout=2)

    if t1.is_alive() or t2.is_alive() or t3.is_alive():
        print("Deadlock detected! Some threads are still waiting...")


def demonstrate_deadlock():
    """
    演示死锁场景

    运行多次,可能出现死锁(线程永久阻塞)
    """
    print("=== Demonstrating Deadlock Risk ===")

    # 场景 1: 双向转账导致死锁
    t1 = threading.Thread(
        target=transfer_funds,
        args=('A', 'B', 100),
        name="Transfer-A-to-B"
    )
    t2 = threading.Thread(
        target=transfer_funds,
        args=('B', 'A', 50),
        name="Transfer-B-to-A"
    )

    t1.start()
    t2.start()

    # 设置超时,避免测试永久挂起
    t1.join(timeout=2)
    t2.join(timeout=2)

    if t1.is_alive() or t2.is_alive():
        print("\n!!! DEADLOCK DETECTED !!!")
        print("Threads are blocked waiting for each other")
    else:
        print("\nNo deadlock this time (lucky!)")

    print(f"\nFinal balances: {balances}")


if __name__ == "__main__":
    demonstrate_deadlock()
    print("\n" + "="*50 + "\n")
    circular_dependency_example()
