"""
Negative Example: Correct exception handling with resource cleanup

正确做法：使用 try-finally 或 with 语句确保资源释放
"""


def read_and_process_file_correct(filename):
    """正确：使用 with 语句自动关闭文件"""
    try:
        with open(filename, 'r') as f:
            data = f.read()
            result = process(data)
            return result
    except ValueError:
        print("处理失败")
        return None
    # with 语句确保文件在任何情况下都会关闭


def download_and_save_correct(url, filepath):
    """正确：使用 finally 确保资源关闭"""
    import urllib.request

    response = None
    f = None

    try:
        response = urllib.request.urlopen(url)
        f = open(filepath, 'wb')
        data = response.read()
        f.write(data)
        return True
    except IOError as e:
        print(f"操作失败: {e}")
        return False
    finally:
        # 确保资源在任何情况下都被释放
        if f:
            f.close()
        if response:
            response.close()


def connect_and_query_correct(db_config):
    """正确：使用 with 语句或 finally 块"""
    import sqlite3

    conn = None
    cursor = None

    try:
        conn = sqlite3.connect(db_config['database'])
        cursor = conn.cursor()
        cursor.execute(db_config['query'])
        results = cursor.fetchall()
        return results
    except sqlite3.Error as e:
        print(f"查询失败: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def acquire_and_use_lock_correct(lock, data):
    """正确：使用 with 语句或 finally 释放锁"""
    import threading

    lock.acquire()
    try:
        result = process(data)
        return result
    except Exception as e:
        print(f"处理失败: {e}")
        return None
    finally:
        lock.release()  # 确保锁在任何情况下都被释放


def parse_config_correct(config_str):
    """正确：捕获具体的异常类型"""
    import json

    try:
        config = json.loads(config_str)
        return config
    except json.JSONDecodeError:  # 具体的异常类型
        print("配置解析失败")
        return {}
    except (ValueError, TypeError) as e:  # 其他可能的具体异常
        print(f"配置错误: {e}")
        return {}


def divide_numbers_correct(a, b):
    """正确：捕获正确的异常类型"""
    try:
        result = a / b
        return result
    except ZeroDivisionError:  # 正确的异常类型
        print("除数不能为零")
        return 0
    except TypeError:
        print("参数类型错误")
        return 0


def process(data):
    """辅助函数"""
    if not data:
        raise ValueError("Empty data")
    return data.upper()
