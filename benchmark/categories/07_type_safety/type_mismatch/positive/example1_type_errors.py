"""
Type Mismatch Issues
演示类型不匹配导致的运行时错误
"""

from typing import List

# Bug TYPE-MIS-001: 参数类型不匹配
def calculate_total(prices: List[int]) -> int:
    """
    Bug: 类型注解声明 List[int]，但传入 str

    风险:
    - 传入字符串会引发 TypeError
    - 类型检查工具可检测但运行时仍会出错
    """
    return sum(prices)


# Bug TYPE-MIS-002: 返回类型不匹配
def get_user_name(user_id: int) -> str:
    """
    Bug: 声明返回 str，实际返回 dict

    风险:
    - 调用者期望 str，实际得到 dict
    - 后续操作可能失败
    """
    user = find_user(user_id)
    if user:
        return user  # Bug: 返回 dict 而不是 str
    return "Unknown"


# Bug TYPE-MIS-003: 容器类型错误
def process_numbers(values: List[int]) -> List[str]:
    """
    Bug: 列表混合类型，违反类型注解

    风险:
    - 类型注解声明 List[int]，实际包含 str
    - 后续数值运算会失败
    """
    numbers: List[int] = [1, 2, "three", 4]  # Bug: 包含字符串
    results = []
    for num in numbers:
        try:
            results.append(str(num * 2))  # "three" * 2 会失败或产生意外结果
        except TypeError:
            results.append("error")
    return results


# Helper function
def find_user(user_id: int) -> dict:
    """模拟查找用户"""
    return {"id": user_id, "name": f"User{user_id}", "email": f"user{user_id}@example.com"}


if __name__ == "__main__":
    print("Type mismatch bugs (DANGEROUS)")

    # Bug TYPE-MIS-001: 传入错误类型
    try:
        total = calculate_total("not a list")  # 类型错误
    except TypeError as e:
        print(f"TYPE-MIS-001: {e}")

    # Bug TYPE-MIS-002: 返回类型不匹配
    name = get_user_name(123)
    print(f"TYPE-MIS-002: Expected str, got {type(name)}: {name}")

    # Bug TYPE-MIS-003: 混合类型列表
    result = process_numbers([1, 2, 3])
    print(f"TYPE-MIS-003: {result}")
