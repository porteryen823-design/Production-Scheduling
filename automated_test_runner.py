"""
自動化測試執行器
執行完整的測試流程：清空資料 -> 產生 Lot -> 重新排程 -> 模擬時鐘
"""
import sys
import os
import json
import random
import argparse
import subprocess
from datetime import datetime, timedelta
from typing import Dict, Any
import mysql.connector
from dotenv import load_dotenv

# 設定 UTF-8 編碼輸出（解決 Windows 控制台編碼問題）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 載入環境變數
load_dotenv()

# 資料庫連線設定
db_config = {
    'host': os.getenv('MYSQL_HOST'),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE')
}

class AutomatedTestRunner:
    """自動化測試執行器"""
    
    def __init__(self, config_path: str):
        """
        初始化測試執行器
        
        Args:
            config_path: 測試配置檔案路徑
        """
        self.config_path = config_path
        self.config = self.load_config()
        self.db_settings = self.load_db_settings()
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
    def load_db_settings(self) -> Dict[str, Any]:
        """從資料庫載入模擬設定"""
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT parameter_name, parameter_value FROM ui_settings WHERE parameter_name IN ('spin_iterations', 'spin_timedelta', 'simulation_start_time', 'simulation_start_time_setting')")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            settings = {}
            for row in rows:
                try:
                    name = row['parameter_name']
                    value = row['parameter_value']
                    if name in ['spin_iterations', 'spin_timedelta']:
                        settings[name] = int(value)
                    elif name in ['simulation_start_time', 'simulation_start_time_setting']:
                        settings[name] = value
                except (ValueError, TypeError):
                    continue
                    
            if settings:
                print(f"✅ Loaded settings from database: {settings}", flush=True)
            return settings
        except Exception as e:
            print(f"⚠️ Could not load settings from database: {e}", flush=True)
            return {}

    def load_config(self) -> Dict[str, Any]:
        """載入測試配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"✅ Loaded test config: {config['name']}", flush=True)
            print(f"   Description: {config['description']}", flush=True)
            return config
        except Exception as e:
            print(f"❌ Failed to load config file: {e}", flush=True)
            sys.exit(1)
    
    def clean_test_data(self) -> bool:
        """清空測試資料"""
        print("\n" + "="*60, flush=True)
        print("Step 1: Clean test data", flush=True)
        print("="*60, flush=True)
        
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            
            # Call stored procedure
            cursor.callproc('sp_clean_lots')
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print("✅ Test data cleaned successfully", flush=True)
            return True
            
        except mysql.connector.Error as err:
            print(f"❌ Database error: {err}", flush=True)
            return False
        except Exception as e:
            print(f"❌ Error: {e}", flush=True)
            return False

    def init_simulation_settings(self, start_time: datetime) -> bool:
        """初始化模擬設定，確保同步"""
        print(f"\nInitializing simulation settings to baseline (Start: {start_time.strftime('%Y-%m-%d %H:%M:%S')})...", flush=True)
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            
            # 將基準時間同步到 simulation_start_time 和 simulation_end_time
            # 並強制開啟模擬模式設定
            settings = [
                ('simulation_start_time', start_time.strftime('%Y-%m-%d %H:%M:%S')),
                ('simulation_end_time', start_time.strftime('%Y-%m-%d %H:%M:%S')),
                ('insert_lot_data_use_simulation_end_time', 'True'),
                ('use_sp_for_lot_insert', 'True')
            ]
            
            for name, value in settings:
                cursor.execute("""
                    INSERT INTO ui_settings (parameter_name, parameter_value)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE parameter_value = %s
                """, (name, value, value))
                
            conn.commit()
            cursor.close()
            conn.close()
            print("✅ Simulation settings initialized", flush=True)
            return True
        except Exception as e:
            print(f"⚠️ Failed to initialize simulation settings: {e}", flush=True)
            return False
    
    def _run_script(self, args: list, step_name: str) -> bool:
        """協助執行外部腳本並即時輸出內容"""
        try:
            # 建立子程序，將 stdout/stderr 導向 PIPE
            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='ignore',
                bufsize=1  # 行緩衝
            )

            # 即時讀取並輸出
            if process.stdout:
                for line in iter(process.stdout.readline, ""):
                    print(f"   {line.strip()}", flush=True)
                process.stdout.close()

            return_code = process.wait()
            
            if return_code == 0:
                print(f"✅ {step_name} completed", flush=True)
                return True
            else:
                print(f"❌ {step_name} failed (Code: {return_code})", flush=True)
                return False

        except Exception as e:
            print(f"❌ Error executing {step_name}: {e}", flush=True)
            return False

    def generate_lots(self, count: int) -> bool:
        """
        Produce Lot data
        
        Args:
            count: Number of Lots to produce
        """
        print(f"\nGenerating {count} Lots...", flush=True)
        insert_script_path = os.path.join(self.base_dir, 'insert_lot_data.py')
        args = [sys.executable, '-u', insert_script_path, '--count', str(count)]
        return self._run_script(args, "Generate Lot")
    
    def reschedule(self, start_time: datetime) -> bool:
        """
        Execute rescheduling
        
        Args:
            start_time: Schedule start time
        """
        print(f"\nExecuting rescheduling (Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')})...", flush=True)
        script_path = os.path.join(self.base_dir, 'Scheduler_Full_Example_Qtime_V1_Wip_DB_Incremental_Scheduling.py')
        args = [sys.executable, '-u', script_path, '--start-time', start_time.strftime('%Y-%m-%d %H:%M:%S')]
        return self._run_script(args, "Reschedule")
    
    def simulate_clock(self, start_time: datetime, iterations: int, timedelta_seconds: int) -> bool:
        """
        Execute simulation clock
        
        Args:
            start_time: Simulation start time
            iterations: Number of iterations
            timedelta_seconds: Time delta (seconds)
        """
        print(f"\nExecuting simulation clock (Start: {start_time.strftime('%Y-%m-%d %H:%M:%S')}, "
              f"Iterations: {iterations}, Delta: {timedelta_seconds}s)...", flush=True)
        script_path = os.path.join(self.base_dir, 'SimulateAPS.py')
        args = [
            sys.executable, '-u', script_path,
            '--iterations', str(iterations),
            '--timedelta', str(timedelta_seconds),
            '--start-time', start_time.strftime('%Y-%m-%d %H:%M:%S')
        ]
        return self._run_script(args, "Simulation Clock")
    
    def get_simulation_start_time(self) -> datetime:
        """從資料庫取得模擬起始點設定，優先使用 simulation_start_time_setting"""
        # 優先選擇固定基準設定
        baseline = self.db_settings.get('simulation_start_time_setting')
        db_start = self.db_settings.get('simulation_start_time')
        
        target_str = baseline if baseline else db_start
        
        if target_str:
            try:
                return datetime.strptime(target_str, '%Y-%m-%d %H:%M:%S')
            except Exception as e:
                print(f"⚠️ Invalid time format in DB: {e}", flush=True)
        
        # 預設後備時間
        return datetime(2026, 1, 22, 14, 0, 0)

    def get_simulation_end_time(self) -> datetime:
        """從資料庫取得最後的模擬結束時間"""
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT parameter_value FROM ui_settings WHERE parameter_name = 'simulation_end_time' LIMIT 1")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result and result[0]:
                simulation_end_time_str = result[0]
                # 將字串轉換為 datetime 物件
                simulation_end_time = datetime.strptime(simulation_end_time_str, '%Y-%m-%d %H:%M:%S')
                return simulation_end_time
            else:
                # 如果沒有資料，返回模擬起始點
                return self.get_simulation_start_time()
                
        except Exception as e:
            print(f"⚠️ Failed to get simulation end time: {e}", flush=True)
            return self.get_simulation_start_time()
    
    def run_cycle(self, cycle_num: int, total_cycles: int, current_time: datetime) -> datetime:
        """
        執行單次循環
        
        Args:
            cycle_num: 當前循環編號
            total_cycles: 總循環次數
            current_time: 當前時間
            
        Returns:
            下一次循環的開始時間
        """
        print("\n" + "="*60, flush=True)
        print(f"Cycle {cycle_num}/{total_cycles}", flush=True)
        print("="*60, flush=True)
        
        # Step 2: Generate Lot
        print("\n" + "-"*60, flush=True)
        print("Step 2: Generate Lot", flush=True)
        print("-"*60, flush=True)
        lots_count = self.config['lots_per_cycle']
        if not self.generate_lots(lots_count):
            print(f"❌ Cycle {cycle_num} failed: Generate Lot failed", flush=True)
            return current_time
        
        # Step 3: Reschedule
        print("\n" + "-"*60, flush=True)
        print("Step 3: Reschedule", flush=True)
        print("-"*60, flush=True)
        if not self.reschedule(current_time):
            print(f"❌ Cycle {cycle_num} failed: Reschedule failed", flush=True)
            return current_time
        
        # Step 4: Simulation Clock
        print("\n" + "-"*60, flush=True)
        print("Step 4: Simulation Clock", flush=True)
        print("-"*60, flush=True)
        
        # Priority: use DB settings
        iterations = self.db_settings.get('spin_iterations', self.config.get('simulation_iterations', 50))
        timedelta_seconds = self.db_settings.get('spin_timedelta', self.config.get('simulation_timedelta', 60))
        
        if not self.simulate_clock(current_time, iterations, timedelta_seconds):
            print(f"❌ Cycle {cycle_num} failed: Simulation clock failed", flush=True)
            return current_time
        
        # Get simulation end time, add 5 mins for next start
        end_time = self.get_simulation_end_time()
        next_time = end_time + timedelta(minutes=5)
        
        print(f"\n✅ Cycle {cycle_num} completed", flush=True)
        print(f"   Simulation end time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
        print(f"   Next start time: {next_time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
        
        return next_time
    
    def run(self):
        """執行完整測試流程"""
        # 取得最終使用的模擬設定用於顯示
        iterations = self.db_settings.get('spin_iterations', self.config.get('simulation_iterations', 50))
        timedelta_seconds = self.db_settings.get('spin_timedelta', self.config.get('simulation_timedelta', 60))

        print("\n" + "="*60, flush=True)
        print(f"Starting automated test: {self.config['name']}", flush=True)
        print("="*60, flush=True)
        print(f"Total cycles: {self.config['cycles']}", flush=True)
        print(f"Lots per cycle: {self.config['lots_per_cycle']}", flush=True)
        print(f"Batch range: {self.config['lot_quantity_min']}-{self.config['lot_quantity_max']}", flush=True)
        print(f"Simulation iterations: {iterations} (Source: {'Database' if 'spin_iterations' in self.db_settings else 'Config file'})", flush=True)
        print(f"Time delta: {timedelta_seconds}s (Source: {'Database' if 'spin_timedelta' in self.db_settings else 'Config file'})", flush=True)
        
        # Step 1: Clean test data
        if not self.clean_test_data():
            print("\n❌ Test failed: Clean test data failed", flush=True)
            return
        
        # 從資料庫取得起始時間 (simulation_start_time)
        start_date = self.get_simulation_start_time()
        current_time = start_date
        
        print(f"📍 Test Baseline Start Time: {start_date.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
        
        # 初始化資料庫中的時間設定，避免第一批次抓到 NOW()
        if not self.init_simulation_settings(start_date):
            print("\n⚠️ Warning: Simulation settings initialization failed, may cause time drift", flush=True)
        
        # Step 1.5: Generate initial Lot (if configured)
        initial_lots = self.config.get('initial_lots', 0)
        if initial_lots > 0:
            print("\n" + "="*60, flush=True)
            print(f"Generate initial Lot: {initial_lots}", flush=True)
            print("="*60, flush=True)
            if not self.generate_lots(initial_lots):
                print("\n❌ Test failed: Generate initial Lot failed", flush=True)
                return
        
        # 執行 N 次循環
        total_cycles = self.config['cycles']
        for cycle_num in range(1, total_cycles + 1):
            current_time = self.run_cycle(cycle_num, total_cycles, current_time)
        
        # Test completion
        print("\n" + "="*60, flush=True)
        print("✅ Automated test completed", flush=True)
        print("="*60, flush=True)
        print(f"Test name: {self.config['name']}", flush=True)
        print(f"Completed cycles: {total_cycles}", flush=True)
        total_lots = self.config.get('initial_lots', 0) + (total_cycles * self.config['lots_per_cycle'])
        print(f"Total Lots generated: {total_lots}", flush=True)
        print("="*60, flush=True)


def main():
    """主程式"""
    parser = argparse.ArgumentParser(description='自動化測試執行器')
    parser.add_argument('--config', required=True, help='測試配置檔案路徑')
    
    args = parser.parse_args()
    
    # 建立並執行測試
    runner = AutomatedTestRunner(args.config)
    runner.run()


if __name__ == "__main__":
    main()
