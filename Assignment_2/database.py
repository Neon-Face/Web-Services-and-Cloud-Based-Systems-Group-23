import sqlite3

def show_all_data(db_path):
    # 连接到 SQLite 数据库
    conn = sqlite3.connect(db_path)  # 确保路径正确
    cursor = conn.cursor()

    # 查询 users 表中的所有数据
    cursor.execute("SELECT * FROM User")

    # 获取查询结果
    users = cursor.fetchall()

    # 打印查询结果
    print("ID | Username | Pwd")
    print("-" * 20)
    for user in users:
        print(f"{user[0]} | {user[1]} {user[2]}")



    # 关闭数据库连接
    conn.close()
    return

def check_user_exists(db_path, username):

    conn = sqlite3.connect(db_path)  # 确保路径正确
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM User WHERE username = ?", (username,))
    user = cursor.fetchone()

    conn.close()

    return user is not None

def get_credentials(db_path, username):

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT username,password_hash FROM User WHERE username = ?", (username,))
    
    result = cursor.fetchone()
    
    conn.close()
    
    return (result[0],result[1]) if result else None

def update_password(db_path, username, new_password):

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("UPDATE User SET password = ? WHERE username = ?", (new_password, username))
    
    affected_rows = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return affected_rows > 0

show_all_data('instance/users.db')