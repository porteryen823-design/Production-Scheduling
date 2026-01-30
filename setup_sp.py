import mysql.connector
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 資料庫連線設定
db_config = {
    'host': os.getenv('MYSQL_HOST'),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE')
}

def setup_database():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # 1. 增加 ui_settings 參數
        print("Checking/Adding ui_settings parameter 'use_sp_for_lot_insert'...")
        cursor.execute("SELECT parameter_value FROM ui_settings WHERE parameter_name = 'use_sp_for_lot_insert'")
        result = cursor.fetchone()
        if not result:
            cursor.execute("INSERT INTO ui_settings (parameter_name, parameter_value) VALUES ('use_sp_for_lot_insert', 'False')")
            print("Added 'use_sp_for_lot_insert' = 'False'")
        else:
            print(f"'use_sp_for_lot_insert' already exists with value: {result[0]}")

        # 2. 建立 Stored Procedure
        print("Creating Stored Procedure 'sp_InsertLot'...")
        
        # 先刪除舊的 (如果有)
        cursor.execute("DROP PROCEDURE IF EXISTS sp_InsertLot")
        
        sp_sql = """
        CREATE PROCEDURE sp_InsertLot(
            IN p_Count INT,
            IN p_Priority INT,
            IN p_UseSimEndTime BOOLEAN
        )
        BEGIN
            DECLARE v_NextLotId VARCHAR(20);
            DECLARE v_NextIdNum INT;
            DECLARE v_DueDate DATETIME;
            DECLARE v_BaseDate DATETIME;
            DECLARE v_SimEndTimeStr VARCHAR(100);
            DECLARE i INT DEFAULT 0;

            -- Create temporary table to store inserted LotIds
            CREATE TEMPORARY TABLE IF NOT EXISTS temp_inserted_lots (LotId VARCHAR(20));
            DELETE FROM temp_inserted_lots;

            -- 1. Get Initial NextIdNum
            SELECT LotId INTO v_NextLotId FROM Lots ORDER BY LotId DESC LIMIT 1;
            IF v_NextLotId IS NULL THEN
                SET v_NextIdNum = 1;
            ELSE
                SET v_NextIdNum = CAST(SUBSTRING(v_NextLotId, 5) AS UNSIGNED) + 1;
            END IF;

            -- 2. Calculate Base Date once
            SET v_BaseDate = NOW();
            IF p_UseSimEndTime THEN
                SELECT parameter_value INTO v_SimEndTimeStr FROM ui_settings WHERE parameter_name = 'simulation_end_time';
                IF v_SimEndTimeStr IS NOT NULL AND v_SimEndTimeStr != '' THEN
                    SET v_BaseDate = STR_TO_DATE(v_SimEndTimeStr, '%Y-%m-%d %H:%i:%s');
                END IF;
            END IF;

            -- 3. Loop for insertions
            WHILE i < p_Count DO
                SET v_NextLotId = CONCAT('LOT_', LPAD(v_NextIdNum, 4, '0'));
                
                SET v_DueDate = DATE_ADD(v_BaseDate, INTERVAL 3 DAY);
                -- Format to hour
                SET v_DueDate = STR_TO_DATE(DATE_FORMAT(v_DueDate, '%Y-%m-%d %H:00:00'), '%Y-%m-%d %H:%i:%s');

                -- Insert into Lots
                INSERT INTO Lots (LotId, Priority, DueDate, ActualFinishDate, ProductID, ProductName, CustomerID, CustomerName, LotCreateDate)
                VALUES (
                    v_NextLotId, 
                    p_Priority, 
                    v_DueDate, 
                    NULL, 
                    CONCAT('PROD_', LPAD(v_NextIdNum, 4, '0')), 
                    CONCAT('Product ', LPAD(v_NextIdNum, 4, '0')), 
                    CONCAT('CUST_', LPAD(v_NextIdNum, 4, '0')), 
                    CONCAT('Customer ', LPAD(v_NextIdNum, 4, '0')), 
                    NOW()
                );

                -- Insert into LotOperations
                INSERT INTO LotOperations (LotId, Step, MachineGroup, Duration, Sequence, StepStatus) VALUES
                (v_NextLotId, 'STEP1', 'M01', 240, 1, 0),
                (v_NextLotId, 'STEP2', 'M02', 120, 2, 0),
                (v_NextLotId, 'STEP3', 'M03', 300, 3, 0),
                (v_NextLotId, 'STEP4', 'M04', 280, 4, 0),
                (v_NextLotId, 'STEP5', 'M05', 360, 5, 0),
                (v_NextLotId, 'STEP6', 'M06', 200, 6, 0),
                (v_NextLotId, 'STEP7', 'M07', 180, 7, 0),
                (v_NextLotId, 'STEP8', 'M08', 160, 8, 0);

                INSERT INTO temp_inserted_lots (LotId) VALUES (v_NextLotId);

                SET v_NextIdNum = v_NextIdNum + 1;
                SET i = i + 1;
            END WHILE;

            -- Return all inserted LotIds
            SELECT LotId AS InsertedLotId FROM temp_inserted_lots;
            DROP TEMPORARY TABLE temp_inserted_lots;
        END
        """
        cursor.execute(sp_sql)
        print("Stored Procedure 'sp_InsertLot' created successfully.")

        conn.commit()
        cursor.close()
        conn.close()
        print("Database setup complete.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")

if __name__ == "__main__":
    setup_database()
