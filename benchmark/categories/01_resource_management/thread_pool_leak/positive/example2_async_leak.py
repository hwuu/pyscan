"""
Example 2: ThreadPoolExecutor leak in async function (BUG_0010 simplified)

Bug: 异步函数中每次调用都创建新线程池但未关闭
Difficulty: Medium
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor


async def run_in_thread_pool(func, *args, **kwargs):
    """
    在线程池中运行函数（BUG_0010 简化版）

    Bug: 每次调用都创建新的 ThreadPoolExecutor 但未关闭
    """
    executor = ThreadPoolExecutor(max_workers=1)  # BUG: RM-TPL-003
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, func, *args, **kwargs)
    return result  # executor 未关闭，长期运行会累积大量线程


def blocking_task(x):
    """模拟阻塞任务"""
    return x * 2


async def main():
    """主函数：多次调用会创建多个未关闭的线程池"""
    results = []
    for i in range(10):
        result = await run_in_thread_pool(blocking_task, i)
        results.append(result)
    # 10 个 ThreadPoolExecutor 实例泄露
    return results
