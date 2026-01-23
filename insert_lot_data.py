import mysql.connector
import os
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv

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

def calculate_due_date():
    """計算 DueDate：目前日期 + 3天，時間到小時"""
    now = datetime.now()
    due_date = now + timedelta(days=3)
    # 時間到小時，格式為 ISO 格式但時間只到小時
    return due_date.strftime("%Y-%m-%dT%H:00:00.0")

def insert_lot_data():
    """插入 Lot 資料到資料庫"""
    try:
        # 連接到資料庫
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # 取得下一個 LotId
        next_lot_id = get_next_lot_id(cursor)
        print(f"Next LotId: {next_lot_id}")

        # 計算 DueDate
        due_date = calculate_due_date()
        print(f"DueDate: {due_date}")

        # 插入 Lots 表
        cursor.execute("""
            INSERT INTO Lots (LotId, Priority, DueDate, ActualFinishDate, ProductID, ProductName, CustomerID, CustomerName, LotCreateDate)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (next_lot_id, lot_template["Priority"], due_date, None, f"PROD_{next_lot_id.split('_')[1]}", f"Product {next_lot_id.split('_')[1]}", f"CUST_{next_lot_id.split('_')[1]}", f"Customer {next_lot_id.split('_')[1]}", datetime.now()))

        # 插入 LotOperations 表
        for sequence, (step, machine_group, duration) in enumerate(lot_template["Operations"], 1):
            cursor.execute("""
                INSERT INTO LotOperations (LotId, Step, MachineGroup, Duration, Sequence, CheckInTime, CheckOutTime, StepStatus, PlanCheckInTime, PlanCheckOutTime, PlanMachineId, PlanHistory)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (next_lot_id, step, machine_group, duration, sequence, None, None, 0, None, None, None, None))

        # 提交交易
        conn.commit()

        print(f"Successfully inserted Lot: {next_lot_id}")
        print(f"Inserted {len(lot_template['Operations'])} operation steps")

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
    for i in range(args.count):
        print(f"\nInserting Lot data #{i+1}:")
        insert_lot_data()
    print(f"\nTotal inserted {args.count} Lot data")