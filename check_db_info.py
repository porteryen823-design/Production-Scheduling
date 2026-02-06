import mysql.connector
import os
import sys
import io
from dotenv import load_dotenv

# 強制要求：涉及 UI 輸出或自動化腳本的 Python 檔案，必須在程式進入點加入編碼修正
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("正在加載 .env 環境變數...")
load_dotenv()

db_config = {
    'host': os.getenv('MYSQL_HOST'),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE'),
    'connect_timeout': 5  # 增加 5 秒連線逾時，避免無限卡住
}

print(f"嘗試連線至資料庫: {db_config['host']} (User: {db_config['user']})")

try:
    conn = mysql.connector.connect(**db_config)
    print("連線成功！正在取得資料表結構...")
    cursor = conn.cursor()
    
    for table in ['Lots', 'LotOperations']:
        cursor.execute(f"DESCRIBE {table}")
        print(f"\nTable: {table}")
        for row in cursor.fetchall():
            print(row)
        
    cursor.close()
    conn.close()
    print("\n操作完成並已關閉連線。")
except Exception as e:
    print(f"\n連線或執行發生錯誤: {e}")
    print("請檢查：")
    print(f"1. 虛擬機是否能連通 {db_config['host']} (嘗試 ping {db_config['host']})")
    print("2. MySQL 是否允許遠端連線")
    print("3. 防火牆是否開啟 3306 埠")

