import mysql.connector
import os
import time
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 參數解析
parser = argparse.ArgumentParser(description='APS 模擬程式')
parser.add_argument('--iterations', type=int, default=100, help='模擬次數 (預設: 100)')
parser.add_argument('--timedelta', type=int, default=120, help='每次模擬時間增量秒數 (預設: 120)')
parser.add_argument('--start-time', type=str, default='2026-01-22 13:00:00', help='模擬起始時間 (格式: YYYY-MM-DD HH:MM:SS, 預設: 2026-01-22 13:00:00)')
args = parser.parse_args()

# 解析起始時間
SIMULATE_START = datetime.strptime(args.start_time, '%Y-%m-%d %H:%M:%S')

print(f"Simulation start time: {SIMULATE_START}, Iterations: {args.iterations}, Time delta: {args.timedelta} seconds", flush=True)

# 資料庫連線設定
db_config = {
    'host': os.getenv('MYSQL_HOST'),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE')
}

def load_lot_operations():
    """載入 LotOperations 資料"""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT LotId, Step, PlanCheckInTime, PlanCheckOutTime, StepStatus, CheckInTime, CheckOutTime
            FROM LotOperations
            WHERE PlanCheckInTime IS NOT NULL AND PlanCheckOutTime IS NOT NULL
            ORDER BY LotId, Step
        """)

        operations = cursor.fetchall()
        cursor.close()
        conn.close()

        print(f"Loaded {len(operations)} operation steps", flush=True)
        return operations

    except mysql.connector.Error as err:
        print(f"Database error: {err}", flush=True)
        return []
    except Exception as e:
        print(f"Error: {e}", flush=True)
        return []

def update_operation_status(operation, checkin_time=None, checkout_time=None, step_status=None):
    """更新作業狀態"""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        lot_id = operation['LotId']
        step = operation['Step']

        # 建構動態更新語句
        updates = []
        params = []

        if checkin_time is not None:
            updates.append("CheckInTime = %s")
            params.append(checkin_time)
        if checkout_time is not None:
            updates.append("CheckOutTime = %s")
            params.append(checkout_time)
        if step_status is not None:
            updates.append("StepStatus = %s")
            params.append(step_status)

        if updates:
            query = f"UPDATE LotOperations SET {', '.join(updates)} WHERE LotId = %s AND Step = %s"
            params.extend([lot_id, step])
            cursor.execute(query, params)
            conn.commit()

            # 同步更新本地 operation 物件
            if checkin_time is not None:
                operation['CheckInTime'] = checkin_time
            if checkout_time is not None:
                operation['CheckOutTime'] = checkout_time
            if step_status is not None:
                operation['StepStatus'] = step_status

            cursor.close()
            conn.close()
            return True
        else:
            cursor.close()
            conn.close()
            return False

    except mysql.connector.Error as err:
        print(f"Update error: {err}", flush=True)
        return False
    except Exception as e:
        print(f"Update error: {e}", flush=True)
        return False

# 載入作業資料
operations = load_lot_operations()

if not operations:
    print("Failed to load operation data", flush=True)
    exit(1)

# 模擬開始
simulation_time = SIMULATE_START
for i in range(args.iterations):
    print(f"\nSimulation time: {simulation_time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    # 檢查每個作業步驟
    for op in operations:
        lot_id = op['LotId']
        step = op['Step']
        plan_checkin = op['PlanCheckInTime']
        plan_checkout = op['PlanCheckOutTime']
        current_status = op['StepStatus']

        # 條件 1: 若 StepStatus = 0，且 simulation_time >= PlanCheckInTime
        if current_status == 0 and plan_checkin and simulation_time >= plan_checkin:
            if update_operation_status(op, checkin_time=simulation_time, step_status=1):
                print(f"  {lot_id} {step}: CheckIn - {simulation_time.strftime('%H:%M:%S')}", flush=True)

        # 條件 2: 若 StepStatus = 1，且 simulation_time >= PlanCheckOutTime 且 CheckInTime 不為null
        elif current_status == 1 and plan_checkout and simulation_time >= plan_checkout and op['CheckInTime'] is not None:
            if update_operation_status(op, checkout_time=simulation_time, step_status=2):
                print(f"  {lot_id} {step}: CheckOut - {simulation_time.strftime('%H:%M:%S')}", flush=True)

    simulation_time += timedelta(seconds=args.timedelta)
    time.sleep(0.1)  # 模擬延遲，方便觀察輸出


print("\nSimulation completed", flush=True)