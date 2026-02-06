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

class BookingColorMap:
    COLOR_BY_BOOKING = {
        1: "#FFE5B4",   # 已預約 / 進行中作業(WIP)
        2:  "#00BFFF",    # 已鎖定 /已完成作業(COMPLETED)
        3: "#A9A9A9",   # 已超過現在時間
        1002: "#8A2BE2", # 凍結作業(FROZEN)
        0:"#5DC85D",  # 新排程 (重排)
        10: "#2C562C",  # 新排程 (新加入)        
        -1: "#FF4500",  # 維修/維修計畫
        -2: "#B87333",  # 當機
        -20: "#808080", # 預留
        -21: "#C0C0C0", # 預留
        -22: "#FFFDD0", # 預留
    }

    @staticmethod
    def get_color(booking: int) -> str:
        return BookingColorMap.COLOR_BY_BOOKING.get(booking, "#F0F8FF")


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
#horizon = sum(op[2] for job in jobs_data for op in job["Operations"]) * 1
#print(f"Horizon: {horizon}", flush=True)

horizon = max(sum(op[2] for op in job["Operations"]) for job in jobs_data) + 60*24* 15 # 多增加 3天
print(f"Horizon: {horizon}", flush=True)
print(f"Schedule Range Start: {SCHEDULE_START}", flush=True)
print(f"Schedule Range End  : {SCHEDULE_START + timedelta(minutes=horizon)}", flush=True)


overall_start_time = time.perf_counter()
print(f"overall_start_time: {overall_start_time}", flush=True)

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

print("============================================================", flush=True)
print(f"Solver Status: {solver.StatusName(status) if len(batches)>0 else 'N/A'}", flush=True)
print(f"Solve Duration: {solve_duration:.4f} seconds", flush=True)
print(f"CPU Cores: {os.cpu_count()}", flush=True)
print("============================================================", flush=True)

# =====================================================
# Generate JSON Results (Ref: V1)
# =====================================================
if total_solved_tasks:
    print("\nGenerating result files...", flush=True)
    import json
    
    plan_result_dir = "plan_result"
    os.makedirs(plan_result_dir, exist_ok=True)
    
    # 1. LotStepResult.json & Data Preparation
    lot_step_results = []
    for (lot_id, step_name), res in total_solved_tasks.items():
        job_info = next(j for j in jobs_data if j["LotId"] == lot_id)
        step_idx = next(i for i, op in enumerate(job_info["Operations"]) if op[0] == step_name) + 1
        
        st_dt = SCHEDULE_START + timedelta(minutes=res['start_min'])
        et_dt = SCHEDULE_START + timedelta(minutes=res['end_min'])
        
        # 模擬 Booking 邏輯 (V2 預設為 0: 重排)
        booking = 0
        
        lot_step_results.append({
            "LotId": lot_id,
            "Product": "", # V2 目前無 Product ID
            "Priority": job_info["Priority"],
            "StepIdx": step_idx,
            "Step": step_name,
            "Machine": res['machine'],
            "Start": st_dt.strftime("%Y-%m-%dT%H:%M:%S"),
            "End": et_dt.strftime("%Y-%m-%dT%H:%M:%S"),
            "Booking": booking
        })

    with open(os.path.join(plan_result_dir, "LotStepResult.json"), 'w', encoding='utf-8') as f:
        json.dump(lot_step_results, f, indent=4, ensure_ascii=False)
    print(f"✅ Saved results to {os.path.join(plan_result_dir, 'LotStepResult.json')}", flush=True)

    # 2. LotPlanResult.json
    lot_plan_results = []
    for job in jobs_data:
        lot_id = job["LotId"]
        # 找出該 Lot 的所有步驟結果
        lot_tasks = {step: info for (l_id, step), info in total_solved_tasks.items() if l_id == lot_id}
        
        if lot_tasks:
            last_step = job["Operations"][-1][0]
            if last_step in lot_tasks:
                last_res = lot_tasks[last_step]
                plan_date = SCHEDULE_START + timedelta(minutes=last_res['end_min'])
                due_date = datetime.fromisoformat(job["DueDate"])
                
                # 計算延遲時間 (D:HH)
                diff = plan_date - due_date
                if diff.total_seconds() > 0:
                    delay_str = f"{diff.days}:{diff.seconds // 3600:02d}"
                else:
                    abs_diff = abs(diff)
                    delay_str = f"-{abs_diff.days}:{abs_diff.seconds // 3600:02d}"
                
                lot_plan_results.append({
                    "Lot": lot_id,
                    "Product": "",
                    "Priority": job["Priority"],
                    "DueDate": job["DueDate"],
                    "PlanFinishDate": plan_date.strftime("%Y-%m-%dT%H:%M:%S"),
                    "ActualFinishDate": None,
                    "delay time": delay_str
                })

    stats = {
        "optimization_type": "incremental_scheduling_v2",
        "batch_count": len(jobs_data),
        "calculation_duration": f"{solve_duration:.4f}",
        "calculation_end": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    }
    
    with open(os.path.join(plan_result_dir, "LotPlanResult.json"), 'w', encoding='utf-8') as f:
        json.dump({"statistics": stats, "lot_results": lot_plan_results}, f, indent=4, ensure_ascii=False)
    print(f"✅ Saved results to {os.path.join(plan_result_dir, 'LotPlanResult.json')}", flush=True)

    # 3. machineTaskSegment.json
    task_segments = []
    machine_map = {}
    for r in lot_step_results:
        m = r["Machine"]
        if m not in machine_map: machine_map[m] = []
        machine_map[m].append(r)

    for m_id in sorted(machine_map.keys()):
        # 機台主節點
        task_segments.append({
            "id": m_id,
            "text": m_id,
            "parent": None,
            "render": "split"
        })
        
        # 機台下的任務節點
        for r in machine_map[m_id]:
            task_segments.append({
                "id": f"{r['Machine']}_{r['LotId']}_{r['Step']}",
                "text": f"{r['LotId']} {r['Step']}",
                "parent": r["Machine"],
                "start_date": r["Start"],
                "end_date": r["End"],
                "Booking": r["Booking"],
                "color": BookingColorMap.get_color(r["Booking"])
            })

    output_path = os.path.join(plan_result_dir, "machineTaskSegment.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(task_segments, f, indent=4, ensure_ascii=False)
    
    print(f"✅ Saved results to {output_path}", flush=True)

print("\nScheduling Complete.")
sys.stdout.flush()
