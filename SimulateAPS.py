import mysql.connector
import os
import time
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv

# =====================================================
# Windows Unicode Output Encoding Fix
# =====================================================
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# 載入環境變數
load_dotenv()

# Parameter Parsing
parser = argparse.ArgumentParser(description='APS Simulation Program')
parser.add_argument('--iterations', type=int, default=100, help='Number of iterations (default: 100)')
parser.add_argument('--timedelta', type=int, default=120, help='Time delta per iteration in seconds (default: 120)')
parser.add_argument('--start-time', type=str, default='2026-01-22 13:00:00', help='Simulation start time (format: YYYY-MM-DD HH:MM:SS, default: 2026-01-22 13:00:00)')
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

def load_simulation_settings():
    """從資料庫載入模擬設定"""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT parameter_name, parameter_value FROM ui_settings WHERE parameter_name IN ('spin_iterations', 'spin_timedelta')")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # 將結果轉換為字典
        settings = {row['parameter_name']: row['parameter_value'] for row in rows}
        return settings
    except Exception as e:
        print(f"Warning: Could not load settings from database: {e}", flush=True)
        return None

# 嘗試從資料庫載入設定
db_settings = load_simulation_settings()
iterations = args.iterations
time_delta = args.timedelta

if db_settings:
    try:
        if 'spin_iterations' in db_settings:
            iterations = int(db_settings['spin_iterations'])
        if 'spin_timedelta' in db_settings:
            time_delta = int(db_settings['spin_timedelta'])
        print(f"Loaded settings from database: Iterations={iterations}, TimeDelta={time_delta}", flush=True)
    except (ValueError, TypeError):
        print(f"Warning: Settings in database are not valid numbers, using defaults.", flush=True)
else:
    print(f"Using command line/default settings: Iterations={iterations}, TimeDelta={time_delta}", flush=True)

def load_lot_operations():
    """載入 LotOperations 資料"""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT lo.LotId, lo.Step, lo.PlanCheckInTime, lo.PlanCheckOutTime, lo.StepStatus, lo.CheckInTime, lo.CheckOutTime, lo.Sequence,
                   (SELECT MAX(Sequence) FROM LotOperations WHERE LotId = lo.LotId) as MaxSequence
            FROM LotOperations lo
            WHERE lo.PlanCheckInTime IS NOT NULL AND lo.PlanCheckOutTime IS NOT NULL
            ORDER BY lo.LotId, lo.Sequence
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

def update_operation_status(operation, checkin_time=None, checkout_time=None, step_status=None, is_last_step=False):
    """更新作業狀態，若為最後一步則同步更新 Lots 表的 ActualFinishDate"""
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
            
            # 若是最後一步且正在 CheckOut，則更新 Lots 表的 ActualFinishDate
            if checkout_time is not None and is_last_step:
                cursor.execute("UPDATE Lots SET ActualFinishDate = %s WHERE LotId = %s", (checkout_time, lot_id))
                print(f"  -> Lot {lot_id} is completed. ActualFinishDate updated.", flush=True)

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
for i in range(iterations):
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
            is_last = (op['Sequence'] == op['MaxSequence'])
            if update_operation_status(op, checkout_time=simulation_time, step_status=2, is_last_step=is_last):
                print(f"  {lot_id} {step}: CheckOut - {simulation_time.strftime('%H:%M:%S')}", flush=True)

    simulation_time += timedelta(seconds=time_delta)
    time.sleep(0.02)  # 模擬延遲，方便觀察輸出





print("\nSimulation completed", flush=True)

# 更新 ui_settings 資料表 (simulation_start_time 和 simulation_end_time)
try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    # 計算最後模擬的時間點
    final_time = simulation_time - timedelta(seconds=time_delta)
    
    # 將時間轉換為字串格式
    start_time_str = SIMULATE_START.strftime('%Y-%m-%d %H:%M:%S')
    end_time_str = final_time.strftime('%Y-%m-%d %H:%M:%S')
    
    # 使用 UPSERT (INSERT ... ON DUPLICATE KEY UPDATE) 更新 simulation_start_time
    query_start = """
        INSERT INTO ui_settings (parameter_name, parameter_value, remark)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE parameter_value = VALUES(parameter_value), updated_at = NOW()
    """
    cursor.execute(query_start, ('simulation_start_time', start_time_str, '模擬起始時間'))
    print(f"Updated ui_settings: simulation_start_time = {start_time_str}", flush=True)
    
    # 使用 UPSERT 更新 simulation_end_time
    query_end = """
        INSERT INTO ui_settings (parameter_name, parameter_value, remark)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE parameter_value = VALUES(parameter_value), updated_at = NOW()
    """
    cursor.execute(query_end, ('simulation_end_time', end_time_str, '模擬結束時間'))
    print(f"Updated ui_settings: simulation_end_time = {end_time_str}", flush=True)
    
    conn.commit()
    cursor.close()
    conn.close()
except mysql.connector.Error as err:
    print(f"Database error during ui_settings update: {err}", flush=True)
except Exception as e:
    print(f"Error during ui_settings update: {e}", flush=True)