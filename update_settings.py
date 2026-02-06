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

try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("UPDATE ui_settings SET parameter_value = 'True' WHERE parameter_name = 'use_sp_for_lot_insert'")
    conn.commit()
    print("Settings updated: use_sp_for_lot_insert = True")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
