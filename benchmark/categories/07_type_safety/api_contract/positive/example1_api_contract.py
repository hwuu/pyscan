"""
Type Safety - API Contract Violations
演示 API 契约违反导致的运行时错误
"""

from abc import ABC, abstractmethod
from typing import List, Optional


# Bug TYPE-API-001: 可变默认参数
def append_to_list(item, items=[]):
    """
    Bug: 使用可变对象（列表）作为默认参数

    问题:
    1. 默认参数在函数定义时创建，所有调用共享同一个列表
    2. 多次调用会累积之前的修改
    3. 导致意外的状态共享

    影响: High - 数据污染，难以调试
    CWE: CWE-1174 (ASP.NET Misconfiguration: Improper Model Validation)
    """
    # Bug: items=[] 是可变默认参数
    items.append(item)
    return items


def add_to_dict(key, value, config={}):
    """
    Bug: 使用可变字典作为默认参数

    问题:
    1. 所有调用共享同一个 config 字典
    2. 配置会在调用之间泄露
    3. 测试和生产环境配置混淆
    """
    # Bug: config={} 是可变默认参数
    config[key] = value
    return config


def process_with_mutable_default(data, cache=set()):
    """
    Bug: 使用可变集合作为默认参数
    """
    # Bug: cache=set() 是可变默认参数
    cache.add(data)
    return list(cache)


# Bug TYPE-API-002: 继承方法签名不一致
class BaseHandler:
    """基类定义了 handle 方法"""

    def handle(self, request: dict) -> str:
        """处理请求"""
        return "Base handler"


class SpecialHandler(BaseHandler):
    """
    Bug: 子类修改了方法签名

    问题:
    1. 父类接受 dict，子类接受 str
    2. 违反里氏替换原则 (LSP)
    3. 多态调用时会出错
    """

    # Bug: 参数类型与父类不一致
    def handle(self, request: str) -> str:  # Bug: request 类型改变了
        """Bug: 参数类型从 dict 改为 str"""
        return f"Special: {request}"


class AnotherHandler(BaseHandler):
    """
    Bug: 子类修改了返回类型
    """

    # Bug: 返回类型与父类不一致
    def handle(self, request: dict) -> List[str]:  # Bug: 返回类型改变了
        """Bug: 返回类型从 str 改为 List[str]"""
        return [f"Processed: {k}={v}" for k, v in request.items()]


# Bug TYPE-API-003: 抽象方法未实现
class DataProcessor(ABC):
    """定义了数据处理接口"""

    @abstractmethod
    def process(self, data: str) -> str:
        """抽象方法: 处理数据"""
        pass

    @abstractmethod
    def validate(self, data: str) -> bool:
        """抽象方法: 验证数据"""
        pass


class IncompleteProcessor(DataProcessor):
    """
    Bug: 只实现了部分抽象方法

    问题:
    1. 缺少 validate 方法实现
    2. 无法实例化（TypeError）
    3. 违反接口契约

    影响: Critical - 运行时错误
    """

    def process(self, data: str) -> str:
        """实现了 process"""
        return data.upper()

    # Bug: 缺少 validate 方法实现
    # TypeError: Can't instantiate abstract class IncompleteProcessor


# Bug TYPE-API-004: 返回类型不一致
def get_user_age(user_id: int) -> int:
    """
    Bug: 声明返回 int，但可能返回 None

    问题:
    1. 类型注解说返回 int
    2. 实际可能返回 None
    3. 调用者假设非空，导致 AttributeError
    """
    users = {
        1: {"name": "Alice", "age": 25},
        2: {"name": "Bob", "age": 30}
    }

    user = users.get(user_id)
    # Bug: user 可能是 None，但直接访问 ['age']
    if user:
        return user['age']
    # Bug: 隐式返回 None，但类型注解是 int
    return None  # Bug: 应该返回 int，但返回了 None


def fetch_data(url: str) -> dict:
    """
    Bug: 声明返回 dict，但错误时返回 str

    问题:
    1. 正常情况返回 dict
    2. 错误情况返回 str (错误消息)
    3. 调用者期望 dict，可能导致 TypeError
    """
    import random

    # 模拟 API 调用
    if random.random() < 0.5:
        return {"status": "success", "data": [1, 2, 3]}
    else:
        # Bug: 错误时返回 str，而不是 dict
        return "Error: Connection failed"  # Bug: 返回类型不一致


def calculate_average(numbers: List[int]) -> float:
    """
    Bug: 空列表时返回 None 而不是 float
    """
    if not numbers:
        # Bug: 返回 None，但类型注解是 float
        return None  # Bug: 应该返回 0.0 或抛出异常

    return sum(numbers) / len(numbers)


if __name__ == "__main__":
    print("=== Bug TYPE-API-001: 可变默认参数 ===")
    list1 = append_to_list("a")
    print(f"First call: {list1}")  # ['a']
    list2 = append_to_list("b")
    print(f"Second call: {list2}")  # Bug: ['a', 'b'] - 共享同一个列表!

    print("\n=== Bug TYPE-API-002: 继承签名不一致 ===")
    def process_all(handlers: List[BaseHandler], request: dict):
        """多态调用"""
        for handler in handlers:
            # 期望所有 handler.handle 接受 dict
            print(handler.handle(request))

    try:
        handlers = [BaseHandler(), SpecialHandler()]
        # process_all(handlers, {"key": "value"})  # Bug: SpecialHandler 期望 str
    except Exception as e:
        print(f"Error: {e}")

    print("\n=== Bug TYPE-API-003: 抽象方法未实现 ===")
    try:
        processor = IncompleteProcessor()  # TypeError
    except TypeError as e:
        print(f"Cannot instantiate: {e}")

    print("\n=== Bug TYPE-API-004: 返回类型不一致 ===")
    age = get_user_age(999)  # 返回 None
    print(f"Age: {age}")
    # 如果调用者假设 age 是 int:
    # next_year = age + 1  # TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'
