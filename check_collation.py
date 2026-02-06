import sys
import io
import mysql.connector
import os
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 載入環境變數
load_dotenv()

# 資料庫連線設定
db_config = {
    'host': os.getenv('MYSQL_HOST'),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE')
}

try:
    print(f"Connecting to database: {db_config['host']}")
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    # 檢查資料庫預設 collation
    cursor.execute(f"SELECT DEFAULT_CHARACTER_SET_NAME, DEFAULT_COLLATION_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = '{db_config['database']}'")
    db_info = cursor.fetchone()
    print(f"\nDatabase Default Charset: {db_info[0]}, Collation: {db_info[1]}")
    
    # 檢查 Lots 表的 collation
    print("\n=== Lots Table Columns Collation ===")
    cursor.execute("""
        SELECT COLUMN_NAME, CHARACTER_SET_NAME, COLLATION_NAME 
        FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'Lots' 
        AND CHARACTER_SET_NAME IS NOT NULL
    """, (db_config['database'],))
    
    for row in cursor.fetchall():
        print(f"{row[0]}: {row[1]} / {row[2]}")
    
    # 檢查 LotOperations 表的 collation
    print("\n=== LotOperations Table Columns Collation ===")
    cursor.execute("""
        SELECT COLUMN_NAME, CHARACTER_SET_NAME, COLLATION_NAME 
        FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'LotOperations' 
        AND CHARACTER_SET_NAME IS NOT NULL
    """, (db_config['database'],))
    
    for row in cursor.fetchall():
        print(f"{row[0]}: {row[1]} / {row[2]}")
    
    cursor.close()
    conn.close()
    print("\nCheck completed.")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
