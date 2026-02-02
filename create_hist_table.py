"""
本程式用於建立模擬規劃歷史表 (SimulationPlanningJob_Hist)。
主要功能：
1. 讀取 .env 或環境變數中的資料庫連線資訊。
2. 優先使用 MySQL 的 `CREATE TABLE ... LIKE` 語法，完整複製 `SimulationPlanningJob` 的結構。
3. 若 LIKE 語法失敗，則會嘗試透過 SQLAlchemy 的模型定義 (metadata) 進行建立。
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

# 從環境變數讀取資料庫連線資訊
DB_HOST = os.getenv('MYSQL_HOST', 'localhost')
DB_PORT = os.getenv('MYSQL_PORT', '3306')
DB_USER = os.getenv('MYSQL_USER', 'root')
DB_PASSWORD = os.getenv('MYSQL_PASSWORD', '1234')
DB_NAME = os.getenv('MYSQL_DATABASE', 'Scheduling')

# 組成 SQLAlchemy 連線字串
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def create_hist_table():
    """執行歷史表建立邏輯"""
    print("Creating table: SimulationPlanningJob_Hist...")
    engine = create_engine(DATABASE_URL)
    
    # 優先嘗試 MySQL 特有的 LIKE 語法，以確保結構完全一致
    sql = "CREATE TABLE IF NOT EXISTS SimulationPlanningJob_Hist LIKE SimulationPlanningJob;"
    
    try:
        with engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()
        print("Table SimulationPlanningJob_Hist created successfully.")
    except Exception as e:
        # 如果 LIKE 失敗（例如非 MySQL 環境），則嘗試使用 SQLAlchemy Metadata 建立
        print(f"Error creating table via LIKE: {e}")
        print("Attempting to create using SQLAlchemy metadata...")
        try:
            from backend.src.domain.models.simulation_planning_job_hist import SimulationPlanningJobHist
            SimulationPlanningJobHist.__table__.create(engine)
            print("Table created via SQLAlchemy successfully.")
        except Exception as e2:
             print(f"Fallback create failed: {e2}")

if __name__ == "__main__":
    create_hist_table()
