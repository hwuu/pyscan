"""
Example 2: Exception path file leak - 异常路径下的文件泄露

Bug: 异常发生时文件未关闭
Difficulty: Medium
"""


def process_data_file(filename):
    """处理数据文件，异常时未关闭"""
    f = open(filename, "r")  # BUG: RM-FL-003
    try:
        data = f.read()
        result = parse_data(data)
    except ValueError:
        # 异常路径直接返回，f 未关闭
        return None

    f.close()
    return result


def parse_data(data):
    """模拟数据解析"""
    if not data:
        raise ValueError("Empty data")
    return data.split(",")


def load_config_with_fallback(primary_file, fallback_file):
    """加载配置，有多个 return 路径"""
    f = open(primary_file, "r")  # BUG: RM-FL-004
    content = f.read()

    if not content:
        # 第一个 return 路径，f 未关闭
        return open(fallback_file, "r").read()

    f.close()
    return content
