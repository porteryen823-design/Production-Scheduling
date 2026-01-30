-- Optimized MariaDB Stored Procedure for Batch Updates
-- Note: MariaDB 10.5 supports JSON_TABLE

DELIMITER //

CREATE OR REPLACE PROCEDURE sp_UpdatePlanResultsJSON_Optimized(
    IN p_LotsJson LONGTEXT,
    IN p_OpsJson LONGTEXT
)
BEGIN
    -- 1. Batch Update Lots using JOIN and JSON_TABLE
    IF p_LotsJson IS NOT NULL AND JSON_VALID(p_LotsJson) THEN
        UPDATE Lots l
        JOIN (
            SELECT 
                LotId,
                PlanFinishDate,
                ROUND(TIMESTAMPDIFF(SECOND, DueDate, PlanFinishDate) / 86400, 2) as NewDelayDays
            FROM JSON_TABLE(p_LotsJson, '$[*]' COLUMNS (
                LotId VARCHAR(50) PATH '$.LotId',
                PlanFinishDate DATETIME PATH '$.PlanFinishDate'
            )) as jt
            JOIN Lots ON Lots.LotId = jt.LotId
        ) src ON l.LotId = src.LotId
        SET l.PlanFinishDate = src.PlanFinishDate,
            l.Delay_Days = src.NewDelayDays;
    END IF;

    -- 2. Update LotOperations
    -- For JSON_ARRAY_APPEND, sequential processing is usually safer, 
    -- but we can still use a loop for now or optimize further if needed.
    -- Given PlanHistory is a JSON array, concurrent updates on the SAME row is rare 
    -- but possible if threads process different operations of the same lot.
    IF p_OpsJson IS NOT NULL AND JSON_VALID(p_OpsJson) THEN
        SET @i = 0;
        SET @n = JSON_LENGTH(p_OpsJson);
        WHILE @i < @n DO
            SET @v_LotId = JSON_VALUE(p_OpsJson, CONCAT('$[', @i, '].LotId'));
            SET @v_Step = JSON_VALUE(p_OpsJson, CONCAT('$[', @i, '].Step'));
            SET @v_Start = JSON_VALUE(p_OpsJson, CONCAT('$[', @i, '].Start'));
            SET @v_End = JSON_VALUE(p_OpsJson, CONCAT('$[', @i, '].End'));
            SET @v_Machine = JSON_VALUE(p_OpsJson, CONCAT('$[', @i, '].Machine'));
            SET @v_HistoryInfo = JSON_EXTRACT(p_OpsJson, CONCAT('$[', @i, '].HistoryInfo'));

            IF @v_LotId IS NOT NULL AND @v_Step IS NOT NULL THEN
                UPDATE LotOperations
                SET PlanCheckInTime = @v_Start,
                    PlanCheckOutTime = @v_End,
                    PlanMachineId = @v_Machine,
                    PlanHistory = JSON_ARRAY_APPEND(IFNULL(PlanHistory, '[]'), '$', @v_HistoryInfo)
                WHERE LotId = @v_LotId AND Step = @v_Step;
            END IF;

            SET @i = @i + 1;
        END WHILE;
    END IF;
END //

DELIMITER ;
