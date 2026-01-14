from ortools.sat.python import cp_model
from datetime import datetime, timedelta

def main():
    # 排程開始時間
    schedule_start = datetime(2026, 1, 7, 13, 0, 0)

    model = cp_model.CpModel()
    num_a = 3
    num_b = 2
    num_jobs = num_a + num_b

    # 定義產品流程與加工時間
    process_map = {
        "A": [("S01", 3), ("S02", 3), ("S03", 3), ("S04", 3), ("S05", 1)],
        "B": [("S01", 3), ("S02", 3), ("S04", 3), ("S05", 1)]
    }

    # 機台數設定
    machines_per_station = {
        "S01": 2, "S02": 2, "S03": 2, "S04": 2, "S05": 1
    }

    all_intervals = {}
    job_starts = []
    job_ends = []
    assigned_machines = {}

    for job_id in range(num_jobs):
        product_type = "A" if job_id < num_a else "B"
        flow = process_map[product_type]

        first_start = None
        last_end = None

        for step, (station, duration) in enumerate(flow):
            m = 0 
            
            start = model.NewIntVar(0, 1000, f'start_{job_id}_{station}_{m}')
            end = model.NewIntVar(0, 1000, f'end_{job_id}_{station}_{m}')
            interval = model.NewIntervalVar(start, duration, end, f'interval_{job_id}_{station}_{m}')

            machine_key = f"{station}_{m}"
            if machine_key not in all_intervals:
                all_intervals[machine_key] = []
            all_intervals[machine_key].append(interval)

            if (job_id, station) not in assigned_machines:
                assigned_machines[(job_id, station)] = (m, start, end)

            if step == 0:
                first_start = start
            
            if step > 0:
                model.Add(start >= last_end)
            
            last_end = end
            if step == len(flow) - 1:
                job_ends.append(end)
        
        job_starts.append(first_start)

    for machine_key, intervals in all_intervals.items():
        model.AddNoOverlap(intervals)

    makespan = model.NewIntVar(0, 1000, "makespan")
    model.AddMaxEquality(makespan, job_ends)
    model.Minimize(makespan)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print(f"Optimal Schedule Found! Makespan: {solver.Value(makespan)} hours")

        product_labels = ["A" if i < num_a else "B" for i in range(num_jobs)]

        for i in range(len(job_ends)):
            label = product_labels[i]
            start_offset = solver.Value(job_starts[i])
            end_offset = solver.Value(job_ends[i])
            
            start_time = schedule_start + timedelta(hours=start_offset)
            end_time = schedule_start + timedelta(hours=end_offset)
            
            duration = end_offset - start_offset
            print(f"Lot {i} ({label}): {start_time.strftime('%Y-%m-%d %H:%M')} ~ {end_time.strftime('%Y-%m-%d %H:%M')} Total: {duration}h")

        print("\nEvery Lot Process and Machine Assignment:")
        for i in range(num_jobs):
            label = product_labels[i]
            flow = process_map[label]
            print(f"\nLot{i + 1} ({label})")
            for station, duration in flow:
                if (i, station) in assigned_machines:
                    m_id, s_var, e_var = assigned_machines[(i, station)]
                    s_offset = solver.Value(s_var)
                    e_offset = solver.Value(e_var)
                    
                    s_time = schedule_start + timedelta(hours=s_offset)
                    e_time = schedule_start + timedelta(hours=e_offset)
                    
                    print(f" - {station} use machine {station}-Machine-{m_id + 1}, time: {s_time.strftime('%Y-%m-%d %H:%M')} ~ {e_time.strftime('%Y-%m-%d %H:%M')}")
    else:
        print("No solution found.")

if __name__ == "__main__":
    main()
