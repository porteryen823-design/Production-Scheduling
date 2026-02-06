import mysql.connector
import os
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv
import random
import warnings

# 隱藏特定版本的 MySQL Connector 廢棄警告
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*stored_results.*")

# 載入環境變數
load_dotenv()

# 參數解析
parser = argparse.ArgumentParser(description='Insert Lot data into database')
parser.add_argument('--count', type=int, default=1, help='Number of Lots to insert (default: 1)')
args = parser.parse_args()

# 資料庫連線設定
db_config = {
    'host': os.getenv('MYSQL_HOST'),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE')
}

# Lot 資料範本
lot_template = {
    "Priority": 100,
    "Operations": [
        ("STEP1", "M01", 240),
        ("STEP2", "M02", 120),
        ("STEP3", "M03", 300),
        ("STEP4", "M04", 280),
        ("STEP5", "M05", 360),
        ("STEP6", "M06", 200),
        ("STEP7", "M07", 180),
        ("STEP8", "M08", 160),
        ("STEP9", "M09", 140),
        ("STEP10", "M10", 120),
        ("STEP11", "M11", 100),
        ("STEP12", "M12", 80),
        ("STEP13", "M13", 160),
        ("STEP14", "M14", 140),
        ("STEP15", "M15", 120),
    ],
}

def get_next_lot_id(cursor):
    """取得下一個 LotId"""
    cursor.execute("SELECT LotId FROM Lots ORDER BY LotId DESC LIMIT 1")
    result = cursor.fetchone()

    if result:
        # 解析現有的 LotId，例如 "LOT_0001" -> 1
        current_id = int(result[0].split('_')[1])
        next_id = current_id + 1
    else:
        # 如果沒有資料，從 1 開始
        next_id = 1

    # 格式化為四碼流水碼
    return f"LOT_{next_id:04d}"

def calculate_due_date(cursor):
    """計算 DueDate：
    若 insert_lot_data_use_simulation_end_time = 'True'，DueDate = simulation_end_time + 3天
    否則 DueDate = 目前日期 + 3天，時間到小時
    """
    use_sim_end = False
    sim_end_time = None

    try:
        # 讀取相關設定
        cursor.execute("SELECT parameter_name, parameter_value FROM ui_settings WHERE parameter_name IN ('insert_lot_data_use_simulation_end_time', 'simulation_end_time')")
        settings = {row[0]: row[1] for row in cursor.fetchall()}
        
        if settings.get('insert_lot_data_use_simulation_end_time') == 'True':
            use_sim_end = True
            if settings.get('simulation_end_time'):
                sim_end_time = datetime.strptime(settings['simulation_end_time'], '%Y-%m-%d %H:%M:%S')
    except Exception as e:
        print(f"Warning: Could not read ui_settings for DueDate calculation: {e}")

    if use_sim_end and sim_end_time:
        base_date = sim_end_time
        print(f"Using simulation_end_time as base: {base_date}")
    else:
        base_date = datetime.now()
        print(f"Using current time as base: {base_date}")

    due_date = base_date + timedelta(days=3)
    # 格式化為 ISO 格式但時間只到小時
    return due_date.strftime("%Y-%m-%dT%H:00:00.0")

def insert_lot_data(count):
    """插入 Lot 資料到資料庫"""
    try:
        # 連接到資料庫
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # 讀取 use_sp_for_lot_insert 設定
        cursor.execute("SELECT parameter_value FROM ui_settings WHERE parameter_name = 'use_sp_for_lot_insert'")
        result = cursor.fetchone()
        use_sp = result[0] == 'True' if result else False

        # 讀取 insert_lot_data_use_simulation_end_time 設定 (SP 也需要)
        cursor.execute("SELECT parameter_value FROM ui_settings WHERE parameter_name = 'insert_lot_data_use_simulation_end_time'")
        result = cursor.fetchone()
        use_sim_end = result[0] == 'True' if result else False

        if use_sp:
            print(f"Using Stored Procedure 'sp_InsertLot' to insert {count} records...")
            # SP parameters: p_Count, p_Priority, p_UseSimEndTime
            cursor.callproc('sp_InsertLot', (count, lot_template["Priority"], use_sim_end))
            
            # Get LotId returned from SP
            for result in cursor.stored_results():
                rows = result.fetchall()
                for row in rows:
                    print(f"Successfully inserted Lot: {row[0]} (via SP)")
        else:
            for i in range(count):
                print(f"\nInserting Lot record #{i+1} (manual):")
                # Get next LotId
                next_lot_id = get_next_lot_id(cursor)
                print(f"Next LotId: {next_lot_id}")

                # Calculate DueDate
                due_date = calculate_due_date(cursor)
                print(f"DueDate: {due_date}")

                # 插入 Lots 表
                cursor.execute("""
                    INSERT INTO Lots (LotId, Priority, DueDate, ActualFinishDate, ProductID, ProductName, CustomerID, CustomerName, LotCreateDate)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (next_lot_id, lot_template["Priority"], due_date, None, f"PROD_{next_lot_id.split('_')[1]}", f"Product {next_lot_id.split('_')[1]}", f"CUST_{next_lot_id.split('_')[1]}", f"Customer {next_lot_id.split('_')[1]}", datetime.now()))

                # 決定隨機作業數量 (9-15)
                num_ops = random.randint(9, 15)
                lot_ops = lot_template["Operations"][:num_ops]
                print(f"Generating {num_ops} operations for this Lot")

                # 插入 LotOperations 表
                for sequence, (step, machine_group, duration) in enumerate(lot_ops, 1):
                    cursor.execute("""
                        INSERT INTO LotOperations (LotId, Step, MachineGroup, Duration, Sequence, CheckInTime, CheckOutTime, StepStatus, PlanCheckInTime, PlanCheckOutTime, PlanMachineId, PlanHistory)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (next_lot_id, step, machine_group, duration, sequence, None, None, 0, None, None, None, None))

                print(f"Successfully inserted Lot: {next_lot_id}")

        # Commit transaction
        conn.commit()
        print(f"\nTotal inserted {count} Lot records")

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        if 'conn' in locals():
            conn.rollback()
    except Exception as e:
        print(f"Error: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    insert_lot_data(args.count)