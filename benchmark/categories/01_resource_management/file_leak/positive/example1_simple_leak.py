"""
Example 1: Simple file leak - 最简单的文件泄露

Bug: open() 调用后未关闭文件句柄
Difficulty: Easy
"""


def read_config():
    """读取配置文件但未关闭句柄"""
    f = open("config.txt", "r")  # BUG: RM-FL-001
    content = f.read()
    return content


def write_log(message):
    """写入日志但未关闭句柄"""
    f = open("log.txt", "a")  # BUG: RM-FL-002
    f.write(message + "\n")
    # 缺少 f.close()
