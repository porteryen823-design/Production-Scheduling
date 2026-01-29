import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

db_config = {
    'host': os.getenv('MYSQL_HOST'),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE')
}

def alter_table():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # 檢查欄位是否存在
        cursor.execute("DESCRIBE DynamicSchedulingJob")
        columns = [row[0] for row in cursor.fetchall()]
        
        if 'simulation_end_time' not in columns:
            print("Adding simulation_end_time column to DynamicSchedulingJob...")
            cursor.execute("ALTER TABLE DynamicSchedulingJob ADD COLUMN simulation_end_time DATETIME;")
            conn.commit()
            print("Column added successfully.")
        else:
            print("Column simulation_end_time already exists.")
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    alter_table()
