"""
Dangerous API Usage
演示使用危险 API 的安全风险
"""

import pickle
import yaml

# Bug API-DANGER-001: pickle.loads 不可信数据
def load_user_session(session_data):
    """
    Bug: pickle.loads() 反序列化不可信数据

    攻击场景:
    - 攻击者构造恶意 pickle 数据
    - 反序列化时执行任意代码（__reduce__ 方法）
    - 可实现 RCE (远程代码执行)

    风险:
    - Severity: Critical
    - CWE-502: Deserialization of Untrusted Data
    """
    # Bug: pickle.loads 可执行任意代码
    session = pickle.loads(session_data)
    return session


# Bug API-DANGER-002: yaml.load 不安全
def load_config_yaml(config_content):
    """
    Bug: yaml.load() 使用默认 Loader，可执行任意 Python 代码

    攻击场景:
    - 构造恶意 YAML:
      ```yaml
      !!python/object/apply:os.system
      args: ['rm -rf /']
      ```
    - yaml.load 会执行 Python 代码

    风险:
    - Severity: High
    - CWE-502: Deserialization of Untrusted Data

    修复:
    - 使用 yaml.safe_load() 替代
    """
    # Bug: yaml.load 默认 Loader 不安全
    config = yaml.load(config_content, Loader=yaml.FullLoader)
    return config


if __name__ == "__main__":
    print("Dangerous API examples (DANGEROUS)")

    # 示例: 安全的 pickle 使用（仅用于可信数据）
    safe_data = {'user': 'alice', 'role': 'admin'}
    serialized = pickle.dumps(safe_data)
    # Bug: 如果 serialized 来自用户输入，则不安全
    deserialized = load_user_session(serialized)
    print(f"API-DANGER-001: {deserialized}")

    # 示例: 安全的 YAML 使用
    safe_yaml = "name: test\nvalue: 123"
    # Bug: 如果 YAML 来自用户输入，则不安全
    config = load_config_yaml(safe_yaml)
    print(f"API-DANGER-002: {config}")
