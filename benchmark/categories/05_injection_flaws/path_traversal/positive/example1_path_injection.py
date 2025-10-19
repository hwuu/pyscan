"""
Example 1: Path traversal vulnerabilities

Bug: 路径拼接未验证，存在路径遍历风险
Difficulty: High
"""

import os


def read_user_file(filename):
    """
    读取用户文件（Bug: 路径遍历）

    Bug: 用户可以通过 "../../../etc/passwd" 访问任意文件
    """
    base_dir = "/var/app/uploads"
    file_path = os.path.join(base_dir, filename)  # BUG: SEC-PT-001
    # 应该验证 file_path 在 base_dir 内

    with open(file_path, 'r') as f:
        return f.read()


def download_file(file_id):
    """
    下载文件（Bug: 未验证路径）

    Bug: file_id 可能包含 "../" 导致访问上层目录
    """
    import flask

    storage_path = "/opt/storage"
    # BUG: SEC-PT-002 - 直接拼接用户输入
    full_path = f"{storage_path}/{file_id}"

    return flask.send_file(full_path)


def serve_static_file(request):
    """
    提供静态文件（Bug: 路径未规范化）

    Bug: 使用未规范化的路径，可能被绕过
    """
    static_dir = "/var/www/static"
    requested_file = request.args.get('file')

    # BUG: SEC-PT-003 - 未规范化路径
    file_path = os.path.join(static_dir, requested_file)

    if not file_path.startswith(static_dir):
        # 检查不够，可能被符号链接或 ../ 绕过
        raise ValueError("Invalid path")

    with open(file_path, 'rb') as f:
        return f.read()


def delete_user_upload(username, filename):
    """
    删除用户上传（Bug: 路径拼接不安全）

    Bug: filename 可能包含 "../" 删除其他用户文件
    """
    upload_dir = f"/uploads/{username}"
    # BUG: SEC-PT-004
    file_to_delete = os.path.join(upload_dir, filename)

    if os.path.exists(file_to_delete):
        os.remove(file_to_delete)
        return True
    return False


def load_template(template_name):
    """
    加载模板文件（Bug: 模板注入风险）

    Bug: 用户可以通过 "../../../../etc/passwd" 读取任意文件
    """
    template_dir = "/app/templates"
    # BUG: SEC-PT-005 - 未验证 template_name
    template_path = os.path.join(template_dir, template_name)

    with open(template_path, 'r') as f:
        return f.read()
