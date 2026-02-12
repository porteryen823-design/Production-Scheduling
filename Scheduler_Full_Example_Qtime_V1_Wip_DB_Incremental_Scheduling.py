# 因應資料量可能會有幾百個 lots,作業站 20~30站, 會無法在限定時間內完成計算,需要用分批處理方式
# 需要未來依照客戶需求調整參數, 依照客戶狀況調整參數

import sys
import io
import mysql.connector
import os
import time
import json
import argparse
from ortools.sat.python import cp_model
from datetime import datetime, timedelta
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 載入環境變數
load_dotenv()

# 解析命令行參數
parser = argparse.ArgumentParser()
parser.add_argument('--start-time', type=str, default='2026-01-22 14:00:00',
                    help='Scheduling start time (YYYY-MM-DD HH:MM:SS)')
args = parser.parse_args()
print(f"Scheduling start time: {args.start_time}")

# 資料庫連線設定
db_config = {
    'host': os.getenv('MYSQL_HOST'),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE')
}

# =====================================================
# 基本設定
# =====================================================
SCHEDULE_START = datetime.strptime(args.start_time, '%Y-%m-%d %H:%M:%S')
OBJECTIVE_TYPE = "total_completion_time"   # "makespan" | "weighted_delay" | "total_completion_time"


# 下面順序可以調整, 須注意與前端UI同步
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

def load_machine_unavailable_periods():
    """從資料庫載入機台不可用時段"""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT Id, MachineId, StartTime, EndTime, PeriodType, Reason, Priority
            FROM machine_unavailable_periods
            WHERE Status = 'ACTIVE'
            AND StartTime < DATE_ADD(%s, INTERVAL 30 DAY)
            AND EndTime > %s
            ORDER BY MachineId, StartTime
        """, (SCHEDULE_START, SCHEDULE_START))

        unavailable_periods = cursor.fetchall()
        cursor.close()
        conn.close()
        print(f"Loaded {len(unavailable_periods)} machine unavailable periods from database")
        
        machine_unavailable = {}
        for period in unavailable_periods:
            machine_id = period['MachineId']
            if machine_id not in machine_unavailable:
                machine_unavailable[machine_id] = []
            machine_unavailable[machine_id].append(period)

        return machine_unavailable

    except Exception as e:
        print(f"Error loading machine unavailable periods: {e}")
        return {}

def load_jobs_from_database():
    """從資料庫載入 jobs_data"""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT parameter_value FROM ui_settings WHERE parameter_name = 'scheduler_exclude_completed_lots'")
        row = cursor.fetchone()
        exclude_completed = True
        if row:
            exclude_completed = row['parameter_value'].lower() == 'true'
            
        print(f"Scheduler setting: exclude_completed_lots = {exclude_completed}")

        query = "SELECT LotId, Priority, DueDate, ActualFinishDate, PlanFinishDate, PlanStartTime, LotCreateDate FROM Lots"
        if exclude_completed:
            query += " WHERE ActualFinishDate IS NULL"
        query += " ORDER BY LotId"
        
        cursor.execute(query)
        lots_data = cursor.fetchall()

        jobs_data = []
        for lot in lots_data:
            lot_id = lot.get('LotId', None)
            if not lot_id: continue

            cursor.execute("""
                SELECT Step, MachineGroup, Duration, Sequence, StepStatus, CheckInTime, CheckOutTime, PlanCheckInTime, PlanCheckOutTime, PlanMachineId
                FROM LotOperations
                WHERE LotId = %s
                AND LotId IS NOT NULL
                ORDER BY Sequence
            """, (lot_id,))

            operations_data = cursor.fetchall()

            completed_ops = {}
            wip_ops = {}
            frozen_ops = {}
            new_schedule_type = {}

            for op in operations_data:
                step = op.get('Step', None)
                status = op.get('StepStatus', None)
                check_in = op.get('CheckInTime', None)
                plan_check_in = op.get('PlanCheckInTime', None)
                plan_check_out = op.get('PlanCheckOutTime', None)
                machine = op.get('PlanMachineId', None)

                if status == 0:
                    new_schedule_type[step] = 0 if plan_check_in is None else 10
                elif status == 2:
                    completed_ops[step] = {"start_time": plan_check_in, "end_time": plan_check_out, "machine": machine}
                elif status == 1:
                    elapsed = 0
                    if check_in:
                        elapsed = int((SCHEDULE_START - check_in).total_seconds() / 60)
                    wip_ops[step] = {
                        "start_time": plan_check_in, 
                        "end_time": plan_check_out,
                        "elapsed_minutes": max(0, elapsed),
                        "machine": machine
                    }

            cursor.execute("""
                SELECT Step, MachineId, StartTime, EndTime
                FROM FrozenOperations
                WHERE LotId = %s
            """, (lot_id,))
            frozen_data = cursor.fetchall()
            for frozen in frozen_data:
                frozen_ops[frozen['Step']] = {
                    "start_time": frozen['StartTime'],
                    "end_time": frozen['EndTime'],
                    "machine": frozen['MachineId']
                }

            operations = []
            for op in operations_data:
                operations.append((op['Step'], op['MachineGroup'], op['Duration']))

            job = {
                "LotId": lot_id,
                "Priority": lot['Priority'],
                "DueDate": lot['DueDate'].strftime("%Y-%m-%dT%H:%M:%S") if lot['DueDate'] else None,
                "ActualFinishDate": lot['ActualFinishDate'].strftime("%Y-%m-%dT%H:%M:%S") if lot['ActualFinishDate'] else None,
                "PlanFinishDate": lot['PlanFinishDate'].strftime("%Y-%m-%dT%H:%M:%S") if lot['PlanFinishDate'] else None,
                "PlanStartTime": lot['PlanStartTime'].strftime("%Y-%m-%dT%H:%M:%S") if lot['PlanStartTime'] else None,
                "LotCreateDate": lot['LotCreateDate'].strftime("%Y-%m-%dT%H:%M:%S") if lot['LotCreateDate'] else None,
                "Operations": operations,
                "CompletedOps": completed_ops,
                "WIPOps": wip_ops,
                "FrozenOps": frozen_ops,
                "NewScheduleType": new_schedule_type,
            }
            jobs_data.append(job)

        cursor.close()
        conn.close()
        print(f"Loaded {len(jobs_data)} jobs from database")
        sys.stdout.flush()
        return jobs_data
    except Exception as e:
        print(f"Error loading jobs: {e}")
        sys.stdout.flush()
        return []

def save_jobs_to_plan_raw(jobs_data):
    import time
    plan_id = f"PLAN_{int(time.time())}"
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        raw_data_json = json.dumps(jobs_data, ensure_ascii=False, default=str)
        cursor.execute("INSERT INTO PlanRaw (PlanID, RawData) VALUES (%s, %s)", (plan_id, raw_data_json))
        conn.commit()
        cursor.close()
        conn.close()
        
        os.makedirs('plan_result', exist_ok=True)
        with open('plan_result/LotPlanRaw.json', 'w', encoding='utf-8') as f:
            json.dump(jobs_data, f, ensure_ascii=False, indent=2, default=str)
        return plan_id
    except Exception as e:
        print(f"Error saving PlanRaw: {e}")
        return None

def update_plan_chunk(lots_chunk, ops_chunk):
    """Worker function for updating a chunk of data in a separate thread"""
    conn = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        cursor.callproc('sp_UpdatePlanResultsJSON', (
            json.dumps(lots_chunk, ensure_ascii=False),
            json.dumps(ops_chunk, ensure_ascii=False)
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True, len(lots_chunk)
    except Exception as e:
        if conn: conn.rollback()
        print(f"!!! DB Update Task Error: {e}")
        return False, str(e)

def update_plan_times(lot_results, plan_id, all_tasks_status):
    """Update plan times using Multi-threading and Stored Procedure"""
    main_start = datetime.now()
    try:
        lots_json_list = []
        ops_json_list = []

        for lot_id, operations in lot_results.items():
            job_info = next((j for j in jobs_data if j["LotId"] == lot_id), None)
            if not job_info: continue
            
            lot_finish_time = max((res['end_time'] for res in operations.values()), default=None)
            lot_start_time = min((res['start_time'] for res in operations.values()), default=None)

            if lot_finish_time:
                due_date = datetime.fromisoformat(job_info["DueDate"]) if job_info["DueDate"] else lot_finish_time
                delay_days = round((lot_finish_time - due_date).total_seconds() / 86400, 2)
                
                lots_json_list.append({
                    "LotId": lot_id,
                    "PlanFinishDate": lot_finish_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "PlanStartTime": lot_start_time.strftime("%Y-%m-%d %H:%M:%S") if lot_start_time else None,
                    "Delay_Days": delay_days
                })

            for step, result in operations.items():
                if all_tasks_status.get((lot_id, step)) != "Normal":
                    continue

                start_time = result['start_time']
                end_time = result['end_time']
                machine = result['machine']

                history_entry = {
                    "PlanID": plan_id,
                    "PlanCheckInTime": start_time.strftime("%Y-%m-%dT%H:%M:%S") if start_time else None,
                    "PlanCheckOutTime": end_time.strftime("%Y-%m-%dT%H:%M:%S") if end_time else None,
                    "PlanMachineId": machine,
                    "CreatedAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                }

                ops_json_list.append({
                    "LotId": lot_id,
                    "Step": step,
                    "Start": start_time.strftime("%Y-%m-%d %H:%M:%S") if start_time else None,
                    "End": end_time.strftime("%Y-%m-%d %H:%M:%S") if end_time else None,
                    "Machine": machine,
                    "HistoryInfo": history_entry
                })

        # Multi-threading logic: Split data into chunks by LotId to keep Lots and Ops synchronized
        lot_ids = list(lot_results.keys())
        chunk_size = 50
        lot_id_chunks = [lot_ids[i:i + chunk_size] for i in range(0, len(lot_ids), chunk_size)]
        
        tasks = []
        for lid_chunk in lot_id_chunks:
            l_c = [l for l in lots_json_list if l["LotId"] in lid_chunk]
            o_c = [o for o in ops_json_list if o["LotId"] in lid_chunk]
            if l_c or o_c:
                tasks.append((l_c, o_c))

        print(f"Starting parallel database update with {len(tasks)} tasks (Chunk size: {chunk_size})...")
        
        results = []
        # Use more workers for better concurrency, but balance with DB connection limits
        num_workers = min(len(tasks), 8)
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(update_plan_chunk, t[0], t[1]) for t in tasks]
            for future in futures:
                res, info = future.result()
                results.append((res, info))

        main_end = datetime.now()
        success_count = sum(1 for r in results if r[0])
        total_items = sum(r[1] if isinstance(r[1], int) else 0 for r in results)
        error_msgs = [r[1] for r in results if not r[0]]
        
        print(f"Successfully updated plan times using {success_count}/{len(tasks)} parallel tasks (Total items: {total_items}) - Total Time: {main_end - main_start}")
        if error_msgs:
            print(f"Update errors encountered: {set(error_msgs)}")
    except Exception as e:
        print(f"Parallel update error: {e}")

def load_machine_groups():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT MachineId, GroupId FROM Machines WHERE is_active = 1 ORDER BY GroupId, MachineId")
        rows = cursor.fetchall()
        groups = {}
        for row in rows:
            gid = row['GroupId']; mid = row['MachineId']
            if gid not in groups: groups[gid] = []
            groups[gid].append(mid)
        cursor.close()
        conn.close()
        return groups
    except:
        return {}

def calculate_and_save_utilization(final_lot_results, plan_id, machine_groups):
    """計算並儲存機台群組利用率"""
    if not final_lot_results:
        return

    all_starts = []
    all_ends = []
    
    # 統計各群組的使用分鐘數
    group_used_minutes = {g: 0 for g in machine_groups.keys()}
    
    for lot_id, operations in final_lot_results.items():
        for step, res in operations.items():
            all_starts.append(res['start_time'])
            all_ends.append(res['end_time'])
            
            # 尋找機台所屬群組 (優化：預先建立 machine_to_group map)
            machine = res['machine']
            duration = (res['end_time'] - res['start_time']).total_seconds() / 60
            
            for gid, ms in machine_groups.items():
                if machine in ms:
                    group_used_minutes[gid] += duration
                    break
    
    if not all_starts or not all_ends:
        return
        
    window_start = min(all_starts)
    window_end = max(all_ends)
    window_duration = (window_end - window_start).total_seconds() / 60
    
    if window_duration <= 0:
        return

    print(f"\n=== Machine Group Utilizations (Plan: {plan_id}) ===")
    print(f"Window: {window_start} to {window_end} ({window_duration:.1f} mins)")
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        insert_data = []
        for gid, used_mins in group_used_minutes.items():
            machine_count = len(machine_groups[gid])
            total_capacity = machine_count * window_duration
            utilization = (used_mins / total_capacity * 100) if total_capacity > 0 else 0
            
            print(f"- {gid}: {utilization:6.2f}% | Used: {used_mins:8.1f} min | Capacity: {total_capacity:8.1f} min")
            
            insert_data.append((
                plan_id, gid, window_start, window_end, machine_count,
                int(used_mins), int(total_capacity), float(utilization)
            ))
            
        # 批次插入
        cursor.executemany("""
            INSERT INTO MachineGroupUtilization 
            (PlanID, GroupId, CalculationWindowStart, CalculationWindowEnd, MachineCount, TotalUsedMinutes, TotalCapacityMinutes, UtilizationRate)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, insert_data)
        
        conn.commit()
        cursor.close()
        conn.close()
        print(f"Successfully saved utilization results to database.")
    except Exception as e:
        print(f"Error saving utilization results: {e}")

# =====================================================
# Main Logic
# =====================================================
jobs_data = load_jobs_from_database()
if not jobs_data:
    print("No jobs to schedule.")
    exit(1)

machine_unavailable = load_machine_unavailable_periods()
plan_id = save_jobs_to_plan_raw(jobs_data)
MACHINE_GROUPS = load_machine_groups()
if not MACHINE_GROUPS:
    MACHINE_GROUPS = {"M01": ["M01-1", "M01-2", "M01-3"], "M02": ["M02-1", "M02-2"], "M03": ["M03-1", "M03-2", "M03-3"]}

# Incremental Scheduling Batching
lots_to_schedule = jobs_data
batch_threshold = int(os.getenv('INCREMENTAL_BATCH_THRESHOLD', 30))
initial_size = int(os.getenv('INCREMENTAL_BATCH_INITIAL_SIZE', 30))
step_size = int(os.getenv('INCREMENTAL_BATCH_STEP_SIZE', 3))

if len(lots_to_schedule) > batch_threshold:
    batches = []
    # 第一步：先取初始批次
    batches.append(lots_to_schedule[:initial_size])
    # 第二步：之後每次增加固定步長
    remaining_lots = lots_to_schedule[initial_size:]
    for i in range(0, len(remaining_lots), step_size):
        batches.append(remaining_lots[i : i + step_size])
else:
    batches = [lots_to_schedule]

# Global result storage
final_lot_results = {} # lot -> step -> {start_time, end_time, machine}
all_tasks_info = {} # (lot, step) -> {status, ...}
calc_start_time = datetime.now()
total_solved_tasks = {} # (lot, step) -> {start_min, end_min, machine}

for batch_idx, current_batch in enumerate(batches):
    progress = int((batch_idx) / len(batches) * 100)
    print(f"\n>>> Solving Batch {batch_idx + 1}/{len(batches)} ({len(current_batch)} lots) - Progress: {progress}%")
    sys.stdout.flush()
    
    model = cp_model.CpModel()
    # Horizon: Sum of durations of all lots * safety factor
    #horizon = sum(op[2] for job in jobs_data for op in job["Operations"]) * 10
    horizon = max(sum(op[2] for op in job["Operations"]) for job in jobs_data) + 60*24* 50 # 多增加 3天
    machines = {m: [] for g in MACHINE_GROUPS.values() for m in g}
    batch_tasks = {}

    # 1. Add Fixed Machine Intervals from previous batches
    for (lot_id, step_name), res in total_solved_tasks.items():
        dur = res['end_min'] - res['start_min']
        itv = model.NewFixedSizeIntervalVar(res['start_min'], dur, f"fix_{lot_id}_{step_name}")
        machines[res['machine']].append(itv)

    # 2. Add Machine Unavailability
    for machine_id, unavailable_periods in machine_unavailable.items():
        if machine_id not in machines: continue
        for period in unavailable_periods:
            s_m = int((period['StartTime'] - SCHEDULE_START).total_seconds() / 60)
            e_m = int((period['EndTime'] - SCHEDULE_START).total_seconds() / 60)
            if e_m <= 0 or s_m >= horizon: continue
            s_m = max(0, s_m); e_m = min(horizon, e_m)
            if e_m <= s_m: continue
            itv = model.NewFixedSizeIntervalVar(s_m, e_m - s_m, f"unav_{machine_id}_{period['Id']}")
            machines[machine_id].append(itv)

    # 3. Add Current Batch Lots
    for job in current_batch:
        lot = job["LotId"]
        
        # Determine Release Time (Earliest Start)
        release_min = 0
        p_start = job.get("PlanStartTime")
        l_create = job.get("LotCreateDate")
        
        target_release = None
        if p_start:
            target_release = datetime.fromisoformat(p_start)
        elif l_create:
            target_release = datetime.fromisoformat(l_create)
            
        if target_release:
            # Calculate release minute relative to SCHEDULE_START
            # If target_release is BEFORE SCHEDULE_START, it becomes 0 (ready immediatley)
            # If target_release is AFTER SCHEDULE_START, it becomes positive delay
            delta_min = int((target_release - SCHEDULE_START).total_seconds() / 60)
            release_min = max(0, delta_min)

        print(f"Lot {lot}: Release Constraint = {release_min} min (from {target_release})")

        completed_ops = job.get("CompletedOps", {})
        wip_ops = job.get("WIPOps", {})
        frozen_ops = job.get("FrozenOps", {})

        prev_end = release_min
        for step, group, duration in job["Operations"]:
            submachines = MACHINE_GROUPS[group]
            
            # --- Completed ---
            if step in completed_ops:
                info = completed_ops[step]
                s = max(0, int((info["start_time"] - SCHEDULE_START).total_seconds() / 60))
                e = int((info["end_time"] - SCHEDULE_START).total_seconds() / 60)
                if e <= 0:
                    start_var, end_var = model.NewConstant(0), model.NewConstant(0)
                    batch_tasks[(lot, step)] = {"start": start_var, "end": end_var, "machine": info["machine"], "status": "Completed"}
                    prev_end = 0; continue
                start_var, end_var = model.NewConstant(s), model.NewConstant(e)
                itv = model.NewFixedSizeIntervalVar(s, e - s, f"{lot}_{step}_completed")
                machines[info["machine"]].append(itv)
                batch_tasks[(lot, step)] = {"start": start_var, "end": end_var, "machine": info["machine"], "status": "Completed"}
                prev_end = e; continue

            # --- WIP ---
            if step in wip_ops:
                info = wip_ops[step]
                elapsed = info["elapsed_minutes"]
                remaining = max(0, duration - elapsed)
                start_var, end_var = model.NewConstant(prev_end), model.NewConstant(prev_end + remaining)
                itv = model.NewFixedSizeIntervalVar(prev_end, remaining, f"{lot}_{step}_wip")
                machines[info["machine"]].append(itv)
                batch_tasks[(lot, step)] = {"start": start_var, "end": end_var, "machine": info["machine"], "status": "WIP"}
                prev_end = prev_end + remaining; continue

            # --- Frozen ---
            if step in frozen_ops:
                info = frozen_ops[step]
                s = max(0, int((info["start_time"] - SCHEDULE_START).total_seconds() / 60))
                e = int((info["end_time"] - SCHEDULE_START).total_seconds() / 60)
                if e <= 0:
                    start_var, end_var = model.NewConstant(0), model.NewConstant(0)
                    batch_tasks[(lot, step)] = {"start": start_var, "end": end_var, "machine": info["machine"], "status": "Frozen"}
                    prev_end = 0; continue
                start_var, end_var = model.NewConstant(s), model.NewConstant(e)
                itv = model.NewFixedSizeIntervalVar(s, e - s, f"{lot}_{step}_frozen")
                machines[info["machine"]].append(itv)
                batch_tasks[(lot, step)] = {"start": start_var, "end": end_var, "machine": info["machine"], "status": "Frozen"}
                prev_end = e; continue

            # --- Normal ---
            start_var = model.NewIntVar(0, horizon, f"{lot}_{step}_start")
            end_var = model.NewIntVar(0, horizon, f"{lot}_{step}_end")
            machine_choice = model.NewIntVar(0, len(submachines) - 1, f"{lot}_{step}_machine")
            model.Add(start_var >= prev_end)

            itvs, presents = [], []
            for i, m in enumerate(submachines):
                p = model.NewBoolVar(f"{lot}_{step}_p_{i}")
                itv = model.NewOptionalIntervalVar(start_var, duration, end_var, p, f"{lot}_{step}_{m}")
                itvs.append(itv); presents.append(p); machines[m].append(itv)
                model.Add(machine_choice == i).OnlyEnforceIf(p)
                model.Add(machine_choice != i).OnlyEnforceIf(p.Not())
            model.Add(sum(presents) == 1)

            batch_tasks[(lot, step)] = {
                "start": start_var, "end": end_var, "machine_group": group,
                "machine_choice": machine_choice, "status": "Normal"
            }
            prev_end = end_var

    # 4. No Overlap
    for m, itvs in machines.items():
        if itvs: model.AddNoOverlap(itvs)

    # 5. Q-time Constraints (per batch)
    for job in current_batch:
        lot = job["LotId"]
        ops_names = [s for s, _, _ in job["Operations"]]
        if "STEP3" in ops_names and "STEP4" in ops_names:
            if (lot, "STEP3") in batch_tasks and (lot, "STEP4") in batch_tasks:
                model.Add(batch_tasks[(lot, "STEP4")]["start"] - batch_tasks[(lot, "STEP3")]["end"] <= 200)

    # 6. Objective (per batch)
    is_fast_verification = os.getenv('SCHEDULER_FAST_VERIFICATION', 'true').lower() == 'true'
    if is_fast_verification:
        # Fast verification mode: no objective
        pass
    else:
        # Calculate makespan for current batch
        batch_makespan = model.NewIntVar(0, horizon, f"batch_makespan_{batch_idx}")
        last_step_ends = []
        for job in current_batch:
            last_step = job["Operations"][-1][0]
            last_step_ends.append(batch_tasks[(job["LotId"], last_step)]["end"])
        model.AddMaxEquality(batch_makespan, last_step_ends)

        if OBJECTIVE_TYPE == "weighted_delay":
            delay_vars = []
            for job in current_batch:
                lot = job["LotId"]
                if job["DueDate"]:
                    due = datetime.fromisoformat(job["DueDate"])
                    due_min = int((due - SCHEDULE_START).total_seconds() / 60)
                    last_step = job["Operations"][-1][0]
                    
                    delay = model.NewIntVar(0, horizon, f"{lot}_delay_b{batch_idx}")
                    model.Add(delay >= batch_tasks[(lot, last_step)]["end"] - due_min)
                    model.Add(delay >= 0)
                    delay_vars.append(delay * job["Priority"])
            
            if delay_vars:
                model.Minimize(sum(delay_vars) * 1000 + batch_makespan)
            else:
                model.Minimize(batch_makespan)

        elif OBJECTIVE_TYPE == "total_completion_time":
            completion_times = []
            for job in current_batch:
                last_step = job["Operations"][-1][0]
                completion_times.append(batch_tasks[(job["LotId"], last_step)]["end"])
            model.Minimize(sum(completion_times))

        else: # makespan
            model.Minimize(batch_makespan)

    # 7. Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = int(os.getenv('SOLVER_MAX_TIME_IN_SECONDS', 30))
    solver.parameters.num_search_workers = int(os.getenv('SOLVER_NUM_SEARCH_WORKERS', 8))
    solver.parameters.log_search_progress = os.getenv('SOLVER_LOG_SEARCH_PROGRESS', 'false').lower() == 'true'
    #solver.parameters.relative_gap_limit = 0.15

    batch_solve_start = datetime.now()
    status = solver.Solve(model)
    batch_solve_end = datetime.now()
    batch_duration = batch_solve_end - batch_solve_start

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print(f"Batch {batch_idx + 1} solved: {solver.StatusName(status)} (Time: {batch_duration.total_seconds():.2f}s)")
        sys.stdout.flush()
        for job in current_batch:
            lot = job["LotId"]
            lot_ops = {}
            for step, group, dur in job["Operations"]:
                t = batch_tasks[(lot, step)]
                st_min = solver.Value(t["start"])
                et_min = solver.Value(t["end"])
                
                if t["status"] in ["Completed", "WIP", "Frozen"]:
                    m_name = t["machine"]
                    # Get actual datetimes for output
                    if t["status"] == "Completed":
                        st_dt = job["CompletedOps"][step]["start_time"]
                        et_dt = job["CompletedOps"][step]["end_time"]
                    elif t["status"] == "WIP":
                        st_dt = job["WIPOps"][step]["start_time"]
                        et_dt = job["WIPOps"][step]["end_time"]
                    else: # Frozen
                        st_dt = job["FrozenOps"][step]["start_time"]
                        et_dt = job["FrozenOps"][step]["end_time"]
                else:
                    idx = solver.Value(t["machine_choice"])
                    m_name = MACHINE_GROUPS[group][idx]
                    st_dt = SCHEDULE_START + timedelta(minutes=st_min)
                    et_dt = SCHEDULE_START + timedelta(minutes=et_min)

                lot_ops[step] = {'start_time': st_dt, 'end_time': et_dt, 'machine': m_name}
                total_solved_tasks[(lot, step)] = {'start_min': st_min, 'end_min': et_min, 'machine': m_name}
                all_tasks_info[(lot, step)] = t
            final_lot_results[lot] = lot_ops
    else:
        print(f"Batch {batch_idx + 1} failed or no solution: {solver.StatusName(status)} (Time: {batch_duration.total_seconds():.2f}s)")
        sys.stdout.flush()

print(f"\n>>> All batches solved! (100% Progress)")
sys.stdout.flush()

# =====================================================
# Database Update & Results Export
# =====================================================
# We need a status map for update_plan_times
all_tasks_status = {k: v['status'] for k, v in all_tasks_info.items()}
update_plan_times(final_lot_results, plan_id, all_tasks_status)
calc_end_time = datetime.now()

# Generate JSON result files
plan_result_dir = "plan_result"
os.makedirs(plan_result_dir, exist_ok=True)

# 1. LotStepResult.json
lot_step_results = []
for lot_id, operations in final_lot_results.items():
    job_info = next(j for j in jobs_data if j["LotId"] == lot_id)
    for step, res in operations.items():
        task_status = all_tasks_info[(lot_id, step)]["status"]
        booking = 0
        if task_status in ["Completed", "Frozen"]: booking = 2
        elif task_status == "WIP": booking = 1
        elif task_status == "Normal":
            booking = job_info.get("NewScheduleType", {}).get(step, 0)
        
        lot_step_results.append({
            "LotId": lot_id, "Product": "", "Priority": job_info["Priority"],
            "StepIdx": next(i for i, op in enumerate(job_info["Operations"]) if op[0] == step) + 1,
            "Step": step, "Machine": res['machine'],
            "Start": res['start_time'].strftime("%Y-%m-%dT%H:%M:%S"),
            "End": res['end_time'].strftime("%Y-%m-%dT%H:%M:%S"),
            "Booking": booking
        })
with open(os.path.join(plan_result_dir, "LotStepResult.json"), 'w', encoding='utf-8') as f:
    json.dump(lot_step_results, f, indent=4, ensure_ascii=False)

# 2. LotPlanResult.json
lot_plan_results = []
for job in jobs_data:
    lot_id = job["LotId"]
    if lot_id in final_lot_results:
        last_step = job["Operations"][-1][0]
        plan_date = final_lot_results[lot_id][last_step]["end_time"]
        due_date = datetime.fromisoformat(job["DueDate"]) if job["DueDate"] else plan_date
        diff = plan_date - due_date
        delay_str = f"{diff.days}:{diff.seconds//3600:02d}" if diff.total_seconds() > 0 else f"-{abs(diff).days}:{abs(diff).seconds//3600:02d}"
        lot_plan_results.append({
            "Lot": lot_id, "Product": "", "Priority": job["Priority"], "DueDate": job["DueDate"],
            "PlanFinishDate": plan_date.strftime("%Y-%m-%dT%H:%M:%S"), "ActualFinishDate": job["ActualFinishDate"],
            "delay time": delay_str
        })
stats = {
    "optimization_type": "incremental_scheduling", "batch_count": len(jobs_data),
    "calculation_duration": str(calc_end_time - calc_start_time),
    "calculation_end": calc_end_time.strftime("%Y-%m-%dT%H:%M:%S")
}
with open(os.path.join(plan_result_dir, "LotPlanResult.json"), 'w', encoding='utf-8') as f:
    json.dump({"statistics": stats, "lot_results": lot_plan_results}, f, indent=4, ensure_ascii=False)

# 3. machineTaskSegment.json
task_segments = []
machine_map = {}
for r in lot_step_results:
    m = r["Machine"]
    if m not in machine_map: machine_map[m] = []
    machine_map[m].append(r)

for m_id in sorted(machine_map.keys()):
    task_segments.append({"id": m_id, "text": m_id, "parent": None, "render": "split"})
    if m_id in machine_unavailable:
        for p in machine_unavailable[m_id]:
            task_segments.append({
                "id": f"{m_id}_u_{p['Id']}", "text": f"{p['PeriodType']}: {p['Reason']}",
                "parent": m_id, "start_date": p["StartTime"].strftime("%Y-%m-%dT%H:%M:%S"),
                "end_date": p["EndTime"].strftime("%Y-%m-%dT%H:%M:%S"), "Booking": -1, "color": BookingColorMap.get_color(-1)
            })
    for r in machine_map[m_id]:
        task_segments.append({
            "id": f"{r['Machine']}_{r['LotId']}_{r['Step']}", "text": f"{r['LotId']} {r['Step']}",
            "parent": r["Machine"], "start_date": r["Start"], "end_date": r["End"],
            "Booking": r["Booking"], "color": BookingColorMap.get_color(r["Booking"])
        })
with open(os.path.join(plan_result_dir, "machineTaskSegment.json"), 'w', encoding='utf-8') as f:
    json.dump(task_segments, f, indent=4, ensure_ascii=False)

# 4. Save to DynamicSchedulingJob using Stored Procedure
try:
    with open('plan_result/LotPlanRaw.json', 'r', encoding='utf-8') as f: raw_j = f.read()
    with open('plan_result/LotPlanResult.json', 'r', encoding='utf-8') as f: res_j = f.read()
    with open('plan_result/LotStepResult.json', 'r', encoding='utf-8') as f: step_j = f.read()
    with open('plan_result/machineTaskSegment.json', 'r', encoding='utf-8') as f: seg_j = f.read()

    conn = mysql.connector.connect(**db_config); cursor = conn.cursor()
    
    # Call Stored Procedure
    schedule_id = f"SCH_INC_{int(datetime.now().timestamp())}"
    plan_summary = f"Incremental Schedule - {len(jobs_data)} lots"
    
    save_start = datetime.now()
    cursor.callproc('sp_SaveDynamicSchedulingJob', (
        schedule_id,
        raw_j,
        "SYSTEM",
        plan_summary,
        res_j,
        step_j,
        seg_j
    ))
    save_end = datetime.now()
    
    conn.commit(); cursor.close(); conn.close()
    print(f"Saved results to DynamicSchedulingJob (via SP) - Time: {save_end - save_start}")
    sys.stdout.flush()
except Exception as e:
    print(f"Error saving job: {e}")
    sys.stdout.flush()

# Calculate and save Utilization metrics
calculate_and_save_utilization(final_lot_results, plan_id, MACHINE_GROUPS)

print(f"Total calculation duration: {calc_end_time - calc_start_time}")
print("\nScheduling Complete.")
sys.stdout.flush()
