"""
SMTP Connection Leak Examples
演示 SMTP 连接未关闭导致的资源泄露
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# Bug RM-NET-004: SMTP 连接未关闭
def send_email_smtp(smtp_server, port, sender, password, recipient, subject, body):
    """
    Bug: SMTP 连接未关闭

    问题:
    - 创建 SMTP 连接后未调用 quit()
    - 连接在函数结束时未被释放
    - 服务器端连接累积，可能达到限制

    影响:
    - SMTP 服务器连接数限制
    - 可能被服务器拒绝连接
    - 网络资源浪费

    CWE: CWE-404 (Improper Resource Shutdown or Release)
    """
    # Bug: 创建连接后未关闭
    server = smtplib.SMTP(smtp_server, port)
    server.starttls()
    server.login(sender, password)

    # 构造邮件
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient

    try:
        server.send_message(msg)
        return True
    except smtplib.SMTPException as e:
        print(f"Failed to send email: {e}")
        return False
    # Bug: server 未调用 quit() 关闭连接


def send_bulk_emails(smtp_server, port, sender, password, recipients):
    """
    Bug: 循环中创建多个未关闭的连接

    场景:
    - 每个收件人都创建新连接
    - 所有连接都未关闭
    - 批量发送时快速耗尽连接
    """
    sent_count = 0

    for recipient in recipients:
        # Bug: 每次循环创建新连接且不关闭
        server = smtplib.SMTP(smtp_server, port)
        server.starttls()
        server.login(sender, password)

        msg = MIMEText(f"Hello {recipient}")
        msg['Subject'] = "Bulk Email"
        msg['From'] = sender
        msg['To'] = recipient

        try:
            server.send_message(msg)
            sent_count += 1
        except smtplib.SMTPException as e:
            print(f"Failed to send to {recipient}: {e}")
        # Bug: server 未关闭，循环累积连接

    return sent_count


def send_with_attachment(smtp_server, port, sender, password, recipient,
                        subject, body, attachment_path):
    """
    Bug: 异常情况下连接未关闭

    问题:
    - 正常路径下关闭连接
    - 异常路径下连接泄露
    """
    server = smtplib.SMTP(smtp_server, port)
    server.starttls()
    server.login(sender, password)

    # 构造多部分邮件
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient
    msg.attach(MIMEText(body))

    # Bug: 如果读取附件时出错，连接不会关闭
    with open(attachment_path, 'rb') as f:
        attachment = MIMEText(f.read(), 'base64')
        msg.attach(attachment)

    server.send_message(msg)

    # 只在正常情况下关闭
    server.quit()  # Bug: 异常时不会执行到这里


def send_email_ssl(smtp_server, port, sender, password, recipient, subject, body):
    """
    Bug: SMTP_SSL 连接未关闭

    说明:
    - SMTP_SSL 也需要显式关闭
    - 比普通 SMTP 消耗更多资源
    """
    # Bug: 创建 SSL 连接但未关闭
    server = smtplib.SMTP_SSL(smtp_server, port)
    server.login(sender, password)

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient

    try:
        server.send_message(msg)
        return True
    except smtplib.SMTPException as e:
        print(f"Failed to send email: {e}")
        return False
    # Bug: server 未调用 quit()


def partial_close_bug(smtp_server, port, sender, password, recipient, subject, body):
    """
    Bug: 部分路径下未关闭连接

    场景:
    - 某些条件分支下关闭连接
    - 其他分支下泄露连接
    """
    server = smtplib.SMTP(smtp_server, port)
    server.starttls()

    # 登录可能失败
    try:
        server.login(sender, password)
    except smtplib.SMTPAuthenticationError:
        print("Authentication failed")
        # Bug: 返回时未关闭 server
        return False

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient

    try:
        server.send_message(msg)
        server.quit()  # 只在成功时关闭
        return True
    except smtplib.SMTPException as e:
        print(f"Failed to send: {e}")
        # Bug: 异常时未关闭 server
        return False


if __name__ == "__main__":
    print("=== Demonstrating SMTP Connection Leaks ===")
    print("\n!!! WARNING: These examples contain REAL resource leak bugs !!!")
    print("!!! Running these functions repeatedly will leak SMTP connections !!!\n")

    # 示例 1: 单个邮件发送泄露
    print("1. Single email connection leak (COMMENTED OUT):")
    print("   send_email_smtp('smtp.gmail.com', 587, ...)")
    # send_email_smtp("smtp.gmail.com", 587, "sender@example.com", "password",
    #                 "recipient@example.com", "Test", "Hello")

    # 示例 2: 批量发送泄露
    print("\n2. Bulk email connection leak (COMMENTED OUT):")
    print("   send_bulk_emails('smtp.gmail.com', 587, ..., recipients)")
    # recipients = ["user1@example.com", "user2@example.com", "user3@example.com"]
    # send_bulk_emails("smtp.gmail.com", 587, "sender@example.com", "password", recipients)

    # 示例 3: SSL 连接泄露
    print("\n3. SSL connection leak (COMMENTED OUT):")
    print("   send_email_ssl('smtp.gmail.com', 465, ...)")
    # send_email_ssl("smtp.gmail.com", 465, "sender@example.com", "password",
    #                "recipient@example.com", "Test", "Hello")

    print("\nAll dangerous calls are commented out for safety.")
