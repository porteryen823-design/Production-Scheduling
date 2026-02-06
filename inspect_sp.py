
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

def show_procedure(proc_name):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(f"SHOW CREATE PROCEDURE {proc_name}")
        rows = cursor.fetchall()
        print(f"Procedure {proc_name}:")
        for row in rows:
            print(row[2]) # The 3rd column contains the Create Procedure body
        conn.close()
    except Exception as e:
        print(f"Error inspecting {proc_name}: {e}")

show_procedure('sp_LoadSimulationToHist')
