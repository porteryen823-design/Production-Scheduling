
import sys
import io
import os
import mysql.connector
from dotenv import load_dotenv

# =====================================================
# Windows Unicode Output Encoding Fix
# =====================================================
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

def show_tables():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        rows = cursor.fetchall()
        print("Tables in database:")
        for row in rows:
            print(row[0])
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

show_tables()
