"""
Negative Example: Correct ThreadPoolExecutor usage

正确做法：使用 with 语句或显式 shutdown
"""

from concurrent.futures import ThreadPoolExecutor
import asyncio


def run_tasks_correct(tasks):
    """正确：使用 with 语句"""
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(process_task, task) for task in tasks]
        results = [f.result() for f in futures]
    # executor 自动 shutdown()
    return results


def run_single_task_correct(task_func):
    """正确：显式 shutdown"""
    executor = ThreadPoolExecutor(max_workers=1)
    try:
        future = executor.submit(task_func)
        result = future.result()
        return result
    finally:
        executor.shutdown(wait=True)


async def run_in_thread_pool_correct(func, *args, **kwargs):
    """正确：使用 with 语句"""
    with ThreadPoolExecutor(max_workers=1) as executor:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(executor, func, *args, **kwargs)
    return result


def process_task(task):
    """模拟任务处理"""
    return task * 2
