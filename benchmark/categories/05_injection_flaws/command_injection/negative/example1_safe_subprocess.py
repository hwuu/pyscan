"""
Safe Command Execution Examples
演示安全的命令执行方式,避免命令注入
"""

import subprocess
import shlex
import re
from pathlib import Path


# 正确示例 1: 使用参数列表,不使用 shell
def backup_file_safe(filename):
    """
    正确: 使用参数列表 + shell=False

    关键:
    1. 参数作为列表传递,不是字符串拼接
    2. shell=False 禁用 shell 解释
    3. subprocess 直接调用 tar,不经过 shell
    4. 特殊字符(; & | 等)被视为普通字符,不会被解释

    优点:
    - 完全消除命令注入风险
    - 即使 filename 包含 "; rm -rf /",也只是文件名的一部分
    """
    # 验证文件名(可选,但推荐)
    if not is_safe_filename(filename):
        raise ValueError(f"Invalid filename: {filename}")

    # 正确: 使用列表,shell=False
    command = ["tar", "-czf", "backup.tar.gz", filename]
    print(f"Executing: {' '.join(command)}")

    try:
        result = subprocess.run(
            command,
            shell=False,  # 关键: 禁用 shell
            check=True,
            capture_output=True,
            text=True
        )
        print(f"Success: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return False


# 正确示例 2: 输入验证 + 白名单
def is_safe_filename(filename):
    """
    正确: 验证文件名是否安全

    策略:
    1. 只允许安全字符: 字母、数字、点、下划线、连字符
    2. 拒绝包含 shell 特殊字符的输入
    3. 限制长度
    """
    # 白名单: 只允许安全字符
    safe_pattern = re.compile(r'^[a-zA-Z0-9._-]+$')
    return (
        filename and
        len(filename) < 255 and
        safe_pattern.match(filename) and
        '..' not in filename  # 防止路径遍历
    )


def compress_directory_safe(dir_name, output_file):
    """
    正确: 验证输入 + 使用参数列表
    """
    # 1. 验证目录存在
    dir_path = Path(dir_name)
    if not dir_path.exists() or not dir_path.is_dir():
        raise ValueError(f"Invalid directory: {dir_name}")

    # 2. 验证输出文件名
    if not is_safe_filename(output_file):
        raise ValueError(f"Invalid output file: {output_file}")

    # 3. 使用参数列表执行命令
    command = ["zip", "-r", output_file, str(dir_path)]
    subprocess.run(command, shell=False, check=True)


# 正确示例 3: 使用 shlex.quote 转义 (如果必须使用 shell)
def search_logs_safe(pattern, log_file="/var/log/app.log"):
    """
    正确: 如果必须使用 shell,使用 shlex.quote 转义

    注意:
    1. 优先使用 shell=False
    2. 如果必须用 shell,用 shlex.quote 转义所有用户输入
    3. shlex.quote 会正确转义 shell 特殊字符
    """
    # 验证日志文件路径
    log_path = Path(log_file)
    if not log_path.exists():
        raise ValueError(f"Log file not found: {log_file}")

    # 使用 shlex.quote 转义 pattern
    safe_pattern = shlex.quote(pattern)
    safe_log_file = shlex.quote(str(log_path))

    # 即使使用 shell=True,参数也被正确转义
    command = f"grep {safe_pattern} {safe_log_file}"
    subprocess.run(command, shell=True, check=True)


# 正确示例 4: 完全避免 shell,使用 Python API
def ping_host_safe(hostname):
    """
    正确: 使用参数列表 + 验证主机名格式

    最佳实践:
    1. 验证主机名或 IP 格式
    2. 使用白名单或正则验证
    3. 使用 shell=False
    """
    # 验证是否为有效的主机名或 IP
    if not is_valid_hostname(hostname):
        raise ValueError(f"Invalid hostname: {hostname}")

    # 使用参数列表
    command = ["ping", "-c", "4", hostname]
    result = subprocess.run(
        command,
        shell=False,
        capture_output=True,
        text=True,
        timeout=10  # 添加超时
    )

    return result.returncode == 0


def is_valid_hostname(hostname):
    """验证主机名或 IP 地址格式"""
    # 简单验证 (实际应用应使用更严格的验证)
    import socket

    # 尝试解析为 IP 地址
    try:
        socket.inet_aton(hostname)
        return True
    except socket.error:
        pass

    # 验证主机名格式
    hostname_pattern = re.compile(
        r'^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)*[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$',
        re.IGNORECASE
    )
    return bool(hostname_pattern.match(hostname))


# 正确示例 5: 使用 Python 库代替系统命令
def git_clone_safe(repo_url, dest_dir):
    """
    正确: 使用 GitPython 库代替命令行

    优点:
    1. 不涉及 shell 命令
    2. 类型安全的 API
    3. 更好的错误处理
    """
    try:
        import git
        git.Repo.clone_from(repo_url, dest_dir)
        print(f"Cloned {repo_url} to {dest_dir}")
    except ImportError:
        print("GitPython not installed, using subprocess with validation")

        # 如果没有 GitPython,使用安全的 subprocess
        if not is_valid_git_url(repo_url):
            raise ValueError(f"Invalid git URL: {repo_url}")

        if not is_safe_filename(dest_dir):
            raise ValueError(f"Invalid destination: {dest_dir}")

        command = ["git", "clone", repo_url, dest_dir]
        subprocess.run(command, shell=False, check=True)


def is_valid_git_url(url):
    """验证 git URL 格式"""
    # 只允许 http(s) 和 git 协议
    url_pattern = re.compile(
        r'^(https?|git)://[a-z0-9.-]+/[a-z0-9._/-]+\.git$',
        re.IGNORECASE
    )
    return bool(url_pattern.match(url))


# 正确示例 6: 使用 PIL/Pillow 代替 ImageMagick
def convert_image_safe(input_file, output_file):
    """
    正确: 使用 Pillow 库代替系统命令

    优点:
    1. 完全避免命令注入
    2. 纯 Python 实现,可移植性好
    3. 更安全的图像处理
    """
    try:
        from PIL import Image

        # 验证文件扩展名
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
        input_ext = Path(input_file).suffix.lower()
        output_ext = Path(output_file).suffix.lower()

        if input_ext not in allowed_extensions or output_ext not in allowed_extensions:
            raise ValueError("Unsupported file format")

        # 使用 PIL 处理图像
        with Image.open(input_file) as img:
            img = img.resize((800, 600))
            img.save(output_file)
        print(f"Converted {input_file} to {output_file}")

    except ImportError:
        print("Pillow not installed, using subprocess with validation")

        # 如果没有 PIL,使用安全的 subprocess
        if not is_safe_filename(input_file) or not is_safe_filename(output_file):
            raise ValueError("Invalid filename")

        command = ["convert", input_file, "-resize", "800x600", output_file]
        subprocess.run(command, shell=False, check=True)


if __name__ == "__main__":
    print("=== Demonstrating Safe Command Execution ===\n")

    # 示例 1: 安全的文件备份
    print("1. Safe file backup:")
    backup_file_safe("data.txt")

    # 示例 2: 即使输入恶意,也不会被执行
    print("\n2. Malicious input is safely handled:")
    try:
        backup_file_safe("data.txt; echo HACKED")
    except ValueError as e:
        print(f"Rejected malicious input: {e}")

    # 示例 3: 安全的主机 ping
    print("\n3. Safe ping:")
    try:
        result = ping_host_safe("8.8.8.8")
        print(f"Ping result: {result}")
    except ValueError as e:
        print(f"Error: {e}")

    print("\n✅ All operations are safe from command injection!")
