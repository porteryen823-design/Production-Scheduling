# FastAPI 後端專案 README

## 專案概述

基於 MySQL 資料庫的生產排程系統 FastAPI 後端 Web API,提供完整的 CRUD 操作和資料查詢功能。

## Technology Profile

- **Technology Profile**: Profile A (前後端分離)
- **後端框架**: FastAPI 0.109+
- **資料庫**: MySQL (使用 PyMySQL 驅動)
- **ORM**: SQLAlchemy 2.0+

## 專案結構

```
backend/
├─ src/
│  ├─ main.py                    # FastAPI 應用程式入口
│  ├─ api/v1/                    # API 路由和 Schemas
│  ├─ core/                      # 核心配置
│  ├─ domain/models/             # SQLAlchemy 資料模型
│  ├─ infra/db/                  # 資料庫連線
│  └─ utils/                     # 工具函數
├─ requirements.txt
├─ .env.example
└─ README.md
```

## 安裝與執行

### 1. 建立虛擬環境

```bash
python -m venv venv
venv\Scripts\activate
```

### 2. 安裝依賴

```bash
pip install -r requirements.txt
```

### 3. 配置環境變數

複製 `.env.example` 為 `.env` 並填入資料庫連線資訊:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=Scheduling
```

### 4. 啟動伺服器

```bash
python src/main.py
```

或使用 uvicorn:

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## API 文件

啟動伺服器後,訪問以下 URL 查看 API 文件:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API 端點

### 工單管理 (Lots)
- `GET /api/v1/lots` - 取得所有工單
- `GET /api/v1/lots/{lot_id}` - 取得單一工單
- `POST /api/v1/lots` - 建立工單
- `PUT /api/v1/lots/{lot_id}` - 更新工單
- `DELETE /api/v1/lots/{lot_id}` - 刪除工單
- `GET /api/v1/lots/by-priority/sorted` - 依優先權排序

### 工單作業管理 (LotOperations)
- `GET /api/v1/lot-operations` - 取得所有工單作業
- `GET /api/v1/lot-operations/lot/{lot_id}` - 取得指定工單的所有作業
- `GET /api/v1/lot-operations/{lot_id}/{step}` - 取得單一工單作業
- `POST /api/v1/lot-operations` - 建立工單作業
- `PUT /api/v1/lot-operations/{lot_id}/{step}` - 更新工單作業
- `DELETE /api/v1/lot-operations/{lot_id}/{step}` - 刪除工單作業
- `PUT /api/v1/lot-operations/{lot_id}/{step}/check-in` - 作業 CheckIn
- `PUT /api/v1/lot-operations/{lot_id}/{step}/check-out` - 作業 CheckOut

### 機台管理 (Machines & MachineGroups)
- `GET /api/v1/machine-groups` - 取得所有機器群組
- `GET /api/v1/machines` - 取得所有機器
- 完整 CRUD 操作

### 作業狀態管理
- `GET /api/v1/completed-operations` - 已完成作業
- `GET /api/v1/wip-operations` - 進行中作業
- `GET /api/v1/frozen-operations` - 凍結作業

### 機台不可用時段管理
- `GET /api/v1/machine-unavailable-periods` - 取得所有機台不可用時段
- 支援依機台和類型篩選

### 動態排程作業管理
- `GET /api/v1/dynamic-scheduling-jobs` - 取得所有動態排程作業
- 完整 CRUD 操作

### 排程資料查詢 (專為甘特圖設計)
- `GET /api/schedule?offset={offset}&limit={limit}` - 取得排程資料
  - `offset`: 偏移量 (0 是最新一筆,1 是第二新,依此類推)
  - `limit`: 限制數量 (預設 1,最大 10)
  - 返回包含 `ScheduleId`, `CreateDate`, `machineTaskSegment`, `total` 等欄位
  - 按 `CreateDate` 降序排列

## 資料表結構

專案支援以下資料表:
- Lots - 工單基本資訊
- LotOperations - 工單的作業步驟
- MachineGroups - 機器群組
- Machines - 機器
- CompletedOperations - 已完成的作業
- WIPOperations - 進行中的作業
- FrozenOperations - 凍結的作業
- machine_unavailable_periods - 機台不可用時段
- DynamicSchedulingJob - 動態排程作業

詳細資料表結構請參考 `mysql.md`。


啟動後端簡易方式:
  C:\VSCode_Proj\APS01\backend\venv\Scripts\python.exe backend\src\main.py 

如果某個 FastAPI 程式佔用了 port:8000，你可以透過以下步驟找到並刪除（結束）該進程：
🔍 步驟 1：查詢佔用 8000 埠的進程
打開 命令提示字元 (cmd) 或 PowerShell，輸入：
netstat -ano | findstr :8000


這會顯示類似：
TCP    0.0.0.0:8000    0.0.0.0:0    LISTENING    12345


最後一欄的數字 12345 就是佔用該埠的 PID (Process ID)。

🛑 步驟 2：結束該進程
使用以下指令結束該 PID：
taskkill /PID 12345 /F


其中 12345 替換成你查到的 PID。
