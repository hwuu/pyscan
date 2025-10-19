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


# Bug EXC-CATCH-005: except 仅 pass
def save_important_data(data, filename):
    """
    Bug: 异常被捕获但仅 pass，完全吞掉错误

    风险:
    - 数据保存失败但程序继续运行
    - 用户误以为操作成功
    - 无法调试问题
    """
    try:
        with open(filename, 'w') as f:
            f.write(data)
    except:
        pass  # Bug: 异常被吞掉，无任何处理


# Bug EXC-CATCH-006: 捕获后未记录
def fetch_critical_config(url):
    """
    Bug: 异常捕获后未记录日志，返回 None

    风险:
    - 配置加载失败但无日志
    - 调试困难
    - 生产环境问题难以排查
    """
    import requests
    try:
        response = requests.get(url, timeout=5)
        return response.json()
    except Exception:
        # Bug: 异常未记录，直接返回 None
        return None


if __name__ == "__main__":
    print("Exception catching bugs (continued)")


# Bug EXC-CATCH-007: 捕获 BaseException
def critical_operation():
    """
    Bug: 捕获 BaseException，包括 SystemExit 和 KeyboardInterrupt

    风险:
    - 会捕获 KeyboardInterrupt (Ctrl+C)
    - 会捕获 SystemExit (sys.exit())
    - 程序无法正常退出
    - 难以调试和中断

    CWE: CWE-396 (Incorrect Exception Handling)
    """
    try:
        # 某些关键操作
        import sys
        # 假设某处调用 sys.exit(1)
        sys.exit(1)
    except BaseException:  # Bug: 捕获了 SystemExit
        # 程序应该退出，但被捕获了
        print("捕获了异常，继续运行")
        pass


# Bug EXC-CATCH-008: 多余的 except 分支
def redundant_exception_handling(data):
    """
    Bug: 多余的 except 分支（死代码）

    问题:
    - ValueError 是 Exception 的子类
    - 先捕获 Exception 会覆盖 ValueError
    - ValueError 分支永远不会执行

    CWE: CWE-561 (Dead Code)
    """
    try:
        value = int(data)
        return value * 2
    except Exception as e:  # Bug: 先捕获父类
        print(f"Exception: {e}")
        return 0
    except ValueError as e:  # Bug: 死代码 - 永远不会执行
        # ValueError 已经被上面的 Exception 捕获
        print(f"ValueError: {e}")
        return -1


# Bug EXC-CATCH-009: except 顺序错误
def wrong_exception_order(filename):
    """
    Bug: except 子句顺序错误

    问题:
    - IOError 是 OSError 的别名（Python 3.3+）
    - FileNotFoundError 是 OSError 的子类
    - 正确顺序应该是从具体到一般

    CWE: CWE-484 (Omitted Break Statement in Switch)
    """
    try:
        with open(filename, 'r') as f:
            return f.read()
    except OSError as e:  # Bug: 先捕获父类
        print(f"OS Error: {e}")
        return None
    except FileNotFoundError as e:  # Bug: 死代码 - FileNotFoundError 是 OSError 子类
        print(f"File not found: {e}")
        return ""
    except PermissionError as e:  # Bug: 死代码 - PermissionError 也是 OSError 子类
        print(f"Permission denied: {e}")
        return ""


if __name__ == "__main__":
    print("Exception catching bugs - extended examples")
