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
    cursor.execute("SELECT LotId, COUNT(*) FROM LotOperations WHERE LotId IN ('LOT_0066', 'LOT_0067', 'LOT_0068', 'LOT_0069', 'LOT_0070') GROUP BY LotId")
    rows = cursor.fetchall()
    for row in rows:
        print(f"Lot {row[0]} has {row[1]} operations")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
