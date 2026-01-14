import json
import os
import sys
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional, Any
from ortools.sat.python import cp_model
import mysql.connector
from dotenv import load_dotenv
from flask import Flask, jsonify, request

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

    def __init__(self, optimization_type: int = 1, alpha: float = 0.5, beta: float = 0.5):
        """
        初始化排程器
        :param optimization_type: 優化類型 (1: 交期優先, 2: 優先權優先, 3: 多目標優化, 4: 準時交貨優先)
        :param alpha: 多目標優化中加權完成時間的權重
        :param beta: 多目標優化中延遲的權重
        """
        self.optimization_type = optimization_type
        self.alpha = alpha
        self.beta = beta
        self.schedule_id: Optional[str] = None

        self.file_new_lot_plan = r"C:\Data\APS\lot_Plan\lot_Plan.json"
        self.file_lot_step_result_new = r"C:\Data\APS\Lot_Plan_result\LotStepResult.json"
        self.file_lot_plan_result = r"C:\Data\APS\Lot_Plan_result\LotPlanResult.json"
        self.file_schedule_log = r"C:\Data\APS\ScheduleLog\SheduleLog.json"

        # 設定 PlanResult 目錄
        self.plan_result_dir = os.path.join("wwwroot", "PlanResult", str(self.optimization_type))
        os.makedirs(self.plan_result_dir, exist_ok=True)

        # 確保目錄存在
        for f in [self.file_new_lot_plan, self.file_lot_step_result_new, self.file_lot_plan_result, self.file_schedule_log]:
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
        load_dotenv()
        log_str = ["New Schedule"]

        # 讀取資料
        schedule_logs = self.load_json(self.file_schedule_log, [])
        new_log = {
            "Logid": datetime.now().strftime("%Y%m%d%H%M%S%f"),
            "Start": datetime.now().isoformat(),
            "LogType": "New Schedule"
        }

        lots = self.load_json(self.file_new_lot_plan, [])

        # 初始化回傳結果
        result_summary = {
            "optimization_type": self.optimization_type,
            "objective_desc": self.get_objective_description(),
            "has_solution": False,
            "earliest_start": None,
            "latest_end": None,
            "duration_str": "0:00:00"
        }

        model = cp_model.CpModel()
        all_tasks = []
        machine_to_intervals = {}

        # 變數範圍設定為 30 天 (分鐘)
        horizon = 24 * 60 * 30

        # 建立新排程任務
        for lot in lots:
            prev_end = None
            for op in lot["Operations"]:
                machines = self.MACHINE_GROUPS[op["MachineGroup"]]
                duration_min = int(op["DurationMinutes"])

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



        # 設定目標函數
        self.set_objective_function(model, lots, all_tasks, horizon)

        # 求解
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = int(os.getenv('SOLVER_MAX_TIME_IN_SECONDS', '60'))
        solver.parameters.num_search_workers = int(os.getenv('SOLVER_NUM_SEARCH_WORKERS', '12'))
        solver.parameters.random_seed = int(os.getenv('SOLVER_RANDOM_SEED', '42'))
        solver.parameters.log_search_progress = os.getenv('SOLVER_LOG_SEARCH_PROGRESS', 'false').lower() == 'true'
        solver.parameters.cp_model_presolve = os.getenv('SOLVER_CP_MODEL_PRESOLVE', 'true').lower() == 'true'
        solver.parameters.linearization_level = int(os.getenv('SOLVER_LINEARIZATION_LEVEL', '2'))

        # 記錄計算開始時間
        calc_start_time = datetime.now()
        status = solver.Solve(model)
        calc_end_time = datetime.now()

        results_new = []
        earliest_start = None
        latest_end = None
        duration_str = "0:00:00"
        has_solution = False

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            has_solution = True
            result_summary["has_solution"] = True
            print("Optimal" if status == cp_model.OPTIMAL else "Feasible")

            # 顯示計算資訊
            calc_total_time = calc_end_time - calc_start_time
            print(f"計算起訖時間: {calc_start_time.isoformat()} ~ {calc_end_time.isoformat()}   計算總時間: {calc_total_time}")
            print(f"計算批數: {len(lots)}")

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
                total_duration = latest_end - earliest_start
                days = total_duration.days
                hours = total_duration.seconds // 3600
                minutes = (total_duration.seconds % 3600) // 60
                duration_str = f"{days}:{hours:02d}:{minutes:02d}"
                result_summary["earliest_start"] = earliest_start
                result_summary["latest_end"] = latest_end
                result_summary["duration_str"] = duration_str
                print(f"最早投入時間: {earliest_start.isoformat()}   最後一批產出時間: {latest_end.isoformat()}   總時間: {duration_str}")
            else:
                print("無結果")
        else:
            print("❌ 無可行解")
            has_solution = False

        # 儲存結果
        self.save_json(self.file_lot_step_result_new, results_new)
        # 同時儲存到 PlanResult 目錄
        new_path = os.path.join(self.plan_result_dir, "LotStepResult.json")
        self.save_json(new_path, results_new)

        # 產生 Lot_Plan_Result
        lot_plan_results = []
        if has_solution:
            for lot in lots:
                # 找到該 lot 的所有任務
                lot_tasks = [r for r in results_new if r["LotId"] == lot["LotId"]]
                if lot_tasks:
                    # 找到最後一個步驟的 End 時間
                    last_task = max(lot_tasks, key=lambda x: x["StepIdx"])
                    plan_date = last_task["End"]
                    due_date_str = lot["DueDate"]
                    due_date = datetime.fromisoformat(due_date_str)
                    plan_datetime = datetime.fromisoformat(plan_date)
                    delay_timedelta = plan_datetime - due_date
                    total_seconds = delay_timedelta.total_seconds()
                    if total_seconds == 0:
                        delay_time = "0:00"
                    elif total_seconds > 0:
                        # 延遲的情況
                        days = delay_timedelta.days
                        hours = delay_timedelta.seconds // 3600
                        delay_time = f"{days}:{hours:02d}"
                    else:
                        # 提早的情況，使用負數
                        abs_timedelta = abs(delay_timedelta)
                        days = abs_timedelta.days
                        hours = abs_timedelta.seconds // 3600
                        delay_time = f"-{days}:{hours:02d}"
                    lot_plan_results.append({
                        "Lot": lot["LotId"],
                        "Product": lot["Product"],
                        "Priority": lot["Priority"],
                        "Due Date": due_date_str,
                        "Plan Date": plan_date,
                        "delay time": delay_time
                    })

        # 計算統計資訊
        stats = self.calculate_statistics(lot_plan_results, calc_start_time, calc_end_time, earliest_start, latest_end, duration_str)

        # 將統計資訊加入結果
        result_with_stats = {
            "statistics": stats,
            "lot_results": lot_plan_results
        }

        # 儲存 Lot_Plan_Result
        self.save_json(self.file_lot_plan_result, result_with_stats)
        # 同時儲存到 PlanResult 目錄
        new_path = os.path.join(self.plan_result_dir, "LotPlanResult.json")
        self.save_json(new_path, result_with_stats)

        # 計算機台群組利用率
        top5_utilizations = self.calculate_machine_group_utilization(results_new) if has_solution else []

        # 這裡簡化處理，直接印出結果
        #for r in results_new:
            #print(f"{r['LotId']} {r['Step']}: {r['Start']} ~ {r['End']} @ {r['Machine']}")

        if has_solution:
            # 產生甘特圖資料
            gantt_dir = r"C:\Data\APS\Gantt"
            os.makedirs(gantt_dir, exist_ok=True)
            task_segments = self.generate_gantt_segments(results_new, GanttType.NEW, os.path.join(gantt_dir, "machineTaskSegment.json"))
            # 同時儲存到 PlanResult 目錄
            new_gantt_dir = os.path.join(self.plan_result_dir, "Gantt")
            os.makedirs(new_gantt_dir, exist_ok=True)
            task_segments_new = self.generate_gantt_segments(results_new, GanttType.NEW, os.path.join(new_gantt_dir, "machineTaskSegment.json"))
        else:
            task_segments_new = []

        # 更新 Log
        new_log["Remark"] = "Plan finished"
        new_log["RemarkData"] = "\n".join(log_str)
        new_log["End"] = datetime.now().isoformat()
        schedule_logs.append(new_log)
        self.save_json(self.file_schedule_log, schedule_logs)
        # 同時儲存到 PlanResult 目錄
        new_path = os.path.join(self.plan_result_dir, "SheduleLog.json")
        self.save_json(new_path, schedule_logs)

        # 插入資料到 MySQL
        if not all([os.getenv('MYSQL_HOST'), os.getenv('MYSQL_PORT'), os.getenv('MYSQL_USER'), os.getenv('MYSQL_PASSWORD'), os.getenv('MYSQL_DATABASE')]):
            print("MySQL 環境變數未設定")
            return result_summary
        try:
            conn = mysql.connector.connect(
                host=os.getenv('MYSQL_HOST'),
                port=int(os.getenv('MYSQL_PORT')),
                user=os.getenv('MYSQL_USER'),
                password=os.getenv('MYSQL_PASSWORD'),
                database=os.getenv('MYSQL_DATABASE')
            )
            cursor = conn.cursor()
            schedule_id = self.schedule_id if self.schedule_id else datetime.now().strftime("%Y%m%d%H%M")
            optimization_type = self.optimization_type
            lot_step_result = json.dumps(results_new, ensure_ascii=False)
            lot_plan_result = json.dumps(result_with_stats, ensure_ascii=False)
            machine_task_segment = json.dumps(task_segments_new, ensure_ascii=False)
            top5_machine_group_utilizations = json.dumps(top5_utilizations, ensure_ascii=False)
            schedule_result = "PASS" if has_solution else "❌ 無可行解"
            schedule_time_span = f"總時間: {duration_str}" if has_solution else "❌ 無可行解"
            sql = "INSERT INTO PlanResult (ScheduleId, optimization_type, LotStepResult, LotPlanResult, machineTaskSegment, Top5MachineGroupUtilizations, ScheduleResult, ScheduleTimeSpan) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (schedule_id, optimization_type, lot_step_result, lot_plan_result, machine_task_segment, top5_machine_group_utilizations, schedule_result, schedule_time_span))

            conn.commit()
            print("資料已插入 MySQL")
        except mysql.connector.Error as err:
            print(f"MySQL 錯誤: {err}")
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()

        return result_summary



    def generate_gantt_segments(self, results: List[Dict], gantt_type: GanttType, output_path: str) -> List[Dict]:
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
        return task_segments

    def calculate_statistics(self, lot_plan_results: List[Dict], calc_start_time: datetime, calc_end_time: datetime,
                           earliest_start: Optional[datetime], latest_end: Optional[datetime], duration_str: str) -> Dict:
        """
        計算統計資訊
        """
        # 計算延遲狀態統計
        early_count = 0
        on_time_count = 0
        minor_delay_count = 0
        major_delay_count = 0

        for result in lot_plan_results:
            delay_str = result["delay time"]
            if delay_str == "0:00" or delay_str == "-0:00":
                on_time_count += 1
            elif delay_str.startswith('-'):
                early_count += 1
            else:
                # 解析延遲時間
                try:
                    days, hours = delay_str.split(':')
                    total_days = int(days) + int(hours) / 24
                    if total_days <= 2:
                        minor_delay_count += 1
                    else:
                        major_delay_count += 1
                except:
                    major_delay_count += 1  # 解析失敗算重大延遲

        # 計算總時間
        calc_total_time = calc_end_time - calc_start_time

        # 取得優化目標描述
        objective_desc = self.get_objective_description()

        stats = {
            "optimization_type": self.optimization_type,
            "batch_count": len(lot_plan_results),
            "optimization_goal": objective_desc,
            "calculation_start": calc_start_time.isoformat(),
            "calculation_end": calc_end_time.isoformat(),
            "calculation_duration": str(calc_total_time),
            "earliest_input_time": earliest_start.isoformat() if earliest_start else None,
            "latest_output_time": latest_end.isoformat() if latest_end else None,
            "total_schedule_duration": duration_str,
            "early_count": early_count,
            "on_time_count": on_time_count,
            "minor_delay_count": minor_delay_count,
            "major_delay_count": major_delay_count
        }

        return stats

    def get_objective_description(self) -> str:
        """
        取得優化目標的描述
        """
        if self.optimization_type == 1:
            return "交期優先 (最小化總完成時間)"
        elif self.optimization_type == 2:
            return "優先權優先 (最小化加權完成時間)"
        elif self.optimization_type == 3:
            return f"多目標優化 (α={self.alpha}, β={self.beta})"
        elif self.optimization_type == 4:
            return "準時交貨優先 (最小化總延遲時間)"
        else:
            return "未知優化類型"

    def calculate_machine_group_utilization(self, results: List[Dict]) -> List[Dict]:
        if not results:
            print("無結果，無法計算利用率")
            return []

        # 計算實際排程時間視窗：最早投入時間 ~ 最後一批產出時間
        earliest_start = min(datetime.fromisoformat(r["Start"]) for r in results)
        latest_end = max(datetime.fromisoformat(r["End"]) for r in results)
        schedule_window_minutes = (latest_end - earliest_start).total_seconds() / 60

        group_utilizations = {}

        for group, machines in self.MACHINE_GROUPS.items():
            total_available = len(machines) * schedule_window_minutes
            total_scheduled = 0.0

            for r in results:
                if r["Machine"] in machines:
                    start = datetime.fromisoformat(r["Start"])
                    end = datetime.fromisoformat(r["End"])
                    duration = (end - start).total_seconds() / 60  # 分鐘
                    total_scheduled += duration

            utilization = total_scheduled / total_available if total_available > 0 else 0
            group_utilizations[group] = (utilization, total_scheduled, total_available)

        # 排序並列出前5名
        sorted_groups = sorted(group_utilizations.items(), key=lambda x: x[1][0], reverse=True)
        print("=== Top 5 Machine Group Utilizations (based on actual schedule window): ===")
        top5_list = []
        for i, (group, (util, used, capacity)) in enumerate(sorted_groups[:5]):
            top5_list.append({
                "rank": i+1,
                "group": group,
                "utilization": util,
                "used_minutes": used,
                "capacity_minutes": capacity
            })
            line = f"{i+1}. {group} | Utilization: {util:.2%} | Used: {used:.1f} min | Capacity: {capacity:.1f} min"
            print(line)

        return top5_list

    def set_objective_function(self, model: cp_model.CpModel, lots: List[Dict], all_tasks: List[Dict], horizon: int):
        """
        設定目標函數
        :param model: CP模型
        :param lots: Lot列表
        :param all_tasks: 所有任務列表
        :param horizon: 時間範圍
        """
        if self.optimization_type == 1:
            # 1. 交期優先：最小化 makespan (最後一批產出時間)
            makespan = model.NewIntVar(0, horizon, 'makespan')
            for lot in lots:
                lot_tasks = [t for t in all_tasks if t["lot"] == lot]
                last_task = max(lot_tasks, key=lambda x: x["op"]["StepIdx"])
                model.Add(makespan >= last_task["end"])
            model.Minimize(makespan)
            print("優化目標：交期優先 (最小化總完成時間)")

        elif self.optimization_type == 2:
            # 2. 優先權優先：最小化加權完成時間 Σ(Priority_i × completion_time_i)
            weighted_completion = model.NewIntVar(0, horizon * 1000, 'weighted_completion')  # 假設Priority最大1000
            total_weighted = []
            for lot in lots:
                lot_tasks = [t for t in all_tasks if t["lot"] == lot]
                last_task = max(lot_tasks, key=lambda x: x["op"]["StepIdx"])
                priority = lot["Priority"]
                weighted_end = model.NewIntVar(0, horizon * priority, f'weighted_end_{lot["LotId"]}')
                model.Add(weighted_end == last_task["end"] * priority)
                total_weighted.append(weighted_end)

            model.Add(weighted_completion == sum(total_weighted))
            model.Minimize(weighted_completion)
            print("優化目標：優先權優先 (最小化加權完成時間)")

        elif self.optimization_type == 3:
            # 3. 多目標優化：Minimize(α × weighted_completion_time + β × makespan)
            makespan = model.NewIntVar(0, horizon, 'makespan')
            for lot in lots:
                lot_tasks = [t for t in all_tasks if t["lot"] == lot]
                last_task = max(lot_tasks, key=lambda x: x["op"]["StepIdx"])
                model.Add(makespan >= last_task["end"])

            weighted_completion = model.NewIntVar(0, horizon * 1000, 'weighted_completion')
            total_weighted = []
            for lot in lots:
                lot_tasks = [t for t in all_tasks if t["lot"] == lot]
                last_task = max(lot_tasks, key=lambda x: x["op"]["StepIdx"])
                priority = lot["Priority"]
                weighted_end = model.NewIntVar(0, horizon * priority, f'weighted_end_{lot["LotId"]}')
                model.Add(weighted_end == last_task["end"] * priority)
                total_weighted.append(weighted_end)

            model.Add(weighted_completion == sum(total_weighted))

            # 多目標：α × weighted_completion + β × makespan
            # 注意：OR-Tools CP-SAT 僅支援整數係數，因此我們將權重放大 100 倍
            objective = model.NewIntVar(0, horizon * 1000 * 100, 'multi_objective')
            alpha_int = int(self.alpha * 100)
            beta_int = int(self.beta * 100)
            model.Add(objective == alpha_int * weighted_completion + beta_int * makespan)
            model.Minimize(objective)
            print(f"優化目標：多目標優化 (α={self.alpha}, β={self.beta}, 放大係數=100)")

        elif self.optimization_type == 4:
            # 4. 準時交貨優先：最小化總延遲時間 Σ max(0, completion_time - DueDate)
            total_lateness = model.NewIntVar(0, horizon * len(lots), 'total_lateness')
            lateness_terms = []

            for lot in lots:
                lot_tasks = [t for t in all_tasks if t["lot"] == lot]
                last_task = max(lot_tasks, key=lambda x: x["op"]["StepIdx"])

                # 將 DueDate 轉換為相對於 SCHEDULE_START 的分鐘數
                due_date = datetime.fromisoformat(lot["DueDate"])
                due_minutes = int((due_date - self.SCHEDULE_START).total_seconds() / 60)

                # 計算延遲：max(0, completion_time - DueDate)
                lateness = model.NewIntVar(0, horizon, f'lateness_{lot["LotId"]}')
                model.AddMaxEquality(lateness, [last_task["end"] - due_minutes, 0])
                lateness_terms.append(lateness)

            model.Add(total_lateness == sum(lateness_terms))
            model.Minimize(total_lateness)
            print("優化目標：準時交貨優先 (最小化總延遲時間)")

        else:
            raise ValueError(f"無效的優化類型: {self.optimization_type}，請選擇 1, 2, 3 或 4")



if __name__ == "__main__":
    load_dotenv()

    # 記錄程式開始執行時間
    program_start_time = datetime.now()
    schedule_id = program_start_time.strftime("%Y%m%d%H%M")

    # 讀取 MySQL 中的 PlanModel 表
    if not all([os.getenv('MYSQL_HOST'), os.getenv('MYSQL_PORT'), os.getenv('MYSQL_USER'), os.getenv('MYSQL_PASSWORD'), os.getenv('MYSQL_DATABASE')]):
        print("MySQL 環境變數未設定")
        sys.exit(1)

    try:
        conn = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST'),
            port=int(os.getenv('MYSQL_PORT')),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            database=os.getenv('MYSQL_DATABASE')
        )
        cursor = conn.cursor()
        cursor.execute("SELECT SeqNo, `Select` FROM PlanModel WHERE `Select` = 1")
        plan_models = cursor.fetchall()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"MySQL 錯誤: {err}")
        sys.exit(1)

    # 解析命令行參數 (用於多目標優化的權重)
    alpha = 0.5
    beta = 0.5

    if len(sys.argv) > 1:
        try:
            alpha = float(sys.argv[1])
        except ValueError:
            print("錯誤：alpha 必須是浮點數")
            sys.exit(1)

    if len(sys.argv) > 2:
        try:
            beta = float(sys.argv[2])
        except ValueError:
            print("錯誤：beta 必須是浮點數")
            sys.exit(1)

    # 讀取 lots 用於 ScheduleJob
    lots = []
    if os.path.exists(r"C:\Data\APS\lot_Plan\lot_Plan.json"):
        with open(r"C:\Data\APS\lot_Plan\lot_Plan.json", 'r', encoding='utf-8') as f:
            lots = json.load(f)

    # 使用迴圈執行每個選定的優化類型
    executed_types = []
    summaries = []
    for optimization_type, select in plan_models:
        if select == 1:
            seq_no_int = int(optimization_type)
            executed_types.append(seq_no_int)
            print(f"執行優化類型: {seq_no_int}, ScheduleId: {schedule_id}")
            scheduler = SchedulerFullExample(optimization_type=seq_no_int, alpha=alpha, beta=beta)
            # 修改 scheduler 的 schedule_id
            scheduler.schedule_id = schedule_id
            summary = scheduler.run()
            summaries.append(summary)

    # 插入 ScheduleJob 表
    if executed_types:
        def duration_to_minutes(dur_str):
            if dur_str == "0:00:00":
                return 0
            parts = dur_str.split(':')
            days = int(parts[0])
            hours = int(parts[1])
            minutes = int(parts[2])
            return days * 24 * 60 + hours * 60 + minutes

        best_summary = min((s for s in summaries if s["has_solution"]), key=lambda s: duration_to_minutes(s["duration_str"]), default=None)

        plan_summary_lines = []
        for summary in summaries:
            plan_summary_lines.append(f"執行優化類型: {summary['optimization_type']} 優化目標：{summary['objective_desc']}")
            if summary["has_solution"]:
                plan_summary_lines.append(f"最早投入時間: {summary['earliest_start'].isoformat()}   最後一批產出時間: {summary['latest_end'].isoformat()}   總時間: {summary['duration_str']}")
            else:
                plan_summary_lines.append("❌ 無可行解")
            plan_summary_lines.append("============================================================")

        if best_summary:
            plan_summary_lines.append(f"目前最短製造時間 總時間: {best_summary['duration_str']}")
            plan_summary_lines.append(f"採用 優化類型: {best_summary['optimization_type']} 優化目標：{best_summary['objective_desc']}")

        plan_summary = "\n".join(plan_summary_lines)

        try:
            conn = mysql.connector.connect(
                host=os.getenv('MYSQL_HOST'),
                port=int(os.getenv('MYSQL_PORT')),
                user=os.getenv('MYSQL_USER'),
                password=os.getenv('MYSQL_PASSWORD'),
                database=os.getenv('MYSQL_DATABASE')
            )
            cursor = conn.cursor()
            lot_plan_json = json.dumps(lots, ensure_ascii=False)
            create_date = datetime.now().isoformat()
            create_user = 'system'
            sql_schedule_job = "INSERT INTO ScheduleJob (ScheduleId, LotPlan, PlanSummary, CreateDate, CreateUser) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql_schedule_job, (schedule_id, lot_plan_json, plan_summary, create_date, create_user))
            conn.commit()
            print("ScheduleJob 資料已插入 MySQL")
        except mysql.connector.Error as err:
            print(f"MySQL 錯誤: {err}")
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()

    # 如果有 --api 參數，啟動 Flask API
    if len(sys.argv) > 3 and sys.argv[3] == '--api':
        app = Flask(__name__)

        @app.after_request
        def after_request(response):
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
            return response

        @app.route('/get_schedule_jobs')
        def get_schedule_jobs():
            try:
                conn = mysql.connector.connect(
                    host=os.getenv('MYSQL_HOST'),
                    port=int(os.getenv('MYSQL_PORT')),
                    user=os.getenv('MYSQL_USER'),
                    password=os.getenv('MYSQL_PASSWORD'),
                    database=os.getenv('MYSQL_DATABASE')
                )
                cursor = conn.cursor()
                cursor.execute("SELECT ScheduleId, CreateDate, CreateUser, LotPlan, PlanSummary FROM ScheduleJob")
                rows = cursor.fetchall()
                result = []
                for row in rows:
                    result.append({
                        'ScheduleId': row[0],
                        'CreateDate': row[1],
                        'CreateUser': row[2],
                        'LotPlan': row[3],
                        'PlanSummary': row[4]
                    })
                cursor.close()
                conn.close()
                return jsonify(result)
            except mysql.connector.Error as err:
                return jsonify({'error': str(err)}), 500

        @app.route('/get_plan_models')
        def get_plan_models():
            try:
                limit = request.args.get('limit', 10, type=int)
                conn = mysql.connector.connect(
                    host=os.getenv('MYSQL_HOST'),
                    port=int(os.getenv('MYSQL_PORT')),
                    user=os.getenv('MYSQL_USER'),
                    password=os.getenv('MYSQL_PASSWORD'),
                    database=os.getenv('MYSQL_DATABASE')
                )
                cursor = conn.cursor()
                cursor.execute("SELECT SeqNo, `Select`, optimization_type, Name, Description, Remark FROM PlanModel LIMIT %s", (limit,))
                rows = cursor.fetchall()
                result = []
                for row in rows:
                    result.append({
                        'SeqNo': row[0],
                        'Select': row[1],
                        'optimization_type': row[2],
                        'Name': row[3],
                        'Description': row[4],
                        'Remark': row[5]
                    })
                cursor.close()
                conn.close()
                return jsonify(result)
            except mysql.connector.Error as err:
                return jsonify({'error': str(err)}), 500

        @app.route('/get_json/<path:filepath>')
        def get_json(filepath):
            try:
                # 安全檢查，避免訪問不允許的文件
                allowed_paths = ['lot_Plan/Lot_Plan.json']
                if filepath not in allowed_paths:
                    return jsonify({'error': 'Access denied'}), 403
                full_path = os.path.join(r"C:\Data\APS", filepath)
                if os.path.exists(full_path):
                    with open(full_path, 'r', encoding='utf-8') as f:
                        return jsonify(json.load(f))
                else:
                    return jsonify({'error': 'File not found'}), 404
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @app.route('/save_json/<path:filepath>', methods=['POST', 'OPTIONS'])
        def save_json(filepath):
            if request.method == 'OPTIONS':
                response = jsonify({})
                response.headers.add('Access-Control-Allow-Origin', '*')
                response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
                response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
                return response

            try:
                # 安全檢查，只允許保存特定文件
                allowed_files = ['ModelList.json', 'LotPlans.json']
                if filepath not in allowed_files:
                    response = jsonify({'error': 'Access denied'})
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
                    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
                    return response, 403
                data = request.get_json()
                full_path = os.path.join("wwwroot", "vue-app", "wwwroot", "workshop", filepath)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                response = jsonify({'message': 'File saved successfully'})
                response.headers.add('Access-Control-Allow-Origin', '*')
                response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
                response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
                return response
            except Exception as e:
                response = jsonify({'error': str(e)})
                response.headers.add('Access-Control-Allow-Origin', '*')
                response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
                response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
                return response, 500

        app.run(host='0.0.0.0', port=5000)
