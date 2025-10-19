"""
Negative Example: Safe path handling

正确做法：验证路径、使用安全的文件操作
"""

import os
import pathlib


def read_user_file_safe(filename):
    """正确：使用 pathlib 解析并验证路径"""
    base_dir = pathlib.Path("/var/app/uploads")

    # 解析路径
    file_path = (base_dir / filename).resolve()

    # 验证解析后的路径在 base_dir 内
    if not file_path.is_relative_to(base_dir):
        raise ValueError("Path traversal attempt detected")

    # 检查是否为符号链接
    if file_path.is_symlink():
        raise ValueError("Symlink not allowed")

    with open(file_path, 'r') as f:
        return f.read()


def serve_static_file_safe(request):
    """正确：使用 pathlib 规范化路径并验证"""
    static_dir = pathlib.Path("/var/www/static")
    requested_file = request.args.get('file')

    # 解析并规范化路径
    file_path = (static_dir / requested_file).resolve()

    # 验证路径在 static_dir 内（resolve 后检查）
    if not file_path.is_relative_to(static_dir):
        raise ValueError("Invalid path")

    # 检查文件存在且是文件（不是目录或符号链接）
    if not file_path.is_file():
        raise ValueError("Not a file")

    with open(file_path, 'rb') as f:
        return f.read()


def delete_user_upload_safe(username, filename):
    """正确：验证文件名，使用白名单"""
    # 白名单：只允许字母数字和常见扩展名
    import re
    if not re.match(r'^[a-zA-Z0-9_\-\.]+$', filename):
        raise ValueError("Invalid filename")

    # 进一步验证扩展名
    allowed_extensions = {'.jpg', '.png', '.pdf', '.txt'}
    file_ext = pathlib.Path(filename).suffix
    if file_ext not in allowed_extensions:
        raise ValueError("File type not allowed")

    upload_dir = pathlib.Path(f"/uploads/{username}")
    file_to_delete = (upload_dir / filename).resolve()

    # 验证路径
    if not file_to_delete.is_relative_to(upload_dir):
        raise ValueError("Path traversal attempt")

    if file_to_delete.exists():
        file_to_delete.unlink()
        return True
    return False


def extract_archive_safe(username, archive_path):
    """正确：验证压缩包成员路径"""
    import tarfile

    extract_dir = pathlib.Path(f"/var/uploads/{username}")

    with tarfile.open(archive_path, 'r') as tar:
        for member in tar.getmembers():
            # 验证成员路径
            member_path = (extract_dir / member.name).resolve()

            # 检查解析后的路径在 extract_dir 内
            if not member_path.is_relative_to(extract_dir):
                raise ValueError(f"Path traversal in archive: {member.name}")

            # 检查成员不是符号链接或硬链接
            if member.issym() or member.islnk():
                raise ValueError(f"Symlink in archive: {member.name}")

        # 安全解压
        tar.extractall(extract_dir)


def safe_write_with_fd(username, filename, data):
    """正确：使用文件描述符避免 TOCTOU"""
    user_dir = pathlib.Path(f"/home/{username}")
    file_path = (user_dir / filename).resolve()

    # 验证路径
    if not file_path.is_relative_to(user_dir):
        raise ValueError("Invalid path")

    # 使用 O_NOFOLLOW 防止符号链接攻击
    # 使用 O_CREAT | O_EXCL 防止竞态条件
    import os
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW

    try:
        fd = os.open(file_path, flags, 0o600)
        os.write(fd, data.encode())
        os.close(fd)
    except FileExistsError:
        raise ValueError("File already exists")
    except OSError as e:
        raise ValueError(f"Failed to create file: {e}")
