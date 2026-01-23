from ortools.sat.python import cp_model
from datetime import datetime, timedelta

# =====================================================
# 基本設定
# =====================================================
SCHEDULE_START = datetime(2026, 1, 18, 13, 0, 0)
OBJECTIVE_TYPE = "weighted_delay"   # "makespan" | "weighted_delay"


# =====================================================
# Job 資料
# =====================================================
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
        ],
        # 已完成作業（有 start_time 和 end_time）
        "CompletedOps": {
            "STEP1": {
                "machine": "M01-1",
                "start_time": datetime(2026, 1, 18, 7, 0, 0),
                "end_time": datetime(2026, 1, 18, 11, 0, 0),
            },
        },
        # 進行中作業（有 start_time 和 elapsed_minutes，但沒有 end_time）
        "WIPOps": {
            "STEP2": {
                "machine": "M02-1",
                "start_time": datetime(2026, 1, 18, 11, 0, 0),
                "elapsed_minutes": 60,  # 已處理 60 分鐘，還需 60 分鐘
            },
        },
        # 凍結時間窗（已排程但尚未開始，不可更改）
        "FrozenOps": {
            # 例如: STEP3 已經排定但還沒開始
            # "STEP3": {
            #     "machine": "M03-2",
            #     "start_time": datetime(2026, 1, 18, 14, 0, 0),
            #     "end_time": datetime(2026, 1, 18, 19, 0, 0),
            # },
        },
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

# =====================================================
# Machine Groups
# =====================================================
MACHINE_GROUPS = {
    "M01": ["M01-1", "M01-2", "M01-3"],
    "M02": ["M02-1", "M02-2"],
    "M03": ["M03-1", "M03-2", "M03-3"],
    "M04": ["M04-1", "M04-2", "M04-3"],
    "M05": ["M05-1", "M05-2"],
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

    for step, group, duration in job["Operations"]:
        submachines = MACHINE_GROUPS[group]

        # -------------------------------------------------
        # 狀態 1: 已完成作業（CompletedOps）
        # -------------------------------------------------
        if step in completed_ops:
            info = completed_ops[step]
            start = int((info["start_time"] - SCHEDULE_START).total_seconds() / 60)
            end = int((info["end_time"] - SCHEDULE_START).total_seconds() / 60)

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
            continue

        # -------------------------------------------------
        # 狀態 2: 進行中作業（WIPOps）
        # -------------------------------------------------
        if step in wip_ops:
            info = wip_ops[step]
            actual_start = int((info["start_time"] - SCHEDULE_START).total_seconds() / 60)
            elapsed = info["elapsed_minutes"]
            remaining = duration - elapsed

            # 開始時間固定為實際開始時間
            start_var = model.NewConstant(actual_start)
            
            # 結束時間 = SCHEDULE_START(0) + 剩餘時間
            end_var = model.NewIntVar(0, horizon, f"{lot}_{step}_end_wip")
            model.Add(end_var == remaining)

            # Interval: 從現在(0)持續到完成
            interval = model.NewIntervalVar(
                0, remaining, remaining, f"{lot}_{step}_wip"
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
            
            print(f"[WIP] {lot} {step} 在 {info['machine']}: "
                  f"已處理 {elapsed} 分鐘, 還需 {remaining} 分鐘")
            continue

        # -------------------------------------------------
        # 狀態 3: 凍結作業（FrozenOps）
        # -------------------------------------------------
        if step in frozen_ops:
            info = frozen_ops[step]
            start = int((info["start_time"] - SCHEDULE_START).total_seconds() / 60)
            end = int((info["end_time"] - SCHEDULE_START).total_seconds() / 60)

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
            
            print(f"[Frozen] {lot} {step} 在 {info['machine']}: "
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

# =====================================================
# 工序順序 & Q-time
# =====================================================
for job in jobs_data:
    lot = job["LotId"]
    ops = job["Operations"]

    # 工序順序約束
    for i in range(len(ops) - 1):
        s1, _, _ = ops[i]
        s2, _, _ = ops[i + 1]
        model.Add(all_tasks[(lot, s1)]["end"] <= all_tasks[(lot, s2)]["start"])

    # Q-time 約束: STEP3 → STEP4 ≤ 200
    if ("STEP3" in [s for s, _, _ in ops]) and ("STEP4" in [s for s, _, _ in ops]):
        model.Add(
            all_tasks[(lot, "STEP4")]["start"]
            - all_tasks[(lot, "STEP3")]["end"]
            <= 200
        )

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
status = solver.Solve(model)

# =====================================================
# Output
# =====================================================
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print(f"\n{'='*60}")
    print(f"求解狀態: {solver.StatusName(status)}")
    print(f"{'='*60}")

    for job in jobs_data:
        lot = job["LotId"]
        print(f"\n工單 {lot} (Priority: {job['Priority']})")
        print(f"{'─'*60}")

        for step, group, dur in job["Operations"]:
            t = all_tasks[(lot, step)]
            st = solver.Value(t["start"])
            et = solver.Value(t["end"])

            # 取得機台名稱
            if t["status"] in ["Completed", "WIP", "Frozen"]:
                machine = t["machine"]
            else:
                idx = solver.Value(t["machine_choice"])
                machine = MACHINE_GROUPS[group][idx]

            # 格式化時間
            start_time = SCHEDULE_START + timedelta(minutes=st)
            end_time = SCHEDULE_START + timedelta(minutes=et)

            status_tag = f"[{t['status']}]"
            
            print(f"  {step:6} | {machine:6} | {status_tag:12} | "
                  f"{start_time.strftime('%m-%d %H:%M')} → "
                  f"{end_time.strftime('%m-%d %H:%M')} "
                  f"({dur} min)")

    # Summary
    print(f"\n{'='*60}")
    print("完工時間 vs DueDate")
    print(f"{'='*60}")
    
    for job in jobs_data:
        lot = job["LotId"]
        due = datetime.fromisoformat(job["DueDate"])
        completion_min = solver.Value(all_tasks[(lot, "STEP5")]["end"])
        completion = SCHEDULE_START + timedelta(minutes=completion_min)

        if completion <= due:
            delta = (due - completion).total_seconds() / (3600 * 24)
            status_str = f"✓ 超前 {delta:.1f} 天"
        else:
            delta = (completion - due).total_seconds() / (3600 * 24)
            status_str = f"✗ 延遲 {delta:.1f} 天"

        print(f"{lot}: 完成 {completion.strftime('%m-%d %H:%M')} | "
              f"DueDate {due.strftime('%m-%d %H:%M')} | {status_str}")

    # Makespan
    makespan_min = max(
        solver.Value(all_tasks[(job["LotId"], "STEP5")]["end"]) 
        for job in jobs_data
    )
    makespan_time = SCHEDULE_START + timedelta(minutes=makespan_min)
    print(f"\n總 Makespan: {makespan_time.strftime('%Y-%m-%d %H:%M:%S')} "
          f"({makespan_min} 分鐘)")

else:
    print("無可行解")