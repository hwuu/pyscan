"""
Example 1: Public API missing input validation

Bug: 公共 API 缺少参数校验
Difficulty: Medium
"""


def create_user(username, email, age):
    """
    创建用户（Bug: 缺少参数校验）

    Bug: 作为公共 API，应该验证所有参数
    """
    # BUG: API-VAL-001 - 缺少参数校验
    # 应该检查:
    # - username: 非空，长度限制，字符限制
    # - email: 格式验证
    # - age: 类型检查，范围验证

    user = {
        'username': username,
        'email': email,
        'age': age,
        'created_at': '2024-01-01'
    }
    return user


def update_config(key, value):
    """
    更新配置（Bug: 缺少 key 白名单验证）

    Bug: 允许任意 key，可能覆盖敏感配置
    """
    # BUG: API-VAL-002 - 缺少 key 白名单
    # 应该只允许特定的配置键

    global_config = {}
    global_config[key] = value
    return True


def set_user_role(user_id, role):
    """
    设置用户角色（Bug: 缺少角色验证）

    Bug: 允许任意角色字符串，可能导致权限提升
    """
    # BUG: API-VAL-003 - 缺少角色白名单
    # 应该只允许 ['user', 'admin', 'moderator']

    users_db = {}
    users_db[user_id] = {'role': role}
    return True


def search_users(query, limit=100):
    """
    搜索用户（Bug: 缺少 limit 范围验证）

    Bug: limit 可能是负数或超大值，导致资源耗尽
    """
    # BUG: API-VAL-004 - 缺少范围验证
    # 应该验证 0 < limit <= 1000

    results = []
    # 查询数据库，返回 limit 条结果
    return results[:limit]


def delete_file(file_path):
    """
    删除文件（Bug: 公共 API 缺少权限和路径验证）

    Bug: 允许删除任意路径文件
    """
    import os

    # BUG: API-VAL-005 - 缺少路径验证
    # 应该验证路径在允许的目录内

    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False
