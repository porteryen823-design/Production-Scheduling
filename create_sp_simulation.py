"""
本程式用於在 MySQL 資料庫中建立 `sp_InsertSimulationPlanning` 預存程序 (Stored Procedure)。
主要功能：
1. 讀取 .env 或環境變數中的資料庫連線配置。
2. 建立預存程序，該程序負責將目前的動態排程結果 (DynamicSchedulingJob) 的快照儲存至模擬規劃表 (SimulationPlanningJob)。
3. 此程序支援傳入自定義的標籤 (key_value) 與備註 (remark)。
"""
import sys
import os
import io
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# 修正 Windows Unicode 輸出問題
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 載入環境變數設定
load_dotenv(os.path.join(os.getcwd(), '.env'))

# 從環境變數讀取資料庫連線參數
DB_HOST = os.getenv('MYSQL_HOST', 'localhost')
DB_PORT = os.getenv('MYSQL_PORT', '3306')
DB_USER = os.getenv('MYSQL_USER', 'root')
DB_PASSWORD = os.getenv('MYSQL_PASSWORD', '1234')
DB_NAME = os.getenv('MYSQL_DATABASE', 'Scheduling')

# 組成 SQLAlchemy 連線字串
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def create_stored_procedure():
    """執行預存程序的建立作業"""
    print("Creating Stored Procedure: sp_InsertSimulationPlanning...")
    engine = create_engine(DATABASE_URL)
    
    # 定義 SQL 分別為：存在則刪除、以及建立新的預存程序
    drop_sql = "DROP PROCEDURE IF EXISTS sp_InsertSimulationPlanning;"
    
    create_sql = """
    CREATE PROCEDURE sp_InsertSimulationPlanning(
        IN p_key_value VARCHAR(100),
        IN p_remark TEXT
    )
    BEGIN
        INSERT INTO SimulationPlanningJob (
            key_value, 
            remark, 
            ScheduleId, 
            LotPlanRaw, 
            CreateDate, 
            CreateUser, 
            PlanSummary, 
            LotPlanResult, 
            LotStepResult, 
            machineTaskSegment, 
            simulation_end_time
        )
        SELECT 
            p_key_value,
            p_remark,
            ScheduleId, 
            LotPlanRaw, 
            CreateDate, 
            CreateUser, 
            PlanSummary, 
            LotPlanResult, 
            LotStepResult, 
            machineTaskSegment, 
            simulation_end_time
        FROM DynamicSchedulingJob;
    END;
    """
    
    try:
        # 開始執行資料庫操作
        with engine.connect() as conn:
            conn.execute(text(drop_sql))
            conn.execute(text(create_sql))
            conn.commit()
        print("Stored Procedure created successfully.")
    except Exception as e:
        print(f"Error creating stored procedure: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_stored_procedure()
