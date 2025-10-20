"""
演示 Layer 4 交叉验证效果的测试代码

包含多个类型错误，mypy 能检测到
"""


def calculate_total(numbers: list[int]) -> int:
    """
    计算数字总和

    Bug: 返回类型声明为 int，但实际返回 str
    """
    total = sum(numbers)
    return str(total)  # Type error: 返回 str 而不是 int


def process_user(user_id: int, name: str) -> dict[str, any]:
    """
    处理用户信息

    Bug: 参数类型错误
    """
    # Bug: user_id 声明为 int，但传入了 str
    result = get_user_data(user_id)
    return {"id": user_id, "name": name, "data": result}


def get_user_data(user_id: str) -> str:
    """获取用户数据"""
    return f"User data for {user_id}"


def format_price(price: float) -> str:
    """
    格式化价格

    Bug: None 检查缺失
    """
    # Bug: price 可能为 None，但没有处理
    return f"${price:.2f}"


def merge_lists(list1: list[str], list2: list[int]) -> list[str]:
    """
    合并两个列表

    Bug: 返回类型不匹配
    """
    # Bug: 返回 list1 + list2 会包含 int，但声明返回 list[str]
    return list1 + list2


def get_config(key: str) -> str:
    """
    获取配置值

    Bug: 可能返回 None
    """
    config = {"debug": "true", "port": "8080"}
    # Bug: 当 key 不存在时返回 None，但类型声明为 str
    return config.get(key)


if __name__ == "__main__":
    # 这些调用都有类型问题
    total = calculate_total([1, 2, 3])
    print(f"Total: {total}")

    user = process_user("123", "Alice")  # 传入 str 而不是 int
    print(f"User: {user}")

    price = format_price(None)  # 传入 None
    print(f"Price: {price}")

    merged = merge_lists(["a", "b"], [1, 2])
    print(f"Merged: {merged}")

    value = get_config("missing_key")
    print(f"Config: {value}")
