"""
Variable Initialization Issues
演示未初始化变量导致的 bug
"""

# Bug DATA-INIT-001: 条件分支未初始化
def process_payment(amount, use_credit_card):
    """
    Bug: 变量在部分分支中未初始化

    风险:
    - use_credit_card=False 时，transaction_id 未定义
    - 后续使用会引发 UnboundLocalError
    """
    if use_credit_card:
        transaction_id = charge_card(amount)
    # Bug: else 分支未初始化 transaction_id

    return save_transaction(transaction_id)  # UnboundLocalError


# Bug DATA-INIT-002: 循环外未初始化
def find_max_value(numbers):
    """
    Bug: 变量在循环内初始化，循环外使用

    风险:
    - numbers 为空时，max_val 未定义
    - 返回时引发 UnboundLocalError
    """
    for num in numbers:
        max_val = num if not locals().get('max_val') or num > max_val else max_val
    # Bug: 如果 numbers 为空，max_val 未初始化
    return max_val


# Bug DATA-INIT-003: 异常分支未初始化
def load_config(config_path):
    """
    Bug: try 块中初始化，except 块未初始化

    风险:
    - 异常时 config 未定义
    - 后续使用会引发 UnboundLocalError
    """
    try:
        config = parse_config_file(config_path)
    except FileNotFoundError:
        print(f"Config file not found: {config_path}")
        # Bug: except 块未初始化 config

    return config.get('database_url')  # 异常后 config 未定义


# Bug DATA-INIT-004: 提前引用
def calculate_discount(price, is_vip):
    """
    Bug: 变量在定义前使用

    风险:
    - 直接引发 UnboundLocalError
    """
    if is_vip:
        final_price = price * discount_rate  # Bug: discount_rate 未定义

    discount_rate = 0.8
    return final_price if is_vip else price


# Bug DATA-INIT-005: 全局声明未初始化
counter = 0

def increment_counter():
    """
    Bug: global 声明但全局变量可能未定义

    风险:
    - 如果全局 counter 被删除，引发 NameError
    """
    global counter
    counter += 1  # Bug: 假设 counter 已定义
    return counter


# Bug DATA-INIT-006: 类变量未初始化
class ShoppingCart:
    """Bug: 实例变量在 __init__ 外使用"""

    def add_item(self, item, price):
        """Bug: self.total 可能未初始化"""
        if not hasattr(self, 'items'):
            self.items = []
        self.items.append(item)
        self.total += price  # Bug: __init__ 未初始化 self.total

    def get_total(self):
        return self.total


# Helper functions (模拟)
def charge_card(amount):
    return f"txn_{amount}"

def save_transaction(txn_id):
    return f"saved_{txn_id}"

def parse_config_file(path):
    return {"database_url": "postgres://localhost/db"}


if __name__ == "__main__":
    print("Variable initialization bugs (DANGEROUS)")
