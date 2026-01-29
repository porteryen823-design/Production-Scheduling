# CustData 資料表說明文件

本目錄包含四個 Excel 工作表，用於 APS（Advanced Planning and Scheduling）生產排程系統的基礎資料管理。

---

## 📋 資料表概覽

| 檔案名稱 | 說明 | 用途 |
|---------|------|------|
| `eqp.xlsx` | 設備主檔 | 管理生產設備資訊與規格 |
| `lot.xlsx` | 批次主檔 | 管理生產批次資訊與狀態 |
| `processflow.xlsx` | 製程流程主檔 | 定義產品製程步驟與參數 |
| `wo.xlsx` | 工單主檔 | 管理生產工單與排程資訊 |

---

## 1️⃣ eqp.xlsx - 設備主檔

### 欄位說明

| 欄位名稱 | 中文說明 | 備註 |
|---------|---------|------|
| `ID` | 設備唯一識別碼 | 主鍵 |
| `EQP_ID` | 設備編號 | 業務識別碼 |
| `EQP_NAME` | 設備名稱 | 設備顯示名稱 |
| `EQP_TYPE` | 設備類型 | 設備分類 |
| `TOOL_GROUP` | 工具群組 | 設備所屬群組 |
| `CAPACITY` | 產能 | 設備處理能力 |
| `STATUS` | 設備狀態 | 如：運行中、停機、維護中 |
| `LOCATION` | 設備位置 | 實體位置資訊 |
| `CREATED_AT` | 建立時間 | 資料建立時間戳記 |
| `CREATEDBY` | 建立者 | 建立此筆資料的使用者 |
| `LAST_UPDATED` | 最後更新時間 | 資料最後修改時間戳記 |
| `UPDATEDBY` | 更新者 | 最後修改此筆資料的使用者 |
| `IS_ACTIVE` | 是否啟用 | 資料有效性標記 |

---

## 2️⃣ lot.xlsx - 批次主檔

### 欄位說明

| 欄位名稱 | 中文說明 | 備註 |
|---------|---------|------|
| `ID` | 批次唯一識別碼 | 主鍵 |
| `LOT_ID` | 批次編號 | 業務識別碼 |
| `WO_ID` | 工單編號 | 關聯到 wo.xlsx |
| `PROCESSFLOW_KEY` | 製程流程鍵值 | 關聯到 processflow.xlsx |
| `FLOW_VERSION` | 流程版本 | 製程版本控制 |
| `CURRENT_STEP` | 當前步驟 | 目前所在製程步驟 |
| `CURRENT_STAGE` | 當前階段 | 目前所在製程階段 |
| `QUANTITY` | 數量 | 批次總數量 |
| `QTY_GOOD` | 良品數量 | 合格品數量 |
| `QTY_SCRAP` | 報廢數量 | 不良品數量 |
| `STATUS` | 批次狀態 | 如：進行中、完成、暫停 |
| `PRIORITY` | 優先順序 | 排程優先權 |
| `DUE_DATE` | 到期日 | 預計完成時間 |
| `HOLD_FLAG` | 暫停標記 | 是否暫停生產 |
| `HOLD_REASON` | 暫停原因 | 暫停原因說明 |
| `CREATED_AT` | 建立時間 | 資料建立時間戳記 |
| `CREATEDBY` | 建立者 | 建立此筆資料的使用者 |
| `LAST_UPDATED` | 最後更新時間 | 資料最後修改時間戳記 |
| `UPDATEDBY` | 更新者 | 最後修改此筆資料的使用者 |
| `IS_ACTIVE` | 是否啟用 | 資料有效性標記 |
| `CARRIER_ID` | 載具編號 | 承載批次的載具 |
| `LOCATION` | 當前位置 | 批次實體位置 |

---

## 3️⃣ processflow.xlsx - 製程流程主檔

### 欄位說明

| 欄位名稱 | 中文說明 | 備註 |
|---------|---------|------|
| `ID` | 製程步驟唯一識別碼 | 主鍵 |
| `PROCESSFLOW_KEY` | 製程流程鍵值 | 製程識別碼 |
| `VERSION` | 版本號 | 製程版本 |
| `NAME` | 製程名稱 | 製程步驟名稱 |
| `STAGE` | 製程階段 | 製程所屬階段 |
| `SEQ` | 步驟序號 | 製程執行順序 |
| `NEXTSTEP_SEQ` | 下一步驟序號 | 正常流程的下一步 |
| `REWORK_RETURN_SEQ` | 重工返回序號 | 重工時返回的步驟 |
| `HAVE_QTIME` | 是否有 Q-Time | 是否有時間限制 |
| `MAX_QTIME` | 最大 Q-Time | 最大允許等待時間 |
| `MIN_QTIME` | 最小 Q-Time | 最小等待時間 |
| `QTIME_START_EVENT` | Q-Time 起始事件 | 開始計時的觸發事件 |
| `QTIME_END_EVENT` | Q-Time 結束事件 | 結束計時的觸發事件 |
| `QTIME_VIOLATION_ACTION` | Q-Time 違規處理 | 超時處理動作 |
| `PROCESSTIME` | 加工時間 | 標準加工時長 |
| `PROCESSUNIT` | 時間單位 | 如：秒、分鐘、小時 |
| `RECIPE` | 配方 | 製程配方參數 |
| `EFFECTIVE_FROM` | 生效起始日 | 製程生效開始時間 |
| `EFFECTIVE_TO` | 生效結束日 | 製程生效結束時間 |
| `RELEASE_STATE` | 發布狀態 | 如：草稿、已發布、已廢止 |
| `CREATED_AT` | 建立時間 | 資料建立時間戳記 |
| `CREATEDBY` | 建立者 | 建立此筆資料的使用者 |
| `LAST_UPDATED` | 最後更新時間 | 資料最後修改時間戳記 |
| `UPDATEDBY` | 更新者 | 最後修改此筆資料的使用者 |
| `IS_AUTOSTEP` | 是否自動步驟 | 是否自動執行 |
| `IS_ACTIVE` | 是否啟用 | 資料有效性標記 |
| `AUTO_MOVENEXT` | 自動移至下一步 | 完成後自動進入下一步 |
| `QTIME_START_STEP` | Q-Time 起始步驟 | Q-Time 計時起始步驟 |
| `CARRIER_TYPE` | 載具類型 | 允許的載具類型 |
| `MANUALPUTRACK` | 手動追蹤 | 是否需要手動追蹤 |

---

## 4️⃣ wo.xlsx - 工單主檔

### 欄位說明

| 欄位名稱 | 中文說明 | 備註 |
|---------|---------|------|
| `   ` | 空白欄位 | 可能為序號或保留欄位 |
| `ID` | 工單唯一識別碼 | 主鍵 |
| `WO_NO` | 工單編號 | 業務識別碼 |
| `NAME` | 工單名稱 | 工單顯示名稱 |
| `PROCESSFLOW_KEY` | 製程流程鍵值 | 關聯到 processflow.xlsx |
| `FLOW_VERSION` | 流程版本 | 使用的製程版本 |
| `QUANTITY` | 計畫數量 | 工單總數量 |
| `QTY_RELEASED` | 已投產數量 | 已發放至產線的數量 |
| `QTY_COMPLETED` | 已完成數量 | 已完工的數量 |
| `QTY_SCRAP` | 報廢數量 | 不良品數量 |
| `WO_TYPE` | 工單類型 | 如：正常單、重工單、試產單 |
| `STATUS` | 工單狀態 | 如：待發放、進行中、已完成 |
| `PRIORITY` | 優先順序 | 排程優先權 |
| `PLAN_START_TIME` | 計畫開始時間 | 預計開始生產時間 |
| `DUE_DATE` | 到期日 | 預計完成時間 |
| `PRODUCT_ID` | 產品編號 | 生產的產品識別碼 |
| `CUSTOMER_CODE` | 客戶代碼 | 客戶識別碼 |
| `LOT_ID_FORMAT` | 批次編號格式 | 批次編號命名規則 |
| `CREATED_AT` | 建立時間 | 資料建立時間戳記 |
| `CREATEDBY` | 建立者 | 建立此筆資料的使用者 |
| `LAST_UPDATED` | 最後更新時間 | 資料最後修改時間戳記 |
| `UPDATEDBY` | 更新者 | 最後修改此筆資料的使用者 |
| `IS_ACTIVE` | 是否啟用 | 資料有效性標記 |
| `START_STEP` | 起始步驟 | 工單開始的製程步驟 |

---

## 🔗 資料表關聯

```
wo.xlsx (工單)
  ├─ PROCESSFLOW_KEY → processflow.xlsx (製程流程)
  └─ WO_ID → lot.xlsx (批次)
       └─ PROCESSFLOW_KEY → processflow.xlsx (製程流程)

eqp.xlsx (設備) - 獨立主檔，透過排程邏輯與其他表關聯
```

---

## 📝 使用說明

1. **資料匯入順序**：
   - 先匯入 `eqp.xlsx`（設備主檔）
   - 再匯入 `processflow.xlsx`（製程流程）
   - 接著匯入 `wo.xlsx`（工單）
   - 最後匯入 `lot.xlsx`（批次）

2. **資料完整性**：
   - 確保外鍵欄位（如 `PROCESSFLOW_KEY`、`WO_ID`）的值在對應的主檔中存在
   - 檢查日期欄位格式一致性
   - 驗證數量欄位的邏輯關係（如：已完成數量 + 報廢數量 ≤ 總數量）

3. **版本控制**：
   - `processflow.xlsx` 和 `lot.xlsx` 都包含版本欄位
   - 確保使用正確的版本號進行關聯

---

## 🛠️ 技術規格

- **檔案格式**：Microsoft Excel (.xlsx)
- **編碼**：UTF-8
- **日期格式**：建議使用 ISO 8601 格式（YYYY-MM-DD HH:MM:SS）
- **布林值**：建議使用 0/1 或 TRUE/FALSE

---

## 📅 文件資訊

- **建立日期**：2026-01-25
- **最後更新**：2026-01-25
- **維護者**：APS01 專案團隊
- **版本**：1.0

---

## 📧 聯絡資訊

如有任何問題或建議，請聯繫專案維護團隊。
