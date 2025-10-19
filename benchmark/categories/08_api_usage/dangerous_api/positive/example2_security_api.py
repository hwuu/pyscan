"""
Dangerous API Usage - Security Issues
演示安全相关的危险 API 使用
"""

import random
import hashlib


# Bug API-DANGER-003: random 用于安全场景
def generate_session_token():
    """
    Bug: 使用 random 模块生成安全令牌

    问题:
    - random 是伪随机数生成器，不是密码学安全的
    - 可预测，攻击者可能猜测令牌
    - 应使用 secrets 模块

    攻击场景:
    - 攻击者分析 random 种子
    - 预测会话令牌
    - 劫持用户会话

    风险: Critical
    CWE-330: Use of Insufficiently Random Values
    """
    # Bug: random 不适合安全场景
    token = ''.join([str(random.randint(0, 9)) for _ in range(32)])
    return token


def generate_password_reset_token(user_id):
    """
    Bug: 使用 random.choice 生成密码重置令牌

    风险:
    - 令牌可预测
    - 攻击者可重置任意用户密码
    """
    import string
    # Bug: random 不是密码学安全的
    chars = string.ascii_letters + string.digits
    token = ''.join(random.choice(chars) for _ in range(20))
    return f"{user_id}:{token}"


def generate_encryption_key():
    """
    Bug: 使用 random 生成加密密钥

    正确做法:
    - 使用 secrets.token_bytes() 或 os.urandom()
    """
    # Bug: 加密密钥应该使用密码学安全的随机数生成器
    key = random.getrandbits(256)
    return key


# Bug API-DANGER-004: assert 用于数据验证
def process_payment(amount, user_id):
    """
    Bug: 使用 assert 进行数据验证

    问题:
    - assert 在优化模式（python -O）下会被忽略
    - 生产环境关键验证可能失效
    - 应使用 if + raise 进行验证

    攻击场景:
    - 生产环境使用 -O 运行
    - assert 被跳过
    - 恶意用户绕过金额验证

    风险: High
    CWE-617: Reachable Assertion
    """
    # Bug: assert 不应用于安全验证
    assert amount > 0, "Amount must be positive"  # Bug: -O 模式下会被忽略
    assert user_id is not None, "User ID required"  # Bug: 同上

    # 处理支付
    print(f"Processing payment of ${amount} for user {user_id}")
    return True


def delete_user_account(user_id, is_admin):
    """
    Bug: 使用 assert 进行权限检查

    风险:
    - 优化模式下权限检查失效
    - 普通用户可能删除管理员账户
    """
    # Bug: 权限检查不应使用 assert
    assert is_admin, "Only admins can delete accounts"  # Bug: 可被绕过

    # 删除账户
    print(f"Deleting account {user_id}")
    return True


def update_user_role(user_id, new_role, current_user_role):
    """
    Bug: 使用 assert 验证业务规则

    问题:
    - 业务规则验证应该总是执行
    - assert 可能在生产环境被禁用
    """
    allowed_roles = ["user", "moderator", "admin"]

    # Bug: 业务规则验证使用 assert
    assert new_role in allowed_roles, f"Invalid role: {new_role}"  # Bug
    assert current_user_role == "admin", "Only admins can change roles"  # Bug

    print(f"Updated user {user_id} to role {new_role}")
    return True


if __name__ == "__main__":
    print("=== Bug API-DANGER-003: random for security ===")
    token = generate_session_token()
    print(f"Session token (INSECURE): {token}")

    reset_token = generate_password_reset_token(12345)
    print(f"Password reset token (INSECURE): {reset_token}")

    print("\n=== Bug API-DANGER-004: assert for validation ===")
    # 正常情况
    process_payment(100, 123)

    # Bug: 如果使用 python -O 运行，下面的调用会通过:
    # process_payment(-100, None)  # assert 会被忽略!

    print("\n正确做法示例:")
    print("- 使用 secrets 模块: secrets.token_urlsafe(32)")
    print("- 使用 if + raise: if amount <= 0: raise ValueError('...')")
