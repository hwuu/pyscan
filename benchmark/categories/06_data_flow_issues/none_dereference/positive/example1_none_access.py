"""
None Dereference Issues
演示 None 解引用导致的 AttributeError
"""

from typing import Optional

# Bug DATA-NULL-001: Optional 未检查
def get_user_email(user_id: int) -> str:
    """
    Bug: Optional 类型未检查直接使用

    风险:
    - find_user 返回 None 时引发 AttributeError
    """
    user: Optional[dict] = find_user(user_id)
    return user['email']  # Bug: user 可能是 None


# Bug DATA-NULL-002: 函数返回 None 未检查
def get_config_value(key: str):
    """
    Bug: dict.get() 返回 None 未检查

    风险:
    - key 不存在时返回 None
    - 调用 .upper() 引发 AttributeError
    """
    config = load_config()
    value = config.get(key)  # 可能返回 None
    return value.upper()  # Bug: value 可能是 None


# Bug DATA-NULL-003: 空列表索引
def get_first_item(items: list):
    """
    Bug: 未检查列表是否为空直接索引

    风险:
    - items 为空时引发 IndexError
    """
    if len(items) == 0:
        return None

    first = items[0]  # 安全
    # 但是后续可能这样用:
    result = process_item(first)
    return result


def unsafe_get_first(items: list):
    """Bug: 完全未检查"""
    return items[0]  # Bug: items 可能为空


# Bug DATA-NULL-004: 空字典键访问
def get_required_field(data: dict, field: str):
    """
    Bug: 使用 [] 访问可能不存在的键

    风险:
    - field 不存在时引发 KeyError
    - 应使用 .get() 或检查 in
    """
    return data[field]  # Bug: field 可能不存在


# Bug DATA-NULL-005: str.find() 返回 -1 未检查
def extract_domain(email: str) -> str:
    """
    Bug: find() 返回 -1 时索引错误

    风险:
    - email 不含 @ 时，idx = -1
    - email[idx+1:] 会从末尾切片，返回错误结果
    """
    idx = email.find('@')  # 不存在时返回 -1
    return email[idx+1:]  # Bug: idx 可能是 -1，但不会抛异常，结果错误


# Helper functions
def find_user(user_id: int) -> Optional[dict]:
    """模拟数据库查询，可能返回 None"""
    if user_id == 999:
        return None
    return {"id": user_id, "email": f"user{user_id}@example.com"}


def load_config() -> dict:
    """模拟配置加载"""
    return {"database": "postgres", "port": 5432}


def process_item(item):
    """模拟处理"""
    return f"processed_{item}"


if __name__ == "__main__":
    print("None dereference bugs (DANGEROUS)")

    # 触发 Bug DATA-NULL-001
    try:
        email = get_user_email(999)
    except (AttributeError, TypeError) as e:
        print(f"DATA-NULL-001: {e}")

    # 触发 Bug DATA-NULL-002
    try:
        val = get_config_value("missing_key")
    except AttributeError as e:
        print(f"DATA-NULL-002: {e}")

    # 触发 Bug DATA-NULL-003
    try:
        item = unsafe_get_first([])
    except IndexError as e:
        print(f"DATA-NULL-003: {e}")

    # 触发 Bug DATA-NULL-004
    try:
        field = get_required_field({"a": 1}, "b")
    except KeyError as e:
        print(f"DATA-NULL-004: {e}")

    # Bug DATA-NULL-005 不会抛异常，但结果错误
    domain = extract_domain("invalid_email")
    print(f"DATA-NULL-005: Wrong result: '{domain}'")
