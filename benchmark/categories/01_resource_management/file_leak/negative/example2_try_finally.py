"""
Negative Example 2: Correct file handling with try-finally

正确做法：使用 try-finally 显式关闭
"""


def process_data_file_correct(filename):
    """正确：使用 try-finally 确保异常时也关闭"""
    f = open(filename, "r")
    try:
        data = f.read()
        result = parse_data(data)
        return result
    except ValueError:
        return None
    finally:
        f.close()  # 无论如何都会执行


def parse_data(data):
    """模拟数据解析"""
    if not data:
        raise ValueError("Empty data")
    return data.split(",")


def load_config_with_cleanup(primary_file, fallback_file):
    """正确：所有路径都关闭文件"""
    f = None
    try:
        f = open(primary_file, "r")
        content = f.read()

        if not content:
            f.close()  # 提前关闭
            with open(fallback_file, "r") as f_fallback:
                return f_fallback.read()

        return content
    finally:
        if f:
            f.close()
