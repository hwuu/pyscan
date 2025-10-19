"""
Example 2: Class member race condition (BUG_0005 simplified)

Bug: 类成员变量在多线程环境未同步
Difficulty: Medium
"""


class GlobalState:
    """全局状态类（简化 BUG_0005）"""

    def __init__(self):
        self.detector = None
        self.config = {}


# 全局实例
global_vars = GlobalState()


def initialize_detector(detector_instance):
    """
    初始化检测器（BUG_0005 简化版）

    Bug: global_vars.detector 的赋值在多线程环境存在竞态
    """
    global global_vars
    global_vars.detector = detector_instance  # BUG: CONC-RC-004
    # 如果多个线程同时调用，可能互相覆盖


def update_config(key, value):
    """
    更新配置

    Bug: 字典修改在多线程环境未同步
    """
    global global_vars
    global_vars.config[key] = value  # BUG: CONC-RC-005


class RequestHandler:
    """请求处理器"""

    def __init__(self):
        self.request_count = 0

    def handle_request(self):
        """处理请求（Bug: 实例变量竞态）"""
        self.request_count += 1  # BUG: CONC-RC-006
        # 如果同一实例被多线程共享，计数可能不准确
        return self.request_count
