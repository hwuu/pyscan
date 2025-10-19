"""
Correct Network Resource Management Examples
演示网络资源的正确管理方式
"""

import socket
import http.client
from contextlib import closing


# 正确示例 1: 使用 with 语句管理 socket
def connect_to_server_correct(host, port):
    """
    正确: 使用 with 语句自动关闭 socket

    优点:
    1. 自动调用 __exit__ 时关闭 socket
    2. 即使发生异常也能确保资源释放
    3. 代码简洁,不易出错
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.connect((host, port))
            sock.sendall(b'GET / HTTP/1.0\r\n\r\n')
            data = sock.recv(1024)
            return data.decode('utf-8')
        except socket.error as e:
            print(f"Connection error: {e}")
            return None
    # sock 在退出 with 块时自动关闭


# 正确示例 2: 使用 try-finally 确保关闭
def connect_with_finally(host, port):
    """
    正确: 使用 try-finally 确保 socket 关闭

    优点:
    1. finally 块保证无论如何都会执行
    2. 即使发生异常也会关闭 socket
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
        sock.sendall(b'GET / HTTP/1.0\r\n\r\n')
        data = sock.recv(1024)
        return data.decode('utf-8')
    except socket.error as e:
        print(f"Connection error: {e}")
        return None
    finally:
        sock.close()  # 确保 socket 关闭


# 正确示例 3: HTTP 连接使用 with 语句
def fetch_data_correct(host, endpoint):
    """
    正确: HTTPConnection 使用 with 语句或显式 close

    方法 1: 使用 closing 上下文管理器
    """
    with closing(http.client.HTTPConnection(host)) as conn:
        conn.request("GET", endpoint)
        response = conn.getresponse()
        data = response.read()
        return data.decode('utf-8')
    # conn 在退出 with 块时自动关闭


# 正确示例 4: 手动管理 HTTP 连接
def fetch_data_manual(host, endpoint):
    """
    正确: 手动管理 HTTPConnection,确保 close

    注意: 需要在 finally 中调用 close()
    """
    conn = http.client.HTTPConnection(host)
    try:
        conn.request("GET", endpoint)
        response = conn.getresponse()
        data = response.read()
        return data.decode('utf-8')
    finally:
        conn.close()  # 确保连接关闭


# 正确示例 5: 循环中正确管理连接
def multiple_requests_correct(hosts):
    """
    正确: 每次循环都使用 with 语句

    优点:
    1. 每个 socket 都自动关闭
    2. 不会累积资源泄露
    """
    results = []
    for host in hosts:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.connect((host, 80))
                results.append(f"Connected to {host}")
            except:
                results.append(f"Failed to connect to {host}")
        # sock 在每次循环结束时自动关闭
    return results


# 正确示例 6: 使用连接池 (推荐用于高并发)
def fetch_with_pool(urls):
    """
    正确: 使用 requests 库的连接池

    优点:
    1. 自动管理连接生命周期
    2. 连接复用,提升性能
    3. 无需手动关闭
    """
    import requests
    with requests.Session() as session:
        results = []
        for url in urls:
            try:
                response = session.get(url, timeout=5)
                results.append(response.text[:100])
            except requests.RequestException as e:
                results.append(f"Error: {e}")
        return results
    # session 自动关闭所有连接


if __name__ == "__main__":
    # 演示正确的资源管理
    data = connect_to_server_correct("example.com", 80)
    print(f"Data: {data[:100] if data else 'None'}...")

    html = fetch_data_correct("example.com", "/")
    print(f"HTML: {html[:100] if html else 'None'}...")

    hosts = ["example.com", "google.com"]
    results = multiple_requests_correct(hosts)
    print(f"Results: {results}")
