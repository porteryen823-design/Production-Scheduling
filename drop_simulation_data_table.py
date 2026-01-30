"""
刪除 SimulationData 資料表
"""
import mysql.connector
import os
from dotenv import load_dotenv

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
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    # 刪除 SimulationData 資料表
    print("正在刪除 SimulationData 資料表...")
    cursor.execute("DROP TABLE IF EXISTS SimulationData")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("✅ SimulationData 資料表已成功刪除")
    
except mysql.connector.Error as err:
    print(f"❌ 資料庫錯誤: {err}")
except Exception as e:
    print(f"❌ 錯誤: {e}")
