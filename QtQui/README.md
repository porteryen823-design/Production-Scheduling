# APS Qt GUI 應用程式

這是一個用 PyQt5 建立的 APS (Advanced Planning and Scheduling) 管理系統 GUI 應用程式，具有彩色輸出顯示以提高可讀性。

## 功能

應用程式包含四個分頁，具有彩色輸出顯示：

### 🎨 顏色說明
- 🟢 <span style="color: #28A745;">綠色</span>：成功操作、CheckIn 事件
- 🔵 <span style="color: #007BFF;">藍色</span>：資訊性內容、Normal 狀態
- 🟡 <span style="color: #FFC107;">黃色</span>：WIP 狀態
- 🔴 <span style="color: #DC3545;">紅色</span>：錯誤信息、CheckOut 事件
- ⚫ <span style="color: #6C757D;">灰色</span>：New Add 狀態、一般資訊

### 📑 分頁功能

### 1. 清空測試資料
- 提供一個 "執行" 按鈕
- 執行後呼叫 MySQL 資料庫的 `sp_clean_lots` 儲存程序
- 將執行結果顯示在文字區域中

### 2. 產生 Lots
- 提供一個 "執行" 按鈕
- 執行 `insert_lot_data.py` 腳本
- 將腳本輸出顯示在文字區域中
- 額外顯示資料庫統計資訊：
  - 總 Lot 數量
  - [Completed] 記錄數 (StepStatus = 2)
  - [WIP] 記錄數 (StepStatus = 1)
  - [Normal] 記錄數 (StepStatus = 0 且 PlanCheckInTime 不為空)
  - [New Add] 記錄數 (StepStatus = 0 且 PlanCheckInTime 為空)

### 3. 模擬時鐘
- 設定開始時間 T0 (日期 + 時分秒)
- 設定模擬分鐘數
- 顯示目前時間 T1
- 參考 `SimulateAPS.py` 的功能，當時間異動時更新 T1 和作業狀態
- 提供開始/停止模擬按鈕
- 將模擬過程顯示在文字區域中

### 4. 重新排程
- 提供一個 "執行" 按鈕
- 執行 `Scheduler_Full_Example_Qtime_V1_Wip_DB.py` 腳本
- 將腳本輸出顯示在文字區域中

## 環境需求

- Python 3.x
- PyQt5
- mysql-connector-python
- python-dotenv
- ortools (用於排程腳本)

## 安裝依賴

```bash
pip install -r requirements.txt
```

## 環境變數

確保 `.env` 檔案包含以下變數：
```
MYSQL_HOST=your_mysql_host
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=your_mysql_database
```

## 運行應用程式

```bash
cd QtQui
python qt_gui.py
```

## 注意事項

- 所有長時間運行的任務都在背景線程中執行，不會阻塞 UI
- 模擬時鐘功能會實際更新資料庫中的作業狀態
- 確保 MySQL 資料庫已正確設定並包含必要的表格和儲存程序