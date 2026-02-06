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

def fix_collation():
    engine = create_engine(DATABASE_URL)
    
    # 我們統一使用 utf8mb4_general_ci (或 utf8mb4_unicode_ci)
    # 根據錯誤訊息，目前兩者混用了。我們統一改為 utf8mb4_unicode_ci
    target_collation = "utf8mb4_unicode_ci"
    target_charset = "utf8mb4"
    
    tables = [
        "DynamicSchedulingJob",
        "DynamicSchedulingJob_Snap",
        "DynamicSchedulingJob_Snap_Hist",
        "DynamicSchedulingJob_Hist"
    ]
    
    try:
        with engine.connect() as conn:
            # 1. 修改資料庫預設編碼
            print(f"Setting database {DB_NAME} default collation to {target_collation}...")
            conn.execute(text(f"ALTER DATABASE {DB_NAME} CHARACTER SET {target_charset} COLLATE {target_collation};"))
            
            # 2. 修改各資料表及其欄位的編碼
            for table in tables:
                print(f"Fixing table: {table}...")
                # 修改表預設編碼
                conn.execute(text(f"ALTER TABLE {table} DEFAULT CHARACTER SET {target_charset} COLLATE {target_collation};"))
                # 強制轉換所有現有欄位的編碼 (CONVERT TO)
                conn.execute(text(f"ALTER TABLE {table} CONVERT TO CHARACTER SET {target_charset} COLLATE {target_collation};"))
            
            conn.commit()
        print("\nCollation fix completed successfully.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_collation()
