from ortools.sat.python import cp_model
from datetime import datetime, timedelta


# =====================================================
# Windows Unicode Output Encoding Fix
# =====================================================
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


SCHEDULE_START = datetime(2026, 1, 18, 13, 0, 0)

# 目標函數類型: "makespan" 或 "weighted_delay"
OBJECTIVE_TYPE = "weighted_delay"

# === Job 資料 ===
jobs_data = [
    {
        "LotId": "LOT_A001",
        "Priority": 100,
        "DueDate": "2026-01-20T18:38:48.970904",
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
    },
     {
        "LotId": "LOT_D001",
        "Priority": 100,
        "DueDate": "2026-01-20T18:38:48.970904",
        "Operations": [
            ("STEP1", "M01", 240),
            ("STEP2", "M02", 120),
            ("STEP3", "M03", 300),
            ("STEP4", "M04", 280),
            ("STEP5", "M05", 360),
        ],
    },
     {
        "LotId": "LOT_E001",
        "Priority": 100,
        "DueDate": "2026-01-20T18:38:48.970904",
        "Operations": [
            ("STEP1", "M01", 240),
            ("STEP2", "M02", 120),
            ("STEP3", "M03", 300),
            ("STEP4", "M04", 280),
            ("STEP5", "M05", 360),
        ],
    },
     {
        "LotId": "LOT_F001",
        "Priority": 100,
        "DueDate": "2026-01-20T18:38:48.970904",
        "Operations": [
            ("STEP1", "M01", 240),
            ("STEP2", "M02", 120),
            ("STEP3", "M03", 300),
            ("STEP4", "M04", 280),
            ("STEP5", "M05", 360),
        ],
    },
     {
        "LotId": "LOT_G001",
        "Priority": 100,
        "DueDate": "2026-01-20T18:38:48.970904",
        "Operations": [
            ("STEP1", "M01", 240),
            ("STEP2", "M02", 120),
            ("STEP3", "M03", 300),
            ("STEP4", "M04", 280),
            ("STEP5", "M05", 360),
        ],
    },
    {
        "LotId": "LOT_B001",
        "Priority": 50,
        "DueDate": "2026-01-19T11:46:01.205277",
        "Operations": [
            ("STEP1", "M01", 240),
            ("STEP2", "M02", 120),
            ("STEP3", "M03", 300),
            ("STEP4", "M04", 180),
            ("STEP5", "M05", 360),
        ],
    },
    {
        "LotId": "LOT_C001",
        "Priority": 50,
        "DueDate": "2026-01-19T08:39:49.243869",
        "Operations": [
            ("STEP1", "M01", 240),
            ("STEP2", "M02", 120),
            ("STEP3", "M03", 230),
            ("STEP4", "M04", 180),
            ("STEP5", "M05", 360),
        ],
    },
]

MACHINE_GROUPS = {
    "M01": ["M01-1", "M01-2", "M01-3"],
    "M02": ["M02-1", "M02-2"],
    "M03": ["M03-1", "M03-2", "M03-3"],
    "M04": ["M04-1", "M04-2", "M04-3"],
    "M05": ["M05-1", "M05-2"],
    "M06": ["M06-1", "M06-2"],
    "M07": ["M07-1", "M07-2"],
    "M08": ["M08-1", "M08-2", "M08-3", "M08-4"],
    "M09": ["M09-1", "M09-2", "M09-3", "M09-4"],
    "M10": ["M10-1", "M10-2", "M10-3", "M10-4"],
    "M11": ["M11-1", "M11-2", "M11-3", "M11-4"],
    "M12": ["M12-1", "M12-2", "M12-3", "M12-4"],
    "M13": ["M13-1", "M13-2", "M13-3", "M13-4"],
    "M14": ["M14-1", "M14-2", "M14-3", "M14-4"],
    "M15": ["M15-1", "M15-2", "M15-3", "M15-4"],
    "M16": ["M16-1", "M16-2", "M16-3", "M16-4"],
}

# === 初始化 OR-Tools 模型 ===
model = cp_model.CpModel()

# 定義機台
machines = {}
for group, sublist in MACHINE_GROUPS.items():
    for sub in sublist:
        machines[sub] = []

# === 建立變數 ===
all_tasks = {}
horizon = sum(op[2] for job in jobs_data for op in job["Operations"])  # 最大時間範圍

for job in jobs_data:
    lot_id = job["LotId"]
    for step_idx, (step, machine_group, duration) in enumerate(job["Operations"]):
        submachines = MACHINE_GROUPS[machine_group]
        num_machines = len(submachines)
        machine_choice = model.NewIntVar(0, num_machines - 1, f"{lot_id}_{step}_machine")
        
        start_var = model.NewIntVar(0, horizon, f"{lot_id}_{step}_start")
        end_var = model.NewIntVar(0, horizon, f"{lot_id}_{step}_end")
        
        intervals = []
        is_present_vars = []
        for i, submachine in enumerate(submachines):
            is_present = model.NewBoolVar(f"{lot_id}_{step}_is_present_{i}")
            is_present_vars.append(is_present)
            interval_var = model.NewOptionalIntervalVar(start_var, duration, end_var, is_present, f"{lot_id}_{step}_interval_{i}")
            intervals.append(interval_var)
            machines[submachine].append(interval_var)
            
            # 約束：如果選擇 i，則 is_present 為 True
            model.Add(machine_choice == i).OnlyEnforceIf(is_present)
            model.Add(machine_choice != i).OnlyEnforceIf(is_present.Not())
        
        # 確保選擇一個機台
        model.Add(sum(is_present_vars) == 1)
        
        all_tasks[(lot_id, step)] = (start_var, end_var, intervals, machine_choice, machine_group, duration, is_present_vars)

# === 加入約束條件 ===
for job in jobs_data:
    lot_id = job["LotId"]
    ops = job["Operations"]

    # 工單內部步驟必須依序
    for i in range(len(ops) - 1):
        step1 = ops[i][0]
        step2 = ops[i + 1][0]
        model.Add(all_tasks[(lot_id, step1)][1] <= all_tasks[(lot_id, step2)][0])

    # Q-time 約束: STEP3 完工 → STEP4 開始 ≤ 400 分鐘 
    step3_end = all_tasks[(lot_id, "STEP3")][1]
    step4_start = all_tasks[(lot_id, "STEP4")][0]
    model.Add(step4_start - step3_end <= 200)
  

# === 機台不可重疊 ===
for machine, intervals in machines.items():
    model.AddNoOverlap(intervals)

# === 延遲變數 (如果需要 weighted_delay) ===
delay_vars = []
if OBJECTIVE_TYPE == "weighted_delay":
    for job in jobs_data:
        lot_id = job["LotId"]
        due_date = datetime.fromisoformat(job["DueDate"])
        due_date_minutes = int((due_date - SCHEDULE_START).total_seconds() / 60)
        completion_var = all_tasks[(lot_id, "STEP5")][1]
        delay_var = model.NewIntVar(0, horizon, f"{lot_id}_delay")
        model.Add(delay_var >= completion_var - due_date_minutes)
        model.Add(delay_var >= 0)
        delay_vars.append(delay_var)

# === 目標函數 ===
if OBJECTIVE_TYPE == "makespan":
    # 最小化 makespan
    obj_var = model.NewIntVar(0, horizon, "makespan")
    model.AddMaxEquality(obj_var, [all_tasks[(job["LotId"], "STEP5")][1] for job in jobs_data])
    model.Minimize(obj_var)
    print("目標函數: 最小化 makespan")
elif OBJECTIVE_TYPE == "weighted_delay":
    # 最小化加權延遲總和
    obj_var = model.NewIntVar(0, 1000000, "weighted_delay")
    weighted_delays = [delay * job["Priority"] for delay, job in zip(delay_vars, jobs_data)]
    model.Add(obj_var == sum(weighted_delays))
    model.Minimize(obj_var)
    print("目標函數: 最小化加權延遲總和")

# === 求解 ===
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
status = solver.Solve(model)

# === 輸出結果 ===
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    print("=== Job Shop Scheduling 結果 ===")
    print(f"求解狀態: {solver.StatusName(status)}")
    for job in jobs_data:
        lot_id = job["LotId"]
        print(f"\n工單 {lot_id}:")
        for step, machine_group, duration in job["Operations"]:
            start = solver.Value(all_tasks[(lot_id, step)][0])
            end = solver.Value(all_tasks[(lot_id, step)][1])
            machine_idx = solver.Value(all_tasks[(lot_id, step)][3])
            selected_machine = MACHINE_GROUPS[machine_group][machine_idx]
            start_time = SCHEDULE_START + timedelta(minutes=start)
            end_time = SCHEDULE_START + timedelta(minutes=end)
            print(f"  {step} ({selected_machine}) : 開始 {start_time.strftime('%Y-%m-%d %H:%M:%S')}, 結束 {end_time.strftime('%Y-%m-%d %H:%M:%S')}, 工時 {duration} 分鐘")

    # Summary: 檢查每批完工時間與 DueDate 的比較
    print("\n=== Summary: 完工時間 vs DueDate ===")
    for job in jobs_data:
        lot_id = job["LotId"]
        due_date_str = job["DueDate"]
        due_date = datetime.fromisoformat(due_date_str)
        completion_minutes = solver.Value(all_tasks[(lot_id, "STEP5")][1])
        completion_time = SCHEDULE_START + timedelta(minutes=completion_minutes)

        if completion_time <= due_date:
            days_ahead = (due_date - completion_time).total_seconds() / (3600 * 24)
            print(f"工單 {lot_id}: 實際完成 {completion_time.strftime('%Y-%m-%d %H:%M:%S')}, DueDate {due_date.strftime('%Y-%m-%d %H:%M:%S')}, 超前完成 {days_ahead:.1f} 天")
        else:
            days_delay = (completion_time - due_date).total_seconds() / (3600 * 24)
            print(f"工單 {lot_id}: 實際完成 {completion_time.strftime('%Y-%m-%d %H:%M:%S')}, DueDate {due_date.strftime('%Y-%m-%d %H:%M:%S')}, 延遲 {days_delay:.1f} 天")

    # 總 makespan
    makespan_minutes = max(solver.Value(all_tasks[(job["LotId"], "STEP5")][1]) for job in jobs_data)
    makespan_time = SCHEDULE_START + timedelta(minutes=makespan_minutes)
    print(f"\n總 makespan: {makespan_time.strftime('%Y-%m-%d %H:%M:%S')} ({makespan_minutes} 分鐘)")
else:
    print("無可行解")