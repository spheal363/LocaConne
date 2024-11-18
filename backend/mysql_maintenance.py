import mysql.connector as mydb

# MySQLコネクションの設定
def create_mysql_connection():
    return mydb.connect(
        host="23.251.151.188", 
        port="3306", 
        user="root", 
        database="locaconne_schema"
    )

# モジュールが直接実行された場合のテスト
if __name__ == "__main__":
    conn = create_mysql_connection()
    if conn.is_connected():
        print("MySQL connection successful")
    else:
        print("MySQL connection failed")
    conn.close()
