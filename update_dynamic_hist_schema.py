import sys
import os
import io
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Windows unicode fix
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Load env
load_dotenv(os.path.join(os.getcwd(), '.env'))

DB_HOST = os.getenv('MYSQL_HOST', 'localhost')
DB_PORT = os.getenv('MYSQL_PORT', '3306')
DB_USER = os.getenv('MYSQL_USER', 'root')
DB_PASSWORD = os.getenv('MYSQL_PASSWORD', '1234')
DB_NAME = os.getenv('MYSQL_DATABASE', 'Scheduling')

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def update_schema_and_sp():
    engine = create_engine(DATABASE_URL)
    
    # 1. 重新建立 DynamicSchedulingJob_Hist (使其結構與 DynamicSchedulingJob 相同)
    drop_table_sql = "DROP TABLE IF EXISTS DynamicSchedulingJob_Hist;"
    create_table_sql = "CREATE TABLE DynamicSchedulingJob_Hist LIKE DynamicSchedulingJob;"
    
    # 2. 更新 Stored Procedure (排除 key_value, remark 欄位)
    drop_sp_sql = "DROP PROCEDURE IF EXISTS sp_LoadSimulationToHist;"
    
    create_sp_sql = """
    CREATE PROCEDURE sp_LoadSimulationToHist(
        IN p_key_value VARCHAR(100)
    )
    BEGIN
        -- 1. 清除現有資料
        TRUNCATE TABLE DynamicSchedulingJob_Hist;
        
        -- 2. 從 DynamicSchedulingJob_Snap 過濾並寫入 (僅對應 DynamicSchedulingJob 的欄位)
        INSERT INTO DynamicSchedulingJob_Hist (
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
            ScheduleId, 
            LotPlanRaw, 
            CreateDate, 
            CreateUser, 
            PlanSummary, 
            LotPlanResult, 
            LotStepResult, 
            machineTaskSegment, 
            simulation_end_time
        FROM DynamicSchedulingJob_Snap
        WHERE key_value = p_key_value;
    END;
    """
    
    try:
        with engine.connect() as conn:
            print("Step 1: Re-creating DynamicSchedulingJob_Hist table to match DynamicSchedulingJob...")
            conn.execute(text(drop_table_sql))
            conn.execute(text(create_table_sql))
            
            # 修正編碼以防萬一
            conn.execute(text("ALTER TABLE DynamicSchedulingJob_Hist CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"))
            
            print("Step 2: Updating Stored Procedure sp_LoadSimulationToHist...")
            conn.execute(text(drop_sp_sql))
            conn.execute(text(create_sp_sql))
            
            conn.commit()
        print("\nSchema and Stored Procedure updated successfully.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    update_schema_and_sp()
