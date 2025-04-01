# 使用輕量版的 Python 映像檔
FROM python:3.9-slim

# 設定工作目錄
WORKDIR /app

# 複製 requirements.txt 並安裝相依套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製所有檔案到容器中
COPY . .

# Cloud Run 會使用環境變數 PORT，所以我們使用該變數啟動應用程式
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "$PORT"]
