"""
Example 2: Incorrect exception type handling

Bug: 异常类型判断错误或过于宽泛
Difficulty: Medium
"""


def parse_config(config_str):
    """
    解析配置（Bug: 捕获过于宽泛的异常）

    Bug: 使用 except Exception 会掩盖真正的错误
    """
    import json

    try:
        config = json.loads(config_str)
        return config
    except Exception:  # BUG: LOGIC-EXC-004 - 过于宽泛
        # 会捕获 KeyboardInterrupt, SystemExit 等不应该捕获的异常
        print("配置解析失败")
        return {}


def divide_numbers(a, b):
    """
    除法操作（Bug: 捕获错误的异常类型）

    Bug: 应该捕获 ZeroDivisionError，却捕获了 ValueError
    """
    try:
        result = a / b
        return result
    except ValueError:  # BUG: LOGIC-EXC-005 - 错误的异常类型
        # ZeroDivisionError 不会被捕获
        print("除法失败")
        return 0


def read_integer_from_file(filename):
    """
    从文件读取整数（Bug: 异常处理不完整）

    Bug: 只捕获了 ValueError，但可能抛出 FileNotFoundError, IOError 等
    """
    try:
        with open(filename, 'r') as f:
            value = int(f.read())  # BUG: LOGIC-EXC-006
            return value
    except ValueError:
        # 只处理了解析失败，文件不存在等异常未处理
        print("无法解析整数")
        return 0


def process_user_input(user_input):
    """
    处理用户输入（Bug: 裸 except 掩盖所有异常）

    Bug: 使用裸 except: 会捕获所有异常，包括 KeyboardInterrupt
    """
    try:
        data = eval(user_input)  # 危险操作
        return data
    except:  # BUG: LOGIC-EXC-007 - 裸 except
        # 会捕获所有异常，包括 SystemExit, KeyboardInterrupt
        print("处理失败")
        return None
