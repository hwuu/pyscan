"""
Example 1: Exception handling with resource cleanup issues

Bug: 异常捕获后未正确释放资源
Difficulty: Medium
"""


def read_and_process_file(filename):
    """
    读取并处理文件（Bug: 异常时资源未释放）

    Bug: 打开文件后，如果 process() 抛出异常，文件句柄不会被关闭
    """
    f = open(filename, 'r')  # BUG: LOGIC-EXC-001
    try:
        data = f.read()
        result = process(data)  # 可能抛出异常
        return result
    except ValueError:
        print("处理失败")
        return None
    # 缺少 finally 块来关闭文件


def process(data):
    """模拟处理函数"""
    if len(data) == 0:
        raise ValueError("Empty data")
    return data.upper()


def download_and_save(url, filepath):
    """
    下载文件并保存（Bug: 异常时文件未关闭）

    Bug: 写入失败时，文件未正确关闭
    """
    import urllib.request

    response = urllib.request.urlopen(url)  # BUG: LOGIC-EXC-002
    f = open(filepath, 'wb')

    try:
        data = response.read()
        f.write(data)  # 可能抛出 IOError
    except IOError as e:
        print(f"写入失败: {e}")
        # Bug: response 和 f 都未关闭
        return False

    f.close()
    return True


def connect_and_query(db_config):
    """
    连接数据库并查询（Bug: 异常时连接未关闭）

    Bug: query 失败时，数据库连接未关闭
    """
    import sqlite3

    conn = sqlite3.connect(db_config['database'])  # BUG: LOGIC-EXC-003
    cursor = conn.cursor()

    try:
        cursor.execute(db_config['query'])
        results = cursor.fetchall()
        return results
    except sqlite3.Error as e:
        print(f"查询失败: {e}")
        # Bug: 缺少 finally 来关闭 cursor 和 conn
        return []
