"""
Negative Example 1: Correct file handling with 'with' statement

正确做法：使用 with 语句自动管理资源
"""


def read_config_correct():
    """正确：使用 with 语句"""
    with open("config.txt", "r") as f:
        content = f.read()
    return content  # f 自动关闭


def write_log_correct(message):
    """正确：使用 with 语句写入日志"""
    with open("log.txt", "a") as f:
        f.write(message + "\n")
    # f 自动关闭


def process_multiple_files():
    """正确：处理多个文件"""
    with open("input.txt", "r") as f_in:
        data = f_in.read()

    with open("output.txt", "w") as f_out:
        f_out.write(data.upper())

    # 两个文件都已关闭
