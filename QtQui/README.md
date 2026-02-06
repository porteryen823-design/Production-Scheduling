# APS Qt GUI 應用程式

這是一個用 PyQt5 建立的 APS (Advanced Planning and Scheduling) 管理系統 GUI 應用程式，具有彩色輸出顯示與多維度資料管理功能。

## 🎯 系統目標

提供一個直覺的介面來管理生產排程模型的生命週期，包含資料清理、批量產生、動態模擬、自動化排程演算法驗證，以及規劃情境的備份與還原。

## 🎨 顏色與狀態說明

系統在各處使用顏色來標示作業狀態，以提高可讀性：

- 🟢 **綠色** (#28A745)：成功操作、CheckIn 事件、Completed 狀態
- 🔵 **藍色** (#007BFF)：資訊性內容、Normal 狀態
- 🟡 **黃色** (#FFC107)：WIP (進行中) 狀態
- 🔴 **紅色** (#DC3545)：錯誤信息、CheckOut 事件
- ⚫ **灰色** (#6C757D)：New Add (新加入) 狀態、一般資訊

---

## 📑 分頁功能詳細說明

應用程式包含九個核心功能分頁：

### 1. 清空測試資料
- **功能**：重置系統至初始狀態。
- **操作**：點擊「執行」呼叫資料庫預存程序 `sp_clean_lots`。

### 2. 產生 Lots
- **功能**：批量產生測試用的 Lot 資料。
- **腳本**：執行 `insert_lot_data.py`。
- **特色**：
  - 可設定產生數量。
  - 支援使用 Stored Procedure (`sp_InsertLot`) 模式。
  - 支援以模擬時鐘結束時間為基準產生。
  - 實時顯示資料庫統計資訊（Total, Completed, WIP, Normal, New Add）。

### 3. 模擬時鐘
- **功能**：模擬時間推進，自動更新作業狀態。
- **腳本**：執行 `SimulateAPS.py`。
- **操作**：設定開始時間 (T0)、模擬次數與時間增量。
- **特色**：模擬結束後會自動更新下次排程的建議開始時間。

### 4. 重新排程
- **功能**：執行排程優化演算法。
- **腳本**：執行 `Scheduler_Full_Example_Qtime_V1_Wip_DB_Incremental_Scheduling.py`。
- **特色**：支援增量排程 (Incremental Scheduling)，並可與模擬時鐘聯動。

### 5. Lots 資料 (表格檢視)
- **功能**：直觀顯示 `Lots` 資料表內容。
- **搜尋**：支援依 `LotId` 與 `Priority` 快速過濾。

### 6. LotOperations 資料 (表格檢視)
- **功能**：顯示詳細的作業步驟與排程結果。
- **特色**：
  - 根據 `StepStatus` (New Add, WIP, Completed) 自動對行進行背景配色。
  - 支援依 `LotId`、`Step` 與「狀態」進行多重過濾。

### 7. 自動化測試
- **功能**：執行端對端的循環測試流程。
- **腳本**：執行 `automated_test_runner.py`。
- **流程**：自動執行「清空 -> 產生 -> 排程 -> 模擬」的循環 (Cycles)。
- **設定**：由 `test_scripts/` 目錄下的 JSON 檔案定義測試情境內容。

### 8. 機台調整
- **機台擴充**：透過倍率快速擴增機台資源（執行 `expanded_machines.py`）。
- **PM 排程**：隨機產生機台維護計畫（呼叫 `generate_random_pm_schedules`）。

### 9. 模擬規劃 (載入與儲存)
- **儲存**：將當前排程結果（快照）存入 `DynamicSchedulingJob_Snap`。
- **還原**：從備份情境中選擇一個 Key，還原至 `DynamicSchedulingJob_Hist` 供分析使用。
- **管理**：支援情境列表刷新與刪除。

---

## 🛠️ 環境需求

- **Python**: 3.11+
- **GUI 框架**: PyQt5
- **資料庫**: MySQL / MariaDB (mysql-connector-python)
- **環境變數管理**: python-dotenv
- **排程引擎**: Google OR-Tools
- **HTTP 客戶端**: requests

## 📦 安裝依賴

```bash
pip install -r requirements.txt
```

## 🔐 環境變數配置

請在專案根目錄建立 `.env` 檔案：
```env
MYSQL_HOST=your_host
MYSQL_USER=your_user
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=your_db
```

## 🚀 運行應用程式

```bash
cd QtQui
python qt_gui.py
```

## ⚠️ 注意事項

1. **編碼處理**：在 Windows 環境下，系統會自動將輸出編碼強制設為 UTF-8 以避免亂碼。
2. **異步執行**：所有耗時腳本均透過背景線程或 `QProcess` 執行，不會造成 UI 凍結。
3. **資料庫依賴**：執行前請確認已匯入必要的 SQL 綱要與預存程序。