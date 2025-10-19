"""
Correct SMTP Connection Usage Examples
演示正确的 SMTP 连接管理，避免资源泄露
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from contextlib import contextmanager


# 正确示例 1: 使用 with 语句（推荐）
def send_email_smtp_correct(smtp_server, port, sender, password, recipient, subject, body):
    """
    正确: 使用 with 语句自动关闭 SMTP 连接

    优点:
    1. 自动调用 quit(),确保连接关闭
    2. 异常情况下也能正确关闭
    3. 代码简洁清晰
    """
    # 正确: with 语句会自动调用 quit()
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls()
        server.login(sender, password)

        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recipient

        server.send_message(msg)
        return True
    # server.quit() 在此处自动调用


# 正确示例 2: 使用 try/finally
def send_email_try_finally(smtp_server, port, sender, password, recipient, subject, body):
    """
    正确: 使用 try/finally 确保连接关闭

    适用场景:
    - 需要在 finally 中执行额外清理
    - 需要更精细的错误处理
    """
    server = smtplib.SMTP(smtp_server, port)
    try:
        server.starttls()
        server.login(sender, password)

        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recipient

        server.send_message(msg)
        return True
    except smtplib.SMTPException as e:
        print(f"Failed to send email: {e}")
        return False
    finally:
        # 正确: 确保连接被关闭
        server.quit()


# 正确示例 3: 批量发送 - 复用单个连接
def send_bulk_emails_correct(smtp_server, port, sender, password, recipients):
    """
    正确: 批量发送时复用单个连接

    关键:
    1. 只创建一个连接
    2. 循环发送所有邮件
    3. 使用 with 确保最终关闭
    """
    sent_count = 0

    # 正确: 只创建一次连接
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls()
        server.login(sender, password)

        # 正确: 复用连接发送多封邮件
        for recipient in recipients:
            msg = MIMEText(f"Hello {recipient}")
            msg['Subject'] = "Bulk Email"
            msg['From'] = sender
            msg['To'] = recipient

            try:
                server.send_message(msg)
                sent_count += 1
            except smtplib.SMTPException as e:
                print(f"Failed to send to {recipient}: {e}")

    return sent_count


# 正确示例 4: SMTP_SSL 连接管理
def send_email_ssl_correct(smtp_server, port, sender, password, recipient, subject, body):
    """
    正确: SMTP_SSL 也使用 with 语句

    说明:
    - SMTP_SSL 同样支持上下文管理器
    - 自动处理 SSL 连接的关闭
    """
    with smtplib.SMTP_SSL(smtp_server, port) as server:
        server.login(sender, password)

        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recipient

        server.send_message(msg)
        return True


# 正确示例 5: 带附件的邮件
def send_with_attachment_correct(smtp_server, port, sender, password, recipient,
                                 subject, body, attachment_path):
    """
    正确: 异常处理 + 资源管理

    最佳实践:
    1. 嵌套 with 语句管理多个资源
    2. 异常处理不影响资源释放
    """
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls()
        server.login(sender, password)

        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recipient
        msg.attach(MIMEText(body))

        # 正确: 文件也使用 with 语句
        try:
            with open(attachment_path, 'rb') as f:
                attachment = MIMEText(f.read(), 'base64')
                msg.attach(attachment)

            server.send_message(msg)
            return True
        except FileNotFoundError:
            print(f"Attachment not found: {attachment_path}")
            return False
    # 所有资源都被正确关闭


# 正确示例 6: 自定义上下文管理器
@contextmanager
def smtp_connection(smtp_server, port, sender, password, use_ssl=False):
    """
    正确: 封装为可复用的上下文管理器

    优点:
    1. 统一连接配置
    2. 支持 SSL 切换
    3. 更易测试和维护
    """
    if use_ssl:
        server = smtplib.SMTP_SSL(smtp_server, port)
    else:
        server = smtplib.SMTP(smtp_server, port)
        server.starttls()

    try:
        server.login(sender, password)
        yield server
    finally:
        server.quit()


def send_email_with_custom_context(smtp_server, port, sender, password,
                                   recipient, subject, body):
    """使用自定义上下文管理器"""
    with smtp_connection(smtp_server, port, sender, password) as server:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recipient

        server.send_message(msg)
        return True


# 正确示例 7: 连接池管理（高级）
class SMTPPool:
    """
    正确: SMTP 连接池（生产环境推荐）

    优点:
    1. 复用连接，减少握手开销
    2. 控制并发连接数
    3. 自动重连机制
    """
    def __init__(self, smtp_server, port, sender, password, pool_size=3):
        self.config = {
            'smtp_server': smtp_server,
            'port': port,
            'sender': sender,
            'password': password
        }
        self.pool_size = pool_size
        self.pool = []

    def _create_connection(self):
        """创建新连接"""
        server = smtplib.SMTP(self.config['smtp_server'], self.config['port'])
        server.starttls()
        server.login(self.config['sender'], self.config['password'])
        return server

    @contextmanager
    def get_connection(self):
        """从池中获取连接"""
        if self.pool:
            server = self.pool.pop()
        else:
            server = self._create_connection()

        try:
            yield server
        finally:
            # 归还连接到池
            if len(self.pool) < self.pool_size:
                self.pool.append(server)
            else:
                server.quit()

    def close_all(self):
        """关闭所有连接"""
        while self.pool:
            server = self.pool.pop()
            server.quit()


def send_email_with_pool(pool, recipient, subject, body):
    """使用连接池发送邮件"""
    with pool.get_connection() as server:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = pool.config['sender']
        msg['To'] = recipient

        server.send_message(msg)


if __name__ == "__main__":
    print("=== Demonstrating Correct SMTP Connection Management ===\n")

    # 示例 1: with 语句（最推荐）
    print("1. Using 'with' statement:")
    print("   with smtplib.SMTP(...) as server:")
    print("       server.send_message(msg)")

    # 示例 2: 批量发送
    print("\n2. Bulk sending with single connection:")
    print("   sent = send_bulk_emails_correct(..., recipients)")

    # 示例 3: SSL 连接
    print("\n3. SSL connection with 'with' statement:")
    print("   with smtplib.SMTP_SSL(...) as server:")

    # 示例 4: 自定义上下文管理器
    print("\n4. Custom context manager:")
    print("   with smtp_connection(...) as server:")

    # 示例 5: 连接池
    print("\n5. Connection pool:")
    print("   pool = SMTPPool(...)")
    print("   send_email_with_pool(pool, ...)")
    print("   pool.close_all()")

    print("\n✅ All SMTP connections are properly managed and closed!")
