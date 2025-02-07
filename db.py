import mysql.connector as mydb
import configparser

def load_db_config():
    """config.ini からデータベース設定を読み込む"""
    config = configparser.ConfigParser()
    config.read("./config.ini")
    return config["mysql"]

def create_mysql_connection():
    """外部ファイルから読み込んだ設定で MySQL に接続"""
    db_config = load_db_config()
    return mydb.connect(
        host=db_config["host"],
        port=db_config["port"],
        user=db_config["user"],
        password=db_config["password"],
        database=db_config["database"]
    )

# モジュール単体でのテスト用
if __name__ == "__main__":
    conn = create_mysql_connection()
    if conn.is_connected():
        print("MySQL connection successful")
    else:
        print("MySQL connection failed")
    conn.close()
