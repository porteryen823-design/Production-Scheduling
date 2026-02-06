import sys
import io
import mysql.connector
import os
from dotenv import load_dotenv

if sys.platform == 'win32':
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

# 讀取 SQL 檔案
with open('setup_sp.sql', 'r', encoding='utf-8') as f:
    sql_content = f.read()

# 分割 SQL 語句（以 DELIMITER 為基準）
sql_statements = []
current_delimiter = ';'
buffer = []

for line in sql_content.split('\n'):
    line = line.strip()
    
    if line.startswith('DELIMITER'):
        # 切換分隔符
        new_delimiter = line.split()[1]
        if buffer:
            sql_statements.append('\n'.join(buffer))
            buffer = []
        current_delimiter = new_delimiter
    elif line.endswith(current_delimiter) and current_delimiter != ';':
        # 遇到自訂分隔符（如 //）
        buffer.append(line[:-len(current_delimiter)])
        sql_statements.append('\n'.join(buffer))
        buffer = []
    elif line:
        buffer.append(line)

if buffer:
    sql_statements.append('\n'.join(buffer))

try:
    print(f"Connecting to database: {db_config['host']}")
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    print("\nUpdating stored procedures with collation fixes...")
    
    for idx, statement in enumerate(sql_statements):
        statement = statement.strip()
        if not statement or statement.startswith('--'):
            continue
            
        if 'CREATE OR REPLACE PROCEDURE' in statement:
            proc_name = statement.split('PROCEDURE')[1].split('(')[0].strip()
            print(f"\n[{idx+1}] Updating procedure: {proc_name}")
            
            try:
                cursor.execute(statement)
                print(f"    ✓ Successfully updated {proc_name}")
            except Exception as e:
                print(f"    ✗ Error updating {proc_name}: {e}")
                # 顯示問題語句的前 200 字元
                print(f"    Statement preview: {statement[:200]}...")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("\n" + "="*60)
    print("Stored procedures update completed!")
    print("="*60)
    
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
