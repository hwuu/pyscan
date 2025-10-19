"""
Negative Example: Well-designed public API with validation

正确做法：完整的参数校验和一致的返回类型
"""

import re
from typing import Dict, List, Optional


def create_user_safe(username: str, email: str, age: int) -> Dict:
    """正确：完整的参数校验"""
    # 验证 username
    if not username or not isinstance(username, str):
        raise ValueError("Username must be a non-empty string")
    if len(username) < 3 or len(username) > 50:
        raise ValueError("Username must be 3-50 characters")
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        raise ValueError("Username can only contain letters, numbers, and underscores")

    # 验证 email
    if not email or not isinstance(email, str):
        raise ValueError("Email must be a non-empty string")
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValueError("Invalid email format")

    # 验证 age
    if not isinstance(age, int):
        raise TypeError("Age must be an integer")
    if age < 0 or age > 150:
        raise ValueError("Age must be between 0 and 150")

    user = {
        'username': username,
        'email': email,
        'age': age,
        'created_at': '2024-01-01'
    }
    return user


def update_config_safe(key: str, value) -> bool:
    """正确：使用白名单验证配置键"""
    # 允许的配置键白名单
    ALLOWED_KEYS = {
        'timeout', 'max_connections', 'debug_mode',
        'log_level', 'cache_size'
    }

    if key not in ALLOWED_KEYS:
        raise ValueError(f"Invalid config key: {key}. Allowed: {ALLOWED_KEYS}")

    # 验证值类型
    if key == 'timeout' and not isinstance(value, int):
        raise TypeError("timeout must be an integer")
    if key == 'debug_mode' and not isinstance(value, bool):
        raise TypeError("debug_mode must be a boolean")

    global_config = {}
    global_config[key] = value
    return True


def set_user_role_safe(user_id: int, role: str) -> bool:
    """正确：使用角色白名单"""
    VALID_ROLES = {'user', 'admin', 'moderator'}

    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("user_id must be a positive integer")

    if role not in VALID_ROLES:
        raise ValueError(f"Invalid role: {role}. Allowed: {VALID_ROLES}")

    users_db = {}
    users_db[user_id] = {'role': role}
    return True


def search_users_safe(query: str, limit: int = 100) -> List[Dict]:
    """正确：验证范围和类型"""
    if not isinstance(query, str):
        raise TypeError("query must be a string")

    if not isinstance(limit, int):
        raise TypeError("limit must be an integer")

    # 验证范围
    if limit <= 0:
        raise ValueError("limit must be positive")
    if limit > 1000:
        raise ValueError("limit cannot exceed 1000")

    results = []
    # 查询数据库
    return results[:limit]


def get_user_by_id_safe(user_id: int) -> Optional[Dict]:
    """正确：一致的返回类型"""
    if not isinstance(user_id, int):
        raise TypeError("user_id must be an integer")

    if user_id < 0:
        raise ValueError("user_id must be non-negative")

    users_db = {
        1: {'name': 'Alice', 'age': 30},
        2: {'name': 'Bob', 'age': 25}
    }

    # 统一返回 Optional[Dict]
    return users_db.get(user_id)  # 找到返回 dict，未找到返回 None


def calculate_average_safe(numbers: List[float]) -> float:
    """正确：一致的返回类型和清晰的错误处理"""
    if not isinstance(numbers, list):
        raise TypeError("numbers must be a list")

    if not numbers:
        raise ValueError("Cannot calculate average of empty list")

    # 统一返回 float
    return sum(numbers) / len(numbers)


def find_items_safe(query: str) -> List[str]:
    """正确：始终返回列表"""
    if not isinstance(query, str):
        raise TypeError("query must be a string")

    items_db = ['apple', 'banana', 'cherry']
    results = [item for item in items_db if query in item]

    # 统一返回 List（空列表表示未找到）
    return results
