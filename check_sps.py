import mysql.connector
import os
import sys
import io
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

load_dotenv()

db_config = {
    'host': os.getenv('MYSQL_HOST'),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE')
}

procedures_to_check = [
    'sp_clean_lots',
    'sp_InsertLot',
    'sp_InsertSimulationPlanning',
    'sp_LoadSimulationToHist',
    'sp_SaveDynamicSchedulingJob',
    'sp_UpdatePlanResultsJSON'
]

conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

print("Checking Stored Procedures in Database:")
print("-" * 40)

for sp in procedures_to_check:
    try:
        cursor.execute(f"SHOW CREATE PROCEDURE {sp}")
        result = cursor.fetchone()
        if result:
            print(f"[OK] {sp} exists.")
            print(f"DEF: {result[2][:200]}...") # Print first 200 chars to verify
        else:
            print(f"[MISSING] {sp} NOT found.")
    except Exception as e:
        print(f"[ERROR] {sp}: {e}")

cursor.close()
conn.close()
