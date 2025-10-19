"""
Database Connection Leak Examples
演示数据库连接未关闭导致的资源泄露
"""

import sqlite3
import mysql.connector  # type: ignore
import psycopg2  # type: ignore


# Bug RM-NET-003: SQLite 连接未关闭
def query_users_sqlite(db_path, user_id):
    """
    Bug: SQLite 连接未关闭

    问题:
    - 创建数据库连接后未调用 close()
    - 连接对象在函数结束时未被释放
    - 长时间运行会累积大量未关闭的连接

    影响:
    - 文件描述符泄露
    - 数据库锁可能无法释放
    - 多次调用导致"too many open files"错误

    CWE: CWE-404 (Improper Resource Shutdown or Release)
    """
    # Bug: 创建连接后未关闭
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        return result
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    # Bug: conn 和 cursor 都未被关闭


def insert_user_sqlite(db_path, username, email):
    """
    Bug: 异常路径下连接未关闭

    场景:
    - 正常路径下可能关闭连接
    - 异常路径下连接泄露
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Bug: 如果这里抛出异常，连接不会被关闭
    cursor.execute(
        "INSERT INTO users (username, email) VALUES (?, ?)",
        (username, email)
    )
    conn.commit()

    # 只在正常路径关闭
    conn.close()  # Bug: 异常路径下不会执行到这里


def query_users_mysql(host, user, password, database, user_id):
    """
    Bug: MySQL 连接未关闭

    问题:
    - MySQL 连接池有限，未关闭会耗尽连接
    - 服务器端可能拒绝新连接
    """
    # Bug: 创建连接后未关闭
    conn = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )

    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        return result
    except mysql.connector.Error as e:
        print(f"MySQL error: {e}")
        return None
    # Bug: conn 和 cursor 都未关闭


def batch_insert_postgres(host, user, password, database, users):
    """
    Bug: PostgreSQL 连接在循环中泄露

    场景:
    - 循环中创建多个连接
    - 每个连接都未关闭
    - 批量操作时快速耗尽连接池
    """
    results = []

    for username, email in users:
        # Bug: 每次循环都创建新连接，且不关闭
        conn = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username, email) VALUES (%s, %s) RETURNING id",
                (username, email)
            )
            user_id = cursor.fetchone()[0]
            conn.commit()
            results.append(user_id)
        except psycopg2.Error as e:
            print(f"PostgreSQL error: {e}")
            conn.rollback()
        # Bug: conn 未关闭，循环结束后累积大量连接

    return results


def transaction_without_close(db_path):
    """
    Bug: 事务中连接未关闭

    问题:
    - 事务未提交或回滚
    - 连接未关闭
    - 可能导致锁等待超时
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Bug: 开始事务但未提交或回滚
    cursor.execute("BEGIN TRANSACTION")

    cursor.execute("UPDATE users SET status = 'active' WHERE status = 'pending'")

    # Bug: 函数直接返回，事务未结束，连接未关闭
    return cursor.rowcount


if __name__ == "__main__":
    print("=== Demonstrating Database Connection Leaks ===")
    print("\n!!! WARNING: These examples contain REAL resource leak bugs !!!")
    print("!!! Running these functions repeatedly will leak database connections !!!\n")

    # 示例 1: SQLite 连接泄露
    print("1. SQLite connection leak (COMMENTED OUT):")
    print("   query_users_sqlite('users.db', 1)")
    # query_users_sqlite("users.db", 1)  # 每次调用都泄露一个连接

    # 示例 2: MySQL 连接泄露
    print("\n2. MySQL connection leak (COMMENTED OUT):")
    print("   query_users_mysql('localhost', 'user', 'pass', 'db', 1)")
    # query_users_mysql("localhost", "user", "password", "testdb", 1)

    # 示例 3: 批量操作中的连接泄露
    print("\n3. Batch operation connection leak (COMMENTED OUT):")
    print("   batch_insert_postgres(..., users)")
    # users = [("alice", "alice@example.com"), ("bob", "bob@example.com")]
    # batch_insert_postgres("localhost", "user", "pass", "db", users)

    print("\nAll dangerous calls are commented out for safety.")
