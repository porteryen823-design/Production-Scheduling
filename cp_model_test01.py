from ortools.sat.python import cp_model


#- 建立模型
model = cp_model.CpModel()

# 宣告變數

x = model.NewIntVar(0, 10, 'x')
y = model.NewIntVar(0, 10, 'y')

# 加入限制條件
model.Add(x != y)
model.Add(x + y <= 15)

# 設定目標函數
model.Maximize(2 * x + 3 * y)

#建立求解器並求解
solver = cp_model.CpSolver()
status = solver.Solve(model)
if status == cp_model.OPTIMAL:
    print(solver.Value(x), solver.Value(y))