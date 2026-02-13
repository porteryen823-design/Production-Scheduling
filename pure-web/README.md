# Pure Web frontend - 生產排程系統 (純網頁版)

## 專案說明
本目錄包含生產排程系統的純網頁版前端，主要由靜態 HTML、CSS、JS 組成。
這些頁面提供了甘特圖監控和報表查看功能，適用於簡單的展示和監控需求。

- **Technology Profile**: Profile C (靜態簡易網頁)

## 目錄結構
- `index.html`: 管理控制台入口
- `css/`: 樣式表 (包含 Bootstrap, FontAwesome, DHTMLX Gantt)
- `js/`: JavaScript 腳本
- `webfonts/`: 字體文件
- `PlanResult/`: local 產出的排程結果 (JSON 格式)

## 使用方法
1. 使用 Nginx 或其他靜態伺服器託管此目錄。
2. 在瀏覽器中開啟 `index.html`。

## 相關服務
預設由 Docker 中的 `nginx:alpine` 服務託管，通訊埠為 `5501`。
