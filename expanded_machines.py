import sys
import io
import os
import argparse
import mysql.connector
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 載入環境變數
load_dotenv()

def generate_machines_sql(multiplier, output_file="expanded_machines.sql"):
    # 原始基礎資料
    base_groups = {
        "M01": 3, "M02": 2, "M03": 3, "M04": 3, "M05": 2,
        "M06": 2, "M07": 2, "M08": 4, "M09": 4, "M10": 4,
        "M11": 4, "M12": 4, "M13": 4, "M14": 4, "M15": 4, "M16": 4
    }
    
    # 加入刪除舊資料的指令
    sql_header = "SET FOREIGN_KEY_CHECKS = 0;\nTRUNCATE TABLE `Machines`;\nSET FOREIGN_KEY_CHECKS = 1;\n\n"
    sql_template = "INSERT INTO `Machines` (`MachineId`, `GroupId`, `machine_name`, `is_active`, `created_at`, `updated_at`) VALUES\n"
    values = []

    for group_id, base_count in base_groups.items():
        # 依照倍率增加數量
        total_count = base_count * multiplier
        for i in range(1, total_count + 1):
            machine_id = f"{group_id}-{i}"
            val = f"('{machine_id}', '{group_id}', NULL, 1, NOW(), NOW())"
            values.append(val)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(sql_header)
        f.write(sql_template)
        f.write(",\n".join(values) + ";")
    
    print(f"成功！已產生 {len(values)} 台機器的資料於 {output_file}")
    return output_file

def apply_sql_to_db(sql_file):
    """將產生的 SQL 套用到資料庫"""
    try:
        db_config = {
            'host': os.getenv('MYSQL_HOST'),
            'user': os.getenv('MYSQL_USER'),
            'password': os.getenv('MYSQL_PASSWORD'),
            'database': os.getenv('MYSQL_DATABASE')
        }
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_queries = f.read()
            
        print("正在清理舊資料並執行 SQL 到資料庫...")
        
        # 將 SQL 內容按分號切割成個別語句執行 (避開 multi=True 的相容性問題)
        statements = sql_queries.split(';')
        for statement in statements:
            stmt = statement.strip()
            if stmt:
                cursor.execute(stmt)
                
        conn.commit()
        
        print(f"✅ 資料庫已重新初始化並對機台進行擴充作業")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ 資料庫套用失敗: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='機台數量擴充工具')
    parser.add_argument('--multiplier', type=int, default=1, help='擴充倍率 (預設為 1)')
    parser.add_argument('--apply', action='store_true', help='是否同時套用到資料庫')
    
    args = parser.parse_args()
    
    sql_file = generate_machines_sql(args.multiplier)
    
    if args.apply:
        apply_sql_to_db(sql_file)
