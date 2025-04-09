# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import motor.motor_asyncio
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)

app = FastAPI()

# 加這一段 ── CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # 本機 React/Vue/Angular 等
        "https://click4news-frontend-app.web.app",   # 你的正式前端網址（Cloud Run 前端）
    ],
    allow_credentials=True,
    allow_methods=["*"],   # GET, POST, PUT, DELETE, OPTIONS...
    allow_headers=["*"],   # Authorization, Content-Type, ...
)
# 連接到 MongoDB Atlas，請確認連線字串正確
client = motor.motor_asyncio.AsyncIOMotorClient(
    "mongodb+srv://vasa2949:sandy@cluster0.j5gm2.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client.sqsMessagesDB  # 請確認這是正確的資料庫名稱

@app.get("/geojson")
async def get_geojson():
    try:
        # 從 news 集合中撈取所有文件（假設每筆都是一個完整的 FeatureCollection）
        articles = await db.raw_messages.find({}).to_list(length=1000)

        # 用來收集「所有文件」的 features
        all_features = []

        for article in articles:
            # 1. 取得該文件的 features
            doc_features = article.get("features", [])
            if not doc_features:
                logging.info(f"文件 {article.get('_id')} 中沒有 features 或結構不符")
                continue

            # 2. 取得該文件的其他欄位
            doc_properties = article.get("properties", {})  # 文件本身帶的 properties（若有）
            doc_title       = article.get("title")
            doc_published  = article.get("publishedAt")
            doc_url         = article.get("url")
            doc_geometry    = article.get("geometry", {})

            # 3. 將「文件層級」的資訊合併到每個 feature
            for feature in doc_features:
                # 若該 feature 沒有 properties，就先建一個空的
                if "properties" not in feature:
                    feature["properties"] = {}

                # (a) 合併文件自己的 properties 到 feature 的 properties
                #     可依照需求決定要不要全部合併，或只挑特定 key
                for key, value in doc_properties.items():
                    feature["properties"][key] = value

                # (b) 如果想把 doc_title, doc_published, doc_url 等也放進 feature.properties
                if doc_title:
                    feature["properties"]["title"] = doc_title
                if doc_published:
                    feature["properties"]["publishedAt"] = doc_published
                if doc_url:
                    feature["properties"]["url"] = doc_url

                # (c) 若你想把文件自己的 geometry 也塞到 feature.properties（或其他結構）
                #     依照你的需求來放；以下只是示範：
                if doc_geometry:
                    feature["properties"]["docGeometry"] = doc_geometry

                # 4. 把處理完的 feature 加入到 all_features
                all_features.append(feature)

        # 5. 最後回傳一個「合併後」的 FeatureCollection
        return {
            "type": "FeatureCollection",
            "features": all_features
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # 啟動伺服器，預設在 http://0.0.0.0:3000
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
