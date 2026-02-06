#  在終端機執行 切換虛擬環境
#  192.168.0.124 mcsadmin/gis5613686
#  source myenv/bin/activate
#  lot x Step x Machine 的組合數目不要太多, 否則會跑很久
#  專門驗證 lot x 多Step, 若機台數目不多, 本程式驗證可以算很快 (100 lot x 15 Step x 3~6 Machine)
#  python Scheduler_Full_Example_Qtime_V2_Wip.py
from ortools.sat.python import cp_model
from datetime import datetime, timedelta
import time
import sys
import io
import os
import argparse


# =====================================================
# Windows Unicode Output Encoding Fix
# =====================================================
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')



# =====================================================
# 載入 .env 設定 (簡易 Parser)
# =====================================================
env_config = {}
if os.path.exists('.env'):
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key_val = line.split('=', 1)
                if len(key_val) == 2:
                    env_config[key_val[0].strip()] = key_val[1].strip()

# 取得配置參數
SOLVER_TIME_LIMIT = int(env_config.get('SOLVER_MAX_TIME_IN_SECONDS', 30))
SOLVER_WORKERS = int(env_config.get('SOLVER_NUM_SEARCH_WORKERS', 8))


parser = argparse.ArgumentParser(description='APS Scheduler V2')
parser.add_argument('--verbose', action='store_true', help='輸出詳細排程結果表格')
args = parser.parse_args()


# =====================================================
# 基本設定
# =====================================================
overall_start_time = time.perf_counter()
SCHEDULE_START = datetime(2026, 2, 1, 13, 0, 0)
OBJECTIVE_TYPE = "weighted_delay"   # "makespan" | "weighted_delay"


# =====================================================
# Job 資料生成
# =====================================================
# 定義 20 個步驟的範本
base_ops = [
    ("STEP1", "M01", 240),
    ("STEP2", "M02", 120),
    ("STEP3", "M03", 300),
    ("STEP4", "M04", 280),
    ("STEP5", "M05", 360),
    ("STEP6", "M06", 240), # 之後補齊
]

# 補齊到 STEP20
for i in range(7, 13):
    base_ops.append((f"STEP{i}", f"M{i:02d}", 360))

# 動態生成 100 個 Job
jobs_data = []
for i in range(1, 60):
    lot_id = f"LOT_{i:03d}"
    
    # 建立作業步驟（STEP1 ~ STEP15）
    # 這裡微調 duration 讓資料有多樣性
    current_ops = []
    for step_idx in range(1, 16):
        step_name = f"STEP{step_idx}"
        group_name = f"M{step_idx:02d}"
        # 基礎時間 + i (批次偏移) + step_idx (步驟偏移)
        duration = 200 + (i % 50) + (step_idx * 10)
        current_ops.append((step_name, group_name, duration))

    job = {
        "LotId": lot_id,
        "Priority": 100 if i == 1 else 50,
        "DueDate": (SCHEDULE_START + timedelta(days=10)).isoformat(), # 增加步驟後 DueDate 延後
        "Operations": current_ops,
    }
        
    jobs_data.append(job)


# =====================================================
# Machine Groups
# =====================================================
# 生成 M01 ~ M15 的機台群組
MACHINE_GROUPS = {}
for i in range(1, 16):
    group_name = f"M{i:02d}"
    # 每個群組 3~6 台設備
    num_machines = 3 + (i % 4)  # 產出比例：3, 4, 5, 6
    MACHINE_GROUPS[group_name] = [f"{group_name}-{j}" for j in range(1, num_machines + 1)]

# =====================================================
# OR-Tools Model
# =====================================================
model = cp_model.CpModel()


# 限制 horizon 避免溢位或效率降低，設定一個合理的上限 (例如 30 天)
horizon = max(sum(op[2] for op in job["Operations"]) for job in jobs_data) + 60*24* 60 # 多增加 60天


# machines[submachine] = [intervals...]
machines = {m: [] for g in MACHINE_GROUPS.values() for m in g}

# all_tasks[(lot, step)] = dict
all_tasks = {}

# =====================================================
# 建立 Task
# =====================================================
for job in jobs_data:
    lot = job["LotId"]
    for step, group, duration in job["Operations"]:
        submachines = MACHINE_GROUPS[group]

        # 狀態 4: 正常
        start_var = model.NewIntVar(0, horizon, f"{lot}_{step}_start")
        end_var = model.NewIntVar(0, horizon, f"{lot}_{step}_end")
        machine_choice = model.NewIntVar(0, len(submachines) - 1, f"{lot}_{step}_machine")
        intervals = []
        present = []
        for i, m in enumerate(submachines):
            p = model.NewBoolVar(f"{lot}_{step}_p_{i}")
            itv = model.NewOptionalIntervalVar(start_var, duration, end_var, p, f"{lot}_{step}_{m}")
            intervals.append(itv)
            present.append(p)
            machines[m].append(itv)
            model.Add(machine_choice == i).OnlyEnforceIf(p)
        model.Add(sum(present) == 1)
        all_tasks[(lot, step)] = {"start": start_var, "end": end_var, "machine_choice": machine_choice, "status": "Normal", "group": group}

# 工序順序
for job in jobs_data:
    lot = job["LotId"]
    ops = job["Operations"]
    for i in range(len(ops) - 1):
        s1 = ops[i][0]
        s2 = ops[i+1][0]
        model.Add(all_tasks[(lot, s1)]["end"] <= all_tasks[(lot, s2)]["start"])

# 機台不可重疊
for m, intervals in machines.items():
    if intervals:
        model.AddNoOverlap(intervals)

# Objective: Minimize delay
delay_vars = []
for job in jobs_data:
    lot = job["LotId"]
    due = datetime.fromisoformat(job["DueDate"])
    due_min = int((due - SCHEDULE_START).total_seconds() / 60)
    delay = model.NewIntVar(0, horizon, f"{lot}_delay")
    # 最後一步是 STEP15
    model.Add(delay >= all_tasks[(lot, "STEP15")]["end"] - due_min)
    model.Add(delay >= 0)
    delay_vars.append(delay * job["Priority"])
model.Minimize(sum(delay_vars))

# Solve
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = SOLVER_TIME_LIMIT 
solver.parameters.num_search_workers = SOLVER_WORKERS
start_solve_time = time.perf_counter()
status = solver.Solve(model)
end_solve_time = time.perf_counter()
solve_duration = end_solve_time - start_solve_time

# Output
print("============================================================")
print(f"Solver Status: {solver.StatusName(status)}")
print(f"Solve Duration: {solve_duration:.4f} seconds")
print(f"CPU Cores: {os.cpu_count()}")
print("============================================================")


# 輸出詳細排程資訊
if args.verbose:
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print(f"{'LotId':<10} | {'Step':<8} | {'Machine':<10} | {'Start Time':<19} | {'End Time':<19}")
        print("-" * 75)
        for job in jobs_data:
            lot = job["LotId"]
            for step, group, duration in job["Operations"]:
                task = all_tasks[(lot, step)]
                
                # 取得機台名稱
                submachines = MACHINE_GROUPS[group]
                m_idx = solver.Value(task["machine_choice"])
                machine_name = submachines[m_idx]
                
                # 取得時間並轉換
                start_min = solver.Value(task["start"])
                end_min = solver.Value(task["end"])
                
                start_dt = SCHEDULE_START + timedelta(minutes=start_min)
                end_dt = SCHEDULE_START + timedelta(minutes=end_min)
                
                print(f"{lot:<10} | {step:<8} | {machine_name:<10} | {start_dt.strftime('%Y-%m-%d %H:%M:%S')} | {end_dt.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 75)
    else:
        print("No feasible solution found to display results.")


