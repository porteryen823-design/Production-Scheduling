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

    # 1. 建立 lot_Plan.json
    # 當前日期作為基準
    today = datetime.now()

    lots = [
        {
            "LotId": "LOT_A001",
            "Product": "PROD_A",
            "Priority": 130,
            "DueDate": (today + timedelta(days=random.uniform(0.5, 10.0))).isoformat(),
            "Operations": [
                {"Step": "STEP1", "StepIdx": 1, "MachineGroup": "M01", "DurationMinutes": 60*4},
                {"Step": "STEP2", "StepIdx": 2, "MachineGroup": "M02", "DurationMinutes": 60*8},
                {"Step": "STEP3", "StepIdx": 3, "MachineGroup": "M03", "DurationMinutes": 60*5},
                {"Step": "STEP4", "StepIdx": 4, "MachineGroup": "M04", "DurationMinutes": 60*3},
                {"Step": "STEP5", "StepIdx": 5, "MachineGroup": "M05", "DurationMinutes": 60*6},
                {"Step": "STEP6", "StepIdx": 6, "MachineGroup": "M06", "DurationMinutes": 60*7},
                {"Step": "STEP7", "StepIdx": 7, "MachineGroup": "M07", "DurationMinutes": 60*8}
            ]
        },
        {
            "LotId": "LOT_A002",
            "Product": "PROD_A",
            "Priority": 220,
            "DueDate": (today + timedelta(days=random.uniform(0.5, 10.0))).isoformat(),
            "Operations": [
                {"Step": "STEP1", "StepIdx": 1, "MachineGroup": "M01", "DurationMinutes": 60*4},
                {"Step": "STEP2", "StepIdx": 2, "MachineGroup": "M02", "DurationMinutes": 60*8},
                {"Step": "STEP3", "StepIdx": 3, "MachineGroup": "M03", "DurationMinutes": 60*5},
                {"Step": "STEP4", "StepIdx": 4, "MachineGroup": "M04", "DurationMinutes": 60*3},
                {"Step": "STEP5", "StepIdx": 5, "MachineGroup": "M05", "DurationMinutes": 60*6},
                {"Step": "STEP6", "StepIdx": 6, "MachineGroup": "M06", "DurationMinutes": 60*7},
                {"Step": "STEP7", "StepIdx": 7, "MachineGroup": "M07", "DurationMinutes": 60*3},
            ]
        },
        {
            "LotId": "LOT_A003",
            "Product": "PROD_A",
            "Priority": 220,
            "DueDate": (today + timedelta(days=random.uniform(0.5, 10.0))).isoformat(),
            "Operations": [
                 {"Step": "STEP1", "StepIdx": 1, "MachineGroup": "M01", "DurationMinutes": 60*4},
                {"Step": "STEP2", "StepIdx": 2, "MachineGroup": "M02", "DurationMinutes": 60*8},
                {"Step": "STEP3", "StepIdx": 3, "MachineGroup": "M03", "DurationMinutes": 60*5},
                {"Step": "STEP4", "StepIdx": 4, "MachineGroup": "M04", "DurationMinutes": 60*3},
                {"Step": "STEP5", "StepIdx": 5, "MachineGroup": "M05", "DurationMinutes": 60*6},
                {"Step": "STEP6", "StepIdx": 6, "MachineGroup": "M06", "DurationMinutes": 60*7},
                {"Step": "STEP7", "StepIdx": 7, "MachineGroup": "M07", "DurationMinutes": 60*3},
            ]
        },
        {
            "LotId": "LOT_A004",
            "Product": "PROD_A",
            "Priority": 100,
            "DueDate": (today + timedelta(days=random.uniform(0.5, 10.0))).isoformat(),
            "Operations": [
                {"Step": "STEP1", "StepIdx": 1, "MachineGroup": "M01", "DurationMinutes": 60*4},
                {"Step": "STEP2", "StepIdx": 2, "MachineGroup": "M02", "DurationMinutes": 60*8},
                {"Step": "STEP3", "StepIdx": 3, "MachineGroup": "M03", "DurationMinutes": 60*5},
                {"Step": "STEP4", "StepIdx": 4, "MachineGroup": "M04", "DurationMinutes": 60*3},
                {"Step": "STEP5", "StepIdx": 5, "MachineGroup": "M05", "DurationMinutes": 60*6},
                {"Step": "STEP6", "StepIdx": 6, "MachineGroup": "M06", "DurationMinutes": 60*7},
                {"Step": "STEP7", "StepIdx": 7, "MachineGroup": "M07", "DurationMinutes": 60*3},
            ]
        },
        {
            "LotId": "LOT_B001",
            "Product": "PROD_B",
            "Priority": 50,
            "DueDate": (today + timedelta(days=random.uniform(0.5, 10.0))).isoformat(),
            "Operations": [
                {"Step": "STEP1", "StepIdx": 1, "MachineGroup": "M01", "DurationMinutes": 60*4},
                {"Step": "STEP2", "StepIdx": 2, "MachineGroup": "M02", "DurationMinutes": 60*8},
                {"Step": "STEP3", "StepIdx": 3, "MachineGroup": "M03", "DurationMinutes": 60*5},
                {"Step": "STEP4", "StepIdx": 4, "MachineGroup": "M04", "DurationMinutes": 60*3},
                {"Step": "STEP5", "StepIdx": 5, "MachineGroup": "M05", "DurationMinutes": 60*6},
                {"Step": "STEP6", "StepIdx": 6, "MachineGroup": "M06", "DurationMinutes": 60*7},
                {"Step": "STEP7", "StepIdx": 7, "MachineGroup": "M07", "DurationMinutes": 60*3},
            ]
        },
        {
            "LotId": "LOT_B002",
            "Product": "PROD_B",
            "Priority": 50,
            "DueDate": (today + timedelta(days=random.uniform(0.5, 10.0))).isoformat(),
            "Operations": [
                {"Step": "STEP1", "StepIdx": 1, "MachineGroup": "M01", "DurationMinutes": 90},
                {"Step": "STEP2", "StepIdx": 2, "MachineGroup": "M02", "DurationMinutes": 60},
                 {"Step": "STEP3", "StepIdx": 3, "MachineGroup": "M03", "DurationMinutes": 60*5},
                {"Step": "STEP4", "StepIdx": 4, "MachineGroup": "M04", "DurationMinutes": 60*3},
            ]
        }
    ]
    with open(r"C:\Data\APS\lot_Plan\lot_Plan.json", 'w', encoding='utf-8') as f:
        json.dump(lots, f, indent=4)



    print("測試資料建立完成。")

if __name__ == "__main__":
    create_test_data()
