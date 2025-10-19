"""
Correct Database Connection Usage Examples
演示正确的数据库连接管理，避免资源泄露
"""

import sqlite3
import mysql.connector  # type: ignore
import psycopg2  # type: ignore
from contextlib import closing


# 正确示例 1: 使用 with 语句（推荐）
def query_users_sqlite_correct(db_path, user_id):
    """
    正确: 使用 with 语句自动关闭连接

    优点:
    1. 自动调用 __exit__,确保连接关闭
    2. 异常情况下也能正确关闭
    3. 代码简洁，不易出错
    """
    # 正确: with 语句会自动关闭连接
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        return result
    # conn 在此处自动关闭


# 正确示例 2: 使用 try/finally
def insert_user_sqlite_correct(db_path, username, email):
    """
    正确: 使用 try/finally 确保关闭

    适用场景:
    - 需要显式控制事务
    - 需要在 finally 中执行清理逻辑
    """
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, email) VALUES (?, ?)",
            (username, email)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Database error: {e}")
        return None
    finally:
        # 正确: 确保连接被关闭
        conn.close()


# 正确示例 3: 使用 contextlib.closing
def query_users_mysql_correct(host, user, password, database, user_id):
    """
    正确: 使用 closing 包装不支持上下文管理器的对象

    说明:
    - mysql.connector 的 connection 支持 with，但某些旧版本不支持
    - closing 确保对象的 close() 方法被调用
    """
    with closing(mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            result = cursor.fetchone()
            return result


# 正确示例 4: 连接池（生产环境推荐）
class DatabasePool:
    """
    正确: 使用连接池管理数据库连接

    优点:
    1. 复用连接，减少创建/销毁开销
    2. 控制最大连接数
    3. 自动管理连接生命周期
    """
    def __init__(self, **config):
        from mysql.connector import pooling
        self.pool = pooling.MySQLConnectionPool(
            pool_name="mypool",
            pool_size=5,  # 最多 5 个连接
            **config
        )

    def query_user(self, user_id):
        """正确: 从连接池获取连接，使用后自动归还"""
        # 从池中获取连接
        conn = self.pool.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            result = cursor.fetchone()
            cursor.close()
            return result
        finally:
            # 正确: 归还连接到池（而非关闭）
            conn.close()  # 对于连接池，close() 是归还而非关闭


# 正确示例 5: 批量操作 - 复用连接
def batch_insert_postgres_correct(host, user, password, database, users):
    """
    正确: 批量操作复用单个连接

    关键:
    1. 只创建一个连接
    2. 使用 with 确保最终关闭
    3. 使用事务提高性能
    """
    results = []

    # 正确: 只创建一次连接
    with closing(psycopg2.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )) as conn:
        with closing(conn.cursor()) as cursor:
            try:
                # 正确: 使用事务批量插入
                for username, email in users:
                    cursor.execute(
                        "INSERT INTO users (username, email) VALUES (%s, %s) RETURNING id",
                        (username, email)
                    )
                    user_id = cursor.fetchone()[0]
                    results.append(user_id)

                # 正确: 一次性提交所有插入
                conn.commit()
            except psycopg2.Error as e:
                print(f"PostgreSQL error: {e}")
                conn.rollback()
                results = []

    return results


# 正确示例 6: 事务管理
def transaction_correct(db_path):
    """
    正确: 显式管理事务并确保连接关闭

    最佳实践:
    1. 使用 with 管理连接
    2. 显式 commit 或 rollback
    3. 异常时自动回滚
    """
    with sqlite3.connect(db_path) as conn:
        try:
            cursor = conn.cursor()

            # 正确: 显式开始事务
            cursor.execute("BEGIN TRANSACTION")

            cursor.execute("UPDATE users SET status = 'active' WHERE status = 'pending'")
            affected_rows = cursor.rowcount

            # 正确: 显式提交事务
            conn.commit()

            return affected_rows
        except sqlite3.Error as e:
            # 正确: 异常时回滚
            conn.rollback()
            print(f"Transaction failed: {e}")
            return 0
    # 连接自动关闭


# 正确示例 7: 自定义上下文管理器
class DatabaseConnection:
    """
    正确: 封装为上下文管理器

    优点:
    1. 统一连接管理逻辑
    2. 支持 with 语句
    3. 更易测试和维护
    """
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path)
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # 发生异常，回滚
            self.conn.rollback()
        else:
            # 正常结束，提交
            self.conn.commit()

        # 总是关闭连接
        self.conn.close()
        return False  # 不抑制异常


def use_custom_context_manager(db_path, user_id):
    """使用自定义上下文管理器"""
    with DatabaseConnection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cursor.fetchone()


if __name__ == "__main__":
    print("=== Demonstrating Correct Database Connection Management ===\n")

    # 示例 1: with 语句（最推荐）
    print("1. Using 'with' statement:")
    try:
        result = query_users_sqlite_correct("test.db", 1)
        print(f"   Query result: {result}")
    except Exception as e:
        print(f"   Error: {e}")

    # 示例 2: try/finally
    print("\n2. Using try/finally:")
    try:
        user_id = insert_user_sqlite_correct("test.db", "alice", "alice@example.com")
        print(f"   Inserted user ID: {user_id}")
    except Exception as e:
        print(f"   Error: {e}")

    # 示例 3: 连接池
    print("\n3. Using connection pool:")
    print("   pool = DatabasePool(...)")
    print("   result = pool.query_user(1)")

    # 示例 4: 批量操作
    print("\n4. Batch operations with single connection:")
    print("   batch_insert_postgres_correct(..., users)")

    # 示例 5: 自定义上下文管理器
    print("\n5. Custom context manager:")
    print("   with DatabaseConnection('test.db') as conn:")
    print("       # 使用连接")

    print("\n✅ All connections are properly managed and closed!")
