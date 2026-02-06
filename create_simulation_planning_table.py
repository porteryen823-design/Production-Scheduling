"""
本程式用於建立模擬規劃主表 (DynamicSchedulingJob_Snap)。
主要功能：
1. 從 .env 讀取資料庫連線資訊。
2. 執行 SQL 指令建立 `DynamicSchedulingJob_Snap` 資料表，用於儲存排程結果的快照。
3. 若資料表已存在，則不會重複建立。
"""
import mysql.connector
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 設定資料庫連線參數
db_config = {
    'host': os.getenv('MYSQL_HOST'),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE')
}

# 定義建立資料表的 SQL 指令
create_table_sql = """
CREATE TABLE IF NOT EXISTS DynamicSchedulingJob_Snap (
    id INT AUTO_INCREMENT PRIMARY KEY,
    key_value VARCHAR(100) NOT NULL,
    remark TEXT,
    ScheduleId VARCHAR(50),
    LotPlanRaw LONGTEXT,
    CreateDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    CreateUser VARCHAR(50),
    PlanSummary VARCHAR(2500),
    LotPlanResult LONGTEXT,
    LotStepResult LONGTEXT,
    machineTaskSegment LONGTEXT,
    simulation_end_time DATETIME
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

def main():
    """執行資料表建立作業"""
    try:
        # 建立與資料庫的連線
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        print("Creating DynamicSchedulingJob_Snap table...")
        
        # 執行 SQL 指令
        cursor.execute(create_table_sql)
        conn.commit()
        
        cursor.close()
        conn.close()
        print("Table DynamicSchedulingJob_Snap created successfully or already exists.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
