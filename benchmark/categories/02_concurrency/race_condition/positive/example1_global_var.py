"""
Example 1: Global variable race condition - 全局变量竞态条件

Bug: 多线程访问全局变量未加锁
Difficulty: Easy
"""

# 全局变量
counter = 0
cache_data = {}


def increment_counter():
    """增加计数器（BUG: 竞态条件）"""
    global counter
    counter += 1  # BUG: CONC-RC-001 读-修改-写不是原子操作


def update_cache(key, value):
    """更新缓存（BUG: 竞态条件）"""
    global cache_data
    cache_data[key] = value  # BUG: CONC-RC-002 字典操作未加锁


def get_and_increment():
    """获取并增加（BUG: 复合操作竞态）"""
    global counter
    old_value = counter  # BUG: CONC-RC-003
    counter = old_value + 1
    return old_value  # 竞态条件：读和写之间可能被其他线程修改
