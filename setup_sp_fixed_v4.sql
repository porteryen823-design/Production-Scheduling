-- Fixed SQL using JSON_TABLE and explicit COLLATION for MySQL 8.0 compatibility

DELIMITER //

-- 1. Save results to DynamicSchedulingJob
DROP PROCEDURE IF EXISTS sp_SaveDynamicSchedulingJob //
CREATE PROCEDURE sp_SaveDynamicSchedulingJob(
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
    
    SELECT parameter_value INTO v_sim_end 
    FROM ui_settings 
    WHERE parameter_name = 'simulation_end_time' 
    LIMIT 1;
    
    INSERT INTO DynamicSchedulingJob (
        ScheduleId, LotPlanRaw, CreateDate, CreateUser, 
        PlanSummary, LotPlanResult, LotStepResult, machineTaskSegment, simulation_end_time
    )
    VALUES (
        p_ScheduleId, p_LotPlanRaw, NOW(), p_CreateUser, 
        p_PlanSummary, p_LotPlanResult, p_LotStepResult, p_machineTaskSegment, v_sim_end
    );
END //

-- 2. Batch update Lot results using JSON_TABLE
DROP PROCEDURE IF EXISTS sp_UpdatePlanResultsJSON //
CREATE PROCEDURE sp_UpdatePlanResultsJSON(
    IN p_LotsJson LONGTEXT,
    IN p_OpsJson LONGTEXT
)
BEGIN
    -- Update Lots table
    IF p_LotsJson IS NOT NULL AND JSON_VALID(p_LotsJson) THEN
        UPDATE Lots l
        INNER JOIN (
            SELECT * FROM JSON_TABLE(p_LotsJson, '$[*]' COLUMNS (
                LotId VARCHAR(50) PATH '$.LotId',
                PlanFinishDate DATETIME PATH '$.PlanFinishDate',
                Delay_Days DOUBLE PATH '$.Delay_Days'
            )) as jt
        ) src ON l.LotId COLLATE utf8mb4_general_ci = src.LotId COLLATE utf8mb4_general_ci
        SET l.PlanFinishDate = src.PlanFinishDate,
            l.Delay_Days = src.Delay_Days;
    END IF;

    -- Update LotOperations table
    IF p_OpsJson IS NOT NULL AND JSON_VALID(p_OpsJson) THEN
        BEGIN
            DECLARE done INT DEFAULT FALSE;
            DECLARE v_LotId VARCHAR(50);
            DECLARE v_Step VARCHAR(50);
            DECLARE v_Start DATETIME;
            DECLARE v_End DATETIME;
            DECLARE v_Machine VARCHAR(50);
            DECLARE v_HistoryInfo JSON;
            
            DECLARE cur CURSOR FOR 
                SELECT LotId, Step, Start, End, Machine, HistoryInfo 
                FROM JSON_TABLE(p_OpsJson, '$[*]' COLUMNS (
                    LotId VARCHAR(50) PATH '$.LotId',
                    Step VARCHAR(50) PATH '$.Step',
                    Start DATETIME PATH '$.Start',
                    End DATETIME PATH '$.End',
                    Machine VARCHAR(50) PATH '$.Machine',
                    HistoryInfo JSON PATH '$.HistoryInfo'
                )) as jt;
                
            DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
            
            OPEN cur;
            read_loop: LOOP
                FETCH cur INTO v_LotId, v_Step, v_Start, v_End, v_Machine, v_HistoryInfo;
                IF done THEN
                    LEAVE read_loop;
                END IF;
                
                UPDATE LotOperations
                SET PlanCheckInTime = v_Start,
                    PlanCheckOutTime = v_End,
                    PlanMachineId = v_Machine,
                    PlanHistory = JSON_ARRAY_APPEND(IFNULL(PlanHistory, '[]'), '$', v_HistoryInfo)
                WHERE LotId COLLATE utf8mb4_general_ci = v_LotId COLLATE utf8mb4_general_ci 
                  AND Step COLLATE utf8mb4_general_ci = v_Step COLLATE utf8mb4_general_ci;
            END LOOP;
            CLOSE cur;
        END;
    END IF;
END //

DELIMITER ;
