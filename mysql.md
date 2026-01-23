# MySQL 資料庫表結構

基於 `Scheduler_Full_Example_Qtime_V1_Wip.py` 中的 `jobs_data` 結構，已在 MySQL 資料庫中建立以下資料表來存儲排程相關資料。

## 新建立的資料表

### 1. Lots - 工單基本資訊
```sql
CREATE TABLE Lots (
    LotId VARCHAR(50) PRIMARY KEY,
    Priority INT NOT NULL,
    DueDate DATETIME NOT NULL,
    ActualFinishDate DATETIME NULL,
    ProductID VARCHAR(50) NULL,
    ProductName VARCHAR(100) NULL,
    CustomerID VARCHAR(50) NULL,
    CustomerName VARCHAR(100) NULL,
    LotCreateDate DATETIME NULL
);
```
- `LotId` (VARCHAR(50), PK): 工單 ID
- `Priority` (INT): 優先權
- `DueDate` (DATETIME): 到期日
- `ActualFinishDate` (DATETIME): 實際完成日期
- `ProductID` (VARCHAR(50)): 產品 ID
- `ProductName` (VARCHAR(100)): 產品名稱
- `CustomerID` (VARCHAR(50)): 客戶 ID
- `CustomerName` (VARCHAR(100)): 客戶名稱
- `LotCreateDate` (DATETIME): 工單建立日期

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

1. **正常作業 (Normal Operations)**: 存儲在 `LotOperations` 表中，可由排程系統動態分配機器
2. **已完成作業 (Completed Operations)**: 存儲在 `CompletedOperations` 表中，包含確定的開始和結束時間
3. **進行中作業 (WIP Operations)**: 存儲在 `WIPOperations` 表中，包含開始時間和已處理時間
4. **凍結作業 (Frozen Operations)**: 存儲在 `FrozenOperations` 表中，已預先排程但尚未開始

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
            -- 隨機選擇開始日期：今天到 30 天後
            SET random_days = FLOOR(RAND() * 31); -- 0-30 天
            SET start_date = DATE_ADD(CURDATE(), INTERVAL random_days DAY);

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
- 每筆記錄的開始時間：從今天開始到 30 天後的隨機日期
- 每筆記錄的持續時間：0.2 到 1 天的隨機時長 (4.8 到 24 小時)
- 確保每個機台的 PM 時間不會相互重疊
- unavailable_type 設為 'PM'，source 設為 'AUTO'，created_by 設為 'SYSTEM'
- 原因欄位會標記是第幾筆記錄 (如 "隨機產生的預防性保養 - M01-1 (1/3)")
- 適用於測試環境產生模擬的保養排程資料，避免過度阻塞機台

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



### 10. DynamicSchedulingJob - 動態排程作業表
```sql
CREATE TABLE DynamicSchedulingJob (
    ScheduleId VARCHAR(50) NOT NULL PRIMARY KEY,
    LotPlanRaw LONGTEXT,
    CreateDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    CreateUser VARCHAR(50),
    PlanSummary VARCHAR(2500),
    LotPlanResult JSON,
    LotStepResult JSON,
    machineTaskSegment JSON
);
```
- `ScheduleId` (VARCHAR(50), PK): 排程作業 ID
- `LotPlanRaw` (LONGTEXT): 工單原始計劃資料
- `CreateDate` (DATETIME): 建立日期 (預設為當前時間戳)
- `CreateUser` (VARCHAR(50)): 建立使用者
- `PlanSummary` (VARCHAR(2500)): 計劃摘要
- `LotPlanResult` (JSON): 工單計劃結果資料
- `LotStepResult` (JSON): 工單步驟結果資料
- `machineTaskSegment` (JSON): 機器任務區段資料

**功能說明**:
- 參照 ScheduleJob 表結構建立，用於動態排程作業
- 新增三個 JSON 欄位用於儲存排程結果資料
- 支援儲存複雜的排程計算結果和機器任務分配資訊

## 📊 資料表功能說明對照表

| 資料表名稱 | 英文名稱 | 主要用途 | 使用時機 | 資料範例 | 是否必要 |
|-----------|---------|---------|---------|---------|---------|
| 機台主檔表 | machines | 儲存所有機台的基本資料 | 系統初始化時建立,新增機台時使用 | M01-1, M01-2 屬於 M01 群組 | ✅ 必要 |
| 機台不可用時段表 | machine_unavailable_periods | 記錄機台無法使用的時間區間，包含維修、保養、作業排程等 | 排程時需要避開這些時段，支援作業排程記錄 | M01-1 在 1/18 14:00-16:00 維修，或記錄 LOT001 STEP1 作業 | ✅ 必要 |
| 動態排程作業表 | DynamicSchedulingJob | 儲存動態排程作業的計劃和結果資料 | 執行動態排程時使用，儲存排程結果 | 排程 ID: SCH001，包含 LotPlanResult、LotStepResult、machineTaskSegment | ✅ 必要 |

## 更新後的資料表關聯圖

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

DynamicSchedulingJob (獨立表)
  ├─── LotPlanResult (JSON)
  ├─── LotStepResult (JSON)
  └─── machineTaskSegment (JSON)
```