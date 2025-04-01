FROM python:3.9-slim

# 設定工作目錄
WORKDIR /app

# 複製相依檔案並安裝依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製所有程式碼到容器
COPY . .

# 使用 shell 形式啟動應用程式，讓環境變數 PORT 能夠正確展開
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
