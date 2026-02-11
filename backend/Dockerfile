# 使用輕量級 Python 3.11 映像檔
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 設定環境變數，確保 Python 輸出直接印到終端機而不緩衝
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 安裝系統依賴 (如果需要的話，這裡可以加入)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements.txt 並安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製所有後端原始碼
COPY . .

# 暴露 FastAPI 預設通訊埠
EXPOSE 8000

# 啟動命令 (使用 uvicorn)
# 使用 --app-dir 指定 src 目錄，這樣程式內的 import 才能正確運作
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "src"]
