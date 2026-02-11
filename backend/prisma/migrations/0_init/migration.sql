-- CreateTable
CREATE TABLE `CompletedOperations` (
    `LotId` VARCHAR(50) NOT NULL,
    `Step` VARCHAR(20) NOT NULL,
    `MachineId` VARCHAR(20) NOT NULL,
    `StartTime` DATETIME(0) NOT NULL,
    `EndTime` DATETIME(0) NOT NULL,

    INDEX `MachineId`(`MachineId`),
    PRIMARY KEY (`LotId`, `Step`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `DynamicSchedulingJob` (
    `ScheduleId` VARCHAR(50) NOT NULL,
    `LotPlanRaw` LONGTEXT NULL,
    `CreateDate` DATETIME(0) NULL DEFAULT CURRENT_TIMESTAMP(0),
    `CreateUser` VARCHAR(50) NULL,
    `simulation_end_time` DATETIME(0) NULL,
    `PlanSummary` VARCHAR(2500) NULL,
    `LotPlanResult` LONGTEXT NULL,
    `LotStepResult` LONGTEXT NULL,
    `machineTaskSegment` LONGTEXT NULL,

    PRIMARY KEY (`ScheduleId`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `DynamicSchedulingJob_Hist` (
    `ScheduleId` VARCHAR(50) NOT NULL,
    `key_value` VARCHAR(100) NOT NULL,
    `remark` TEXT NULL,
    `LotPlanRaw` LONGTEXT NULL,
    `CreateDate` DATETIME(0) NULL DEFAULT CURRENT_TIMESTAMP(0),
    `CreateUser` VARCHAR(50) NULL,
    `simulation_end_time` DATETIME(0) NULL,
    `PlanSummary` VARCHAR(2500) NULL,
    `LotPlanResult` LONGTEXT NULL,
    `LotStepResult` LONGTEXT NULL,
    `machineTaskSegment` LONGTEXT NULL,

    PRIMARY KEY (`ScheduleId`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `DynamicSchedulingJob_Snap` (
    `id` INTEGER NOT NULL AUTO_INCREMENT,
    `key_value` VARCHAR(100) NOT NULL,
    `remark` TEXT NULL,
    `ScheduleId` VARCHAR(50) NULL,
    `LotPlanRaw` LONGTEXT NULL,
    `CreateDate` DATETIME(0) NULL DEFAULT CURRENT_TIMESTAMP(0),
    `CreateUser` VARCHAR(50) NULL,
    `PlanSummary` VARCHAR(2500) NULL,
    `LotPlanResult` LONGTEXT NULL,
    `LotStepResult` LONGTEXT NULL,
    `machineTaskSegment` LONGTEXT NULL,
    `simulation_end_time` DATETIME(0) NULL,

    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `DynamicSchedulingJob_Snap_Hist` (
    `id` INTEGER NOT NULL AUTO_INCREMENT,
    `key_value` VARCHAR(100) NOT NULL,
    `remark` TEXT NULL,
    `ScheduleId` VARCHAR(50) NULL,
    `LotPlanRaw` LONGTEXT NULL,
    `CreateDate` DATETIME(0) NULL DEFAULT CURRENT_TIMESTAMP(0),
    `CreateUser` VARCHAR(50) NULL,
    `PlanSummary` VARCHAR(2500) NULL,
    `LotPlanResult` LONGTEXT NULL,
    `LotStepResult` LONGTEXT NULL,
    `machineTaskSegment` LONGTEXT NULL,
    `simulation_end_time` DATETIME(0) NULL,

    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `FrozenOperations` (
    `LotId` VARCHAR(50) NOT NULL,
    `Step` VARCHAR(20) NOT NULL,
    `MachineId` VARCHAR(20) NOT NULL,
    `StartTime` DATETIME(0) NOT NULL,
    `EndTime` DATETIME(0) NOT NULL,

    INDEX `MachineId`(`MachineId`),
    PRIMARY KEY (`LotId`, `Step`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `LotOperations` (
    `LotId` VARCHAR(50) NOT NULL,
    `Step` VARCHAR(20) NOT NULL,
    `Sequence` INTEGER NOT NULL,
    `MachineGroup` VARCHAR(20) NOT NULL,
    `Duration` INTEGER NOT NULL,
    `CheckInTime` DATETIME(0) NULL,
    `CheckOutTime` DATETIME(0) NULL,
    `StepStatus` INTEGER NULL DEFAULT 0,
    `PlanCheckInTime` DATETIME(0) NULL,
    `PlanCheckOutTime` DATETIME(0) NULL,
    `PlanMachineId` VARCHAR(20) NULL,
    `PlanHistory` LONGTEXT NULL,

    PRIMARY KEY (`LotId`, `Step`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `Lots` (
    `LotId` VARCHAR(50) NOT NULL,
    `Priority` INTEGER NOT NULL,
    `PlanStartTime` DATETIME(0) NULL,
    `DueDate` DATETIME(0) NOT NULL,
    `PlanFinishDate` DATETIME(0) NULL,
    `ActualFinishDate` DATETIME(0) NULL,
    `ProductID` VARCHAR(50) NULL,
    `ProductName` VARCHAR(100) NULL,
    `CustomerID` VARCHAR(50) NULL,
    `CustomerName` VARCHAR(100) NULL,
    `LotCreateDate` DATETIME(0) NULL,
    `Delay_Days` DECIMAL(10, 2) NULL,

    PRIMARY KEY (`LotId`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `MachineGroupUtilization` (
    `id` INTEGER NOT NULL AUTO_INCREMENT,
    `PlanID` VARCHAR(50) NOT NULL,
    `GroupId` VARCHAR(20) NOT NULL,
    `CalculationWindowStart` DATETIME(0) NOT NULL,
    `CalculationWindowEnd` DATETIME(0) NOT NULL,
    `MachineCount` INTEGER NOT NULL,
    `TotalUsedMinutes` INTEGER NOT NULL,
    `TotalCapacityMinutes` INTEGER NOT NULL,
    `UtilizationRate` DECIMAL(5, 2) NOT NULL,
    `CreatedAt` TIMESTAMP(0) NOT NULL DEFAULT CURRENT_TIMESTAMP(0),

    INDEX `idx_group`(`GroupId`),
    INDEX `idx_plan`(`PlanID`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `MachineGroups` (
    `GroupId` VARCHAR(20) NOT NULL,
    `GroupName` VARCHAR(100) NOT NULL,

    PRIMARY KEY (`GroupId`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `Machines` (
    `MachineId` VARCHAR(20) NOT NULL,
    `GroupId` VARCHAR(20) NOT NULL,
    `machine_name` VARCHAR(100) NULL,
    `is_active` BOOLEAN NULL DEFAULT true,
    `created_at` TIMESTAMP(0) NOT NULL DEFAULT CURRENT_TIMESTAMP(0),
    `updated_at` TIMESTAMP(0) NOT NULL DEFAULT CURRENT_TIMESTAMP(0),

    INDEX `GroupId`(`GroupId`),
    PRIMARY KEY (`MachineId`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `PlanModel` (
    `SeqNo` INTEGER NOT NULL,
    `optimization_type` INTEGER NULL DEFAULT 1,
    `Select` INTEGER NULL DEFAULT 1,
    `Name` VARCHAR(50) NULL,
    `Description` VARCHAR(250) NULL,
    `Remark` VARCHAR(2050) NULL,
    `DescImage` BLOB NULL,

    PRIMARY KEY (`SeqNo`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `PlanModel_User_Workshop` (
    `SeqNo` INTEGER NOT NULL AUTO_INCREMENT,
    `ScheduleId` VARCHAR(50) NULL,
    `models` LONGTEXT NULL,
    `lots` LONGTEXT NULL,
    `CreateDate` DATETIME(0) NULL DEFAULT CURRENT_TIMESTAMP(0),

    PRIMARY KEY (`SeqNo`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `PlanRaw` (
    `ID` INTEGER NOT NULL AUTO_INCREMENT,
    `PlanID` VARCHAR(50) NOT NULL,
    `RawData` LONGTEXT NOT NULL,
    `CreatedAt` DATETIME(0) NULL DEFAULT CURRENT_TIMESTAMP(0),

    PRIMARY KEY (`ID`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `PlanResult` (
    `ScheduleId` VARCHAR(50) NOT NULL,
    `optimization_type` INTEGER NOT NULL,
    `ScheduleResult` VARCHAR(50) NULL,
    `ScheduleTimeSpan` VARCHAR(50) NULL,
    `LotStepResult` LONGTEXT NULL,
    `LotPlanResult` LONGTEXT NULL,
    `machineTaskSegment` LONGTEXT NULL,
    `Top5MachineGroupUtilizations` LONGTEXT NULL,
    `ScheduleSummary` VARCHAR(1250) NULL,
    `CreateUser` VARCHAR(50) NULL,
    `CreateDate` DATETIME(0) NULL DEFAULT CURRENT_TIMESTAMP(0),

    PRIMARY KEY (`ScheduleId`, `optimization_type`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `ScheduleJob` (
    `ScheduleId` VARCHAR(50) NOT NULL,
    `LotPlan` LONGTEXT NULL,
    `CreateDate` DATETIME(0) NULL DEFAULT CURRENT_TIMESTAMP(0),
    `CreateUser` VARCHAR(50) NULL,
    `PlanSummary` VARCHAR(2500) NULL,

    PRIMARY KEY (`ScheduleId`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `WIPOperations` (
    `LotId` VARCHAR(50) NOT NULL,
    `Step` VARCHAR(20) NOT NULL,
    `MachineId` VARCHAR(20) NOT NULL,
    `StartTime` DATETIME(0) NOT NULL,
    `ElapsedMinutes` INTEGER NOT NULL,

    INDEX `MachineId`(`MachineId`),
    PRIMARY KEY (`LotId`, `Step`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `machine_unavailable_periods` (
    `Id` INTEGER NOT NULL AUTO_INCREMENT,
    `MachineId` VARCHAR(20) NOT NULL,
    `StartTime` DATETIME(0) NOT NULL,
    `EndTime` DATETIME(0) NOT NULL,
    `PeriodType` ENUM('PM', 'CM', 'BREAK', 'SHIFT_CHANGE', 'DOWNTIME', 'COMPLETED', 'WIP', 'FROZEN', 'RESERVED', 'OTHER') NOT NULL,
    `LotId` VARCHAR(50) NULL,
    `OperationStep` VARCHAR(20) NULL,
    `Reason` VARCHAR(255) NULL,
    `Priority` INTEGER NULL DEFAULT 0,
    `IsRecurring` BOOLEAN NULL DEFAULT false,
    `RecurrenceRule` LONGTEXT NULL,
    `Status` ENUM('ACTIVE', 'CANCELLED', 'COMPLETED') NULL DEFAULT 'ACTIVE',
    `CreatedBy` VARCHAR(50) NULL,
    `CreatedAt` TIMESTAMP(0) NOT NULL DEFAULT CURRENT_TIMESTAMP(0),
    `UpdatedAt` TIMESTAMP(0) NOT NULL DEFAULT CURRENT_TIMESTAMP(0),

    INDEX `idx_lot`(`LotId`),
    INDEX `idx_machine_time`(`MachineId`, `StartTime`, `EndTime`),
    INDEX `idx_period_type`(`PeriodType`),
    INDEX `idx_status`(`Status`),
    PRIMARY KEY (`Id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `ui_settings` (
    `id` INTEGER NOT NULL AUTO_INCREMENT,
    `parameter_name` VARCHAR(255) NOT NULL,
    `parameter_value` TEXT NULL,
    `remark` TEXT NULL,
    `created_at` DATETIME(0) NULL DEFAULT CURRENT_TIMESTAMP(0),
    `updated_at` DATETIME(0) NULL DEFAULT CURRENT_TIMESTAMP(0),

    UNIQUE INDEX `parameter_name`(`parameter_name`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- AddForeignKey
ALTER TABLE `CompletedOperations` ADD CONSTRAINT `CompletedOperations_ibfk_1` FOREIGN KEY (`LotId`) REFERENCES `Lots`(`LotId`) ON DELETE RESTRICT ON UPDATE RESTRICT;

-- AddForeignKey
ALTER TABLE `CompletedOperations` ADD CONSTRAINT `CompletedOperations_ibfk_2` FOREIGN KEY (`MachineId`) REFERENCES `Machines`(`MachineId`) ON DELETE RESTRICT ON UPDATE RESTRICT;

-- AddForeignKey
ALTER TABLE `FrozenOperations` ADD CONSTRAINT `FrozenOperations_ibfk_1` FOREIGN KEY (`LotId`) REFERENCES `Lots`(`LotId`) ON DELETE RESTRICT ON UPDATE RESTRICT;

-- AddForeignKey
ALTER TABLE `FrozenOperations` ADD CONSTRAINT `FrozenOperations_ibfk_2` FOREIGN KEY (`MachineId`) REFERENCES `Machines`(`MachineId`) ON DELETE RESTRICT ON UPDATE RESTRICT;

-- AddForeignKey
ALTER TABLE `LotOperations` ADD CONSTRAINT `LotOperations_ibfk_1` FOREIGN KEY (`LotId`) REFERENCES `Lots`(`LotId`) ON DELETE RESTRICT ON UPDATE RESTRICT;

-- AddForeignKey
ALTER TABLE `Machines` ADD CONSTRAINT `Machines_ibfk_1` FOREIGN KEY (`GroupId`) REFERENCES `MachineGroups`(`GroupId`) ON DELETE RESTRICT ON UPDATE RESTRICT;

-- AddForeignKey
ALTER TABLE `WIPOperations` ADD CONSTRAINT `WIPOperations_ibfk_1` FOREIGN KEY (`LotId`) REFERENCES `Lots`(`LotId`) ON DELETE RESTRICT ON UPDATE RESTRICT;

-- AddForeignKey
ALTER TABLE `WIPOperations` ADD CONSTRAINT `WIPOperations_ibfk_2` FOREIGN KEY (`MachineId`) REFERENCES `Machines`(`MachineId`) ON DELETE RESTRICT ON UPDATE RESTRICT;

