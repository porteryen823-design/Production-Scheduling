import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

db_config = {
    'host': os.getenv('MYSQL_HOST'),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE')
}

conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# Check DynamicSchedulingJob schema
print("=== DynamicSchedulingJob Schema ===")
cursor.execute('SHOW CREATE TABLE DynamicSchedulingJob')
result = cursor.fetchone()
print(result[1])

print("\n\n=== SimulationPlanningJob Schema ===")
cursor.execute('SHOW CREATE TABLE SimulationPlanningJob')
result = cursor.fetchone()
print(result[1])

cursor.close()
conn.close()
