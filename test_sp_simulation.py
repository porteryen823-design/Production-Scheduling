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

def test_stored_procedure():
    print("Testing Stored Procedure: sp_InsertSimulationPlanning...")
    engine = create_engine(DATABASE_URL)
    
    test_key = "AutoTest_Key"
    test_remark = "AutoTest_Remark"
    
    try:
        with engine.connect() as conn:
            # 1. Count DynamicSchedulingJob Source Rows
            src_count = conn.execute(text("SELECT COUNT(*) FROM DynamicSchedulingJob")).scalar()
            print(f"Source (DynamicSchedulingJob) Count: {src_count}")
            
            if src_count == 0:
                print("Warning: DynamicSchedulingJob is empty. Insert will result in 0 rows.")

            # 2. Count DynamicSchedulingJob_Snap Before
            dest_count_before = conn.execute(text(f"SELECT COUNT(*) FROM DynamicSchedulingJob_Snap WHERE key_value = '{test_key}'")).scalar()
            print(f"Destination match Count (Before): {dest_count_before}")
            
            # 3. Call SP
            print(f"Calling SP with key='{test_key}', remark='{test_remark}'...")
            conn.execute(text("CALL sp_InsertSimulationPlanning(:k, :r)"), {"k": test_key, "r": test_remark})
            conn.commit()
            
            # 4. Count DynamicSchedulingJob_Snap After
            # Note: We need a new transaction or commit to see changes if using some isolation levels, 
            # but usually same connection sees it.
            dest_count_after = conn.execute(text(f"SELECT COUNT(*) FROM DynamicSchedulingJob_Snap WHERE key_value = '{test_key}'")).scalar()
            print(f"Destination match Count (After): {dest_count_after}")
            
            # 5. Verify
            expected = dest_count_before + src_count
            if dest_count_after == expected:
                print(f"SUCCESS: Count matches expected ({expected})")
                
                # Show sample
                sample = conn.execute(text(f"SELECT id, key_value, ScheduleId FROM DynamicSchedulingJob_Snap WHERE key_value = '{test_key}' LIMIT 3")).fetchall()
                print("\nSample Data:")
                for row in sample:
                    print(row)
            else:
                print(f"FAILURE: Count mismatch. Expected {expected}, Got {dest_count_after}")

    except Exception as e:
        print(f"Error testing stored procedure: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_stored_procedure()
