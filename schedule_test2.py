import collections
from ortools.sat.python import cp_model
import datetime
import plotly.figure_factory as ff


model = cp_model.CpModel()

# 工序的加工序列
order = {0: [3,1,2,4,6,5],
         1: [2,3,5,6,1,4], 
         2: [3,4,6,1,2,5],
         3: [2,1,3,4,5,6],
         4: [3,2,5,6,1,4],
         5: [2,4,6,1,5,3]}
# 工序在 1~6 机器上的加工时间
process_time = {0: [1,3,6,7,3,6],
         1: [8,5,10,10,10,4], 
         2: [5,4,8,9,1,7],
         3: [5,5,5,3,8,9],
         4: [9,3,5,4,3,1],
         5: [3,3,9,10,4,1]}

# 命名元组：存储变量信息（相当于实例化一道工序）
task_type = collections.namedtuple("task_type", "start end interval")
# 存储所有工序信息
all_tasks = {}
# 将工序信息按可上机器（一台）进行存储
machine_to_intervals = collections.defaultdict(list)

# 时间变量的上界
horizon = sum(p_time for job in process_time for p_time in process_time[job])

for job_id, job in order.items():
    for task_id, machine in enumerate(job):
        duration = process_time[job_id][machine - 1]
        suffix = f"_{job_id}_{task_id}"

        start_var = model.NewIntVar(0, horizon, "start" + suffix)
        end_var = model.NewIntVar(0, horizon, "end" + suffix)
        interval_var = model.NewIntervalVar(
            start=start_var, size=duration, end=end_var, name="interval" + suffix
        )
        all_tasks[job_id, task_id] = task_type(
            start=start_var, end=end_var, interval=interval_var
        )
        machine_to_intervals[machine].append(interval_var)

for machine in machine_to_intervals:
	model.AddNoOverlap(machine_to_intervals[machine])


for job_id, job in order.items():
	for task_id in range(len(job) - 1):
		model.Add(all_tasks[job_id, task_id + 1].start >= all_tasks[job_id, task_id].end)

obj_var = model.NewIntVar(0, horizon, "makespan")
model.AddMaxEquality(obj_var, [all_tasks[index].end for index in all_tasks])
model.Minimize(obj_var)

solver = cp_model.CpSolver()
status = solver.Solve(model)

print(f"Optimal Schedule Length: {solver.ObjectiveValue()}")
print("\nStatistics")
print(f"  - conflicts: {solver.NumConflicts()}")
print(f"  - branches : {solver.NumBranches()}")
print(f"  - wall time: {solver.WallTime()}s")
