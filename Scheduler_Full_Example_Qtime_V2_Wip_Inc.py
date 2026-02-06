#  在終端機執行 切換虛擬環境
#  192.168.0.124 mcsadmin/gis5613686
#  source myenv/bin/activate

from ortools.sat.python import cp_model
from datetime import datetime, timedelta
import time
import sys
import io
import os

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
BATCH_THRESHOLD = int(env_config.get('INCREMENTAL_BATCH_THRESHOLD', 30))
BATCH_INITIAL_SIZE = int(env_config.get('INCREMENTAL_BATCH_INITIAL_SIZE', 30))
BATCH_STEP_SIZE = int(env_config.get('INCREMENTAL_BATCH_STEP_SIZE', 3))
LIMIT_LOTS = int(env_config.get('SCHEDULER_LIMIT_LOTS', 300))
MACHINES_PER_GROUP = int(env_config.get('SCHEDULER_MACHINES_PER_GROUP', 10))

# =====================================================
# 基本設定
# =====================================================
SCHEDULE_START = datetime(2026, 1, 18, 13, 0, 0)
OBJECTIVE_TYPE = "weighted_delay"   # "makespan" | "weighted_delay"


# =====================================================
# Job 資料生成
# =====================================================
# 定義 20 個步驟的範本
base_ops = []
for i in range(1, 21):
    base_ops.append((f"STEP{i}", f"M{i:02d}", 360))

# 動態生成 Jobs
limit_lots = LIMIT_LOTS
jobs_data = []
for i in range(1, limit_lots + 1):
    lot_id = f"LOT_{i:03d}"
    
    # 建立作業步驟（STEP1 ~ STEP20）
    current_ops = []
    for step_idx in range(1, 21):
        step_name = f"STEP{step_idx}"
        group_name = f"M{step_idx:02d}"
        duration = 200 + (i % 50) + (step_idx * 10)
        current_ops.append((step_name, group_name, duration))

    job = {
        "LotId": lot_id,
        "Priority": 100 if i == 1 else 50,
        "DueDate": (SCHEDULE_START + timedelta(days=15)).isoformat(),
        "LotCreateDate": (SCHEDULE_START + timedelta(hours=i)).isoformat(), # 模擬不同的進入時間
        "Operations": current_ops,
    }
    jobs_data.append(job)


# =====================================================
# Machine Groups
# =====================================================
MACHINE_GROUPS = {}
for i in range(1, 21):
    group_name = f"M{i:02d}"
    # 每個群組的設備數量
    num_machines = MACHINES_PER_GROUP + (i % 11)
    MACHINE_GROUPS[group_name] = [f"{group_name}-{j}" for j in range(1, num_machines + 1)]


# =====================================================
# Incremental Scheduling Batching
# =====================================================
if len(jobs_data) > BATCH_THRESHOLD:
    batches = []
    # 第一步：先取初始批次
    batches.append(jobs_data[:BATCH_INITIAL_SIZE])
    # 第二步：之後每次增加固定步長 (不再累積前面的資料)
    remaining_lots = jobs_data[BATCH_INITIAL_SIZE:]
    for i in range(0, len(remaining_lots), BATCH_STEP_SIZE):
        batches.append(remaining_lots[i : i + BATCH_STEP_SIZE])
else:
    batches = [jobs_data]

# 儲存已計算完畢的任務 (Lot, Step) -> {start_min, end_min, machine}
total_solved_tasks = {}
final_status = cp_model.FEASIBLE

# Horizon 上限 (動態計算：所有作業時間總和 * 安全係數)
horizon = sum(op[2] for job in jobs_data for op in job["Operations"]) * 1

overall_start_time = time.perf_counter()

print(f"Starting Incremental Scheduling for {len(jobs_data)} lots in {len(batches)} batches...", flush=True)

for batch_idx, current_batch in enumerate(batches):
    progress = int((batch_idx) / len(batches) * 100)
    batch_start_time = time.perf_counter()
    print(f"\n>>> [Batch {batch_idx + 1}/{len(batches)}] Processing {len(current_batch)} Lots - Progress: {progress}%", flush=True)
    
    model = cp_model.CpModel()
    machines = {m: [] for g in MACHINE_GROUPS.values() for m in g}
    batch_tasks = {}

    # 1. 加入先前批次已決定的固定間隔
    if total_solved_tasks:
        print(f"    * Loading {len(total_solved_tasks)} fixed tasks from previous batches...", flush=True)
    for (lot_id, step_name), res in total_solved_tasks.items():
        dur = res['end_min'] - res['start_min']
        itv = model.NewFixedSizeIntervalVar(res['start_min'], dur, f"fixed_{lot_id}_{step_name}")
        machines[res['machine']].append(itv)

    # 2. 加入當前批次任務
    for job in current_batch:
        lot = job["LotId"]
        
        # Determine Release Time (Earliest Start)
        release_min = 0
        l_create = job.get("LotCreateDate")
        if l_create:
            target_release = datetime.fromisoformat(l_create)
            delta_min = int((target_release - SCHEDULE_START).total_seconds() / 60)
            release_min = max(0, delta_min)

        prev_end = release_min
        for step, group, duration in job["Operations"]:
            submachines = MACHINE_GROUPS[group]
            



            # --- Normal ---
            start_var = model.NewIntVar(0, horizon, f"{lot}_{step}_start")
            end_var = model.NewIntVar(0, horizon, f"{lot}_{step}_end")
            machine_choice = model.NewIntVar(0, len(submachines) - 1, f"{lot}_{step}_machine")
            
            # 順序約束
            model.Add(start_var >= prev_end)

            itvs, presents = [], []
            for i, m in enumerate(submachines):
                p = model.NewBoolVar(f"{lot}_{step}_p_{i}")
                itv = model.NewOptionalIntervalVar(start_var, duration, end_var, p, f"{lot}_{step}_{m}")
                itvs.append(itv)
                presents.append(p)
                machines[m].append(itv)
                model.Add(machine_choice == i).OnlyEnforceIf(p)
            
            model.Add(sum(presents) == 1)
            
            batch_tasks[(lot, step)] = {
                "start": start_var, "end": end_var, "machine_group": group,
                "machine_choice": machine_choice, "status": "Normal"
            }
            prev_end = end_var

    # 3. 機台互斥約束
    for m, itvs in machines.items():
        if itvs:
            model.AddNoOverlap(itvs)

    # 4. Q-time Constraints (與 V1 相同，STEP3 到 STEP4 不得超過 200 分鐘)
    for job in current_batch:
        lot = job["LotId"]
        ops_names = [s for s, _, _ in job["Operations"]]
        if "STEP3" in ops_names and "STEP4" in ops_names:
            if (lot, "STEP3") in batch_tasks and (lot, "STEP4") in batch_tasks:
                model.Add(batch_tasks[(lot, "STEP4")]["start"] - batch_tasks[(lot, "STEP3")]["end"] <= 200)

    # 5. 目標函數 (當前批次的 weighted delay)
    batch_delay_vars = []
    for job in current_batch:
        lot = job["LotId"]
        due = datetime.fromisoformat(job["DueDate"])
        due_min = int((due - SCHEDULE_START).total_seconds() / 60)
        last_step = job["Operations"][-1][0]
        delay = model.NewIntVar(0, horizon, f"{lot}_delay")
        model.Add(delay >= batch_tasks[(lot, last_step)]["end"] - due_min)
        model.Add(delay >= 0)
        batch_delay_vars.append(delay * job["Priority"])
    
    # 增加一個小的 makespan 項以提早完成
    batch_makespan = model.NewIntVar(0, horizon, f"batch_makespan_{batch_idx}")
    model.AddMaxEquality(batch_makespan, [batch_tasks[(j["LotId"], j["Operations"][-1][0])]["end"] for j in current_batch])
    
    model.Minimize(sum(batch_delay_vars) * 100 + batch_makespan)

    # 5. Solve Batch
    print(f"    * Solving Batch {batch_idx + 1} ({len(current_batch)} Lots, Time Limit {SOLVER_TIME_LIMIT}s)...", flush=True)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = SOLVER_TIME_LIMIT 
    # solver.parameters.log_search_progress = True 
    status = solver.Solve(model)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        # 紀錄結果供後續批次使用
        for (lot_id, step_name), task_item in batch_tasks.items():
            st_min = solver.Value(task_item["start"])
            et_min = solver.Value(task_item["end"])
            
            if task_item["status"] in ["Completed", "WIP"]:
                m_name = task_item["machine"]
            else:
                idx = solver.Value(task_item["machine_choice"])
                m_name = MACHINE_GROUPS[task_item["machine_group"]][idx]
            
            total_solved_tasks[(lot_id, step_name)] = {
                "start_min": st_min,
                "end_min": et_min,
                "machine": m_name
            }
    else:
        print(f"    [Warning] Batch {batch_idx + 1} failed. Status: {solver.StatusName(status)}", flush=True)
        if status == cp_model.UNKNOWN:
            print("    [Hint] UNKNOWN status usually means no solution found within the time limit. Try increasing SOLVER_MAX_TIME_IN_SECONDS.", flush=True)
        final_status = status
        print(f"    [Warning] Batch {batch_idx + 1} has no solution. Skipping this batch, which may cause overlapping issues!", flush=True)

    batch_end_time = time.perf_counter()
    duration = batch_end_time - batch_start_time
    print(f"    [Batch {batch_idx + 1}] Finished. Status: {solver.StatusName(status)}, Duration: {duration:.2f}s", flush=True)

overall_end_time = time.perf_counter()
solve_duration = overall_end_time - overall_start_time

# =====================================================
# Output
# =====================================================
print("============================================================", flush=True)
print(f"Solver Status: {solver.StatusName(status) if len(batches)>0 else 'N/A'}", flush=True)
print(f"Solve Duration: {solve_duration:.4f} seconds", flush=True)
print(f"CPU Cores: {os.cpu_count()}", flush=True)
print("============================================================", flush=True)

# 註解掉詳細資訊輸出的範本
# if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
#     # ... 可以從 total_solved_tasks 讀取結果 ...
#     pass
