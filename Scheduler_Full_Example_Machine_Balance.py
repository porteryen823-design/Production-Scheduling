import json
import os
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional, Any
from ortools.sat.python import cp_model

# --- 資料類別定義 ---

class BookingColorMap:
    COLOR_BY_BOOKING = {
        0: "#00BFFF",   # 新排程
        1: "#FFE5B4",   # 已預約
        2: "#32CD32",   # 已鎖定
        3: "#A9A9A9",   # 已超過現在時間
        -1: "#FF4500",  # 維修
        -2: "#B87333",  # 當機
        -20: "#808080", # 預留
        -21: "#C0C0C0", # 預留
        -22: "#FFFDD0", # 預留
    }

    @staticmethod
    def get_color(booking: int) -> str:
        return BookingColorMap.COLOR_BY_BOOKING.get(booking, "#F0F8FF")

class GanttType(Enum):
    NEW = "New"
    OLD = "Old"
    ALL = "All"

# --- 主程式邏輯 ---

class SchedulerFullExample:
    SCHEDULE_START = datetime(2026, 1, 9, 13, 0, 0)

    MACHINE_GROUPS = {
        "M01": ["M01-1", "M01-2", "M01-3"],
        "M02": ["M02-1", "M02-2"],
        "M03": ["M03-1", "M03-2", "M03-3"],
        "M04": ["M04-1", "M04-2", "M04-3"],
        "M05": ["M05-1", "M05-2"],
        "M06": ["M06-1", "M06-2"],
        "M07": ["M07-1", "M07-2"],
        "M08": ["M08-1", "M08-2", "M08-3", "M08-4"],
        "M09": ["M09-1", "M09-2", "M09-3", "M09-4"],
        "M10": ["M10-1", "M10-2", "M10-3", "M10-4"],
        "M11": ["M11-1", "M11-2", "M11-3", "M11-4"],
        "M12": ["M12-1", "M12-2", "M12-3", "M12-4"],
        "M13": ["M13-1", "M13-2", "M13-3", "M13-4"],
        "M14": ["M14-1", "M14-2", "M14-3", "M14-4"],
        "M15": ["M15-1", "M15-2", "M15-3", "M15-4"],
        "M16": ["M16-1", "M16-2", "M16-3", "M16-4"],
    }

    def __init__(self):
        self.file_new_lot_plan = r"C:\Data\APS\lot_Plan\lot_Plan.json"
        self.file_lot_step_result_new = r"C:\Data\APS\Lot_Plan_result\LotStepResult_New.json"
        self.file_schedule_log = r"C:\Data\APS\ScheduleLog\SheduleLog.json"

        # 確保目錄存在
        for f in [self.file_new_lot_plan, self.file_lot_step_result_new, self.file_schedule_log]:
            os.makedirs(os.path.dirname(f), exist_ok=True)

    def load_json(self, path: str, default: Any) -> Any:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default

    def save_json(self, path: str, data: Any):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)


    def run(self):
        log_str = ["New Schedule with Machine Balance"]

        # 讀取資料
        schedule_logs = self.load_json(self.file_schedule_log, [])
        new_log = {
            "Logid": datetime.now().strftime("%Y%m%d%H%M%S%f"),
            "Start": datetime.now().isoformat(),
            "LogType": "New Schedule with Machine Balance"
        }

        lots = self.load_json(self.file_new_lot_plan, [])

        model = cp_model.CpModel()
        all_tasks = []
        machine_to_intervals = {}

        # 建立新排程任務
        for lot in lots:
            prev_end = None
            for op in lot["Operations"]:
                machines = self.MACHINE_GROUPS[op["MachineGroup"]]
                duration_min = int(op["DurationMinutes"])

                # 變數範圍設定為 30 天 (分鐘)
                horizon = 24 * 60 * 30
                start = model.NewIntVar(0, horizon, f'start_{lot["LotId"]}_{op["Step"]}')
                end = model.NewIntVar(0, horizon, f'end_{lot["LotId"]}_{op["Step"]}')
                machine_idx = model.NewIntVar(0, len(machines) - 1, f'midx_{lot["LotId"]}_{op["Step"]}')

                model.Add(end == start + duration_min)
                if prev_end is not None:
                    model.Add(start >= prev_end)
                prev_end = end

                for m_idx, m_name in enumerate(machines):
                    presence = model.NewBoolVar(f'presence_{m_name}_{lot["LotId"]}_{op["Step"]}')
                    interval = model.NewOptionalIntervalVar(
                        start, model.NewConstant(duration_min), end, presence,
                        f'interval_{m_name}_{lot["LotId"]}_{op["Step"]}'
                    )
                    model.Add(machine_idx == m_idx).OnlyEnforceIf(presence)
                    model.Add(machine_idx != m_idx).OnlyEnforceIf(presence.Not())

                    if m_name not in machine_to_intervals:
                        machine_to_intervals[m_name] = []
                    machine_to_intervals[m_name].append(interval)

                all_tasks.append({
                    "start": start, "end": end, "machine_idx": machine_idx,
                    "lot": lot, "op": op, "machines": machines
                })

        # 加入資源限制
        for machine_name, intervals in machine_to_intervals.items():
            model.AddNoOverlap(intervals)

        # Priority-based 順序限制：高 Priority 的 Lot 先開始第一道工序
        sorted_lots = sorted(lots, key=lambda x: x["Priority"], reverse=True)
        for i in range(len(sorted_lots) - 1):
            lot_a = sorted_lots[i]
            lot_b = sorted_lots[i+1]
            task_a = next(t for t in all_tasks if t["lot"] == lot_a and t["op"]["StepIdx"] == 1)
            task_b = next(t for t in all_tasks if t["lot"] == lot_b and t["op"]["StepIdx"] == 1)
            model.Add(task_a["start"] <= task_b["start"])

        # 計算每個機台的總工作時間
        machine_work_times = {}
        for machine_name, intervals in machine_to_intervals.items():
            work_time = model.NewIntVar(0, horizon, f'work_time_{machine_name}')
            model.Add(work_time == sum(interval.SizeExpr() for interval in intervals))
            machine_work_times[machine_name] = work_time

        # 機台平衡：最小化最大和最小工作時間的差
        min_work = model.NewIntVar(0, horizon, 'min_work')
        max_work = model.NewIntVar(0, horizon, 'max_work')
        balance_penalty = model.NewIntVar(0, horizon, 'balance_penalty')

        if machine_work_times:
            work_times_list = list(machine_work_times.values())
            model.AddMinEquality(min_work, work_times_list)
            model.AddMaxEquality(max_work, work_times_list)
            model.Add(balance_penalty == max_work - min_work)

        # 目標函數：最小化 makespan + 平衡懲罰
        makespan = model.NewIntVar(0, horizon, 'makespan')
        for lot in lots:
            # 取得該 Lot 的最後一道工序
            lot_tasks = [t for t in all_tasks if t["lot"] == lot]
            last_task = max(lot_tasks, key=lambda x: x["op"]["StepIdx"])
            model.Add(makespan >= last_task["end"])

        # 組合目標：主要最小化 makespan，次要最小化機台平衡
        model.Minimize(makespan * 1000 + balance_penalty)

        # 求解
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 60  # 增加到60秒讓求解器有更多時間優化
        solver.parameters.num_search_workers = 12
        solver.parameters.random_seed = 42             # 設定固定隨機種子以獲得穩定結果
        solver.parameters.log_search_progress = False  # 減少日誌輸出以加快速度
        solver.parameters.cp_model_presolve = True     # 啟用預處理
        solver.parameters.linearization_level = 2      # 提高線性化等級

        # 記錄計算開始時間
        calc_start_time = datetime.now()
        status = solver.Solve(model)
        calc_end_time = datetime.now()

        results_new = []
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            print("Optimal" if status == cp_model.OPTIMAL else "Feasible")

            # 顯示計算資訊
            calc_total_time = calc_end_time - calc_start_time
            print(f"計算起訖時間: {calc_start_time.isoformat()} ~ {calc_end_time.isoformat()}")
            print(f"計算總時間: {calc_total_time}")
            print(f"計算批數: {len(lots)}")

            # 顯示機台使用統計
            print("機台使用統計:")
            for machine_name, work_var in machine_work_times.items():
                work_minutes = solver.Value(work_var)
                work_hours = work_minutes / 60
                print(f"  {machine_name}: {work_hours:.1f} 小時")

            if machine_work_times:
                min_work_val = solver.Value(min_work)
                max_work_val = solver.Value(max_work)
                balance_val = solver.Value(balance_penalty)
                print(f"機台平衡度: 最小 {min_work_val/60:.1f} 小時, 最大 {max_work_val/60:.1f} 小時, 差異 {balance_val/60:.1f} 小時")

            # 按開始時間排序輸出
            sorted_tasks = sorted(all_tasks, key=lambda x: solver.Value(x["start"]))
            for task in sorted_tasks:
                s_min = solver.Value(task["start"])
                e_min = solver.Value(task["end"])
                s_time = self.SCHEDULE_START + timedelta(minutes=s_min)
                e_time = self.SCHEDULE_START + timedelta(minutes=e_min)
                m_name = task["machines"][solver.Value(task["machine_idx"])]

                results_new.append({
                    "LotId": task["lot"]["LotId"],
                    "Product": task["lot"]["Product"],
                    "Priority": task["lot"]["Priority"],
                    "StepIdx": task["op"]["StepIdx"],
                    "Step": task["op"]["Step"],
                    "Machine": m_name,
                    "Start": s_time.isoformat(),
                    "End": e_time.isoformat(),
                    "Booking": 0
                })

            # 計算最早投入時間和最後產出時間
            if results_new:
                earliest_start = min(datetime.fromisoformat(r["Start"]) for r in results_new)
                latest_end = max(datetime.fromisoformat(r["End"]) for r in results_new)
                print(f"最早投入時間: {earliest_start.isoformat()}")
                print(f"最後一批產出時間: {latest_end.isoformat()}")
            else:
                print("無結果")
        else:
            print("❌ 無可行解")
            return

        # 儲存結果
        self.save_json(self.file_lot_step_result_new, results_new)

        # 這裡簡化處理，直接印出結果
        #for r in results_new:
            #print(f"{r['LotId']} {r['Step']}: {r['Start']} ~ {r['End']} @ {r['Machine']}")

        # 產生甘特圖資料
        gantt_dir = r"C:\Data\APS\Gantt"
        os.makedirs(gantt_dir, exist_ok=True)
        self.generate_gantt_segments(results_new, GanttType.NEW, os.path.join(gantt_dir, "machineTaskSegment_New.json"))

        # 更新 Log
        new_log["Remark"] = "Plan finished with machine balance"
        new_log["RemarkData"] = "\n".join(log_str)
        new_log["End"] = datetime.now().isoformat()
        schedule_logs.append(new_log)
        self.save_json(self.file_schedule_log, schedule_logs)




    def generate_gantt_segments(self, results: List[Dict], gantt_type: GanttType, output_path: str):
        if gantt_type == GanttType.NEW:
            filtered = [r for r in results if r["Booking"] == 0]
        elif gantt_type == GanttType.OLD:
            filtered = [r for r in results if r["Booking"] != 0]
        else:
            filtered = results

        task_segments = []
        # 按機台分組
        grouped = {}
        for r in filtered:
            m = r["Machine"]
            if m not in grouped:
                grouped[m] = []
            grouped[m].append(r)

        for machine_id in sorted(grouped.keys()):
            items = grouped[machine_id]
            # 虛擬節點 (機台列)
            task_segments.append({
                "id": machine_id,
                "text": machine_id,
                "parent": None,
                "render": "split",
                "start_date": None,
                "end_date": None,
                "duration": 0,
                "color": None
            })

            for r in items:
                s_dt = datetime.fromisoformat(r["Start"].replace('Z', ''))
                e_dt = datetime.fromisoformat(r["End"].replace('Z', ''))
                duration_hrs = (e_dt - s_dt).total_seconds() / 3600

                task_segments.append({
                    "id": f"{r['Machine']}_{r['LotId']}_{r['Step']}",
                    "text": f"{r['LotId']} {r['Step']}",
                    "parent": r["Machine"],
                    "render": None,
                    "start_date": s_dt.strftime("%Y-%m-%d %H:%M"),
                    "end_date": e_dt.strftime("%Y-%m-%d %H:%M"),
                    "duration": duration_hrs,
                    "Booking": r["Booking"],
                    "color": BookingColorMap.get_color(r["Booking"])
                })

        self.save_json(output_path, task_segments)




if __name__ == "__main__":
    scheduler = SchedulerFullExample()
    scheduler.run()