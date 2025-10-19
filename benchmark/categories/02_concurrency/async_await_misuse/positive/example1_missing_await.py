"""
Async/Await Misuse Examples - Missing await
演示异步函数调用中忘记 await 导致的问题
"""

import asyncio
import time


# Bug CONC-ASYNC-001: 忘记 await 异步函数
async def fetch_data(url):
    """
    模拟异步数据获取
    """
    print(f"Fetching data from {url}...")
    await asyncio.sleep(1)  # 模拟网络延迟
    return f"Data from {url}"


async def process_item(item):
    """
    模拟异步处理
    """
    print(f"Processing {item}...")
    await asyncio.sleep(0.5)
    return f"Processed: {item}"


async def process_items():
    """
    Bug: 调用异步函数时忘记 await

    问题:
    1. fetch_data() 和 process_item() 返回 coroutine 对象,不是实际结果
    2. 代码不会等待异步操作完成
    3. 可能导致逻辑错误或数据不完整

    影响: High - 程序行为不符合预期
    CWE: CWE-1088 (Synchronous Access of Remote Resource without Timeout)
    """
    items = ["item1", "item2", "item3"]
    results = []

    for item in items:
        # Bug: 忘记 await,返回的是 coroutine 对象而不是实际数据
        data = fetch_data(f"http://api.example.com/{item}")  # Bug: 缺少 await
        result = process_item(data)  # Bug: 缺少 await

        # data 和 result 都是 coroutine 对象,不是字符串
        results.append(result)
        print(f"Added result: {result}")  # 会打印 <coroutine object>

    return results


async def calculate_total():
    """
    Bug: 忘记 await 导致类型错误

    问题:
    1. get_value() 返回 coroutine,不是 int
    2. 无法进行数值计算
    3. 运行时可能抛出 TypeError
    """
    async def get_value(key):
        await asyncio.sleep(0.1)
        values = {'a': 10, 'b': 20, 'c': 30}
        return values.get(key, 0)

    # Bug: 忘记 await
    a = get_value('a')  # Bug: 返回 coroutine,不是 10
    b = get_value('b')  # Bug: 返回 coroutine,不是 20

    # TypeError: unsupported operand type(s) for +: 'coroutine' and 'coroutine'
    try:
        total = a + b  # Bug: 无法计算
        return total
    except TypeError as e:
        print(f"Error: {e}")
        return None


async def mixed_async_sync():
    """
    Bug: 混淆异步和同步调用

    问题:
    1. 部分调用有 await,部分没有
    2. 代码难以理解和维护
    3. 容易引入 bug
    """
    async def async_task(n):
        await asyncio.sleep(0.1)
        return n * 2

    # 正确: 有 await
    result1 = await async_task(5)

    # Bug: 忘记 await
    result2 = async_task(10)  # Bug: 返回 coroutine

    # Bug: 假设 result2 是 int,实际是 coroutine
    print(f"Result 1: {result1}")  # 正确: 10
    print(f"Result 2: {result2}")  # Bug: <coroutine object async_task>

    # Bug: 无法进行计算
    try:
        total = result1 + result2  # TypeError
    except TypeError as e:
        print(f"Error in calculation: {e}")


async def fire_and_forget_issue():
    """
    Bug: "Fire and forget" 模式误用

    问题:
    1. 创建了异步任务但不等待
    2. 任务可能还未完成,函数就返回了
    3. 可能导致资源泄露或数据不一致
    """
    async def save_to_database(data):
        await asyncio.sleep(1)
        print(f"Saved to database: {data}")

    async def send_notification(user):
        await asyncio.sleep(0.5)
        print(f"Sent notification to {user}")

    # Bug: 创建任务但不等待完成
    save_to_database("important data")  # Bug: 忘记 await
    send_notification("admin")  # Bug: 忘记 await

    print("Function returned!")
    # 此时 save_to_database 和 send_notification 可能还未完成
    # 如果主程序退出,这些任务可能被取消


async def main():
    """
    演示忘记 await 的各种问题
    """
    print("=== Example 1: Missing await in loop ===")
    results = await process_items()
    print(f"Results: {results}")
    print(f"Results type: {[type(r).__name__ for r in results]}")

    print("\n=== Example 2: Missing await in calculation ===")
    total = await calculate_total()
    print(f"Total: {total}")

    print("\n=== Example 3: Mixed async/sync ===")
    await mixed_async_sync()

    print("\n=== Example 4: Fire and forget ===")
    await fire_and_forget_issue()
    # 给一点时间让任务运行
    await asyncio.sleep(1.5)


if __name__ == "__main__":
    # 运行异步 main 函数
    asyncio.run(main())
