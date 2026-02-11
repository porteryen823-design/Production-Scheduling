# MySQL 資料庫表結構

基於 `Scheduler_Full_Example_Qtime_V1_Wip.py` 中的 `jobs_data` 結構，已在 MySQL 資料庫中建立以下資料表來存儲排程相關資料。

## 新建立的資料表

### 1. Lots - 工單基本資訊
```sql
CREATE TABLE Lots (
    LotId VARCHAR(50) PRIMARY KEY,
    Priority INT NOT NULL,
    DueDate DATETIME NOT NULL,
    PlanFinishDate DATETIME NULL,
    ActualFinishDate DATETIME NULL,
    ProductID VARCHAR(50) NULL,
    ProductName VARCHAR(100) NULL,
    CustomerID VARCHAR(50) NULL,
    CustomerName VARCHAR(100) NULL,
    LotCreateDate DATETIME NULL,
    Delay_Days DECIMAL(10,2) NULL,
    PlanStartTime DATETIME NULL
);
```
- `LotId` (VARCHAR(50), PK): 工單 ID
- `Priority` (INT): 優先權
- `DueDate` (DATETIME): 到期日
- `PlanFinishDate` (DATETIME): 計劃完成日期
- `ActualFinishDate` (DATETIME): 實際完成日期
- `ProductID` (VARCHAR(50)): 產品 ID
- `ProductName` (VARCHAR(100)): 產品名稱
- `CustomerID` (VARCHAR(50)): 客戶 ID
- `CustomerName` (VARCHAR(100)): 客戶名稱
- `LotCreateDate` (DATETIME): 工單建立日期
- `Delay_Days` (DECIMAL(10,2)): 延遲天數
- `PlanStartTime` (DATETIME): 計劃開始時間

### 2. LotOperations - 工單的作業步驟
```sql
CREATE TABLE LotOperations (
    LotId VARCHAR(50) NOT NULL,
    Step VARCHAR(20) NOT NULL,
    MachineGroup VARCHAR(20) NOT NULL,
    Duration INT NOT NULL,
    Sequence INT NOT NULL,
    CheckInTime DATETIME NULL,
    CheckOutTime DATETIME NULL,
    StepStatus INT DEFAULT 0,
    PlanCheckInTime DATETIME NULL,
    PlanCheckOutTime DATETIME NULL,
    PlanMachineId VARCHAR(20) NULL,
    PlanHistory JSON NULL,
    PRIMARY KEY (LotId, Step),
    FOREIGN KEY (LotId) REFERENCES Lots(LotId)
);
```
- `LotId` (VARCHAR(50), FK): 工單 ID
- `Step` (VARCHAR(20)): 作業步驟名稱
- `MachineGroup` (VARCHAR(20)): 機器群組
- `Duration` (INT): 作業持續時間（分鐘）
- `Sequence` (INT): 作業順序
- `CheckInTime` (DATETIME): 作業開始檢查時間
- `CheckOutTime` (DATETIME): 作業完成檢查時間
- `StepStatus` (INT): 作業狀態 (0:預設, 1:CheckIn, 2:CheckOut)
- `PlanCheckInTime` (DATETIME): 計劃作業開始時間
- `PlanCheckOutTime` (DATETIME): 計劃作業完成時間
- `PlanMachineId` (VARCHAR(20)): 計劃分配機器 ID
- `PlanHistory` (JSON): 計劃歷史記錄，包含每次重排的 PlanID, PlanCheckInTime, PlanCheckOutTime
- PK: (`LotId`, `Step`)

### 3. MachineGroups - 機器群組
```sql
CREATE TABLE MachineGroups (
    GroupId VARCHAR(20) PRIMARY KEY,
    GroupName VARCHAR(100) NOT NULL
);
```
- `GroupId` (VARCHAR(20), PK): 群組 ID
- `GroupName` (VARCHAR(100)): 群組名稱

### 4. Machines - 機器
```sql
CREATE TABLE Machines (
    MachineId VARCHAR(20) PRIMARY KEY,
    GroupId VARCHAR(20) NOT NULL,
    FOREIGN KEY (GroupId) REFERENCES MachineGroups(GroupId)
);
```
- `MachineId` (VARCHAR(20), PK): 機器 ID
- `GroupId` (VARCHAR(20), FK): 所屬群組

### 5. CompletedOperations - 已完成的作業
```sql
CREATE TABLE CompletedOperations (
    LotId VARCHAR(50) NOT NULL,
    Step VARCHAR(20) NOT NULL,
    MachineId VARCHAR(20) NOT NULL,
    StartTime DATETIME NOT NULL,
    EndTime DATETIME NOT NULL,
    PRIMARY KEY (LotId, Step),
    FOREIGN KEY (LotId) REFERENCES Lots(LotId),
    FOREIGN KEY (MachineId) REFERENCES Machines(MachineId)
);
```
- `LotId` (VARCHAR(50)): 工單 ID
- `Step` (VARCHAR(20)): 作業步驟
- `MachineId` (VARCHAR(20)): 使用的機器
- `StartTime` (DATETIME): 開始時間
- `EndTime` (DATETIME): 結束時間
- PK: (`LotId`, `Step`)

### 6. WIPOperations - 進行中的作業
```sql
CREATE TABLE WIPOperations (
    LotId VARCHAR(50) NOT NULL,
    Step VARCHAR(20) NOT NULL,
    MachineId VARCHAR(20) NOT NULL,
    StartTime DATETIME NOT NULL,
    ElapsedMinutes INT NOT NULL,
    PRIMARY KEY (LotId, Step),
    FOREIGN KEY (LotId) REFERENCES Lots(LotId),
    FOREIGN KEY (MachineId) REFERENCES Machines(MachineId)
);
```
- `LotId` (VARCHAR(50)): 工單 ID
- `Step` (VARCHAR(20)): 作業步驟
- `MachineId` (VARCHAR(20)): 使用的機器
- `StartTime` (DATETIME): 開始時間
- `ElapsedMinutes` (INT): 已處理分鐘數
- PK: (`LotId`, `Step`)

### 7. FrozenOperations - 凍結的作業
```sql
CREATE TABLE FrozenOperations (
    LotId VARCHAR(50) NOT NULL,
    Step VARCHAR(20) NOT NULL,
    MachineId VARCHAR(20) NOT NULL,
    StartTime DATETIME NOT NULL,
    EndTime DATETIME NOT NULL,
    PRIMARY KEY (LotId, Step),
    FOREIGN KEY (LotId) REFERENCES Lots(LotId),
    FOREIGN KEY (MachineId) REFERENCES Machines(MachineId)
);
```
- `LotId` (VARCHAR(50)): 工單 ID
- `Step` (VARCHAR(20)): 作業步驟
- `MachineId` (VARCHAR(20)): 使用的機器
- `StartTime` (DATETIME): 開始時間
- `EndTime` (DATETIME): 結束時間
- PK: (`LotId`, `Step`)

## 資料表關聯圖

```
Lots (1) ──── (N) LotOperations
  │
  └─── (1) ──── (N) CompletedOperations
  │
  └─── (1) ──── (N) WIPOperations
  │
  └─── (1) ──── (N) FrozenOperations

MachineGroups (1) ──── (N) Machines
```

## 支援的作業狀態

這些表結構完整支援 `jobs_data` 中的所有資料類型：

1.  **正常作業 (Normal Operations)**: 存儲在 `LotOperations` 表中，可由排程系統動態分配機器
2.  **已完成作業 (Completed Operations)**: 存儲在 `CompletedOperations` 表中，包含確定的開始和結束時間
3.  **進行中作業 (WIP Operations)**: 存儲在 `WIPOperations` 表中，包含開始時間和已處理時間
4.  **凍結作業 (Frozen Operations)**: 存儲在 `FrozenOperations` 表中，已預先排程但尚未開始

## 作業步驟狀態追蹤

`LotOperations` 表中的狀態欄位用於追蹤每個作業步驟的執行狀態：

- `StepStatus`: 作業狀態
    - `0`: 預設狀態 (尚未開始)
    - `1`: CheckIn (作業已開始)
    - `2`: CheckOut (作業已完成)

- `CheckInTime`: 記錄作業開始檢查的時間戳
- `CheckOutTime`: 記錄作業完成檢查的時間戳

## 計劃排程欄位

`LotOperations` 表中的計劃排程欄位用於記錄排程系統計算出的最佳作業計劃：

- `PlanCheckInTime`: 計劃作業開始時間
- `PlanCheckOutTime`: 計劃作業完成時間
- `PlanMachineId`: 計劃分配的具體機器 ID

這些欄位可用於：
- 排程系統預測作業時間
- 生產計劃制定
- 作業進度監控
- 資源分配優化
- 甘特圖顯示
- 生產排程可視化

## 資料完整性

所有表都包含適當的外鍵約束來維持資料完整性：
- `LotOperations`、`CompletedOperations`、`WIPOperations`、`FrozenOperations` 都參考 `Lots.LotId`
- `Machines` 參考 `MachineGroups.GroupId`
- `CompletedOperations`、`WIPOperations`、`FrozenOperations` 都參考 `Machines.MachineId`

## 資料維護 Stored Procedures

### sp_clean_lots
用於清理測試資料的 stored procedure：

```sql
CREATE PROCEDURE sp_clean_lots()
BEGIN
    -- 先刪除 LotOperations 表中的所有資料
    DELETE FROM LotOperations;
    
    -- 然後刪除 Lots 表中的所有資料
    DELETE FROM Lots;

    -- 然後刪除 DynamicSchedulingJob 表中的所有資料
    DELETE FROM DynamicSchedulingJob;    
   
    -- 更新 ui_settings, 將模擬結束時間 初值化= null
    UPDATE ui_settings SET  parameter_value = NULL WHERE  parameter_name= 'simulation_end_time';
    
END
```

**使用方法**:
```sql
CALL sp_clean_lots();
```

**功能說明**:
- 按照外鍵約束的順序刪除資料（先刪除子表 LotOperations，再刪除主表 Lots）
- 用於測試環境清理資料，準備新的測試資料

### generate_random_pm_schedules
產生隨機預防性保養排程的 stored procedure：

```sql
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
    DECLARE max_attempts INT DEFAULT 10;

    DECLARE done INT DEFAULT FALSE;
    DECLARE machine_id_val VARCHAR(20);
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
              AND unavailable_type = 'PM'
              AND Status = 'ACTIVE'
              AND (
                  (start_time <= start_date AND end_time > start_date) OR
                  (start_time < end_date AND end_time >= end_date) OR
                  (start_time >= start_date AND end_time <= end_date)
              );

            -- 如果沒有重疊，插入記錄
            IF overlap_count = 0 THEN
                INSERT INTO machine_unavailable_periods
                (MachineId, start_time, end_time, unavailable_type, reason, source, created_by)
                VALUES
                (machine_id_val, start_date, end_date, 'PM',
                 CONCAT('隨機產生的預防性保養 - ', machine_id_val, ' (', i+1, '/', num_records, ')'),
                 'AUTO', 'SYSTEM');

                SET i = i + 1;
            END IF;
            -- 如果重疊，繼續迴圈重新生成（不增加 i）

        END WHILE;

    END LOOP;

    CLOSE cur;

END
```

**使用方法**:
```sql
CALL generate_random_pm_schedules();
```

**功能說明**:
- 為資料庫中的每個機台隨機產生 1-4 筆預防性保養 (PM) 記錄
- 每筆記錄的開始時間：從 `simulation_start_time_setting` 開始到 30 天後的隨機日期
- 每筆記錄的持續時間：0.2 到 1 天的隨機時長 (4.8 到 24 小時)
- 確保每個機台的 PM 時間不會相互重疊
- unavailable_type 設為 'PM'，source 設為 'AUTO'，created_by 設為 'SYSTEM'
- 原因欄位會標記是第幾筆記錄 (如 "隨機產生的預防性保養 - M01-1 (1/3)")
- 適用於測試環境產生模擬的保養排程資料，避免過度阻塞機台

### sp_InsertLot
用於批次產生測試批號（Lots）與對應作業（Operations）的預存程序。

**功能更新**:
- 支援隨機作業數量：每個批號會隨機產生 **9 到 15 個** 作業步驟。
- 自動對應機台：步驟名稱（STEP1-STEP15）自動對應機台群組（M01-M15）。
- 標準工時：根據範本設定每個步驟的 Duration。
- 支援模擬時間：可選擇以 `simulation_end_time` 或當前時間作為交期（DueDate）的計算基準。

```sql
-- 使用方法 (產生 10 個批號，優先級 100，使用模擬結束時間計算交期)
CALL sp_InsertLot(10, 100, TRUE);
```

### sp_UpdatePlanResultsJSON
高效率的批次排程結果更新預存程序，使用 JSON 格式輸入以減少資料庫來回次數。

**功能說明**:
- 批次更新 `Lots` 表的預計完工時間（PlanFinishDate）。
- 批次更新 `LotOperations` 表的排程時間、機台、以及歷史記錄。
- 內部使用 JSON 導引技術，結合循環處理實現高性能更新。

### sp_SaveDynamicSchedulingJob
將完整的排程結果快照儲存至 `DynamicSchedulingJob` 表。

**功能說明**:
- 一次讀取所有排程結果 JSON。
- 記錄排程 ID、摘要資訊以及詳細的甘特圖段數據。
- 確保前端 API 可以快速讀取最後一次排程狀態。

### sp_InsertSimulationPlanning
將目前的動態排程結果（DynamicSchedulingJob）備份至模擬規劃表。

**功能說明**:
- 將 `DynamicSchedulingJob` 的所有記錄複製到 `DynamicSchedulingJob_Snap`。
- 支援傳入 `key_value` 與 `remark` 作為備份點的識別與註記。

### sp_LoadSimulationToHist
將特定的模擬規劃備份搬移至歷史表或還原至歷史區間。

**功能說明**:
- 將 `DynamicSchedulingJob_Snap` 中符合特定 `key_value` 的資料搬移至歷史存檔。
- 目前實作也支援將資料載入至 `DynamicSchedulingJob_Hist`（依據具體業務需求而定）。

## 機台管理相關資料表

### 8. Machines - 機台主檔表 (已更新)
```sql
CREATE TABLE Machines (
    MachineId VARCHAR(20) PRIMARY KEY,
    GroupId VARCHAR(20) NOT NULL,
    machine_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (GroupId) REFERENCES MachineGroups(GroupId)
);
```
- `MachineId` (VARCHAR(20), PK): 機器 ID
- `GroupId` (VARCHAR(20), FK): 所屬群組
- `machine_name` (VARCHAR(100)): 機台名稱
- `is_active` (BOOLEAN): 是否啟用 (預設 TRUE)
- `created_at` (TIMESTAMP): 建立時間
- `updated_at` (TIMESTAMP): 更新時間

### 9. machine_unavailable_periods - 機台不可用時段統一管理表
```sql
CREATE TABLE machine_unavailable_periods (
    id INT AUTO_INCREMENT PRIMARY KEY,
    MachineId VARCHAR(20) NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,

    -- 擴充類型,包含排程相關
    unavailable_type ENUM(
        -- 原有類型
        'PM',              -- 預防性保養
        'CM',              -- 矯正性維修
        'BREAK',           -- 休息時間
        'SHIFT_CHANGE',    -- 換班時間
        'DOWNTIME',        -- 故障停機

        -- 新增排程類型
        'COMPLETED',       -- 已完成作業 (CompletedOps)
        'WIP',             -- 進行中作業 (WIPOps)
        'FROZEN',          -- 凍結作業 (FrozenOps)
        'RESERVED',        -- 預留/保留
        'OTHER'
    ) NOT NULL,

    -- 關聯資訊
    lot_id VARCHAR(50),              -- 關聯的工單 (如果是作業佔用)
    operation_step VARCHAR(50),      -- 關聯的工序 (STEP1, STEP2...)

    -- 其他資訊
    reason VARCHAR(255),
    is_recurring BOOLEAN DEFAULT FALSE,
    recurrence_rule JSON,

    -- 管理欄位
    source VARCHAR(50),              -- 資料來源: 'MANUAL', 'SCHEDULE', 'AUTO'
    is_locked BOOLEAN DEFAULT FALSE, -- 是否鎖定(不可修改)
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (MachineId) REFERENCES Machines(MachineId) ON DELETE CASCADE,
    INDEX idx_machine_time (MachineId, start_time, end_time),
    INDEX idx_lot (lot_id),
    INDEX idx_type (unavailable_type),
    INDEX idx_source (source),

    CONSTRAINT chk_time_valid CHECK (end_time > start_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```
- `Id` (INT, PK): 自動編號
- `MachineId` (VARCHAR(20), FK): 機台 ID
- `StartTime` (DATETIME): 開始時間
- `EndTime` (DATETIME): 結束時間
- `PeriodType` (ENUM): 時段類型 (支援維修和排程作業類型)
- `LotId` (VARCHAR(50)): 工單批號 (排程作業時必須填寫)
- `OperationStep` (VARCHAR(20)): 作業步驟 (如 STEP1, STEP2)
- `Reason` (VARCHAR(255)): 原因/備註
- `Priority` (INT): 優先級 (用於衝突處理，預設 0)
- `IsRecurring` (BOOLEAN): 是否重複性事件
- `RecurrenceRule` (JSON): 重複規則
- `Status` (ENUM): 狀態 ('ACTIVE', 'CANCELLED', 'COMPLETED')
- `CreatedBy` (VARCHAR(50)): 建立者
- `CreatedAt` (TIMESTAMP): 建立時間
- `UpdatedAt` (TIMESTAMP): 更新時間

### 10. DynamicSchedulingJob - 動態排程作業結果表
```sql
CREATE TABLE DynamicSchedulingJob (
    ScheduleId VARCHAR(50) NOT NULL,
    LotPlanRaw LONGTEXT DEFAULT NULL,
    CreateDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    CreateUser VARCHAR(50) DEFAULT NULL,
    simulation_end_time DATETIME DEFAULT NULL,
    PlanSummary VARCHAR(2500) DEFAULT NULL,
    LotPlanResult LONGTEXT DEFAULT NULL,
    LotStepResult LONGTEXT DEFAULT NULL,
    machineTaskSegment LONGTEXT DEFAULT NULL,
    PRIMARY KEY (ScheduleId)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```
- `ScheduleId` (VARCHAR(50), PK): 排程唯一編號
- `LotPlanRaw` (LONGTEXT): 原始輸入工單資料 (JSON 格式)
- `CreateDate` (DATETIME): 排程執行時間
- `CreateUser` (VARCHAR): 執行者
- `simulation_end_time` (DATETIME): 模擬時鐘結束點
- `PlanSummary` (VARCHAR): 排程結果摘要說明
- `LotPlanResult` (LONGTEXT): 完工時間預測結果 (JSON 格式)
- `LotStepResult` (LONGTEXT): 各工序詳細排程結果 (JSON 格式)
- `machineTaskSegment` (LONGTEXT): 甘特圖用的條狀資料 (JSON 格式)

### 11. ui_settings - UI 介面參數設定表
```sql
CREATE TABLE ui_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    parameter_name VARCHAR(255) UNIQUE NOT NULL,
    parameter_value TEXT,
    remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```
- `id` (INT, PK): 自動編號
- `parameter_name` (VARCHAR, UNIQUE): 參數名稱 (如 `spin_lot_count`, `datetime_start`)
- `parameter_value` (TEXT): 參數值 (字串格式儲存)
- `remark` (TEXT): 備註說明
- `created_at` (DATETIME): 建立時間
- `updated_at` (DATETIME): 最後更新時間

**常用參數清單**:
- `spin_lot_count`: 預設產生的 Lot 數量
- `datetime_start`: 模擬時鐘開始時間
- `spin_iterations`: 模擬次數
- `spin_timedelta`: 模擬時間增量 (秒)
- `datetime_reschedule_start`: 重新排程設定的開始時間


### 12. SimulationData - 模擬結果追蹤表
```sql
CREATE TABLE SimulationData (
    id INT AUTO_INCREMENT PRIMARY KEY,
    simulation_start_time DATETIME,
    simulation_end_time DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
- `id` (INT, PK): 自動編號
- `simulation_start_time` (DATETIME): 該次模擬的啟始時間
- `simulation_end_time` (DATETIME): 該次模擬的實際結束時間
- `created_at` (TIMESTAMP): 紀錄建立時間

**功能說明**:
- 用於記錄每次模擬時鐘運行後的結果範圍。
- `qt_gui.py` 會自動讀取最後一筆紀錄的 `simulation_end_time` 並加上緩衝時間，作為下一次模擬或排程的預設起始點。



### 13. MachineGroupUtilization - 機台群組利用率統計表
```sql
CREATE TABLE MachineGroupUtilization (
    id INT AUTO_INCREMENT PRIMARY KEY,
    PlanID VARCHAR(50) NOT NULL,
    GroupId VARCHAR(20) NOT NULL,
    CalculationWindowStart DATETIME NOT NULL,
    CalculationWindowEnd DATETIME NOT NULL,
    MachineCount INT NOT NULL,
    TotalUsedMinutes INT NOT NULL,
    TotalCapacityMinutes INT NOT NULL,
    UtilizationRate DECIMAL(5, 2) NOT NULL,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_plan (PlanID),
    INDEX idx_group (GroupId)
);
```
- `id` (INT, PK): 自動編號
- `PlanID` (VARCHAR): 關聯的排程編號
- `GroupId` (VARCHAR): 機台群組 ID (如 M01, M02)
- `CalculationWindowStart/End` (DATETIME): 計算利用率所涵蓋的時間視窗
- `MachineCount` (INT): 該群組內的機台總數
- `TotalUsedMinutes` (INT): 該群組在視窗內實際被分配的總加工分鐘數
- `TotalCapacityMinutes` (INT): 該群組在視窗內的總可用產能（分鐘）
- `UtilizationRate` (DECIMAL): 利用率百分比 (如 85.50)
- `CreatedAt` (TIMESTAMP): 紀錄建立時間

### 14. DynamicSchedulingJob_Snap - 模擬規劃備份表 (快照儲存)
```sql
CREATE TABLE DynamicSchedulingJob_Snap (
    id INT AUTO_INCREMENT PRIMARY KEY,
    key_value VARCHAR(100) NOT NULL,
    remark TEXT DEFAULT NULL,
    
    -- 複製自 DynamicSchedulingJob 的欄位
    ScheduleId VARCHAR(50) DEFAULT NULL,
    LotPlanRaw LONGTEXT DEFAULT NULL,
    CreateDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    CreateUser VARCHAR(50) DEFAULT NULL,
    PlanSummary VARCHAR(2500) DEFAULT NULL,
    LotPlanResult LONGTEXT DEFAULT NULL,
    LotStepResult LONGTEXT DEFAULT NULL,
    machineTaskSegment LONGTEXT DEFAULT NULL,
    simulation_end_time DATETIME DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```
- `id` (INT, PK): 自動編號 (備份點唯一 ID)
- `key_value` (VARCHAR): 識別標籤，用於同時存入多筆記錄時作為關聯（已移除索引以支援彈性寫入）
- `remark` (TEXT): 備份備註說明
- `ScheduleId` (VARCHAR): 原排程編號
- `LotPlanRaw` (LONGTEXT): 原始工單資料 JSON
- `PlanSummary` (VARCHAR): 排程摘要
- `LotPlanResult` (LONGTEXT): 完工時間結果 JSON
- `LotStepResult` (LONGTEXT): 詳細工序結果 JSON
- `machineTaskSegment` (LONGTEXT): 甘特圖段落 JSON
- `simulation_end_time` (DATETIME): 當時的模擬結束時間

### 15. DynamicSchedulingJob_Snap_Hist - 模擬規劃歷史表 (封存儲存)
```sql
CREATE TABLE DynamicSchedulingJob_Snap_Hist (
    id INT AUTO_INCREMENT PRIMARY KEY,
    key_value VARCHAR(100) NOT NULL,
    remark TEXT DEFAULT NULL,
    
    -- 欄位與 SimulationPlanningJob 完全一致
    ScheduleId VARCHAR(50) DEFAULT NULL,
    LotPlanRaw LONGTEXT DEFAULT NULL,
    CreateDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    CreateUser VARCHAR(50) DEFAULT NULL,
    PlanSummary VARCHAR(2500) DEFAULT NULL,
    LotPlanResult LONGTEXT DEFAULT NULL,
    LotStepResult LONGTEXT DEFAULT NULL,
    machineTaskSegment LONGTEXT DEFAULT NULL,
    simulation_end_time DATETIME DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```
- **功能**: 用於存放已被執行過或已結案的規劃快照。
- **結構**: 與 `DynamicSchedulingJob_Snap` 完全相同，方便資料搬移與查詢。

### 📊 資料表功能說明對照表 (更新)

| 資料表名稱 | 英文名稱 | 主要用途 | 使用時機 | 資料範例 | 是否必要 |
|-----------|---------|---------|---------|---------|---------|
| 機台主檔表 | machines | 儲存所有機台的基本資料 | 系統初始化時建立,新增機台時使用 | M01-1, M01-2 屬於 M01 群組 | ✅ 必要 |
| 機台不可用時段表 | machine_unavailable_periods | 記錄機台無法使用的時間區間 | 排程時避開維修、保養等 | M01-1 於 1/18 14:00-16:00 維修 | ✅ 必要 |
| 動態排程作業表 | DynamicSchedulingJob | 儲存動態排程結果資料 | 執行動態排程時儲存結果 | 排程結果 JSON 格式儲存 | ✅ 必要 |
| 模擬規劃備份表 | DynamicSchedulingJob_Snap | 儲存模擬規劃的快照/備份 | 手動或自動備份排程結果以便還原 | 存儲特定版本排程結果 | ✅ 必要 |
| UI 介面參數設定表 | ui_settings | 跨工作階段保存介面輸入值 (鍵值對) | GUI 啟動與數值改變時同步 | parameter_name='spin_lot_count', parameter_value='5' | ✅ 必要 |
| 模擬結果追蹤表 | SimulationData | 保存模擬時鐘的最後結束點 | 模擬完成時寫入,作為下次計算參考 | 模擬結束於 2026-01-22 15:30:00 | ✅ 必要 |
| 模擬規劃歷史表 | DynamicSchedulingJob_Snap_Hist | 儲存已結案或歷史規劃紀錄 | 長期保存歷史資料，不影響主表查詢 | 封存的排程結果 | ✅ 必要 |
| 機台群組利用率統計表 | MachineGroupUtilization | 紀錄排程後的資源平衡狀況 | 分析瓶頸與產能規劃 | M01 群組利用率 85.5% | ✅ 必要 |

## 更新後的資料表關聯圖 (Ver 1.3)

```
Lots (1) ──── (N) LotOperations
  │
  ├─── (1) ──── (N) CompletedOperations
  │
  ├─── (1) ──── (N) WIPOperations
  │
  └─── (1) ──── (N) FrozenOperations

MachineGroups (1) ──── (N) Machines
  │
  └─── (1) ──── (N) machine_unavailable_periods

DynamicSchedulingJob (獨立結果表)
  │
  └─── (備份) ─── DynamicSchedulingJob_Snap (快照快照)
          │
          └─── (結案/封存) ─── DynamicSchedulingJob_Snap_Hist (歷史紀錄)

ui_settings (設定檔 / 鍵值對)
SimulationData (模擬紀錄)
```