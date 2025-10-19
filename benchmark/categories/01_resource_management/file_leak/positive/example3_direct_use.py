"""
Example 3: Direct use without reference - 直接使用未保存引用

Bug: 文件对象直接使用未保存引用，依赖隐式清理
Difficulty: Medium
"""


def quick_write(message):
    """直接写入未保存文件句柄"""
    open("quick_log.txt", "a").write(message)  # BUG: RM-FL-005
    # 依赖 __del__ 清理，不可靠


def chain_operations():
    """链式调用，文件未保存引用"""
    content = open("data.txt", "r").read().strip()  # BUG: RM-FL-006
    return content


def nested_open():
    """嵌套 open 调用"""
    data = process(open("input.txt", "r").read())  # BUG: RM-FL-007
    return data


def process(data):
    """模拟处理函数"""
    return data.upper()
