"""
ZIP Path Traversal Example
演示 ZIP 文件解压路径遍历漏洞
"""

import zipfile

# Bug INPUT-PATH-003: ZIP 路径遍历
def extract_zip_unsafe(zip_path, extract_to):
    """
    Bug: zipfile.extractall() 未验证路径
    
    攻击场景:
    - ZIP 中包含文件: ../../etc/passwd
    - 解压后: 覆盖系统文件
    """
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Bug: 直接解压，未验证成员路径
        zip_ref.extractall(extract_to)

if __name__ == "__main__":
    print("ZIP path traversal (DANGEROUS)")
