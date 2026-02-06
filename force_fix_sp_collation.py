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

sp_sql = """
CREATE OR REPLACE PROCEDURE sp_UpdatePlanResultsJSON(
    IN p_LotsJson LONGTEXT,
    IN p_OpsJson LONGTEXT
)
BEGIN
    DECLARE i INT DEFAULT 0;
    DECLARE n INT DEFAULT 0;
    -- 強制變數使用與資料表相同的編碼
    DECLARE v_LotId VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
    DECLARE v_PlanFinishDate DATETIME;
    DECLARE v_PlanStartTime DATETIME;
    DECLARE v_DueDate DATETIME;
    DECLARE v_DelayDays DOUBLE;
    
    DECLARE v_Step VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
    DECLARE v_Start DATETIME;
    DECLARE v_End DATETIME;
    DECLARE v_Machine VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
    DECLARE v_HistoryInfo LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;

    -- Update Lots
    IF p_LotsJson IS NOT NULL AND JSON_VALID(p_LotsJson) THEN
        SET n = JSON_LENGTH(p_LotsJson);
        WHILE i < n DO
            SET v_LotId = JSON_VALUE(p_LotsJson, CONCAT('$[', i, '].LotId'));
            SET v_PlanFinishDate = JSON_VALUE(p_LotsJson, CONCAT('$[', i, '].PlanFinishDate'));
            SET v_PlanStartTime = JSON_VALUE(p_LotsJson, CONCAT('$[', i, '].PlanStartTime'));
            
            IF v_LotId IS NOT NULL THEN
                -- Calculate delay days internally
                -- 加入 COLLATE 確保比較一致
                SELECT DueDate INTO v_DueDate FROM Lots WHERE LotId COLLATE utf8mb4_general_ci = v_LotId;
                
                IF v_DueDate IS NOT NULL AND v_PlanFinishDate IS NOT NULL THEN
                    SET v_DelayDays = ROUND(TIMESTAMPDIFF(SECOND, v_DueDate, v_PlanFinishDate) / 86400, 2);
                ELSE
                    SET v_DelayDays = NULL;
                END IF;

                UPDATE Lots 
                SET PlanFinishDate = v_PlanFinishDate, 
                    PlanStartTime = v_PlanStartTime,
                    Delay_Days = v_DelayDays 
                WHERE LotId COLLATE utf8mb4_general_ci = v_LotId;
            END IF;
            
            SET i = i + 1;
        END WHILE;
    END IF;

    -- Update LotOperations
    IF p_OpsJson IS NOT NULL AND JSON_VALID(p_OpsJson) THEN
        SET i = 0;
        SET n = JSON_LENGTH(p_OpsJson);
        WHILE i < n DO
            SET v_LotId = JSON_VALUE(p_OpsJson, CONCAT('$[', i, '].LotId'));
            SET v_Step = JSON_VALUE(p_OpsJson, CONCAT('$[', i, '].Step'));
            SET v_Start = JSON_VALUE(p_OpsJson, CONCAT('$[', i, '].Start'));
            SET v_End = JSON_VALUE(p_OpsJson, CONCAT('$[', i, '].End'));
            SET v_Machine = JSON_VALUE(p_OpsJson, CONCAT('$[', i, '].Machine'));
            SET v_HistoryInfo = JSON_EXTRACT(p_OpsJson, CONCAT('$[', i, '].HistoryInfo'));

            IF v_LotId IS NOT NULL AND v_Step IS NOT NULL THEN
                UPDATE LotOperations
                SET PlanCheckInTime = v_Start,
                    PlanCheckOutTime = v_End,
                    PlanMachineId = v_Machine,
                    PlanHistory = JSON_ARRAY_APPEND(IFNULL(PlanHistory, '[]'), '$', CAST(v_HistoryInfo AS JSON))
                WHERE LotId COLLATE utf8mb4_general_ci = v_LotId 
                  AND Step COLLATE utf8mb4_general_ci = v_Step;
            END IF;

            SET i = i + 1;
        END WHILE;
    END IF;
END
"""

try:
    print(f"Connecting to {db_config['host']} to fix collation in SP...")
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    # 刪除舊的
    cursor.execute("DROP PROCEDURE IF EXISTS sp_UpdatePlanResultsJSON")
    
    # 建立新的
    cursor.execute(sp_sql)
    
    conn.commit()
    print("✓ Successfully injected fixed sp_UpdatePlanResultsJSON with explicit COLLATE.")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
