"""
Example 2: Inconsistent return types

Bug: 返回值类型不一致
Difficulty: Medium
"""


def get_user_by_id(user_id):
    """
    获取用户（Bug: 返回类型不一致）

    Bug: 成功返回 dict，失败返回 None 或抛出异常
    """
    users_db = {
        1: {'name': 'Alice', 'age': 30},
        2: {'name': 'Bob', 'age': 25}
    }

    # BUG: API-RET-001 - 返回类型不一致
    if user_id in users_db:
        return users_db[user_id]  # 返回 dict
    elif user_id < 0:
        raise ValueError("Invalid user_id")  # 抛出异常
    else:
        return None  # 返回 None

    # 应该统一：始终返回 dict 或 None，或始终抛出异常


def calculate_average(numbers):
    """
    计算平均值（Bug: 返回类型不一致）

    Bug: 空列表返回 0，非空列表返回 float
    """
    # BUG: API-RET-002
    if not numbers:
        return 0  # int
    return sum(numbers) / len(numbers)  # float

    # 应该统一返回 float 或抛出异常


def find_items(query):
    """
    查找项目（Bug: 返回类型不一致）

    Bug: 找到返回列表，未找到返回 False
    """
    items_db = ['apple', 'banana', 'cherry']

    # BUG: API-RET-003
    results = [item for item in items_db if query in item]

    if results:
        return results  # list
    else:
        return False  # bool

    # 应该始终返回列表（空列表表示未找到）


def parse_json_response(response_text):
    """
    解析 JSON 响应（Bug: 返回类型不一致）

    Bug: 成功返回 dict，失败返回字符串错误消息
    """
    import json

    # BUG: API-RET-004
    try:
        return json.loads(response_text)  # dict
    except json.JSONDecodeError:
        return "Invalid JSON"  # str

    # 应该抛出异常或返回 None


def get_config_value(key, default=None):
    """
    获取配置值（Bug: default 类型不确定）

    Bug: 返回值类型取决于 default 参数
    """
    config = {'timeout': 30, 'debug': True}

    # BUG: API-RET-005
    return config.get(key, default)

    # 问题：如果 key='timeout' 返回 int
    #      如果 key='missing' 且 default='default' 返回 str
    #      调用者无法确定返回类型
