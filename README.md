# Scheduler Full Example

這是一個使用 Google OR-Tools CP-SAT 求解器的生產排程系統範例，專為半導體或製造業的 Lot 排程設計。

## 功能特點

### 核心排程功能
- **多機台並行排程**：支援機台組內多機台並行處理
- **工序順序約束**：確保每個 Lot 的工序按步驟順序執行
- **資源衝突避免**：機台不重疊使用
- **Priority-based 順序**：高優先級 Lot 優先開始第一道工序
- **加權結束時間優化**：最小化所有 Lot 的 (Priority × 結束時間) 總和

### 數據處理
- **JSON 數據載入**：從 `lot_Plan.json` 載入 Lot 計劃
- **結果輸出**：儲存排程結果至 `LotStepResult_New.json`
- **日誌記錄**：記錄排程執行至 `SheduleLog.json`

### 可視化支援
- **甘特圖數據生成**：輸出機台任務段數據至 JSON
- **顏色映射**：根據預約狀態提供不同顏色
- **Machine Group Utilizations**：計算各機台群組的利用率，識別瓶頸並輸出 Top 5

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

### 排程結果 (LotStepResult_New.json)
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

#### `GanttType`
- 甘特圖類型枚舉
- NEW：新排程，OLD：舊排程，ALL：全部

### 關鍵約束

1. **工序順序**：`start >= prev_end`
2. **機台不重疊**：`AddNoOverlap(intervals)`
3. **Priority 順序**：高 Priority Lot 先開始第一道工序
4. **資源分配**：動態選擇機台組內可用機台

### 目標函數

系統支援四種不同的優化目標：

1. **交期優先 (1)**：`Minimize(makespan)` - 最小化總完成時間
2. **優先權優先 (2)**：`Minimize(Σ(Priority_i × end_time_i))` - 最小化加權完成時間
3. **多目標優化 (3)**：`Minimize(α × weighted_completion + β × makespan)` - 平衡權重與完成時間
4. **準時交貨優先 (4)**：`Minimize(Σ max(0, end_time_i - DueDate_i))` - 最小化總延遲時間

其中 `end_time_i` 為 Lot i 的最後一道工序結束時間。

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