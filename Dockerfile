# 使用輕量版的 Python 3.9 作為基底映像檔
FROM python:3.9-slim

# 設定工作目錄
WORKDIR /app

# 複製需求檔案到容器中
COPY requirements.txt .

# 安裝 Python 套件
RUN pip install --no-cache-dir -r requirements.txt

# 複製整個專案到容器中
COPY . .

# 設定埠號環境變數（Cloud Run 預設使用 8080 埠）
ENV PORT 8080

# 使用 uvicorn 啟動 FastAPI 應用程式
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
