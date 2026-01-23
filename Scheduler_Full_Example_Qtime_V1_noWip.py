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
        "CompletedOps": {
            "STEP1": {
                "machine": "M01-1",
                "start_time": datetime(2026, 1, 18, 6, 0, 0),
                "end_time": datetime(2026, 1, 18, 10, 0, 0),
            },
            "STEP2": {
                "machine": "M02-1",
                "start_time": datetime(2026, 1, 18, 10, 0, 0),
                "end_time": datetime(2026, 1, 18, 13, 0, 0),
            },
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
horizon = sum(op[2] for job in jobs_data for op in job["Operations"])

# machines[submachine] = [intervals...]
machines = {m: [] for g in MACHINE_GROUPS.values() for m in g}

# all_tasks[(lot, step)] = dict
all_tasks = {}

# =====================================================
# 建立 Task（唯一一次）
# =====================================================
for job in jobs_data:
    lot = job["LotId"]
    completed_ops = job.get("CompletedOps", {})

    for step, group, duration in job["Operations"]:
        submachines = MACHINE_GROUPS[group]

        # -------------------------------------------------
        # 已完成作業（Frozen）
        # -------------------------------------------------
        if step in completed_ops:
            info = completed_ops[step]
            start = int((info["start_time"] - SCHEDULE_START).total_seconds() / 60)
            end = int((info["end_time"] - SCHEDULE_START).total_seconds() / 60)

            start_var = model.NewConstant(start)
            end_var = model.NewConstant(end)

            interval = model.NewFixedSizeIntervalVar(
                start, duration, f"{lot}_{step}_fixed"
            )

            machines[info["machine"]].append(interval)

            all_tasks[(lot, step)] = {
                "start": start_var,
                "end": end_var,
                "machine_group": group,
                "machine": info["machine"],
                "intervals": [interval],
                "is_completed": True,
            }
            continue

        # -------------------------------------------------
        # 未完成作業（可排）
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
            "is_completed": False,
        }

# =====================================================
# 工序順序 & Q-time
# =====================================================
for job in jobs_data:
    lot = job["LotId"]
    ops = job["Operations"]

    for i in range(len(ops) - 1):
        s1, _, _ = ops[i]
        s2, _, _ = ops[i + 1]
        model.Add(all_tasks[(lot, s1)]["end"] <= all_tasks[(lot, s2)]["start"])

    # Q-time: STEP3 → STEP4 ≤ 200
    model.Add(
        all_tasks[(lot, "STEP4")]["start"]
        - all_tasks[(lot, "STEP3")]["end"]
        <= 200
    )

# =====================================================
# 機台不可重疊
# =====================================================
for m, intervals in machines.items():
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
    print(f"Status: {solver.StatusName(status)}")

    for job in jobs_data:
        lot = job["LotId"]
        print(f"\nLot {lot}")

        for step, group, dur in job["Operations"]:
            t = all_tasks[(lot, step)]
            st = solver.Value(t["start"])
            et = solver.Value(t["end"])

            if t["is_completed"]:
                machine = t["machine"]
            else:
                idx = solver.Value(t["machine_choice"])
                machine = MACHINE_GROUPS[group][idx]

            print(
                f"  {step} | {machine} | "
                f"{SCHEDULE_START + timedelta(minutes=st)} → "
                f"{SCHEDULE_START + timedelta(minutes=et)}"
            )
else:
    print("No feasible solution")
