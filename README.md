# Production Scheduling System (APS01)

## Project Profile
- **Backend & Core**: Profile A (FastAPI + Python + MySQL + Google OR-Tools)
- **Frontend (Static)**: Profile C (pure-web: HTML + CSS + JS) - 用於簡單監控與展示
- **Frontend (App)**: Profile A (vue-app: Vue 3 + Vite + Pinia) - 用於完整互動應用

## 專案結構
本專案包含三個主要部分：
1. **backend/**: FastAPI 後端伺服器與排程核心演算法。
2. **pure-web/**: 純網頁版前端 (原 wwwroot)，提供輕量級的甘特圖與報表檢視。
3. **vue-app/**: 現代化 Vue 3 前端應用，提供更完整的互動體驗。

## 系統概述
這是一個結合 Google OR-Tools CP-SAT 求解器、FastAPI 後端、MySQL 資料庫以及 DHTMLX 甘特圖的可視化生產排程系統。專為處理複雜工序與機台約束的製造業設計。

## 功能特點

### 核心排程功能
- **多機台並行排程**：支援機台組內多機台並行處理。
- **增量排程 (Incremental Scheduling)**：支援批次處理大量工單，解決大規模問題的求解瓶頸。
- **工序順序約束**：確保每個 Lot 的工序按步驟順序執行。
- **Q-time 約束**：支援步驟間的等待時間限制（例如 STEP3 → STEP4 ≤ 200 分鐘）。
- **資源衝突避免**：機台不重疊使用。
- **Priority-based 順序**：高優先級 Lot 優先開始第一道工序。
- **多目標優化**：可隨時切換目標函數（Makespan、總完工時間、加權延遲）。

### 數據處理
- **JSON 數據載入**：從 `lot_Plan.json` 載入 Lot 計劃
- **結果輸出**：儲存排程結果至 `LotStepResult_New.json`
- **日誌記錄**：記錄排程執行至 `SheduleLog.json`

### 可視化支援
- **甘特圖數據生成**：輸出機台任務段數據至 JSON
- **顏色映射**：根據預約狀態提供不同顏色
- **模擬時間整合**：甘特圖界面可完整顯示該排程對應的「模擬結束時間」
- **Machine Group Utilizations**：計算各機台群組的利用率

### 資料庫與模擬系統
- **資料庫整合**：完整對接 MySQL，實現排程、工序、設定的持久化儲存。
- **預存程序加速 (Stored Procedures)**：使用 `sp_UpdatePlanResultsJSON` 等 SP 進行大量批次更新，減少資料庫來回開銷。
- **隨機資料產生**：`insert_lot_data.py` 與 `sp_InsertLot` 支援隨機產生 9~15 個作業步驟，提升測試覆蓋。
- **模擬數據記錄 (`SimulationData`)**：獨立記錄模擬時鐘的 `simulation_start_time` 與 `simulation_end_time`。
- **排程與模擬同步**：排程結果 (`DynamicSchedulingJob`) 會自動關聯最後一次模擬的結束時間。
- **GUI 管理工具**：提供 Qt-based 管理界面，支援資料清理、Lots 產生、模擬時鐘啟動及排程觸發。

## 安裝依賴

```bash
pip install ortools
```

## 使用方法

1. **準備數據**：
   運行 `create_test_data.py` 生成測試數據，或手動建立 `C:\Data\APS\lot_Plan\lot_Plan.json`

2. **執行排程**：
   ```bash
   # 預設交期優先 (1)
   python Scheduler_Full_Example.py

   # 交期優先 (1)
   python Scheduler_Full_Example.py 1

   # 優先權優先 (2)
   python Scheduler_Full_Example.py 2

   # 多目標優化 (3)，預設權重 α=0.5, β=0.5
   python Scheduler_Full_Example.py 3

   # 多目標優化，自訂權重 α=0.7, β=0.3
   python Scheduler_Full_Example.py 3 0.7 0.3

   # 準時交貨優先 (4)
   python Scheduler_Full_Example.py 4
   ```

3. **查看結果**：
   - 控制台輸出排程結果
   - `LotStepResult_New.json`：詳細排程數據
   - `machineTaskSegment_New.json`：甘特圖數據
   - 控制台顯示瓶頸機台 Top 5

## 數據格式

### Lot 計劃 (lot_Plan.json)
```json
[
  {
    "LotId": "LOT_A001",
    "Product": "PROD_A",
    "Priority": 220,
    "Operations": [
      {
        "Step": "STEP1",
        "StepIdx": 1,
        "MachineGroup": "M01",
        "DurationMinutes": 240
      }
    ]
  }
]
```

### 排程結果 (LotStepResult.json)
```json
[
  {
    "LotId": "LOT_A001",
    "Product": "PROD_A",
    "Priority": 220,
    "StepIdx": 1,
    "Step": "STEP1",
    "Machine": "M01-1",
    "Start": "2026-01-09T13:00:00",
    "End": "2026-01-09T17:00:00",
    "Booking": 0
  }
]
```

## 結果檔案處理邏輯

系統在排程完成後，會產生三個主要的結果檔案，分別用於詳細記錄、彙整統計及甘特圖顯示。

### 1. LotStepResult.json (詳細排程結果)
此檔案記錄了每個 Lot 的每一道工序在機台上的具體安排。
- **處理邏輯**：
    - 從 CP-SAT 求解器獲取每個任務的 `start` 與 `end` 分鐘數。
    - 將分鐘數轉換為絕對時間 (`SCHEDULE_START` + 偏移)。
    - 記錄分配的具體機台名稱 (`Machine`)。
    - `Booking` 欄位標記為 `0`（代表新產生的排程）。
- **用途**：作為最底層的排程明細，供後續彙整與資料庫存檔。

### 2. LotPlanResult.json (彙整與統計結果)
此檔案對排程結果進行了 Lot 等級的彙整，並計算延遲狀況。
- **處理邏輯**：
    - **Lot 彙整**：針對每個 Lot，找出其 `StepIdx` 最大的最後一道工序，以其結束時間作為該 Lot 的 `Plan Date`。
    - **延遲計算**：`delay time = Plan Date - Due Date`。
        - 格式為 `D:HH` (天:小時)。
        - 若提早完成，則顯示為負數 (例如 `-1:05` 代表提早 1 天 5 小時)。
    - **統計資訊 (statistics)**：
        - 計算總批數、最早投入時間、最晚產出時間。
        - **延遲分類統計**：
            - `early_count`: 提早完成。
            - `on_time_count`: 準時完成 (延遲為 0)。
            - `minor_delay_count`: 延遲 <= 2 天。
            - `major_delay_count`: 延遲 > 2 天或解析失敗。
- **用途**：提供生產管理人員快速掌握訂單交期達成狀況。

### 3. machineTaskSegment.json (甘特圖渲染數據)
此檔案專為前端甘特圖組件 (如 DHTMLX Gantt) 格式化。
- **處理邏輯**：
    - **機台分組**：按機台 ID 進行分組。
    - **虛擬節點**：為每個機台建立一個 `render: "split"` 的父節點，作為該機台所有任務的容器。
    - **任務段建立**：
        - 每個任務段的 `parent` 指向所屬機台。
        - `duration` 轉換為小時單位。
        - **顏色映射**：調用 `BookingColorMap` 根據 `Booking` 狀態賦予顏色（例如：新排程為天藍色 `#00BFFF`）。
- **用途**：前端可視化呈現，支援機台視角的任務分佈查看。

## Machine Group Utilizations 計算說明

系統會在排程完成後自動計算各機台群組的利用率，並輸出利用率最高的 Top 5 群組。

### 計算公式
```
利用率 = (實際被排程加工時間) ÷ (群組機台數 × 排程時間視窗)
```

### 參數定義
- **實際被排程加工時間**：該群組內所有機台分配到的任務總持續時間（分鐘）
- **群組機台數**：`len(MACHINE_GROUPS[group])`，該群組包含的機台數量
- **排程時間視窗**：從最早任務開始時間到最後任務結束時間的持續時間（分鐘）

### 輸出格式
```
=== Top 5 Machine Group Utilizations (based on actual schedule window): ===
1. M08 | Utilization: 87.32% | Used: 14580.0 min | Capacity: 16700.0 min
2. M03 | Utilization: 82.15% | Used: 12360.0 min | Capacity: 15040.0 min
...
```

其中：
- **Utilization**：利用率百分比
- **Used**：實際使用的總加工時間（分鐘）
- **Capacity**：總可用容量 = 群組機台數 × 排程時間視窗（分鐘）

## 架構說明

### 主要類別

#### `SchedulerFullExample`
- 主排程類別
- 包含所有排程邏輯和數據處理

#### `BookingColorMap`
- 預約狀態顏色映射
- 支援新排程、已預約、已鎖定等狀態


### 關鍵約束

1. **工序順序**：`start >= prev_end`
2. **機台不重疊**：`AddNoOverlap(intervals)`
3. **Priority 順序**：高 Priority Lot 先開始第一道工序
4. **資源分配**：動態選擇機台組內可用機台

### 目標函數 (Objective Functions)

系統支援多種不同的優化目標，可透過 `OBJECTIVE_TYPE` 參數設定：

1. **交期優先 (`makespan`)**：最小化總完成時間。
2. **優先權優先 (`weighted_delay`)**：最小化所有 Lot 的 (Priority × 延遲時間)。
3. **總完工時間優化 (`total_completion_time`) [預設]**：最小化每批最後一站完成時間之總和，確保所有批次儘早完工。
    - 公式：`Minimize(Σ(LastStepCompletion) * 10 + Makespan)`
4. **多目標優化**：平衡權重與完成時間。

### 效能優化 (Performance)

為了發揮最大運算與存取效能，系統採用以下技術：
1. **求解器並行計算**：透過 `.env` 中的 `SOLVER_NUM_SEARCH_WORKERS` 設定並行線程數。
2. **資料庫平行更新 (Multi-threading)**：使用 Python `ThreadPoolExecutor` 同時向資料庫發送多個批次更新請求。
3. **高效資料批次法**：將 Lots 資料切割成 Chunk，透過 JSON 格式與 Stored Procedure 同步更新數千筆記錄。
    - *效能對比*：優化後的更新速度比傳統逐筆 SQL 提升約 **60 倍**。
4. **求解時間限制**：透過 `SOLVER_MAX_TIME_IN_SECONDS` 控制計算時間，避免無限鎖死。

## 環境變數配置 (.env)
```ini
MYSQL_HOST=127.0.0.1
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=Scheduling
SOLVER_MAX_TIME_IN_SECONDS=30
SOLVER_NUM_SEARCH_WORKERS=12
SOLVER_LOG_SEARCH_PROGRESS=false
```

## 配置

### 機台組配置
在 `MACHINE_GROUPS` 字典中定義各機台組的可用機台列表。

### 時間參數
- `SCHEDULE_START`：排程開始時間
- `horizon`：最大排程範圍 (30 天)
- `max_time_in_seconds`：求解器最大執行時間 (30 秒)

## 輸出說明

### 控制台輸出
- 排程狀態 (Optimal/Feasible)
- 各任務的開始/結束時間和分配機台
- Machine Group Utilizations (Top 5 利用率最高的群組)

### 文件輸出
- `LotStepResult_New.json`：完整排程結果
- `machineTaskSegment_New.json`：甘特圖渲染數據
- `SheduleLog.json`：執行日誌

## 擴展功能

- 可輕易添加更多約束條件
- 支援不同產品的特殊處理邏輯
- 可整合現有排程數據進行增量排程
- 甘特圖數據可直接用於 Web 可視化

## 注意事項

- 確保數據目錄存在，程式會自動建立
- 大規模問題可能需要調整求解器參數
- Priority 值越大表示優先級越高
- 機台組內機台數量影響並行處理能力
- dhtmlxGantt 7.1,若舊版切換甘特圖會沒作用
