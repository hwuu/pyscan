"""
Deprecated API Usage
演示使用已废弃 API 的风险
"""

import platform

# Bug API-DEP-001: platform.dist() 已废弃
def get_linux_distribution():
    """
    Bug: platform.dist() 在 Python 3.8+ 已被移除

    风险:
    - Python 3.8+ 会引发 AttributeError
    - 应使用 distro 库或 platform.freedesktop_os_release()
    """
    try:
        # Bug: platform.dist() 已废弃并在 Python 3.8 中移除
        dist_info = platform.dist()
        return dist_info
    except AttributeError:
        # Python 3.8+ 会到这里
        return ("unknown", "unknown", "unknown")


# Bug API-DEP-002: imp 模块已废弃
def load_module_dynamically(module_name):
    """
    Bug: imp 模块在 Python 3.4+ 已废弃

    风险:
    - Python 3.12+ 会移除 imp 模块
    - 应使用 importlib
    """
    try:
        import imp  # Bug: imp 已废弃，应使用 importlib

        # 查找模块
        file_info = imp.find_module(module_name)
        # 加载模块
        module = imp.load_module(module_name, *file_info)
        return module
    except ImportError:
        return None


if __name__ == "__main__":
    print("Deprecated API usage (DANGEROUS)")

    # Bug API-DEP-001
    dist = get_linux_distribution()
    print(f"API-DEP-001: Distribution: {dist}")

    # Bug API-DEP-002
    try:
        mod = load_module_dynamically("os")
        print(f"API-DEP-002: Loaded module: {mod}")
    except Exception as e:
        print(f"API-DEP-002: {e}")
