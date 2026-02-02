"""
本程式用於檢查 MySQL 資料庫中是否存在特定的資料表。
主要功能：
1. 讀取 .env 檔案中的資料庫連線配置。
2. 檢查指定的資料表清單（包含歷史表與備份表）是否存在於資料庫中。
3. 輸出檢查結果，方便開發者快速確認資料庫結構。
"""
import mysql.connector
import os
import sys
import io
from dotenv import load_dotenv

# 修正 Windows 環境下的 Unicode 輸出問題
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 載入環境變數
load_dotenv()

# 設定資料庫連線參數
db_config = {
    'host': os.getenv('MYSQL_HOST'),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE')
}

# 定義需要檢查的資料表清單
tables_to_check = [
    'DynamicSchedulingJob_Hist',
    'SimulationPlanningJob_Hist',
    'SimulationPlanningJob'
]

# 建立資料庫連線並執行檢查
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

print("Checking Tables in Database:")
print("-" * 40)

for table in tables_to_check:
    cursor.execute(f"SHOW TABLES LIKE '{table}'")
    result = cursor.fetchone()
    if result:
        print(f"[OK] Table {table} exists.")
    else:
        print(f"[MISSING] Table {table} NOT found.")

cursor.close()
conn.close()
