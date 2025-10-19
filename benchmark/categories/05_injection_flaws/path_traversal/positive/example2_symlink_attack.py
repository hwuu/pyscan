"""
Example 2: Symlink and TOCTOU vulnerabilities

Bug: 符号链接未处理，存在 TOCTOU 攻击
Difficulty: Hard
"""

import os


def safe_write_to_user_dir(username, filename, data):
    """
    写入用户目录（Bug: TOCTOU - Time-of-check Time-of-use）

    Bug: 检查和使用之间存在时间窗口，可能被攻击者利用
    """
    user_dir = f"/home/{username}"
    file_path = os.path.join(user_dir, filename)

    # BUG: SEC-PT-006 - TOCTOU 漏洞
    # 检查路径在用户目录内
    if not os.path.realpath(file_path).startswith(os.path.realpath(user_dir)):
        raise ValueError("Invalid path")

    # 攻击者可以在这里将 file_path 替换为符号链接
    # 指向 /etc/passwd 等敏感文件

    # 写入文件（使用时，文件可能已被替换）
    with open(file_path, 'w') as f:
        f.write(data)


def read_config_file(config_name):
    """
    读取配置文件（Bug: 未检查符号链接）

    Bug: config_name 可能是指向任意文件的符号链接
    """
    config_dir = "/etc/app/configs"
    config_path = os.path.join(config_dir, config_name)

    # BUG: SEC-PT-007 - 未检查是否为符号链接
    if config_path.startswith(config_dir):
        with open(config_path, 'r') as f:
            return f.read()

    raise ValueError("Invalid config")


def extract_archive_to_user_space(username, archive_path):
    """
    解压文件到用户空间（Bug: 未验证压缩包内的文件路径）

    Bug: 压缩包内的文件可能包含 "../" 路径，导致文件覆盖
    """
    import tarfile

    extract_dir = f"/var/uploads/{username}"

    # BUG: SEC-PT-008 - 未验证压缩包成员路径
    with tarfile.open(archive_path, 'r') as tar:
        tar.extractall(extract_dir)
        # 压缩包内的文件可能包含 "../../../etc/cron.d/malicious"


def check_and_delete_temp_file(temp_file_path):
    """
    检查并删除临时文件（Bug: TOCTOU）

    Bug: 检查和删除之间存在时间窗口
    """
    temp_dir = "/tmp/app"

    # BUG: SEC-PT-009 - TOCTOU
    # 检查文件在临时目录内
    if not temp_file_path.startswith(temp_dir):
        raise ValueError("Invalid temp file")

    # 检查文件存在
    if os.path.exists(temp_file_path):
        # 攻击者可以在这里将文件替换为符号链接
        # 指向重要文件（如 /etc/passwd）
        os.remove(temp_file_path)
