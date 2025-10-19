"""
SQL Injection Examples
演示SQL注入漏洞
"""

import sqlite3

# Bug INJ-SQL-001: 字符串拼接 SQL
def get_user_by_id(user_id):
    """
    Bug: 使用 f-string 拼接 SQL
    
    攻击场景:
    - 输入: "1 OR 1=1"
    - SQL: SELECT * FROM users WHERE id=1 OR 1=1
    - 结果: 返回所有用户
    """
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Bug: SQL 拼接
    query = f"SELECT * FROM users WHERE id={user_id}"
    cursor.execute(query)
    return cursor.fetchall()


# Bug INJ-SQL-002: format 格式化 SQL
def search_users(table_name, keyword):
    """
    Bug: 使用 format() 拼接表名和条件
    
    攻击场景:
    - table_name: "users; DROP TABLE users--"
    - 结果: 删除表
    """
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Bug: 表名和条件都未验证
    query = "SELECT * FROM {} WHERE name LIKE '%{}%'".format(table_name, keyword)
    cursor.execute(query)
    return cursor.fetchall()

if __name__ == "__main__":
    print("SQL injection examples (DANGEROUS - do not run)")
