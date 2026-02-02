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
cursor = conn.cursor(dictionary=True)

# Check DynamicSchedulingJob count
cursor.execute('SELECT COUNT(*) as count FROM DynamicSchedulingJob')
count = cursor.fetchone()['count']
print(f'DynamicSchedulingJob 記錄數: {count}')

# Get first 10 records
cursor.execute('SELECT ScheduleId FROM DynamicSchedulingJob LIMIT 10')
results = cursor.fetchall()
print('\n前 10 筆記錄:')
for r in results:
    print(f"  - ScheduleId: {r['ScheduleId']}")

# Check SimulationPlanningJob
cursor.execute('SELECT COUNT(*) as count FROM SimulationPlanningJob')
sim_count = cursor.fetchone()['count']
print(f'\nSimulationPlanningJob 記錄數: {sim_count}')

# Get all simulation planning jobs
cursor.execute('SELECT id, key_value, ScheduleId, CreateDate FROM SimulationPlanningJob ORDER BY CreateDate DESC')
sim_results = cursor.fetchall()
print('\n所有 SimulationPlanningJob (由新到舊):')
for r in sim_results:
    print(f"  - ID: {r['id']}, Key: {r['key_value']}, ScheduleId: {r['ScheduleId']}, Time: {r['CreateDate']}")

cursor.close()
conn.close()
