# 导入所需库，定义护士数量、轮班次数、天数
from ortools.sat.python import cp_model
import datetime
import plotly.figure_factory as ff


num_nurses = 4
num_shifts = 3
num_days = 3
all_nurses = range(num_nurses)
all_shifts = range(num_shifts)
all_days = range(num_days)

# 创建模型，创建Bool类型变量数组(n, d, s)-->（护士编号，哪一天，哪一个轮班），定义了针对护士的轮班分配。
# 如果将 shift s 分配给 d 天的护士 n，shifts[(n, d, s)] 的值为 1，否则为 0。
model = cp_model.CpModel()
shifts = {}
for n in all_nurses:
    for d in all_days:
        for s in all_shifts:
            shifts[(n, d, s)] = model.NewBoolVar('shift_n%id%is%i' % (n, d, s))

# 确保每一天的每一个轮班只有一个护士
for d in all_days:
    for s in all_shifts:
        model.AddExactlyOne(shifts[(n, d, s)] for n in all_nurses)

# 确保每一天每名护士最多轮班一次。
for n in all_nurses:
    for d in all_days:
        model.AddAtMostOne(shifts[(n, d, s)] for s in all_shifts)

# 尽量分配均匀，设定每个护士应该上的最小轮班次数和最大轮班次数。
min_shifts_per_nurse = (num_shifts * num_days) // num_nurses  # num_nurses
if num_shifts * num_days % num_nurses == 0:
    max_shifts_per_nurse = min_shifts_per_nurse
else:
    max_shifts_per_nurse = min_shifts_per_nurse + 1

# 设定每个护士上的最小轮班数为2，最大轮班数为3。
for n in all_nurses:
    shifts_worked = []
    for d in all_days:
        for s in all_shifts:
            shifts_worked.append(shifts[(n, d, s)])
    model.Add(min_shifts_per_nurse <= sum(shifts_worked))
    model.Add(sum(shifts_worked) <= max_shifts_per_nurse)

solver = cp_model.CpSolver()
solver.parameters.linearization_level = 0
# Enumerate all solutions.
solver.parameters.enumerate_all_solutions = True

# 在求解器上注册一个回调，系统会在每个解决方案中调用该回调函数。
class NursesPartialSolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""

    def __init__(self, shifts, num_nurses, num_days, num_shifts, limit):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._shifts = shifts
        self._num_nurses = num_nurses
        self._num_days = num_days
        self._num_shifts = num_shifts
        self._solution_count = 0
        self._solution_limit = limit

    def on_solution_callback(self):
        self._solution_count += 1
        print('Solution %i' % self._solution_count)
        for d in range(self._num_days):
            print('Day %i' % d)
            for n in range(self._num_nurses):
                is_working = False
                for s in range(self._num_shifts):
                    if self.Value(self._shifts[(n, d, s)]):
                        is_working = True
                        print('  Nurse %i works shift %i' % (n, s))
                if not is_working:
                    print('  Nurse {} does not work'.format(n))
        if self._solution_count >= self._solution_limit:
            print('Stop search after %i solutions' % self._solution_limit)
            self.StopSearch()

    def solution_count(self):
        return self._solution_count

# Display the first five solutions.
solution_limit = 5
solution_printer = NursesPartialSolutionPrinter(shifts, num_nurses,
                                                 num_days, num_shifts,
                                                 solution_limit)

# 调用求解器，并显示前五个解决方案
solver.Solve(model, solution_printer)
