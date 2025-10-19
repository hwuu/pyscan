"""
Example 1: ThreadPoolExecutor without shutdown

Bug: 线程池创建后未调用 shutdown()
Difficulty: Easy
"""

from concurrent.futures import ThreadPoolExecutor


def run_tasks_simple(tasks):
    """简单示例：线程池未关闭"""
    executor = ThreadPoolExecutor(max_workers=4)  # BUG: RM-TPL-001
    for task in tasks:
        executor.submit(process_task, task)
    # 缺少 executor.shutdown()


def run_single_task(task_func):
    """单个任务：线程池未关闭"""
    executor = ThreadPoolExecutor(max_workers=1)  # BUG: RM-TPL-002
    future = executor.submit(task_func)
    result = future.result()
    return result  # executor 未关闭


def process_task(task):
    """模拟任务处理"""
    return task * 2
