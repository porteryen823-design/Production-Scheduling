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
    cursor.execute("SHOW CREATE PROCEDURE sp_InsertLot")
    result = cursor.fetchone()
    if result:
        with open('c:/VSCode_Proj/APS01/sp_current.sql', 'w', encoding='utf-8') as f:
            f.write(result[2])
        print("SP definition saved to sp_current.sql")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
