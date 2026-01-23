import mysql.connector
import os
import json
import argparse
from ortools.sat.python import cp_model
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 解析命令行參數
parser = argparse.ArgumentParser()
parser.add_argument('--start-time', type=str, default='2026-01-22 14:00:00',
                    help='排程開始時間 (YYYY-MM-DD HH:MM:SS)')
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
OBJECTIVE_TYPE = "weighted_delay"   # "makespan" | "weighted_delay"

class BookingColorMap:
    COLOR_BY_BOOKING = {
        0: "#00BFFF",   # 新排程
        1: "#FFE5B4",   # 已預約 / 進行中作業(WIP)
        2: "#32CD32",   # 已鎖定 /已完成作業(COMPLETED)
        3: "#A9A9A9",   # 已超過現在時間
        1002: "#8A2BE2", # 凍結作業(FROZEN)
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

        # 載入機台不可用時段，只載入 ACTIVE 狀態且在排程期間內的記錄
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

        # 按機台分組
        machine_unavailable = {}
        for period in unavailable_periods:
            machine_id = period['MachineId']
            if machine_id not in machine_unavailable:
                machine_unavailable[machine_id] = []
            machine_unavailable[machine_id].append(period)

        return machine_unavailable

    except mysql.connector.Error as err:
        print(f"Error loading machine unavailable periods: {err}")
        return {}
    except Exception as e:
        print(f"Error loading machine unavailable periods: {e}")
        return {}

def load_jobs_from_database():
    """從資料庫載入 jobs_data"""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # 載入 Lots 資料
        cursor.execute("""
            SELECT LotId, Priority, DueDate
            FROM Lots
            ORDER BY LotId
        """)
        lots_data = cursor.fetchall()

        jobs_data = []

        for lot in lots_data:
            lot_id = lot['LotId']

            # 載入該 Lot 的作業資料
            cursor.execute("""
                SELECT Step, MachineGroup, Duration, Sequence, StepStatus, CheckInTime, CheckOutTime, PlanCheckInTime, PlanCheckOutTime, PlanMachineId
                FROM LotOperations
                WHERE LotId = %s
                ORDER BY Sequence
            """, (lot_id,))

            operations_data = cursor.fetchall()

            # 初始化狀態字典
            completed_ops = {}
            wip_ops = {}
            frozen_ops = {}

            # 根據 StepStatus 判斷作業狀態
            for op in operations_data:
                step = op['Step']
                status = op['StepStatus']
                check_in = op['CheckInTime']
                check_out = op['CheckOutTime']
                plan_check_in = op['PlanCheckInTime']
                plan_check_out = op['PlanCheckOutTime']
                machine = op['PlanMachineId']

                if status == 2: # Completed
                    completed_ops[step] = {
                        "start_time": plan_check_in,  # 使用計劃時間
                        "end_time": plan_check_out,
                        "machine": machine
                    }
                elif status == 1: # WIP
                    # 計算已處理分鐘數 (相對於排程開始時間)
                    elapsed = 0
                    if check_in:
                        elapsed = int((SCHEDULE_START - check_in).total_seconds() / 60)
                    wip_ops[step] = {
                        "start_time": plan_check_in,  # 使用計劃開始時間
                        "end_time": plan_check_out,   # 使用計劃結束時間
                        "elapsed_minutes": max(0, elapsed),
                        "machine": machine
                    }

            # 載入 FrozenOps (如果有的話，仍從獨立表載入以獲取詳細資訊)
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

            # Log completed_ops and wip_ops
            if completed_ops:
                print(f"[Completed] Lot {lot_id}: {list(completed_ops.keys())}")
            if wip_ops:
                print(f"[WIP] Lot {lot_id}: {list(wip_ops.keys())}")

            # 轉換為 jobs_data 格式
            operations = []
            for op in operations_data:
                operations.append((op['Step'], op['MachineGroup'], op['Duration']))

            job = {
                "LotId": lot_id,
                "Priority": lot['Priority'],
                "DueDate": lot['DueDate'].strftime("%Y-%m-%dT%H:%M:%S") if lot['DueDate'] else None,
                "Operations": operations,
                "CompletedOps": completed_ops,
                "WIPOps": wip_ops,
                "FrozenOps": frozen_ops,
            }

            jobs_data.append(job)

        cursor.close()
        conn.close()

        print(f"Loaded {len(jobs_data)} jobs from database")
        return jobs_data

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []

def save_jobs_to_plan_raw(jobs_data):
    """將 jobs_data 儲存到 PlanRaw 表和 JSON 檔案"""
    import time
    import json
    import os

    plan_id = f"PLAN_{int(time.time())}"

    try:
        # 儲存到資料庫
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        raw_data_json = json.dumps(jobs_data, ensure_ascii=False, default=str)

        cursor.execute("""
            INSERT INTO PlanRaw (PlanID, RawData)
            VALUES (%s, %s)
        """, (plan_id, raw_data_json))

        conn.commit()
        cursor.close()
        conn.close()

        print(f"Saved jobs_data to PlanRaw table (PlanID: {plan_id})")

        # 儲存到 JSON 檔案
        os.makedirs('plan_result', exist_ok=True)
        with open('plan_result/LotPlanRaw.json', 'w', encoding='utf-8') as f:
            json.dump(jobs_data, f, ensure_ascii=False, indent=2, default=str)

        print(f"Saved jobs_data to plan_raw/planraw.json")

        return plan_id

    except mysql.connector.Error as err:
        print(f"Error saving PlanRaw: {err}")
        return None
    except Exception as e:
        print(f"Error saving PlanRaw: {e}")
        return None

def update_plan_times(lot_results, plan_id=None):
    """更新計劃時間、機器和歷史記錄到資料庫"""
    conn = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # 使用提供的 PlanID 或生成新的
        if plan_id is None:
            import time
            plan_id = f"PLAN_{int(time.time())}"

        for lot_id, operations in lot_results.items():
            for step, result in operations.items():
                # Only update plan times for Normal (schedulable) operations
                # COMPLETED, WIP, and Frozen operations should preserve their original planned values
                if all_tasks[(lot_id, step)]["status"] != "Normal":
                    continue

                start_time = result['start_time']
                end_time = result['end_time']
                machine = result['machine']

                # 先讀取現有的計劃時間和歷史記錄
                cursor.execute("""
                    SELECT PlanCheckInTime, PlanCheckOutTime, PlanMachineId, PlanHistory
                    FROM LotOperations
                    WHERE LotId = %s AND Step = %s
                """, (lot_id, step))

                current_data = cursor.fetchone()

                # 準備歷史記錄
                history_entry = {
                    "PlanID": plan_id,
                    "PlanCheckInTime": start_time.strftime("%Y-%m-%dT%H:%M:%S") if start_time else None,
                    "PlanCheckOutTime": end_time.strftime("%Y-%m-%dT%H:%M:%S") if end_time else None,
                    "PlanMachineId": machine,
                    "CreatedAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                }

                # 如果有現有的歷史記錄，將其載入
                history_list = []
                if current_data and current_data[3]:  # PlanHistory
                    try:
                        import json
                        history_list = json.loads(current_data[3])
                    except:
                        history_list = []

                # 添加新的計劃到歷史
                history_list.append(history_entry)

                # 更新資料庫
                import json
                history_json = json.dumps(history_list, ensure_ascii=False)

                cursor.execute("""
                    UPDATE LotOperations
                    SET PlanCheckInTime = %s, PlanCheckOutTime = %s, PlanMachineId = %s, PlanHistory = %s
                    WHERE LotId = %s AND Step = %s
                """, (start_time, end_time, machine, history_json, lot_id, step))

        conn.commit()
        cursor.close()
        conn.close()

        print(f"Successfully updated plan times, machines, and history for {len(lot_results)} lots (PlanID: {plan_id})")

    except mysql.connector.Error as err:
        print(f"Database update error: {err}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"Update error: {e}")
        if conn:
            conn.rollback()

# =====================================================
# Job 資料 - 從資料庫載入
# =====================================================
jobs_data = load_jobs_from_database()

if not jobs_data:
    print("Failed to load data from database, program terminated")
    exit(1)

# =====================================================
# 機台不可用時段 - 從資料庫載入
# =====================================================
machine_unavailable = load_machine_unavailable_periods()

# =====================================================
# 儲存原始資料到 PlanRaw 表
# =====================================================
plan_id = save_jobs_to_plan_raw(jobs_data)

if not plan_id:
    print("Failed to save raw data to PlanRaw, program terminated")
    exit(1)

# =====================================================
# Machine Groups
# =====================================================
MACHINE_GROUPS = {
    "M01": ["M01-1", "M01-2", "M01-3"],
    "M02": ["M02-1", "M02-2"],
    "M03": ["M03-1", "M03-2", "M03-3"],
    "M04": ["M04-1", "M04-2", "M04-3"],
    "M05": ["M05-1", "M05-2"],
    "M06": ["M06-1", "M06-2"],
    "M07": ["M07-1", "M07-2"],
    "M08": ["M08-1", "M08-2", "M08-3", "M08-4"],
}

# =====================================================
# OR-Tools Model
# =====================================================
model = cp_model.CpModel()

# horizon
horizon = sum(op[2] for job in jobs_data for op in job["Operations"]) * 2

# machines[submachine] = [intervals...]
machines = {m: [] for g in MACHINE_GROUPS.values() for m in g}

# all_tasks[(lot, step)] = dict
all_tasks = {}

# =====================================================
# 建立 Task（處理四種狀態）
# =====================================================
for job in jobs_data:
    lot = job["LotId"]
    completed_ops = job.get("CompletedOps", {})
    wip_ops = job.get("WIPOps", {})
    frozen_ops = job.get("FrozenOps", {})

    prev_end = 0  # 前一個步驟的結束時間

    for step, group, duration in job["Operations"]:
        submachines = MACHINE_GROUPS[group]

        # -------------------------------------------------
        # 狀態 1: 已完成作業（CompletedOps）
        # -------------------------------------------------
        if step in completed_ops:
            info = completed_ops[step]
            start = int((info["start_time"] - SCHEDULE_START).total_seconds() / 60)
            end = int((info["end_time"] - SCHEDULE_START).total_seconds() / 60)

            # 如果作業在 SCHEDULE_START 之前已經完成，將其時間調整為從 0 開始
            if end <= 0:
                # 作業已經在排程開始之前完成，創建虛擬任務但不添加到機器約束
                start_var = model.NewConstant(0)
                end_var = model.NewConstant(0)

                all_tasks[(lot, step)] = {
                    "start": start_var,
                    "end": end_var,
                    "machine_group": group,
                    "machine": info["machine"],
                    "intervals": [],
                    "status": "Completed",
                }
                prev_end = 0  # 不影響後續作業
                continue

            if start < 0:
                start = 0

            start_var = model.NewConstant(start)
            end_var = model.NewConstant(end)

            interval = model.NewFixedSizeIntervalVar(
                start, end - start, f"{lot}_{step}_completed"
            )

            machines[info["machine"]].append(interval)

            all_tasks[(lot, step)] = {
                "start": start_var,
                "end": end_var,
                "machine_group": group,
                "machine": info["machine"],
                "intervals": [interval],
                "status": "Completed",
            }
            prev_end = end
            continue

        # -------------------------------------------------
        # 狀態 2: 進行中作業（WIPOps）
        # -------------------------------------------------
        if step in wip_ops:
            info = wip_ops[step]
            elapsed = info["elapsed_minutes"]
            remaining = duration - elapsed

            # 開始時間為前一個步驟的結束時間
            start_var = model.NewConstant(prev_end)
            end_var = model.NewConstant(prev_end + remaining)

            interval = model.NewFixedSizeIntervalVar(
                prev_end, remaining, f"{lot}_{step}_wip"
            )

            machines[info["machine"]].append(interval)

            all_tasks[(lot, step)] = {
                "start": start_var,
                "end": end_var,
                "machine_group": group,
                "machine": info["machine"],
                "intervals": [interval],
                "status": "WIP",
                "remaining_minutes": remaining,
            }

            prev_end = prev_end + remaining

            print(f"[WIP] {lot} {step} at {info['machine']}: "
                  f"Processed {elapsed} min, remaining {remaining} min, starts at {prev_end - remaining}")
            continue

        # -------------------------------------------------
        # 狀態 3: 凍結作業（FrozenOps）
        # -------------------------------------------------
        if step in frozen_ops:
            info = frozen_ops[step]
            start = int((info["start_time"] - SCHEDULE_START).total_seconds() / 60)
            end = int((info["end_time"] - SCHEDULE_START).total_seconds() / 60)

            # 如果作業在 SCHEDULE_START 之前已經完成，將其時間調整為從 0 開始
            if end <= 0:
                # 作業已經在排程開始之前完成，創建虛擬任務但不添加到機器約束
                start_var = model.NewConstant(0)
                end_var = model.NewConstant(0)

                all_tasks[(lot, step)] = {
                    "start": start_var,
                    "end": end_var,
                    "machine_group": group,
                    "machine": info["machine"],
                    "intervals": [],
                    "status": "Frozen",
                }
                prev_end = 0  # 不影響後續作業
                continue

            if start < 0:
                start = 0

            start_var = model.NewConstant(start)
            end_var = model.NewConstant(end)

            interval = model.NewFixedSizeIntervalVar(
                start, end - start, f"{lot}_{step}_frozen"
            )

            machines[info["machine"]].append(interval)

            all_tasks[(lot, step)] = {
                "start": start_var,
                "end": end_var,
                "machine_group": group,
                "machine": info["machine"],
                "intervals": [interval],
                "status": "Frozen",
            }

            prev_end = end

            print(f"[Frozen] {lot} {step} at {info['machine']}: "
                  f"{info['start_time']} → {info['end_time']}")
            continue

        # -------------------------------------------------
        # 狀態 4: 正常作業（NormalOps - 可排程）
        # -------------------------------------------------
        start_var = model.NewIntVar(0, horizon, f"{lot}_{step}_start")
        end_var = model.NewIntVar(0, horizon, f"{lot}_{step}_end")
        machine_choice = model.NewIntVar(
            0, len(submachines) - 1, f"{lot}_{step}_machine"
        )

        model.Add(start_var >= prev_end)

        intervals = []
        present = []

        for i, m in enumerate(submachines):
            p = model.NewBoolVar(f"{lot}_{step}_p_{i}")
            itv = model.NewOptionalIntervalVar(
                start_var, duration, end_var, p, f"{lot}_{step}_{m}"
            )
            intervals.append(itv)
            present.append(p)
            machines[m].append(itv)

            model.Add(machine_choice == i).OnlyEnforceIf(p)
            model.Add(machine_choice != i).OnlyEnforceIf(p.Not())

        model.Add(sum(present) == 1)

        all_tasks[(lot, step)] = {
            "start": start_var,
            "end": end_var,
            "machine_group": group,
            "machine_choice": machine_choice,
            "intervals": intervals,
            "status": "Normal",
        }

        prev_end = end_var

# =====================================================
# Q-time 約束
# =====================================================
for job in jobs_data:
    lot = job["LotId"]
    ops = job["Operations"]

    # Q-time 約束: STEP3 → STEP4 ≤ 200
    if ("STEP3" in [s for s, _, _ in ops]) and ("STEP4" in [s for s, _, _ in ops]):
        model.Add(
            all_tasks[(lot, "STEP4")]["start"]
            - all_tasks[(lot, "STEP3")]["end"]
            <= 200
        )

# =====================================================
# 機台不可用時段約束
# =====================================================
for machine_id, unavailable_periods in machine_unavailable.items():
    if machine_id not in machines:
        continue  # 跳過不存在的機台

    for period in unavailable_periods:
        # 計算不可用時段的開始和結束時間（相對於排程開始時間的分鐘數）
        start_minutes = int((period['StartTime'] - SCHEDULE_START).total_seconds() / 60)
        end_minutes = int((period['EndTime'] - SCHEDULE_START).total_seconds() / 60)

        # 只處理在排程期間內的不可用時段
        if end_minutes <= 0 or start_minutes >= horizon:
            continue

        # 調整時間範圍到排程期間內
        start_minutes = max(0, start_minutes)
        end_minutes = min(horizon, end_minutes)

        if start_minutes >= end_minutes:
            continue

        # 建立不可用時段的固定間隔
        duration = end_minutes - start_minutes
        unavailable_interval = model.NewFixedSizeIntervalVar(
            start_minutes, duration,
            f"unavailable_{machine_id}_{period['Id']}"
        )

        # 將不可用時段加入機台的間隔列表
        machines[machine_id].append(unavailable_interval)

        print(f"[Unavailable] {machine_id}: {period['PeriodType']} "
              f"({period['Reason']}) from {start_minutes} min to {end_minutes} min")

# =====================================================
# 機台不可重疊
# =====================================================
for m, intervals in machines.items():
    if intervals:  # 只處理有作業的機台
        model.AddNoOverlap(intervals)

# =====================================================
# Objective
# =====================================================
delay_vars = []

if OBJECTIVE_TYPE == "weighted_delay":
    for job in jobs_data:
        lot = job["LotId"]
        due = datetime.fromisoformat(job["DueDate"])
        due_min = int((due - SCHEDULE_START).total_seconds() / 60)

        delay = model.NewIntVar(0, horizon, f"{lot}_delay")
        model.Add(delay >= all_tasks[(lot, "STEP5")]["end"] - due_min)
        model.Add(delay >= 0)
        delay_vars.append(delay * job["Priority"])

    model.Minimize(sum(delay_vars))

else:
    makespan = model.NewIntVar(0, horizon, "makespan")
    model.AddMaxEquality(
        makespan,
        [all_tasks[(job["LotId"], "STEP5")]["end"] for job in jobs_data],
    )
    model.Minimize(makespan)

# =====================================================
# Solve
# =====================================================
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
calc_start_time = datetime.now()
status = solver.Solve(model)
calc_end_time = datetime.now()

# =====================================================
# Output & Update Database
# =====================================================
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print(f"\n{'='*60}")
    print(f"Solve status: {solver.StatusName(status)}")
    print(f"{'='*60}")

    # 收集結果用於更新資料庫
    lot_results = {}

    for job in jobs_data:
        lot = job["LotId"]
        completed_ops = job.get("CompletedOps", {})
        wip_ops = job.get("WIPOps", {})
        frozen_ops = job.get("FrozenOps", {})
        print(f"\nLot {lot} (Priority: {job['Priority']})")
        print(f"{'─'*60}")

        lot_operations = {}

        for step, group, dur in job["Operations"]:
            t = all_tasks[(lot, step)]
            st = solver.Value(t["start"])
            et = solver.Value(t["end"])

            # 取得機台名稱和時間
            if t["status"] in ["Completed", "WIP", "Frozen"]:
                machine = t["machine"]
                # 使用原始計劃時間
                if t["status"] == "Completed" and step in completed_ops:
                    start_time = completed_ops[step]["start_time"]
                    end_time = completed_ops[step]["end_time"]
                elif t["status"] == "WIP" and step in wip_ops:
                    start_time = wip_ops[step]["start_time"]
                    end_time = wip_ops[step]["end_time"]
                elif t["status"] == "Frozen" and step in frozen_ops:
                    start_time = frozen_ops[step]["start_time"]
                    end_time = frozen_ops[step]["end_time"]
                else:
                    # Fallback: use calculated time
                    start_time = SCHEDULE_START + timedelta(minutes=solver.Value(t["start"]))
                    end_time = SCHEDULE_START + timedelta(minutes=solver.Value(t["end"]))
            else:
                idx = solver.Value(t["machine_choice"])
                machine = MACHINE_GROUPS[group][idx]
                # 格式化時間
                start_time = SCHEDULE_START + timedelta(minutes=st)
                end_time = SCHEDULE_START + timedelta(minutes=et)

            # 儲存結果用於資料庫更新
            lot_operations[step] = {
                'start_time': start_time,
                'end_time': end_time,
                'machine': machine
            }

            status_tag = f"[{t['status']}]"

            print(f"  {step:6} | {machine:6} | {status_tag:12} | "
                  f"{start_time.strftime('%m-%d %H:%M')} → "
                  f"{end_time.strftime('%m-%d %H:%M')} "
                  f"({dur} min)")

        lot_results[lot] = lot_operations

    # 更新資料庫的計劃時間
    update_plan_times(lot_results, plan_id)

    # -------------------------------------------------
    # 產生結果檔案 (LotStepResult, LotPlanResult, machineTaskSegment)
    # -------------------------------------------------
    plan_result_dir = "plan_result"
    os.makedirs(plan_result_dir, exist_ok=True)
    
    # 1. 產生 LotStepResult.json
    lot_step_results = []
    for lot_id, operations in lot_results.items():
        # 找到原始 job 資料以獲取 Priority
        job_info = next((j for j in jobs_data if j["LotId"] == lot_id), None)
        priority = job_info["Priority"] if job_info else 0
        
        for step, result in operations.items():
            # 判斷 Booking 狀態 (這裡簡化處理：Normal 為 0, 其他依狀態給予不同值)
            task_status = all_tasks[(lot_id, step)]["status"]
            booking = 0
            if task_status == "Completed": booking = 2
            elif task_status == "WIP": booking = 1
            elif task_status == "Frozen": booking = 2
            
            lot_step_results.append({
                "LotId": lot_id,
                "Product": "", # DB 版暫無 Product 資訊
                "Priority": priority,
                "StepIdx": next((i for i, op in enumerate(job_info["Operations"]) if op[0] == step), 0) + 1,
                "Step": step,
                "Machine": result['machine'],
                "Start": result['start_time'].strftime("%Y-%m-%dT%H:%M:%S"),
                "End": result['end_time'].strftime("%Y-%m-%dT%H:%M:%S"),
                "Booking": booking
            })
    
    with open(os.path.join(plan_result_dir, "LotStepResult.json"), 'w', encoding='utf-8') as f:
        json.dump(lot_step_results, f, indent=4, ensure_ascii=False)

    # 2. 產生 LotPlanResult.json
    lot_plan_results = []
    for job in jobs_data:
        lot_id = job["LotId"]
        if lot_id in lot_results:
            # 找到最後一個步驟
            last_step_name = job["Operations"][-1][0]
            if last_step_name in lot_results[lot_id]:
                last_task = lot_results[lot_id][last_step_name]
                plan_date = last_task["end_time"]
                due_date = datetime.fromisoformat(job["DueDate"]) if job["DueDate"] else plan_date
                
                delay_timedelta = plan_date - due_date
                total_seconds = delay_timedelta.total_seconds()
                
                if abs(total_seconds) < 60:
                    delay_time = "0:00"
                elif total_seconds > 0:
                    days = delay_timedelta.days
                    hours = delay_timedelta.seconds // 3600
                    delay_time = f"{days}:{hours:02d}"
                else:
                    abs_timedelta = abs(delay_timedelta)
                    days = abs_timedelta.days
                    hours = abs_timedelta.seconds // 3600
                    delay_time = f"-{days}:{hours:02d}"
                
                lot_plan_results.append({
                    "Lot": lot_id,
                    "Product": "",
                    "Priority": job["Priority"],
                    "Due Date": job["DueDate"],
                    "Plan Date": plan_date.strftime("%Y-%m-%dT%H:%M:%S"),
                    "delay time": delay_time
                })

    # 計算統計資訊
    early_count = 0
    on_time_count = 0
    minor_delay_count = 0
    major_delay_count = 0
    for r in lot_plan_results:
        dt = r["delay time"]
        if dt == "0:00" or dt == "-0:00": on_time_count += 1
        elif dt.startswith('-'): early_count += 1
        else:
            try:
                days, hours = dt.split(':')
                if int(days) <= 2: minor_delay_count += 1
                else: major_delay_count += 1
            except: major_delay_count += 1

    earliest_start = min((r['start_time'] for ops in lot_results.values() for r in ops.values()), default=None)
    latest_end = max((r['end_time'] for ops in lot_results.values() for r in ops.values()), default=None)
    duration_str = "0:00:00"
    if earliest_start and latest_end:
        td = latest_end - earliest_start
        duration_str = f"{td.days}:{td.seconds//3600:02d}:{(td.seconds%3600)//60:02d}"

    stats = {
        "optimization_type": OBJECTIVE_TYPE,
        "batch_count": len(jobs_data),
        "calculation_start": calc_start_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "calculation_end": calc_end_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "calculation_duration": str(calc_end_time - calc_start_time),
        "earliest_input_time": earliest_start.strftime("%Y-%m-%dT%H:%M:%S") if earliest_start else None,
        "latest_output_time": latest_end.strftime("%Y-%m-%dT%H:%M:%S") if latest_end else None,
        "total_schedule_duration": duration_str,
        "early_count": early_count,
        "on_time_count": on_time_count,
        "minor_delay_count": minor_delay_count,
        "major_delay_count": major_delay_count
    }
    
    result_with_stats = {"statistics": stats, "lot_results": lot_plan_results}
    with open(os.path.join(plan_result_dir, "LotPlanResult.json"), 'w', encoding='utf-8') as f:
        json.dump(result_with_stats, f, indent=4, ensure_ascii=False)

    # 3. 產生 machineTaskSegment.json
    task_segments = []
    # 按機台分組
    machine_tasks = {}
    for item in lot_step_results:
        m = item["Machine"]
        if m not in machine_tasks: machine_tasks[m] = []
        machine_tasks[m].append(item)

    for m_id in sorted(machine_tasks.keys()):
        # 機台父節點
        task_segments.append({
            "id": m_id, "text": m_id, "parent": None, "render": "split",
            "start_date": None, "end_date": None, "duration": 0, "color": None
        })

        # 加入機台不可用時段
        if m_id in machine_unavailable:
            for period in machine_unavailable[m_id]:
                s_dt = period["StartTime"]
                e_dt = period["EndTime"]
                duration_hrs = (e_dt - s_dt).total_seconds() / 3600

                # 根據 PeriodType 設定顏色
                booking_color = -1  # 預設維修顏色
                if period["PeriodType"] == "BREAK":
                    booking_color = -3  # 休息
                elif period["PeriodType"] == "DOWNTIME":
                    booking_color = -2  # 當機
                elif period["PeriodType"] == "RESERVED":
                    booking_color = -20  # 預留

                task_segments.append({
                    "id": f"{m_id}_unavailable_{period['Id']}",
                    "text": f"{period['PeriodType']}: {period['Reason']}",
                    "parent": m_id,
                    "render": None,
                    "start_date": s_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                    "end_date": e_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                    "duration": duration_hrs,
                    "Booking": booking_color,
                    "color": BookingColorMap.get_color(booking_color)
                })

        # 加入作業任務
        for r in machine_tasks[m_id]:
            s_dt = datetime.fromisoformat(r["Start"])
            e_dt = datetime.fromisoformat(r["End"])
            duration_hrs = (e_dt - s_dt).total_seconds() / 3600
            task_segments.append({
                "id": f"{r['Machine']}_{r['LotId']}_{r['Step']}",
                "text": f"{r['LotId']} {r['Step']}",
                "parent": r["Machine"],
                "render": None,
                "start_date": s_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                "end_date": e_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                "duration": duration_hrs,
                "Booking": r["Booking"],
                "color": BookingColorMap.get_color(r["Booking"])
            })
            
    with open(os.path.join(plan_result_dir, "machineTaskSegment.json"), 'w', encoding='utf-8') as f:
        json.dump(task_segments, f, indent=4, ensure_ascii=False)

    print(f"Result files generated in {plan_result_dir} directory")

    # -------------------------------------------------
    # 儲存結果到 DynamicSchedulingJob 表
    # -------------------------------------------------
    import time
    import uuid
    schedule_id = f"SCH_{int(time.time())}_{str(uuid.uuid4())[:8]}"

    try:
        # 讀讀 JSON 檔案內容
        with open('plan_result/LotPlanRaw.json', 'r', encoding='utf-8') as f:
            lot_plan_raw_data = f.read()

        with open('plan_result/LotPlanResult.json', 'r', encoding='utf-8') as f:
            lot_plan_result_data = f.read()

        with open('plan_result/LotStepResult.json', 'r', encoding='utf-8') as f:
            lot_step_result_data = f.read()

        with open('plan_result/machineTaskSegment.json', 'r', encoding='utf-8') as f:
            machine_task_segment_data = f.read()

        # 連接到資料庫
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # 插入資料到 DynamicSchedulingJob 表
        cursor.execute("""
            INSERT INTO DynamicSchedulingJob
            (ScheduleId, LotPlanRaw, CreateUser, PlanSummary, LotPlanResult, LotStepResult, machineTaskSegment)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            schedule_id,
            lot_plan_raw_data,
            "SYSTEM",  # CreateUser
            f"Auto-generated schedule for {len(jobs_data)} lots, PlanID: {plan_id}",
            lot_plan_result_data,
            lot_step_result_data,
            machine_task_segment_data
        ))

        conn.commit()
        cursor.close()
        conn.close()

        print(f"Successfully saved scheduling results to DynamicSchedulingJob table (ScheduleId: {schedule_id})")

    except mysql.connector.Error as err:
        print(f"Error saving to DynamicSchedulingJob: {err}")
    except Exception as e:
        print(f"Error saving to DynamicSchedulingJob: {e}")

    # Summary
    print(f"\n{'='*60}")
    print("Completion Time vs DueDate")
    print(f"{'='*60}")

    for job in jobs_data:
        lot = job["LotId"]
        due = datetime.fromisoformat(job["DueDate"])
        completion_min = solver.Value(all_tasks[(lot, "STEP5")]["end"])
        completion = SCHEDULE_START + timedelta(minutes=completion_min)

        if completion <= due:
            delta = (due - completion).total_seconds() / (3600 * 24)
            status_str = f"[OK] Early {delta:.1f} days"
        else:
            delta = (completion - due).total_seconds() / (3600 * 24)
            status_str = f"[DELAY] Late {delta:.1f} days"

        print(f"{lot}: Completed {completion.strftime('%m-%d %H:%M')} | "
              f"DueDate {due.strftime('%m-%d %H:%M')} | {status_str}")

    # Makespan
    makespan_min = max(
        solver.Value(all_tasks[(job["LotId"], "STEP5")]["end"])
        for job in jobs_data
    )
    makespan_time = SCHEDULE_START + timedelta(minutes=makespan_min)
    print(f"\nTotal Makespan: {makespan_time.strftime('%Y-%m-%d %H:%M:%S')} "
          f"({makespan_min} minutes)")

else:
    print("No feasible solution")