"""
Network Resource Leak Examples - Socket and HTTP Connection
演示网络资源(Socket, HTTP连接)未正确关闭导致的资源泄露问题
"""

import socket
import http.client


# Bug RM-NET-001: Socket 未关闭
def connect_to_server(host, port):
    """
    Bug: Socket 连接后未关闭,导致资源泄露

    问题:
    1. socket 对象创建后未使用 close() 或 with 语句
    2. 函数返回前 socket 未释放
    3. 长时间运行会耗尽文件描述符

    影响: High - 资源泄露可能导致系统无法创建新连接
    CWE: CWE-404 (Improper Resource Shutdown or Release)
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Bug: 未关闭
    try:
        sock.connect((host, port))
        sock.sendall(b'GET / HTTP/1.0\r\n\r\n')
        data = sock.recv(1024)
        return data.decode('utf-8')
    except socket.error as e:
        print(f"Connection error: {e}")
        return None
    # Bug: sock 未在 finally 中关闭,异常和正常路径都会泄露


# Bug RM-NET-002: HTTP 连接未关闭
def fetch_data(host, endpoint):
    """
    Bug: HTTP 连接未正确关闭

    问题:
    1. HTTPConnection 对象创建后未关闭
    2. 多次调用会累积大量未关闭连接
    3. 可能触发服务器连接数限制

    影响: High - 连接池耗尽,影响应用性能
    CWE: CWE-404 (Improper Resource Shutdown or Release)
    """
    conn = http.client.HTTPConnection(host)  # Bug: 未关闭
    try:
        conn.request("GET", endpoint)
        response = conn.getresponse()
        data = response.read()
        return data.decode('utf-8')
    except Exception as e:
        print(f"HTTP error: {e}")
        return None
    # Bug: conn 未调用 close(),连接保持打开状态


def multiple_requests(hosts):
    """
    Bug: 循环中创建多个未关闭的连接

    问题:
    1. 每次循环都创建新 Socket 但不关闭
    2. 快速耗尽系统资源

    影响: Critical - 在高并发场景下会迅速失败
    """
    results = []
    for host in hosts:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Bug: 循环泄露
        try:
            sock.connect((host, 80))
            results.append(f"Connected to {host}")
        except:
            results.append(f"Failed to connect to {host}")
        # Bug: sock 未关闭,每次循环都泄露一个 socket
    return results


if __name__ == "__main__":
    # 演示资源泄露
    data = connect_to_server("example.com", 80)
    print(f"Data: {data[:100] if data else 'None'}...")

    html = fetch_data("example.com", "/")
    print(f"HTML: {html[:100] if html else 'None'}...")

    hosts = ["example.com", "google.com", "github.com"]
    results = multiple_requests(hosts)
    print(f"Results: {results}")
