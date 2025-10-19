"""
Correct Async/Await Usage Examples
演示正确的异步函数调用方式
"""

import asyncio


# 正确示例 1: 正确使用 await
async def fetch_data(url):
    """模拟异步数据获取"""
    print(f"Fetching data from {url}...")
    await asyncio.sleep(1)
    return f"Data from {url}"


async def process_item(item):
    """模拟异步处理"""
    print(f"Processing {item}...")
    await asyncio.sleep(0.5)
    return f"Processed: {item}"


async def process_items_correct():
    """
    正确: 所有异步调用都使用 await

    关键:
    1. 调用异步函数时使用 await 关键字
    2. 确保获取实际结果,而不是 coroutine 对象
    3. 代码按预期顺序执行
    """
    items = ["item1", "item2", "item3"]
    results = []

    for item in items:
        # 正确: 使用 await 等待异步操作完成
        data = await fetch_data(f"http://api.example.com/{item}")
        result = await process_item(data)

        # data 和 result 都是字符串,不是 coroutine
        results.append(result)
        print(f"Added result: {result}")

    return results


# 正确示例 2: 并发执行多个异步任务
async def process_items_concurrent():
    """
    正确: 使用 asyncio.gather 并发执行

    优点:
    1. 多个任务并行执行,提升性能
    2. 使用 await 等待所有任务完成
    3. 自动收集所有结果
    """
    items = ["item1", "item2", "item3"]

    # 创建所有任务
    fetch_tasks = [
        fetch_data(f"http://api.example.com/{item}")
        for item in items
    ]

    # 并发执行所有 fetch,等待全部完成
    fetched_data = await asyncio.gather(*fetch_tasks)

    # 处理获取的数据
    process_tasks = [
        process_item(data)
        for data in fetched_data
    ]

    # 并发执行所有 process
    results = await asyncio.gather(*process_tasks)

    return results


# 正确示例 3: 使用 Task 对象管理异步任务
async def process_with_tasks():
    """
    正确: 使用 create_task 创建任务,稍后 await

    优点:
    1. 任务立即开始执行(不等待 await)
    2. 可以在多个任务之间切换
    3. 提供更灵活的控制
    """
    # 创建任务(立即开始执行)
    task1 = asyncio.create_task(fetch_data("url1"))
    task2 = asyncio.create_task(fetch_data("url2"))
    task3 = asyncio.create_task(fetch_data("url3"))

    # 等待所有任务完成
    results = await asyncio.gather(task1, task2, task3)

    return results


# 正确示例 4: 正确的 fire-and-forget 模式
async def background_tasks_correct():
    """
    正确: 如果确实需要 fire-and-forget,使用 create_task 并保存引用

    注意:
    1. 创建 Task 对象,确保任务被调度
    2. 如果不需要等待结果,至少保存 Task 引用
    3. 在程序退出前考虑取消或等待任务
    """
    async def save_to_database(data):
        await asyncio.sleep(1)
        print(f"Saved to database: {data}")

    async def send_notification(user):
        await asyncio.sleep(0.5)
        print(f"Sent notification to {user}")

    # 正确: 使用 create_task 创建后台任务
    save_task = asyncio.create_task(save_to_database("important data"))
    notify_task = asyncio.create_task(send_notification("admin"))

    # 可以选择等待或不等待
    # 如果需要确保完成,可以在适当时机 await
    await asyncio.gather(save_task, notify_task)

    print("All background tasks completed!")


# 正确示例 5: 处理异常
async def handle_errors_correctly():
    """
    正确: await 异步调用并处理异常

    优点:
    1. 异常能被正确捕获
    2. 可以进行错误处理
    """
    async def risky_operation():
        await asyncio.sleep(0.1)
        raise ValueError("Something went wrong")

    try:
        # 正确: await 异步调用
        result = await risky_operation()
    except ValueError as e:
        print(f"Caught exception: {e}")
        result = None

    return result


# 正确示例 6: 使用 asyncio.wait_for 设置超时
async def with_timeout():
    """
    正确: 为异步操作设置超时

    优点:
    1. 避免无限等待
    2. 提供更好的用户体验
    """
    async def slow_operation():
        await asyncio.sleep(10)
        return "Done"

    try:
        # 设置 2 秒超时
        result = await asyncio.wait_for(slow_operation(), timeout=2.0)
    except asyncio.TimeoutError:
        print("Operation timed out")
        result = None

    return result


async def main():
    """演示正确的异步使用"""
    print("=== Sequential processing ===")
    results = await process_items_correct()
    print(f"Results: {results}")

    print("\n=== Concurrent processing ===")
    results = await process_items_concurrent()
    print(f"Results: {results}")

    print("\n=== Using tasks ===")
    results = await process_with_tasks()
    print(f"Results: {results}")

    print("\n=== Background tasks ===")
    await background_tasks_correct()

    print("\n=== Error handling ===")
    result = await handle_errors_correctly()
    print(f"Result: {result}")

    print("\n=== With timeout ===")
    result = await with_timeout()
    print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
