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
            cursor.execute("SELECT parameter_name, parameter_value FROM ui_settings WHERE parameter_name IN ('spin_iterations', 'spin_timedelta')")
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
                except (ValueError, TypeError):
                    continue
                    
            if settings:
                print(f"✅ 從資料庫載入設定: {settings}", flush=True)
            return settings
        except Exception as e:
            print(f"⚠️ 無法從資料庫載入設定: {e}", flush=True)
            return {}

    def load_config(self) -> Dict[str, Any]:
        """載入測試配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"✅ 載入測試配置: {config['name']}", flush=True)
            print(f"   描述: {config['description']}", flush=True)
            return config
        except Exception as e:
            print(f"❌ 載入配置檔案失敗: {e}", flush=True)
            sys.exit(1)
    
    def clean_test_data(self) -> bool:
        """清空測試資料"""
        print("\n" + "="*60, flush=True)
        print("步驟 1: 清空測試資料", flush=True)
        print("="*60, flush=True)
        
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            
            # 呼叫 stored procedure
            cursor.callproc('sp_clean_lots')
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print("✅ 測試資料已成功清空", flush=True)
            return True
            
        except mysql.connector.Error as err:
            print(f"❌ 資料庫錯誤: {err}", flush=True)
            return False
        except Exception as e:
            print(f"❌ 錯誤: {e}", flush=True)
            return False
    
    def generate_lots(self, count: int) -> bool:
        """
        產生 Lot 資料
        
        Args:
            count: 要產生的 Lot 數量
        """
        print(f"\n產生 {count} 個 Lot...", flush=True)
        
        try:
            # 建構命令
            insert_script_path = os.path.join(self.base_dir, 'insert_lot_data.py')
            
            # 隨機產生批量
            lot_qty_min = self.config.get('lot_quantity_min', 1)
            lot_qty_max = self.config.get('lot_quantity_max', 4)
            
            args = [
                sys.executable,
                insert_script_path,
                '--count', str(count)
            ]
            
            # 執行命令
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0:
                print(f"✅ 成功產生 {count} 個 Lot", flush=True)
                # 顯示部分輸出
                output_lines = result.stdout.strip().split('\n')
                for line in output_lines[-5:]:  # 只顯示最後 5 行
                    if line.strip():
                        print(f"   {line}", flush=True)
                return True
            else:
                print(f"❌ 產生 Lot 失敗", flush=True)
                print(f"   錯誤: {result.stderr}", flush=True)
                return False
                
        except Exception as e:
            print(f"❌ 產生 Lot 錯誤: {e}", flush=True)
            return False
    
    def reschedule(self, start_time: datetime) -> bool:
        """
        執行重新排程
        
        Args:
            start_time: 排程開始時間
        """
        print(f"\n執行重新排程 (開始時間: {start_time.strftime('%Y-%m-%d %H:%M:%S')})...", flush=True)
        
        try:
            # 建構命令
            script_path = os.path.join(self.base_dir, 'Scheduler_Full_Example_Qtime_V1_Wip_DB.py')
            args = [
                sys.executable,
                script_path,
                '--start-time', start_time.strftime('%Y-%m-%d %H:%M:%S')
            ]
            
            # 執行命令
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0:
                print(f"✅ 重新排程完成", flush=True)
                return True
            else:
                print(f"❌ 重新排程失敗", flush=True)
                print(f"   錯誤: {result.stderr}", flush=True)
                return False
                
        except Exception as e:
            print(f"❌ 重新排程錯誤: {e}", flush=True)
            return False
    
    def simulate_clock(self, start_time: datetime, iterations: int, timedelta_seconds: int) -> bool:
        """
        執行模擬時鐘
        
        Args:
            start_time: 模擬開始時間
            iterations: 模擬次數
            timedelta_seconds: 時間增量（秒）
        """
        print(f"\n執行模擬時鐘 (開始: {start_time.strftime('%Y-%m-%d %H:%M:%S')}, "
              f"次數: {iterations}, 增量: {timedelta_seconds}秒)...", flush=True)
        
        try:
            # 建構命令
            script_path = os.path.join(self.base_dir, 'SimulateAPS.py')
            args = [
                sys.executable,
                script_path,
                '--iterations', str(iterations),
                '--timedelta', str(timedelta_seconds),
                '--start-time', start_time.strftime('%Y-%m-%d %H:%M:%S')
            ]
            
            # 執行命令
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0:
                print(f"✅ 模擬時鐘完成", flush=True)
                return True
            else:
                print(f"❌ 模擬時鐘失敗", flush=True)
                print(f"   錯誤: {result.stderr}", flush=True)
                return False
                
        except Exception as e:
            print(f"❌ 模擬時鐘錯誤: {e}", flush=True)
            return False
    
    def get_simulation_end_time(self) -> datetime:
        """從資料庫取得最後的模擬結束時間"""
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
                return simulation_end_time
            else:
                # 如果沒有資料，返回預設時間
                return datetime(2026, 1, 22, 14, 0, 0)
                
        except Exception as e:
            print(f"⚠️ 取得模擬結束時間失敗: {e}", flush=True)
            return datetime(2026, 1, 22, 14, 0, 0)
    
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
        print(f"循環 {cycle_num}/{total_cycles}", flush=True)
        print("="*60, flush=True)
        
        # 步驟 2: 產生 Lot
        print("\n" + "-"*60, flush=True)
        print("步驟 2: 產生 Lot", flush=True)
        print("-"*60, flush=True)
        lots_count = self.config['lots_per_cycle']
        if not self.generate_lots(lots_count):
            print(f"❌ 循環 {cycle_num} 失敗：產生 Lot 失敗", flush=True)
            return current_time
        
        # 步驟 3: 重新排程
        print("\n" + "-"*60, flush=True)
        print("步驟 3: 重新排程", flush=True)
        print("-"*60, flush=True)
        if not self.reschedule(current_time):
            print(f"❌ 循環 {cycle_num} 失敗：重新排程失敗", flush=True)
            return current_time
        
        # 步驟 4: 模擬時鐘
        print("\n" + "-"*60, flush=True)
        print("步驟 4: 模擬時鐘", flush=True)
        print("-"*60, flush=True)
        
        # 優先使用資料庫設定
        iterations = self.db_settings.get('spin_iterations', self.config.get('simulation_iterations', 50))
        timedelta_seconds = self.db_settings.get('spin_timedelta', self.config.get('simulation_timedelta', 60))
        
        if not self.simulate_clock(current_time, iterations, timedelta_seconds):
            print(f"❌ 循環 {cycle_num} 失敗：模擬時鐘失敗", flush=True)
            return current_time
        
        # 取得模擬結束時間，並加上 10 分鐘作為下次開始時間
        end_time = self.get_simulation_end_time()
        next_time = end_time + timedelta(minutes=10)
        
        print(f"\n✅ 循環 {cycle_num} 完成", flush=True)
        print(f"   模擬結束時間: {end_time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
        print(f"   下次開始時間: {next_time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
        
        return next_time
    
    def run(self):
        """執行完整測試流程"""
        # 取得最終使用的模擬設定用於顯示
        iterations = self.db_settings.get('spin_iterations', self.config.get('simulation_iterations', 50))
        timedelta_seconds = self.db_settings.get('spin_timedelta', self.config.get('simulation_timedelta', 60))

        print("\n" + "="*60, flush=True)
        print(f"開始執行自動化測試: {self.config['name']}", flush=True)
        print("="*60, flush=True)
        print(f"總循環次數: {self.config['cycles']}", flush=True)
        print(f"每次產生 Lot 數: {self.config['lots_per_cycle']}", flush=True)
        print(f"批量範圍: {self.config['lot_quantity_min']}-{self.config['lot_quantity_max']}", flush=True)
        print(f"模擬次數: {iterations} (來源: {'資料庫' if 'spin_iterations' in self.db_settings else '配置檔案'})", flush=True)
        print(f"時間增量: {timedelta_seconds}秒 (來源: {'資料庫' if 'spin_timedelta' in self.db_settings else '配置檔案'})", flush=True)
        
        # 步驟 1: 清空測試資料
        if not self.clean_test_data():
            print("\n❌ 測試失敗：清空測試資料失敗", flush=True)
            return
        
        # 初始時間
        current_time = datetime(2026, 1, 22, 14, 0, 0)
        
        # 執行 N 次循環
        total_cycles = self.config['cycles']
        for cycle_num in range(1, total_cycles + 1):
            current_time = self.run_cycle(cycle_num, total_cycles, current_time)
        
        # 測試完成
        print("\n" + "="*60, flush=True)
        print("✅ 自動化測試完成", flush=True)
        print("="*60, flush=True)
        print(f"測試名稱: {self.config['name']}", flush=True)
        print(f"完成循環數: {total_cycles}", flush=True)
        print(f"總產生 Lot 數: {total_cycles * self.config['lots_per_cycle']}", flush=True)
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
