import mysql.connector
import os
import json
from dotenv import load_dotenv

load_dotenv()

db_config = {
    'host': os.getenv('MYSQL_HOST'),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE')
}

try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    # 1. Check DynamicSchedulingJob
    print("Checking DynamicSchedulingJob...")
    cursor.execute("SELECT ScheduleId, CreateUser, PlanSummary, simulation_end_time FROM DynamicSchedulingJob ORDER BY CreateDate DESC LIMIT 1")
    job = cursor.fetchone()
    if job:
        print(f"Latest Job: {job}")
    else:
        print("No jobs found.")

    # 2. Check Lots
    print("\nChecking Lots (Sample)...")
    cursor.execute("SELECT LotId, PlanFinishDate, Delay_Days, DueDate FROM Lots WHERE PlanFinishDate IS NOT NULL LIMIT 5")
    lots = cursor.fetchall()
    for lot in lots:
        print(lot)

    # 3. Check LotOperations History
    print("\nChecking LotOperations PlanHistory (Sample)...")
    cursor.execute("SELECT LotId, Step, PlanHistory FROM LotOperations WHERE PlanHistory IS NOT NULL LIMIT 2")
    ops = cursor.fetchall()
    for op in ops:
        history = json.loads(op['PlanHistory'])
        print(f"Lot: {op['LotId']}, Step: {op['Step']}, History Count: {len(history)}")
        print(f"Latest History: {history[-1]}")
        
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
