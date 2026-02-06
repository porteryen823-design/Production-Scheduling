
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

def inspect_table(table_name):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(f"DESCRIBE {table_name}")
        rows = cursor.fetchall()
        print(f"Schema for {table_name}:")
        for row in rows:
            print(row)
        conn.close()
    except Exception as e:
        print(f"Error inspecting {table_name}: {e}")

inspect_table('DynamicSchedulingJob_Snap')
