
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

sql_drop = "DROP PROCEDURE IF EXISTS generate_random_pm_schedules;"

sql_create = """
CREATE PROCEDURE generate_random_pm_schedules()
BEGIN
    -- 變數用於隨機計算
    DECLARE random_days INT;
    DECLARE random_hours DECIMAL(4,2);
    DECLARE start_date DATETIME;
    DECLARE end_date DATETIME;
    DECLARE num_records INT;
    DECLARE i INT DEFAULT 0;
    DECLARE overlap_count INT DEFAULT 0;
    
    -- 新增變數用於讀取設定
    DECLARE base_date DATETIME;
    DECLARE date_str TEXT;

    DECLARE done INT DEFAULT FALSE;
    -- 使用 COLLATE 強制變數的一致性 (雖非必須，但可防禦預設值差異)
    DECLARE machine_id_val VARCHAR(20) CHARSET utf8mb4 COLLATE utf8mb4_general_ci;
    
    DECLARE cur CURSOR FOR SELECT MachineId FROM Machines ORDER BY MachineId;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    -- 1. 讀取 ui_settings 中的 simulation_start_time_setting
    -- 強制字串常值使用 utf8mb4_general_ci 以匹配資料表欄位
    SELECT parameter_value INTO date_str FROM ui_settings 
    WHERE parameter_name = 'simulation_start_time_setting' COLLATE utf8mb4_general_ci 
    LIMIT 1;

    -- 2. 判斷並設定基準日期
    IF date_str IS NOT NULL AND date_str != '' THEN
        -- 嘗試轉換字串為 DATETIME
        SET base_date = CAST(date_str AS DATETIME);
    ELSE
        -- 若無資料，使用當前時間作為基準
        SET base_date = NOW();
    END IF;

    -- 若轉換失敗 (例如格式錯誤導致 NULL)，也 fallback 到 NOW()
    IF base_date IS NULL THEN
        SET base_date = NOW();
    END IF;

    OPEN cur;

    read_loop: LOOP
        FETCH cur INTO machine_id_val;
        IF done THEN
            LEAVE read_loop;
        END IF;

        -- 每個機台隨機產生 1-4 筆 PM 記錄
        SET num_records = FLOOR(RAND() * 4) + 1; -- 1-4 筆

        -- 內層迴圈：為每個機台產生多筆記錄
        SET i = 0;
        WHILE i < num_records DO
            -- 隨機選擇開始日期：基準日 到 30 天後
            SET random_days = FLOOR(RAND() * 31); -- 0-30 天
            
            -- 使用 base_date 取代原本的 CURDATE()
            SET start_date = DATE_ADD(base_date, INTERVAL random_days DAY);

            -- 隨機選擇持續時間：0.2 到 1 天 (4.8 到 24 小時)
            SET random_hours = 4.8 + (RAND() * 19.2); -- 4.8 到 24.0 小時
            SET end_date = DATE_ADD(start_date, INTERVAL random_hours HOUR);

            -- 檢查是否與現有的 PM 記錄重疊
            SELECT COUNT(*) INTO overlap_count
            FROM machine_unavailable_periods
            WHERE MachineId = machine_id_val 
              AND PeriodType = 'PM' COLLATE utf8mb4_general_ci
              AND Status = 'ACTIVE' COLLATE utf8mb4_general_ci
              AND (
                  (StartTime <= start_date AND EndTime > start_date) OR
                  (StartTime < end_date AND EndTime >= end_date) OR
                  (StartTime >= start_date AND EndTime <= end_date)
              );

            -- 如果沒有重疊，插入記錄
            IF overlap_count = 0 THEN
                INSERT INTO machine_unavailable_periods
                (MachineId, StartTime, EndTime, PeriodType, Reason, CreatedBy)
                VALUES
                (machine_id_val, start_date, end_date, 'PM',
                 CONCAT('隨機產生的預防性保養 - ', machine_id_val, ' (', i+1, '/', num_records, ')'),
                 'SYSTEM');

                SET i = i + 1;
            END IF;
            -- 如果重疊，繼續迴圈重新生成（不增加 i）即 retry

        END WHILE;

    END LOOP;

    CLOSE cur;

END
"""

try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    print("Dropping old procedure...")
    cursor.execute(sql_drop)
    
    print("Creating new procedure...")
    cursor.execute(sql_create)
    
    conn.commit()
    print("Successfully updated stored procedure: generate_random_pm_schedules with Collation Fix")
    
    cursor.close()
    conn.close()

except mysql.connector.Error as err:
    print(f"Error: {err}")
except Exception as e:
    print(f"Error: {e}")
