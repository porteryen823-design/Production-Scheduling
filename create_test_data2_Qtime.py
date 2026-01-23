import json
import os
import random
from datetime import datetime, timedelta

def create_test_data():
    # 建立目錄
    os.makedirs(r"C:\Data\APS\lot_Plan", exist_ok=True)
    os.makedirs(r"C:\Data\APS\MachineUsage", exist_ok=True)
    os.makedirs(r"C:\Data\APS\Lot_Plan_result", exist_ok=True)
    os.makedirs(r"C:\Data\APS\ScheduleLog", exist_ok=True)

    # 定義產品的 Operations 模板
    prod_a_operations = [
        {"Step": "STEP1", "StepIdx": 1, "MachineGroup": "M01", "DurationMinutes": 60*4},
        {"Step": "STEP2", "StepIdx": 2, "MachineGroup": "M02", "DurationMinutes": 60*2},
        {"Step": "STEP3", "StepIdx": 3, "MachineGroup": "M03", "DurationMinutes": 60*5},
        {"Step": "STEP4", "StepIdx": 4, "MachineGroup": "M04", "DurationMinutes": 60*3},
        {"Step": "STEP5", "StepIdx": 5, "MachineGroup": "M05", "DurationMinutes": 60*6}
    ]

    prod_b_operations = [
        {"Step": "STEP1", "StepIdx": 1, "MachineGroup": "M01", "DurationMinutes": 60*4},
        {"Step": "STEP2", "StepIdx": 2, "MachineGroup": "M02", "DurationMinutes": 60*2},
        {"Step": "STEP3", "StepIdx": 3, "MachineGroup": "M03", "DurationMinutes": 60*5},
        {"Step": "STEP4", "StepIdx": 4, "MachineGroup": "M04", "DurationMinutes": 60*3},
        {"Step": "STEP5", "StepIdx": 5, "MachineGroup": "M05", "DurationMinutes": 60*6}
    ]

    prod_c_operations = [
        {"Step": "STEP1", "StepIdx": 1, "MachineGroup": "M01", "DurationMinutes": 60*4},
        {"Step": "STEP2", "StepIdx": 2, "MachineGroup": "M02", "DurationMinutes": 60*2},
        {"Step": "STEP3", "StepIdx": 3, "MachineGroup": "M03", "DurationMinutes": 60*5},
        {"Step": "STEP4", "StepIdx": 4, "MachineGroup": "M04", "DurationMinutes": 60*3},
        {"Step": "STEP5", "StepIdx": 5, "MachineGroup": "M05", "DurationMinutes": 60*6}
    ]

    # 定義 Priority 範圍
    priorities_a = [100, 130, 150, 180, 200, 220]
    priorities_b = [50, 60, 70, 80, 90]
    priorities_c = [50, 60, 70, 80, 90, 100, 110, 120, 130, 140]

    # 當前日期作為基準
    today = datetime.now()

    lots = []

    # 生成 LOT_A001 到 LOT_A030
    for i in range(1, 2):
        lot_id = f"LOT_A{i:03d}"
        priority = priorities_a[(i-1) % len(priorities_a)]
        lots.append({
            "LotId": lot_id,
            "Product": "PROD_A",
            "Priority": priority,
            "DueDate": (today + timedelta(days=random.uniform(0.5, 10.0))).isoformat(),
            "Operations": prod_a_operations.copy()
        })

    # 生成 LOT_B001 到 LOT_B020
    for i in range(1, 2):
        lot_id = f"LOT_B{i:03d}"
        priority = priorities_b[(i-1) % len(priorities_b)]
        lots.append({
            "LotId": lot_id,
            "Product": "PROD_B",
            "Priority": priority,
            "DueDate": (today + timedelta(days=random.uniform(0.5, 10.0))).isoformat(),
            "Operations": prod_b_operations.copy()
        })

    # 生成 LOT_C001 到 LOT_C100
    for i in range(1, 2):
        lot_id = f"LOT_C{i:03d}"
        priority = priorities_c[(i-1) % len(priorities_c)]
        lots.append({
            "LotId": lot_id,
            "Product": "PROD_C",
            "Priority": priority,
            "DueDate": (today + timedelta(days=random.uniform(0.5, 10.0))).isoformat(),
            "Operations": prod_c_operations.copy()
        })

    # 寫入檔案
    with open(r"C:\Data\APS\lot_Plan\lot_Plan.json", 'w', encoding='utf-8') as f:
        json.dump(lots, f, indent=4)

    print("測試資料建立完成。")

if __name__ == "__main__":
    create_test_data()