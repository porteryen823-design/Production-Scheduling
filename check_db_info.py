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
    
    for table in ['Lots', 'LotOperations']:
        cursor.execute(f"DESCRIBE {table}")
        print(f"\nTable: {table}")
        for row in cursor.fetchall():
            print(row)
        
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
