import sys
import os
import subprocess
import threading
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, cast
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QTextEdit, QListWidget, QLabel,
    QDateTimeEdit, QSpinBox, QGroupBox, QMessageBox, QTableWidget,
    QTableWidgetItem, QLineEdit, QComboBox, QHeaderView
)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, QDateTime, QProcess
from PyQt5.QtGui import QFont, QColor
import mysql.connector
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 資料庫連線設定
db_config = {
    'host': os.getenv('MYSQL_HOST'),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE')
}

class WorkerThread(QThread):
    """用於執行長時間任務的線程"""
    finished = pyqtSignal(object)  # 發送結果訊號
    error = pyqtSignal(str)     # 發送錯誤訊號

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("產線 Plan 管理系統[模擬用/測試用] V1.0")
        self.setGeometry(100, 100, 1000, 700)

        # 建立中央 widget 和佈局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 建立分頁 widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # 載入設定
        self.load_settings()

        # 建立七個分頁
        self.create_tab1()  # 清空測試資料
        self.create_tab2()  # 產生 Lots
        self.create_tab3()  # 模擬時鐘
        self.create_tab4()  # 重新排成
        self.create_tab5()  # Lots 資料
        self.create_tab6()  # LotOperations 資料
        self.create_tab7()  # 自動化測試

    def create_tab1(self):
        """第一個分頁：清空測試資料"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 標題
        title = QLabel("清空測試資料")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)

        # 按鈕
        self.btn_clean_data = QPushButton("執行")
        self.btn_clean_data.clicked.connect(self.clean_test_data)
        layout.addWidget(self.btn_clean_data)

        # 結果顯示區域
        self.text_clean_result = QTextEdit()
        self.text_clean_result.setReadOnly(True)
        self.text_clean_result.setAcceptRichText(True)
        layout.addWidget(self.text_clean_result)

        self.tab_widget.addTab(tab, "清空測試資料")

    def create_tab2(self):
        """第二個分頁：產生 Lots"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 標題
        title = QLabel("產生 Lots")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)

        # 控制區域
        control_layout = QHBoxLayout()
        control_layout.addWidget(QLabel("產生數量:"))
        self.spin_lot_count = QSpinBox()
        self.spin_lot_count.setRange(1, 100)
        self.spin_lot_count.setValue(self.default_spin_lot_count)
        self.spin_lot_count.valueChanged.connect(self.save_settings)
        control_layout.addWidget(self.spin_lot_count)

        self.btn_generate_lots = QPushButton("執行")
        self.btn_generate_lots.clicked.connect(self.generate_lots)
        control_layout.addWidget(self.btn_generate_lots)

        self.btn_show_stats = QPushButton("目前 Lots 資訊")
        self.btn_show_stats.clicked.connect(self.show_current_stats)
        control_layout.addWidget(self.btn_show_stats)

        layout.addLayout(control_layout)

        # 結果顯示區域
        self.text_generate_result = QTextEdit()
        self.text_generate_result.setReadOnly(True)
        # 啟用 HTML 格式支持
        self.text_generate_result.setAcceptRichText(True)
        layout.addWidget(self.text_generate_result)

        # QProcess 相關變數
        self.generate_process: Optional[QProcess] = None

        self.tab_widget.addTab(tab, "產生 Lots")

    def create_tab3(self):
        """第三個分頁：模擬時鐘"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 標題
        title = QLabel("模擬時鐘")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)

        # 控制區域
        control_group = QGroupBox("控制參數")
        control_layout = QVBoxLayout(control_group)

        # 第一行：開始時間和模擬次數
        row1_layout = QHBoxLayout()
        row1_layout.addWidget(QLabel("模擬時鐘開始時間:"))
        self.datetime_start = QDateTimeEdit()
        self.datetime_start.setDateTime(QDateTime.fromString(self.default_datetime_start, "yyyy-MM-dd hh:mm:ss"))
        self.datetime_start.dateTimeChanged.connect(self.save_settings)
        row1_layout.addWidget(self.datetime_start)

        row1_layout.addWidget(QLabel("模擬次數:"))
        self.spin_iterations = QSpinBox()
        self.spin_iterations.setRange(1, 10000)
        self.spin_iterations.setValue(self.default_spin_iterations)
        self.spin_iterations.valueChanged.connect(self.save_settings)
        row1_layout.addWidget(self.spin_iterations)

        control_layout.addLayout(row1_layout)

        # 第二行：timedelta
        row2_layout = QHBoxLayout()
        row2_layout.addWidget(QLabel("時間增量(秒):"))
        self.spin_timedelta = QSpinBox()
        self.spin_timedelta.setRange(1, 3600)
        self.spin_timedelta.setValue(self.default_spin_timedelta)
        self.spin_timedelta.valueChanged.connect(self.save_settings)
        row2_layout.addWidget(self.spin_timedelta)

        # 開始/停止按鈕
        self.btn_start_simulation = QPushButton("開始模擬")
        self.btn_start_simulation.clicked.connect(self.start_simulation)
        row2_layout.addWidget(self.btn_start_simulation)

        self.btn_stop_simulation = QPushButton("停止模擬")
        self.btn_stop_simulation.clicked.connect(self.stop_simulation)
        self.btn_stop_simulation.setEnabled(False)
        row2_layout.addWidget(self.btn_stop_simulation)

        control_layout.addLayout(row2_layout)

        layout.addWidget(control_group)

        # 結果顯示區域
        self.text_simulation_result = QTextEdit()
        self.text_simulation_result.setReadOnly(True)
        self.text_simulation_result.setAcceptRichText(True)
        layout.addWidget(self.text_simulation_result)

        # QProcess 相關變數
        self.simulation_process: Optional[QProcess] = None

        self.tab_widget.addTab(tab, "模擬時鐘")

    def create_tab4(self):
        """第四個分頁：重新排程"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 標題
        title = QLabel("重新排程")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)

        # 控制區域
        control_group = QGroupBox("控制參數")
        control_layout = QVBoxLayout(control_group)

        # 排程開始時間
        row_layout = QHBoxLayout()
        row_layout.addWidget(QLabel("排程開始時間:"))
        self.datetime_reschedule_start = QDateTimeEdit()
        self.datetime_reschedule_start.setDateTime(QDateTime.fromString(self.default_datetime_reschedule_start, "yyyy-MM-dd hh:mm:ss"))
        self.datetime_reschedule_start.dateTimeChanged.connect(self.save_settings)
        row_layout.addWidget(self.datetime_reschedule_start)

        control_layout.addLayout(row_layout)

        layout.addWidget(control_group)

        # 按鈕
        self.btn_reschedule = QPushButton("執行")
        self.btn_reschedule.clicked.connect(self.reschedule)
        layout.addWidget(self.btn_reschedule)

        # 結果顯示區域
        self.text_reschedule_result = QTextEdit()
        self.text_reschedule_result.setReadOnly(True)
        self.text_reschedule_result.setAcceptRichText(True)
        layout.addWidget(self.text_reschedule_result)

        # QProcess 相關變數
        self.reschedule_process: Optional[QProcess] = None

        self.tab_widget.addTab(tab, "重新排程")

    def create_tab5(self):
        """第五個分頁：Lots 資料"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 標題
        title = QLabel("Lots 資料")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)

        # 過濾區域
        filter_group = QGroupBox("過濾條件")
        filter_layout = QHBoxLayout(filter_group)

        filter_layout.addWidget(QLabel("LotId:"))
        self.filter_lot_id = QLineEdit()
        self.filter_lot_id.setPlaceholderText("輸入 LotId")
        self.filter_lot_id.textChanged.connect(self.filter_lots_data)
        filter_layout.addWidget(self.filter_lot_id)

        filter_layout.addWidget(QLabel("Priority:"))
        self.filter_priority = QComboBox()
        self.filter_priority.addItem("全部", "")
        self.filter_priority.addItem("100", "100")
        self.filter_priority.addItem("200", "200")
        self.filter_priority.currentTextChanged.connect(self.filter_lots_data)
        filter_layout.addWidget(self.filter_priority)

        self.btn_refresh_lots = QPushButton("重新載入")
        self.btn_refresh_lots.clicked.connect(self.load_lots_data)
        filter_layout.addWidget(self.btn_refresh_lots)

        layout.addWidget(filter_group)

        # 表格
        self.table_lots = QTableWidget()
        self.table_lots.setAlternatingRowColors(True)
        self.table_lots.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table_lots)

        self.tab_widget.addTab(tab, "Lots")

        # 載入數據
        self.load_lots_data()

    def create_tab6(self):
        """第六個分頁：LotOperations 資料"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 標題
        title = QLabel("LotOperations 資料")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)

        # 過濾區域
        filter_group = QGroupBox("過濾條件")
        filter_layout = QHBoxLayout(filter_group)

        filter_layout.addWidget(QLabel("LotId:"))
        self.filter_op_lot_id = QLineEdit()
        self.filter_op_lot_id.setPlaceholderText("輸入 LotId")
        self.filter_op_lot_id.textChanged.connect(self.filter_operations_data)
        filter_layout.addWidget(self.filter_op_lot_id)

        filter_layout.addWidget(QLabel("Step:"))
        self.filter_step = QLineEdit()
        self.filter_step.setPlaceholderText("輸入 Step")
        self.filter_step.textChanged.connect(self.filter_operations_data)
        filter_layout.addWidget(self.filter_step)

        filter_layout.addWidget(QLabel("狀態:"))
        self.filter_status = QComboBox()
        self.filter_status.addItem("全部", "")
        self.filter_status.addItem("New Add (0)", "0")
        self.filter_status.addItem("WIP (1)", "1")
        self.filter_status.addItem("Completed (2)", "2")
        self.filter_status.currentTextChanged.connect(self.filter_operations_data)
        filter_layout.addWidget(self.filter_status)

        self.btn_refresh_operations = QPushButton("重新載入")
        self.btn_refresh_operations.clicked.connect(self.load_operations_data)
        filter_layout.addWidget(self.btn_refresh_operations)

        layout.addWidget(filter_group)

        # 表格
        self.table_operations = QTableWidget()
        self.table_operations.setAlternatingRowColors(True)
        self.table_operations.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table_operations)

        self.tab_widget.addTab(tab, "LotOperations")

        # 載入數據
        self.load_operations_data()

    def load_lots_data(self):
        """載入 Lots 資料"""
        def run_load_lots():
            try:
                conn = mysql.connector.connect(**db_config)
                cursor = conn.cursor(dictionary=True)

                cursor.execute("""
                    SELECT LotId, Priority, DueDate, LotCreateDate
                    FROM Lots
                    ORDER BY LotId
                """)

                lots_data = cursor.fetchall()
                cursor.close()
                conn.close()

                return lots_data

            except mysql.connector.Error as err:
                return f"資料庫錯誤: {err}"
            except Exception as e:
                return f"錯誤: {e}"

        # 建立線程執行任務
        self.worker = WorkerThread(run_load_lots)
        self.worker.finished.connect(self.on_lots_data_loaded)
        self.worker.error.connect(self.on_lots_data_error)
        self.worker.start()

    def on_lots_data_loaded(self, data):
        if isinstance(data, list):
            self.display_lots_data(data)
        else:
            QMessageBox.warning(self, "錯誤", f"載入 Lots 資料失敗: {data}")

    def on_lots_data_error(self, error):
        QMessageBox.warning(self, "錯誤", f"載入 Lots 資料錯誤: {error}")

    def display_lots_data(self, lots_data, filtered_data=None):
        """顯示 Lots 資料"""
        display_data = filtered_data if filtered_data is not None else lots_data

        self.table_lots.setRowCount(len(display_data))
        self.table_lots.setColumnCount(4)
        self.table_lots.setHorizontalHeaderLabels(["LotId", "Priority", "DueDate", "LotCreateDate"])

        # 設置列寬
        header = self.table_lots.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        for row, lot in enumerate(display_data):
            self.table_lots.setItem(row, 0, QTableWidgetItem(str(lot['LotId'])))
            self.table_lots.setItem(row, 1, QTableWidgetItem(str(lot['Priority'])))
            self.table_lots.setItem(row, 2, QTableWidgetItem(str(lot['DueDate']) if lot['DueDate'] else ""))
            self.table_lots.setItem(row, 3, QTableWidgetItem(str(lot['LotCreateDate']) if lot['LotCreateDate'] else ""))

        # 存儲原始數據用於過濾
        self.lots_data = lots_data

    def filter_lots_data(self):
        """過濾 Lots 資料"""
        if not hasattr(self, 'lots_data'):
            return

        lot_id_filter = self.filter_lot_id.text().strip().lower()
        priority_filter = self.filter_priority.currentData()

        filtered_data = []
        for lot in self.lots_data:
            # LotId 過濾
            if lot_id_filter and lot_id_filter not in str(lot['LotId']).lower():
                continue

            # Priority 過濾
            if priority_filter and str(lot['Priority']) != priority_filter:
                continue

            filtered_data.append(lot)

        self.display_lots_data(self.lots_data, filtered_data)

    def load_operations_data(self):
        """載入 LotOperations 資料"""
        def run_load_operations():
            try:
                conn = mysql.connector.connect(**db_config)
                cursor = conn.cursor(dictionary=True)

                cursor.execute("""
                    SELECT LotId, Step, MachineGroup, Duration, Sequence, StepStatus,
                           CheckInTime, CheckOutTime, PlanMachineId, PlanCheckInTime, PlanCheckOutTime
                    FROM LotOperations
                    ORDER BY LotId, Sequence
                """)

                operations_data = cursor.fetchall()
                cursor.close()
                conn.close()

                return operations_data

            except mysql.connector.Error as err:
                return f"資料庫錯誤: {err}"
            except Exception as e:
                return f"錯誤: {e}"

        # 建立線程執行任務
        self.worker = WorkerThread(run_load_operations)
        self.worker.finished.connect(self.on_operations_data_loaded)
        self.worker.error.connect(self.on_operations_data_error)
        self.worker.start()

    def on_operations_data_loaded(self, data):
        if isinstance(data, list):
            self.display_operations_data(data)
        else:
            QMessageBox.warning(self, "錯誤", f"載入 LotOperations 資料失敗: {data}")

    def on_operations_data_error(self, error):
        QMessageBox.warning(self, "錯誤", f"載入 LotOperations 資料錯誤: {error}")

    def display_operations_data(self, operations_data, filtered_data=None):
        """顯示 LotOperations 資料"""
        display_data = filtered_data if filtered_data is not None else operations_data

        self.table_operations.setRowCount(len(display_data))
        self.table_operations.setColumnCount(11)
        self.table_operations.setHorizontalHeaderLabels([
            "LotId", "Step", "MachineGroup", "Duration", "Sequence", "StepStatus",
            "CheckInTime", "CheckOutTime", "PlanMachineId", "PlanCheckInTime", "PlanCheckOutTime"
        ])

        # 設置列寬
        header = self.table_operations.horizontalHeader()
        for i in range(11):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)

        status_map = {0: "New Add", 1: "WIP", 2: "Completed"}
        status_colors = {
            0: QColor("#E3F2FD"),  # 淺藍色 for New Add
            1: QColor("#FFF3E0"),  # 淺橙色 for WIP
            2: QColor("#E8F5E8")   # 淺綠色 for Completed
        }

        for row, op in enumerate(display_data):
            self.table_operations.setItem(row, 0, QTableWidgetItem(str(op['LotId'])))
            self.table_operations.setItem(row, 1, QTableWidgetItem(str(op['Step'])))
            self.table_operations.setItem(row, 2, QTableWidgetItem(str(op['MachineGroup'])))
            self.table_operations.setItem(row, 3, QTableWidgetItem(str(op['Duration'])))
            self.table_operations.setItem(row, 4, QTableWidgetItem(str(op['Sequence'])))

            # StepStatus 欄位設置顏色
            status_item = QTableWidgetItem(status_map.get(op['StepStatus'], str(op['StepStatus'])))
            status_item.setBackground(status_colors.get(op['StepStatus'], QColor("#FFFFFF")))
            self.table_operations.setItem(row, 5, status_item)

            self.table_operations.setItem(row, 6, QTableWidgetItem(str(op['CheckInTime']) if op['CheckInTime'] else ""))
            self.table_operations.setItem(row, 7, QTableWidgetItem(str(op['CheckOutTime']) if op['CheckOutTime'] else ""))
            self.table_operations.setItem(row, 8, QTableWidgetItem(str(op['PlanMachineId']) if op['PlanMachineId'] else ""))
            self.table_operations.setItem(row, 9, QTableWidgetItem(str(op['PlanCheckInTime']) if op['PlanCheckInTime'] else ""))
            self.table_operations.setItem(row, 10, QTableWidgetItem(str(op['PlanCheckOutTime']) if op['PlanCheckOutTime'] else ""))

        # 存儲原始數據用於過濾
        self.operations_data = operations_data

    def filter_operations_data(self):
        """過濾 LotOperations 資料"""
        if not hasattr(self, 'operations_data'):
            return

        lot_id_filter = self.filter_op_lot_id.text().strip().lower()
        step_filter = self.filter_step.text().strip().lower()
        status_filter = self.filter_status.currentData()

        filtered_data = []
        for op in self.operations_data:
            # LotId 過濾
            if lot_id_filter and lot_id_filter not in str(op['LotId']).lower():
                continue

            # Step 過濾
            if step_filter and step_filter not in str(op['Step']).lower():
                continue

            # Status 過濾
            if status_filter and str(op['StepStatus']) != status_filter:
                continue

            filtered_data.append(op)

        self.display_operations_data(self.operations_data, filtered_data)

    def clean_test_data(self):
        """執行清空測試資料"""
        def run_clean():
            try:
                conn = mysql.connector.connect(**db_config)
                cursor = conn.cursor()

                # 呼叫 stored procedure
                cursor.callproc('sp_clean_lots')

                conn.commit()
                cursor.close()
                conn.close()

                return "測試資料已成功清空"

            except mysql.connector.Error as err:
                return f"資料庫錯誤: {err}"
            except Exception as e:
                return f"錯誤: {e}"

        # 禁用按鈕
        self.btn_clean_data.setEnabled(False)
        self.btn_clean_data.setText("執行中...")

        # 建立線程執行任務
        self.worker = WorkerThread(run_clean)
        self.worker.finished.connect(self.on_clean_finished)
        self.worker.error.connect(self.on_clean_error)
        self.worker.start()

    def on_clean_finished(self, result):
        self.text_clean_result.setHtml(f'<span style="color: #28A745; font-weight: bold;">{result}</span>')
        self.btn_clean_data.setEnabled(True)
        self.btn_clean_data.setText("執行")

    def on_clean_error(self, error):
        self.text_clean_result.setHtml(f'<span style="color: #DC3545; font-weight: bold;">錯誤: {error}</span>')
        self.btn_clean_data.setEnabled(True)
        self.btn_clean_data.setText("執行")

    def generate_lots(self):
        """執行產生 Lots"""
        if self.generate_process is not None:
            return

        # 取得參數
        count = self.spin_lot_count.value()

        # 建構命令
        insert_script_path = os.path.join(os.path.dirname(__file__), '..', 'insert_lot_data.py')
        args = [
            sys.executable,
            '-u',  # 強制無緩衝輸出
            insert_script_path,
            '--count', str(count)
        ]

        # 啟動 QProcess
        self.generate_process = QProcess()
        self.generate_process.readyReadStandardOutput.connect(self.handle_generate_output)
        self.generate_process.readyReadStandardError.connect(self.handle_generate_error)
        self.generate_process.finished.connect(self.on_generate_finished)

        self.generate_process.start(args[0], args[1:])

        # 更新 UI
        self.btn_generate_lots.setEnabled(False)
        self.btn_generate_lots.setText("執行中...")

        self.text_generate_result.clear()
        self.text_generate_result.append(f'<span style="color: #28A745; font-weight: bold;">開始產生 {count} 筆 Lot 資料...</span>')

    def handle_generate_output(self):
        """處理產生 Lots 程式的標準輸出"""
        if self.generate_process is not None:
            output = self.generate_process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
            if output:
                # 美化輸出結果，添加顏色
                colored_output = output.replace("下一個 LotId:", '<span style="color: #2E86AB; font-weight: bold;">📋 下一個 LotId:</span>')
                colored_output = colored_output.replace("DueDate:", '<span style="color: #17A2B8; font-weight: bold;">📅 DueDate:</span>')
                colored_output = colored_output.replace("成功插入 Lot:", '<span style="color: #28A745; font-weight: bold;">✅ 成功插入 Lot:</span>')
                colored_output = colored_output.replace("插入了", '<span style="color: #28A745; font-weight: bold;">📊 插入了</span>')
                colored_output = colored_output.replace("個作業步驟", '<span style="color: #28A745; font-weight: bold;">個作業步驟</span>')
                colored_output = colored_output.replace("總共插入了", '<span style="color: #28A745; font-weight: bold;">總共插入了</span>')

                # 將換行符轉換為 HTML 換行
                html_output = colored_output.replace('\n', '<br>')
                self.text_generate_result.append(html_output)

    def handle_generate_error(self):
        """處理產生 Lots 程式的錯誤輸出"""
        if self.generate_process is not None:
            error = self.generate_process.readAllStandardError().data().decode('utf-8', errors='ignore')
            if error:
                # 將錯誤輸出標示為紅色
                html_error = f'<span style="color: #DC3545;">{error.replace(chr(10), "<br>")}</span>'
                self.text_generate_result.append(html_error)

    def on_generate_finished(self, exit_code, exit_status):
        """產生 Lots 程式完成時的處理"""
        self.generate_process = None
        self.btn_generate_lots.setEnabled(True)
        self.btn_generate_lots.setText("執行")

        if exit_code == 0:
            # 獲取統計資訊並顯示
            stats = self.get_database_stats()
            if stats:
                html_stats = f"""
                <br><span style="color: #6C757D; font-weight: bold; font-size: 14px;">📊 資料庫統計</span><br>
                <span style="color: #2E86AB;">總 Lot 數量: {stats['total_lots']}</span><br>
                <span style="color: #28A745;">[Completed] 記錄數: {stats['completed_count']}</span><br>
                <span style="color: #FFC107;">[WIP] 記錄數: {stats['wip_count']}</span><br>
                <span style="color: #007BFF;">[Normal] 記錄數: {stats['normal_count']}</span><br>
                <span style="color: #6C757D;">[New Add] 記錄數: {stats['new_add_count']}</span>
                """
                self.text_generate_result.append(html_stats)
        else:
            self.text_generate_result.append(f'<span style="color: #DC3545; font-weight: bold;">產生 Lots 異常結束 (代碼: {exit_code})</span>')

    def show_current_stats(self):
        """顯示目前 Lots 統計資訊"""
        def run_show_stats():
            stats = self.get_database_stats()
            if stats:
                html_content = f"""
                <h3 style="color: #2E86AB;">📊 資料庫統計</h3>
                <p style="font-size: 14px; color: #333;">
                    <strong style="color: #1A5F7A;">總 Lot 數量:</strong> <span style="color: #2E86AB; font-weight: bold;">{stats['total_lots']}</span><br>
                    <strong style="color: #28A745;">[Completed] 記錄數:</strong> <span style="color: #28A745; font-weight: bold;">{stats['completed_count']}</span><br>
                    <strong style="color: #FFC107;">[WIP] 記錄數:</strong> <span style="color: #FFC107; font-weight: bold;">{stats['wip_count']}</span><br>
                    <strong style="color: #007BFF;">[Normal] 記錄數:</strong> <span style="color: #007BFF; font-weight: bold;">{stats['normal_count']}</span><br>
                    <strong style="color: #6C757D;">[New Add] 記錄數:</strong> <span style="color: #6C757D; font-weight: bold;">{stats['new_add_count']}</span>
                </p>
                """
                return html_content
            else:
                return "<p style='color: #DC3545;'>無法獲取統計資訊</p>"

        # 建立線程執行任務
        self.worker = WorkerThread(run_show_stats)
        self.worker.finished.connect(self.on_show_stats_finished)
        self.worker.error.connect(self.on_show_stats_error)
        self.worker.start()

    def on_show_stats_finished(self, result):
        self.text_generate_result.setHtml(result)

    def on_show_stats_error(self, error):
        self.text_generate_result.setHtml(f"<p style='color: #DC3545; font-weight: bold;'>錯誤: {error}</p>")

    def start_simulation(self):
        """開始模擬時鐘"""
        if self.simulation_process is not None:
            return

        # 取得參數
        start_datetime = self.datetime_start.dateTime().toPyDateTime()
        reschedule_start_datetime = self.datetime_reschedule_start.dateTime().toPyDateTime()
        iterations = self.spin_iterations.value()
        time_delta = self.spin_timedelta.value()

        # 檢查開始時間必須 >= 重新排程開始時間
        if start_datetime < reschedule_start_datetime:
            QMessageBox.warning(self, "時間設定錯誤",
                              f"模擬開始時間 ({start_datetime.strftime('%Y-%m-%d %H:%M:%S')}) "
                              f"必須大於等於重新排程開始時間 ({reschedule_start_datetime.strftime('%Y-%m-%d %H:%M:%S')})")
            return

        # 更新重新排程的開始時間為模擬結束時間
        simulation_end_datetime = start_datetime + timedelta(seconds=iterations * time_delta)
        self.datetime_reschedule_start.setDateTime(QDateTime(simulation_end_datetime))

        # 建構命令
        simulateaps_path = os.path.join(os.path.dirname(__file__), '..', 'SimulateAPS.py')
        args = [
            sys.executable,
            '-u',  # 強制無緩衝輸出
            simulateaps_path,
            '--iterations', str(iterations),
            '--timedelta', str(time_delta),
            '--start-time', start_datetime.strftime('%Y-%m-%d %H:%M:%S')
        ]

        # 啟動 QProcess
        self.simulation_process = QProcess()
        self.simulation_process.readyReadStandardOutput.connect(self.handle_simulation_output)
        self.simulation_process.readyReadStandardError.connect(self.handle_simulation_error)
        self.simulation_process.finished.connect(self.on_simulation_finished)

        self.simulation_process.start(args[0], args[1:])

        # 更新 UI
        self.btn_start_simulation.setEnabled(False)
        self.btn_stop_simulation.setEnabled(True)

        self.text_simulation_result.clear()
        self.text_simulation_result.append(f'<span style="color: #28A745; font-weight: bold;">開始模擬: {start_datetime.strftime("%Y-%m-%d %H:%M:%S")}</span>')
        self.text_simulation_result.append(f'<span style="color: #007BFF;">模擬次數: {iterations}, 時間增量: {time_delta}秒</span>')

    def stop_simulation(self):
        """停止模擬時鐘"""
        if self.simulation_process is not None:
            self.simulation_process.terminate()
            if not self.simulation_process.waitForFinished(3000):  # 等待3秒
                self.simulation_process.kill()
            self.simulation_process = None

        self.btn_start_simulation.setEnabled(True)
        self.btn_stop_simulation.setEnabled(False)
        self.text_simulation_result.append('<span style="color: #DC3545; font-weight: bold;">模擬已停止</span>')

    def handle_simulation_output(self):
        """處理模擬程式的標準輸出"""
        if self.simulation_process is not None:
            output = self.simulation_process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
            if output:
                # 將換行符轉換為 HTML 換行
                html_output = output.replace('\n', '<br>')
                self.text_simulation_result.append(html_output)

    def handle_simulation_error(self):
        """處理模擬程式的錯誤輸出"""
        if self.simulation_process is not None:
            error = self.simulation_process.readAllStandardError().data().decode('utf-8', errors='ignore')
            if error:
                # 將錯誤輸出標示為紅色
                html_error = f'<span style="color: #DC3545;">{error.replace(chr(10), "<br>")}</span>'
                self.text_simulation_result.append(html_error)

    def handle_reschedule_output(self):
        """處理重新排程程式的標準輸出"""
        if self.reschedule_process is not None:
            output = self.reschedule_process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
            if output:
                # 將換行符轉換為 HTML 換行
                html_output = output.replace('\n', '<br>')
                self.text_reschedule_result.append(html_output)

    def handle_reschedule_error(self):
        """處理重新排程程式的錯誤輸出"""
        if self.reschedule_process is not None:
            error = self.reschedule_process.readAllStandardError().data().decode('utf-8', errors='ignore')
            if error:
                # 將錯誤輸出標示為紅色
                html_error = f'<span style="color: #DC3545;">{error.replace(chr(10), "<br>")}</span>'
                self.text_reschedule_result.append(html_error)

    def on_simulation_finished(self, exit_code, exit_status):
        """模擬程式完成時的處理"""
        self.simulation_process = None
        self.btn_start_simulation.setEnabled(True)
        self.btn_stop_simulation.setEnabled(False)

        if exit_code == 0:
            self.text_simulation_result.append('<span style="color: #28A745; font-weight: bold;">模擬完成</span>')
            
            # 從資料庫讀取最後的模擬時間
            try:
                conn = mysql.connector.connect(**db_config)
                cursor = conn.cursor()
                cursor.execute("SELECT simulation_end_time FROM SimulationData ORDER BY id DESC LIMIT 1")
                result = cursor.fetchone()
                cursor.close()
                conn.close()

                if result and result[0]:
                    simulation_end_time = result[0]
                    if isinstance(simulation_end_time, str):
                        simulation_end_time = datetime.strptime(simulation_end_time, '%Y-%m-%d %H:%M:%S')
                    
                    # 新的開始時間 = 模擬結束時間 + 10 分鐘
                    new_start_time = simulation_end_time + timedelta(minutes=10)
                    
                    # 更新 UI 控制項
                    self.datetime_start.setDateTime(QDateTime(new_start_time))
                    self.datetime_reschedule_start.setDateTime(QDateTime(new_start_time))
                    
                    # 儲存到資料庫設定
                    self.save_settings()
                    
                    self.text_simulation_result.append(f'<span style="color: #6C757D;">自動更新下次開始時間為: {new_start_time.strftime("%Y-%m-%d %H:%M:%S")}</span>')
            except Exception as e:
                print(f"更新模擬結束時間失敗: {e}")
        else:
            self.text_simulation_result.append(f'<span style="color: #DC3545; font-weight: bold;">模擬異常結束 (代碼: {exit_code})</span>')



    def get_database_stats(self):
        """獲取資料庫統計資訊"""
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()

            stats: Dict[str, int] = {}

            # 總 Lot 數量
            cursor.execute("SELECT COUNT(*) FROM Lots")
            result = cursor.fetchone()
            stats['total_lots'] = int(result[0]) if result else 0  # type: ignore

            # Completed 統計 (StepStatus = 2)
            cursor.execute("SELECT COUNT(*) FROM LotOperations WHERE StepStatus = 2")
            result = cursor.fetchone()
            stats['completed_count'] = int(result[0]) if result else 0  # type: ignore

            # WIP 統計 (StepStatus = 1)
            cursor.execute("SELECT COUNT(*) FROM LotOperations WHERE StepStatus = 1")
            result = cursor.fetchone()
            stats['wip_count'] = int(result[0]) if result else 0  # type: ignore

            # Normal 統計 (StepStatus = 0 AND PlanCheckInTime IS NOT NULL)
            cursor.execute("SELECT COUNT(*) FROM LotOperations WHERE StepStatus = 0 AND PlanCheckInTime IS NOT NULL")
            result = cursor.fetchone()
            stats['normal_count'] = int(result[0]) if result else 0  # type: ignore

            # New Add 統計 (StepStatus = 0 AND PlanCheckInTime IS NULL)
            cursor.execute("SELECT COUNT(*) FROM LotOperations WHERE StepStatus = 0 AND PlanCheckInTime IS NULL")
            result = cursor.fetchone()
            stats['new_add_count'] = int(result[0]) if result else 0  # type: ignore

            cursor.close()
            conn.close()

            return stats

        except Exception as e:
            print(f"獲取統計資訊錯誤: {e}")
            return None



    def reschedule(self):
        """執行重新排成"""
        if self.reschedule_process is not None:
            return

        # 當點擊重新排程按鈕時，將模擬時鐘的開始時間設置為重新排程的開始時間
        reschedule_start_datetime = self.datetime_reschedule_start.dateTime()
        self.datetime_start.setDateTime(reschedule_start_datetime)

        # 取得排程開始時間
        start_datetime = self.datetime_reschedule_start.dateTime().toPyDateTime()

        # 建構命令
        script_path = os.path.join(os.path.dirname(__file__), '..', 'Scheduler_Full_Example_Qtime_V1_Wip_DB.py')
        args = [
            sys.executable,
            '-u',  # 強制無緩衝輸出
            script_path,
            '--start-time', start_datetime.strftime('%Y-%m-%d %H:%M:%S')
        ]

        # 啟動 QProcess
        self.reschedule_process = QProcess()
        self.reschedule_process.readyReadStandardOutput.connect(self.handle_reschedule_output)
        self.reschedule_process.readyReadStandardError.connect(self.handle_reschedule_error)
        self.reschedule_process.finished.connect(self.on_reschedule_finished)
        self.reschedule_process.errorOccurred.connect(self.on_reschedule_error)

        self.reschedule_process.start(args[0], args[1:])

        # 更新 UI
        self.btn_reschedule.setEnabled(False)
        self.btn_reschedule.setText("執行中...")

        self.text_reschedule_result.clear()
        self.text_reschedule_result.append(f'<span style="color: #28A745; font-weight: bold;">開始重新排程: {start_datetime.strftime("%Y-%m-%d %H:%M:%S")}</span>')

    def on_reschedule_error(self, error):
        """處理重新排程程式的錯誤"""
        self.text_reschedule_result.append(f'<span style="color: #DC3545; font-weight: bold;">重新排程錯誤: {error}</span>')
        self.reschedule_process = None
        self.btn_reschedule.setEnabled(True)
        self.btn_reschedule.setText("執行")

    def on_reschedule_finished(self, exit_code, exit_status):
        """重新排程程式完成時的處理"""
        self.reschedule_process = None
        self.btn_reschedule.setEnabled(True)
        self.btn_reschedule.setText("執行")

        if exit_code == 0:
            self.text_reschedule_result.append('<span style="color: #28A745; font-weight: bold;">重新排程完成</span>')
        else:
            self.text_reschedule_result.append(f'<span style="color: #DC3545; font-weight: bold;">重新排程異常結束 (代碼: {exit_code})</span>')

    def load_settings(self):
        """載入設定"""
        def run_load_settings():
            try:
                conn = mysql.connector.connect(**db_config)
                cursor = conn.cursor(dictionary=True)

                cursor.execute("SELECT parameter_name, parameter_value FROM ui_settings")
                rows = cursor.fetchall()

                cursor.close()
                conn.close()

                # 將結果轉換為字典
                settings = {row['parameter_name']: row['parameter_value'] for row in rows}
                return settings

            except mysql.connector.Error as err:
                print(f"載入設定錯誤: {err}")
                return None
            except Exception as e:
                print(f"載入設定錯誤: {e}")
                return None

        def convert_value(value, value_type, default):
            """轉換資料型別"""
            if value is None:
                return default
            try:
                if value_type == 'int':
                    return int(value)
                elif value_type == 'str':
                    return str(value)
                else:
                    return value
            except (ValueError, TypeError):
                return default

        # 載入設定
        settings = run_load_settings()
        if settings:
            # 設定預設值，並進行型別轉換
            self.default_spin_lot_count = convert_value(settings.get('spin_lot_count'), 'int', 5)
            self.default_datetime_start = convert_value(settings.get('datetime_start'), 'str', '2026-01-22 14:00:00')
            self.default_spin_iterations = convert_value(settings.get('spin_iterations'), 'int', 50)
            self.default_spin_timedelta = convert_value(settings.get('spin_timedelta'), 'int', 60)
            self.default_datetime_reschedule_start = convert_value(settings.get('datetime_reschedule_start'), 'str', '2026-01-22 14:00:00')
        else:
            # 使用硬編碼預設值
            self.default_spin_lot_count = 5
            self.default_datetime_start = '2026-01-22 14:00:00'
            self.default_spin_iterations = 50
            self.default_spin_timedelta = 60
            self.default_datetime_reschedule_start = '2026-01-22 14:00:00'

        # 確保 datetime 欄位為字串格式
        if isinstance(self.default_datetime_start, datetime):
            self.default_datetime_start = self.default_datetime_start.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(self.default_datetime_reschedule_start, datetime):
            self.default_datetime_reschedule_start = self.default_datetime_reschedule_start.strftime('%Y-%m-%d %H:%M:%S')

    def save_settings(self):
        """儲存設定"""
        def run_save_settings():
            try:
                conn = mysql.connector.connect(**db_config)
                cursor = conn.cursor()

                # 取得當前值
                spin_lot_count = self.spin_lot_count.value()
                datetime_start = self.datetime_start.dateTime().toPyDateTime().strftime('%Y-%m-%d %H:%M:%S')
                spin_iterations = self.spin_iterations.value()
                spin_timedelta = self.spin_timedelta.value()
                datetime_reschedule_start = self.datetime_reschedule_start.dateTime().toPyDateTime().strftime('%Y-%m-%d %H:%M:%S')

                # 定義參數映射
                parameters = [
                    ('spin_lot_count', str(spin_lot_count)),
                    ('datetime_start', datetime_start),
                    ('spin_iterations', str(spin_iterations)),
                    ('spin_timedelta', str(spin_timedelta)),
                    ('datetime_reschedule_start', datetime_reschedule_start)
                ]

                # 使用 INSERT ... ON DUPLICATE KEY UPDATE 更新設定
                for param_name, param_value in parameters:
                    cursor.execute("""
                        INSERT INTO ui_settings (parameter_name, parameter_value)
                        VALUES (%s, %s)
                        ON DUPLICATE KEY UPDATE parameter_value = %s
                    """, (param_name, param_value, param_value))

                conn.commit()
                cursor.close()
                conn.close()

                return True

            except mysql.connector.Error as err:
                print(f"儲存設定錯誤: {err}")
                return False
            except Exception as e:
                print(f"儲存設定錯誤: {e}")
                return False

        # 儲存設定
        success = run_save_settings()
        if not success:
            QMessageBox.warning(self, "錯誤", "儲存設定失敗")

    def create_tab7(self):
        """第七個分頁：自動化測試"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 標題
        title = QLabel("自動化測試")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)

        # 說明文字
        description = QLabel(
            "選擇測試腳本並執行完整的自動化測試流程：\n"
            "1. 清空測試資料\n"
            "2. 產生 Lot（可設定批量）\n"
            "3. 重新排程\n"
            "4. 模擬時鐘\n"
            "5. 重複步驟 2-4 共 N 次"
        )
        description.setStyleSheet("color: #6C757D; padding: 10px; background-color: #F8F9FA; border-radius: 5px;")
        layout.addWidget(description)

        # 測試腳本選擇區域
        script_group = QGroupBox("測試腳本選擇")
        script_layout = QVBoxLayout(script_group)

        # 腳本列表
        self.test_script_list = QListWidget()
        self.test_script_list.setAlternatingRowColors(True)
        self.test_script_list.currentItemChanged.connect(self.on_test_script_selected)
        script_layout.addWidget(self.test_script_list)

        # 腳本詳細資訊
        self.test_script_info = QTextEdit()
        self.test_script_info.setReadOnly(True)
        self.test_script_info.setMaximumHeight(120)
        self.test_script_info.setAcceptRichText(True)
        script_layout.addWidget(self.test_script_info)

        layout.addWidget(script_group)

        # 控制按鈕
        button_layout = QHBoxLayout()
        
        self.btn_refresh_scripts = QPushButton("🔄 重新載入腳本")
        self.btn_refresh_scripts.clicked.connect(self.load_test_scripts)
        button_layout.addWidget(self.btn_refresh_scripts)

        self.btn_run_test = QPushButton("▶️ 執行測試")
        self.btn_run_test.clicked.connect(self.run_automated_test)
        self.btn_run_test.setEnabled(False)
        self.btn_run_test.setStyleSheet("""
            QPushButton {
                background-color: #28A745;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6C757D;
            }
        """)
        button_layout.addWidget(self.btn_run_test)

        self.btn_stop_test = QPushButton("⏹️ 停止測試")
        self.btn_stop_test.clicked.connect(self.stop_automated_test)
        self.btn_stop_test.setEnabled(False)
        self.btn_stop_test.setStyleSheet("""
            QPushButton {
                background-color: #DC3545;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #C82333;
            }
            QPushButton:disabled {
                background-color: #6C757D;
            }
        """)
        button_layout.addWidget(self.btn_stop_test)

        layout.addLayout(button_layout)

        # 執行結果顯示區域
        result_label = QLabel("執行結果")
        result_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(result_label)

        self.text_test_result = QTextEdit()
        self.text_test_result.setReadOnly(True)
        self.text_test_result.setAcceptRichText(True)
        layout.addWidget(self.text_test_result)

        # QProcess 相關變數
        self.test_process: Optional[QProcess] = None
        self.selected_test_config: Optional[str] = None

        self.tab_widget.addTab(tab, "自動化測試")

        # 載入測試腳本
        self.load_test_scripts()

    def load_test_scripts(self):
        """載入測試腳本列表"""
        self.test_script_list.clear()
        self.test_script_info.clear()
        
        # 取得測試腳本目錄
        test_scripts_dir = os.path.join(os.path.dirname(__file__), '..', 'test_scripts')
        
        if not os.path.exists(test_scripts_dir):
            self.test_script_info.setHtml(
                '<span style="color: #DC3545; font-weight: bold;">❌ 測試腳本目錄不存在</span>'
            )
            return
        
        # 讀取所有 JSON 配置檔案
        config_files = []
        for filename in os.listdir(test_scripts_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(test_scripts_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        config_files.append({
                            'filename': filename,
                            'filepath': filepath,
                            'config': config
                        })
                except Exception as e:
                    print(f"載入配置檔案 {filename} 失敗: {e}")
        
        # 排序並加入列表
        config_files.sort(key=lambda x: x['filename'])
        
        for item in config_files:
            config = item['config']
            display_name = f"{config['name']} ({item['filename']})"
            list_item = self.test_script_list.addItem(display_name)
            # 將完整路徑存儲在 item 的 data 中
            self.test_script_list.item(self.test_script_list.count() - 1).setData(256, item['filepath'])
        
        if config_files:
            self.test_script_info.setHtml(
                f'<span style="color: #28A745;">✅ 載入了 {len(config_files)} 個測試腳本</span>'
            )
        else:
            self.test_script_info.setHtml(
                '<span style="color: #FFC107;">⚠️ 沒有找到測試腳本</span>'
            )

    def on_test_script_selected(self, current, previous):
        """當選擇測試腳本時"""
        if current is None:
            self.btn_run_test.setEnabled(False)
            self.selected_test_config = None
            return
        
        # 取得配置檔案路徑
        config_path = current.data(256)
        self.selected_test_config = config_path
        
        # 讀取並顯示配置詳情
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            info_html = f"""
            <div style="padding: 10px; background-color: #F8F9FA; border-radius: 5px;">
                <h3 style="color: #2E86AB; margin-top: 0;">{config['name']}</h3>
                <p style="color: #6C757D; margin: 5px 0;"><strong>描述：</strong>{config['description']}</p>
                <p style="color: #333; margin: 5px 0;"><strong>循環次數：</strong>{config['cycles']}</p>
                <p style="color: #333; margin: 5px 0;"><strong>每次產生 Lot 數：</strong>{config['lots_per_cycle']}</p>
                <p style="color: #333; margin: 5px 0;"><strong>批量範圍：</strong>{config['lot_quantity_min']}-{config['lot_quantity_max']}</p>
                <p style="color: #333; margin: 5px 0;"><strong>模擬次數：</strong>{config['simulation_iterations']}</p>
                <p style="color: #333; margin: 5px 0;"><strong>時間增量：</strong>{config['simulation_timedelta']} 秒</p>
                <p style="color: #28A745; margin: 5px 0; font-weight: bold;">
                    總計將產生 {config['cycles'] * config['lots_per_cycle']} 個 Lot
                </p>
            </div>
            """
            
            self.test_script_info.setHtml(info_html)
            self.btn_run_test.setEnabled(True)
            
        except Exception as e:
            self.test_script_info.setHtml(
                f'<span style="color: #DC3545;">❌ 讀取配置失敗: {e}</span>'
            )
            self.btn_run_test.setEnabled(False)

    def run_automated_test(self):
        """執行自動化測試"""
        if self.test_process is not None:
            return
        
        if self.selected_test_config is None:
            QMessageBox.warning(self, "錯誤", "請先選擇測試腳本")
            return
        
        # 確認執行
        reply = QMessageBox.question(
            self,
            "確認執行",
            "確定要執行自動化測試嗎？\n這將清空所有測試資料並重新開始。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # 建構命令
        runner_script_path = os.path.join(os.path.dirname(__file__), '..', 'automated_test_runner.py')
        args = [
            sys.executable,
            '-u',  # 強制無緩衝輸出
            runner_script_path,
            '--config', self.selected_test_config
        ]
        
        # 啟動 QProcess
        self.test_process = QProcess()
        self.test_process.readyReadStandardOutput.connect(self.handle_test_output)
        self.test_process.readyReadStandardError.connect(self.handle_test_error)
        self.test_process.finished.connect(self.on_test_finished)
        
        self.test_process.start(args[0], args[1:])
        
        # 更新 UI
        self.btn_run_test.setEnabled(False)
        self.btn_stop_test.setEnabled(True)
        self.btn_refresh_scripts.setEnabled(False)
        self.test_script_list.setEnabled(False)
        
        self.text_test_result.clear()
        self.text_test_result.append(
            '<span style="color: #28A745; font-weight: bold; font-size: 14px;">🚀 開始執行自動化測試...</span>'
        )

    def stop_automated_test(self):
        """停止自動化測試"""
        if self.test_process is not None:
            self.test_process.terminate()
            if not self.test_process.waitForFinished(3000):  # 等待3秒
                self.test_process.kill()
            self.test_process = None
        
        self.btn_run_test.setEnabled(True)
        self.btn_stop_test.setEnabled(False)
        self.btn_refresh_scripts.setEnabled(True)
        self.test_script_list.setEnabled(True)
        
        self.text_test_result.append(
            '<br><span style="color: #DC3545; font-weight: bold;">⏹️ 測試已停止</span>'
        )

    def handle_test_output(self):
        """處理測試程式的標準輸出"""
        if self.test_process is not None:
            output = self.test_process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
            if output:
                # 美化輸出
                html_output = output
                
                # 替換特殊符號和關鍵字
                html_output = html_output.replace('✅', '<span style="color: #28A745; font-weight: bold;">✅</span>')
                html_output = html_output.replace('❌', '<span style="color: #DC3545; font-weight: bold;">❌</span>')
                html_output = html_output.replace('⚠️', '<span style="color: #FFC107; font-weight: bold;">⚠️</span>')
                html_output = html_output.replace('📊', '<span style="color: #2E86AB; font-weight: bold;">📊</span>')
                html_output = html_output.replace('🚀', '<span style="color: #17A2B8; font-weight: bold;">🚀</span>')
                
                # 高亮顯示步驟標題
                html_output = html_output.replace('步驟 1:', '<span style="color: #2E86AB; font-weight: bold;">步驟 1:</span>')
                html_output = html_output.replace('步驟 2:', '<span style="color: #2E86AB; font-weight: bold;">步驟 2:</span>')
                html_output = html_output.replace('步驟 3:', '<span style="color: #2E86AB; font-weight: bold;">步驟 3:</span>')
                html_output = html_output.replace('步驟 4:', '<span style="color: #2E86AB; font-weight: bold;">步驟 4:</span>')
                
                # 高亮顯示循環標題
                import re
                html_output = re.sub(r'循環 (\d+)/(\d+)', 
                                    r'<span style="color: #17A2B8; font-weight: bold; font-size: 13px;">🔄 循環 \1/\2</span>', 
                                    html_output)
                
                # 將換行符轉換為 HTML 換行
                html_output = html_output.replace('\n', '<br>')
                
                self.text_test_result.append(html_output)
                
                # 自動滾動到底部
                scrollbar = self.text_test_result.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())

    def handle_test_error(self):
        """處理測試程式的錯誤輸出"""
        if self.test_process is not None:
            error = self.test_process.readAllStandardError().data().decode('utf-8', errors='ignore')
            if error:
                html_error = f'<span style="color: #DC3545;">{error.replace(chr(10), "<br>")}</span>'
                self.text_test_result.append(html_error)

    def on_test_finished(self, exit_code, exit_status):
        """測試程式完成時的處理"""
        self.test_process = None
        self.btn_run_test.setEnabled(True)
        self.btn_stop_test.setEnabled(False)
        self.btn_refresh_scripts.setEnabled(True)
        self.test_script_list.setEnabled(True)
        
        if exit_code == 0:
            self.text_test_result.append(
                '<br><span style="color: #28A745; font-weight: bold; font-size: 14px;">🎉 自動化測試完成！</span>'
            )
        else:
            self.text_test_result.append(
                f'<br><span style="color: #DC3545; font-weight: bold;">❌ 測試異常結束 (代碼: {exit_code})</span>'
            )

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()