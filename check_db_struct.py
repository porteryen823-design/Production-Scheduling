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

def check_structure():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    print("--- ui_settings table ---")
    cursor.execute("DESCRIBE ui_settings")
    for row in cursor.fetchall():
        print(row)
        
    print("\n--- Lots table ---")
    cursor.execute("DESCRIBE Lots")
    for row in cursor.fetchall():
        print(row)
        
    print("\n--- LotOperations table ---")
    cursor.execute("DESCRIBE LotOperations")
    for row in cursor.fetchall():
        print(row)

    print("\n--- DynamicSchedulingJob table ---")
    cursor.execute("DESCRIBE DynamicSchedulingJob")
    for row in cursor.fetchall():
        print(row)

    print("\n--- SimulationPlanningJob table ---")
    cursor.execute("DESCRIBE SimulationPlanningJob")
    for row in cursor.fetchall():
        print(row)
        
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_structure()
