-- MariaDB Stored Procedures for Scheduler Optimization

DELIMITER //

-- 1. Save results to DynamicSchedulingJob
CREATE OR REPLACE PROCEDURE sp_SaveDynamicSchedulingJob(
    IN p_ScheduleId VARCHAR(50),
    IN p_LotPlanRaw LONGTEXT,
    IN p_CreateUser VARCHAR(50),
    IN p_PlanSummary VARCHAR(2500),
    IN p_LotPlanResult LONGTEXT,
    IN p_LotStepResult LONGTEXT,
    IN p_machineTaskSegment LONGTEXT
)
BEGIN
    DECLARE v_sim_end DATETIME;
    
    -- Get simulation_end_time from ui_settings
    SELECT parameter_value INTO v_sim_end 
    FROM ui_settings 
    WHERE parameter_name = 'simulation_end_time' 
    LIMIT 1;
    
    INSERT INTO DynamicSchedulingJob (
        ScheduleId, 
        LotPlanRaw, 
        CreateDate,
        CreateUser, 
        PlanSummary, 
        LotPlanResult, 
        LotStepResult, 
        machineTaskSegment, 
        simulation_end_time
    )
    VALUES (
        p_ScheduleId, 
        p_LotPlanRaw, 
        NOW(),
        p_CreateUser, 
        p_PlanSummary, 
        p_LotPlanResult, 
        p_LotStepResult, 
        p_machineTaskSegment, 
        v_sim_end
    );
END //

-- 2. Batch update Lot results using JSON
-- Expected p_LotsJson: [{"LotId": "...", "PlanFinishDate": "...", "Delay_Days": ...}, ...]
-- Expected p_OpsJson: [{"LotId": "...", "Step": "...", "Start": "...", "End": "...", "Machine": "...", "HistoryEntry": "..."}]
CREATE OR REPLACE PROCEDURE sp_UpdatePlanResultsJSON(
    IN p_LotsJson LONGTEXT,
    IN p_OpsJson LONGTEXT
)
BEGIN
    DECLARE i INT DEFAULT 0;
    DECLARE n INT DEFAULT 0;
    DECLARE v_LotId VARCHAR(50);
    DECLARE v_PlanFinishDate DATETIME;
    DECLARE v_DelayDays DOUBLE;
    
    DECLARE v_Step VARCHAR(50);
    DECLARE v_Start DATETIME;
    DECLARE v_End DATETIME;
    DECLARE v_Machine VARCHAR(50);
    DECLARE v_HistoryInfo LONGTEXT;

    -- Update Lots
    SET n = JSON_LENGTH(p_LotsJson);
    WHILE i < n DO
        SET v_LotId = JSON_VALUE(p_LotsJson, CONCAT('$[', i, '].LotId'));
        SET v_PlanFinishDate = JSON_VALUE(p_LotsJson, CONCAT('$[', i, '].PlanFinishDate'));
        SET v_DelayDays = JSON_VALUE(p_LotsJson, CONCAT('$[', i, '].Delay_Days'));

        UPDATE Lots 
        SET PlanFinishDate = v_PlanFinishDate, 
            Delay_Days = v_DelayDays 
        WHERE LotId COLLATE utf8mb4_general_ci = v_LotId COLLATE utf8mb4_general_ci;
        
        SET i = i + 1;
    END WHILE;

    -- Update LotOperations
    SET i = 0;
    SET n = JSON_LENGTH(p_OpsJson);
    WHILE i < n DO
        SET v_LotId = JSON_VALUE(p_OpsJson, CONCAT('$[', i, '].LotId'));
        SET v_Step = JSON_VALUE(p_OpsJson, CONCAT('$[', i, '].Step'));
        SET v_Start = JSON_VALUE(p_OpsJson, CONCAT('$[', i, '].Start'));
        SET v_End = JSON_VALUE(p_OpsJson, CONCAT('$[', i, '].End'));
        SET v_Machine = JSON_VALUE(p_OpsJson, CONCAT('$[', i, '].Machine'));
        SET v_HistoryInfo = JSON_EXTRACT(p_OpsJson, CONCAT('$[', i, '].HistoryInfo'));

        UPDATE LotOperations
        SET PlanCheckInTime = v_Start,
            PlanCheckOutTime = v_End,
            PlanMachineId = v_Machine,
            PlanHistory = JSON_ARRAY_APPEND(IFNULL(PlanHistory, '[]'), '$', CAST(v_HistoryInfo AS JSON))
        WHERE LotId COLLATE utf8mb4_general_ci = v_LotId COLLATE utf8mb4_general_ci 
          AND Step COLLATE utf8mb4_general_ci = v_Step COLLATE utf8mb4_general_ci;

        SET i = i + 1;
    END WHILE;
END //

DELIMITER ;
