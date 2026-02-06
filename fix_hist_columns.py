
import sys
import io
import os
import mysql.connector
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

load_dotenv()

db_config = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', '1234'),
    'database': os.getenv('MYSQL_DATABASE', 'Scheduling')
}

def fix_hist_table():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        print("Checking DynamicSchedulingJob_Hist columns...")
        cursor.execute("DESCRIBE DynamicSchedulingJob_Hist")
        columns = [row[0] for row in cursor.fetchall()]
        
        if 'key_value' not in columns:
            print("Adding key_value column to DynamicSchedulingJob_Hist...")
            cursor.execute("ALTER TABLE DynamicSchedulingJob_Hist ADD COLUMN key_value VARCHAR(100) NOT NULL AFTER ScheduleId")
        
        if 'remark' not in columns:
            print("Adding remark column to DynamicSchedulingJob_Hist...")
            cursor.execute("ALTER TABLE DynamicSchedulingJob_Hist ADD COLUMN remark TEXT AFTER key_value")
            
        conn.commit()
        print("Done fixing DynamicSchedulingJob_Hist.")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_hist_table()
