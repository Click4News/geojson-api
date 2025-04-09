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
        "https://your-frontend.app",   # 你的正式前端網址（Cloud Run 前端）
        # 或者開發階段直接 "*"
        # "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],   # GET, POST, PUT, DELETE, OPTIONS...
    allow_headers=["*"],   # Authorization, Content-Type, ...
)

# 以下是你原本的程式
client = motor.motor_asyncio.AsyncIOMotorClient(
    "mongodb+srv://vasa2949:…@cluster0.j5gm2.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client.sqsMessagesDB

@app.get("/geojson")
async def get_geojson():
    try:
        articles = await db.raw_messages.find({}).to_list(length=1000)
        all_features = []
        for article in articles:
            doc_features = article.get("features", [])
            if not doc_features:
                logging.info(f"文件 {article.get('_id')} 中沒有 features 或結構不符")
                continue
            doc_properties = article.get("properties", {})
            doc_title      = article.get("title")
            doc_published  = article.get("publishedAt")
            doc_url        = article.get("url")
            doc_geometry   = article.get("geometry", {})

            for feature in doc_features:
                feature.setdefault("properties", {})
                # 合併 properties
                for k, v in doc_properties.items():
                    feature["properties"][k] = v
                if doc_title:
                    feature["properties"]["title"] = doc_title
                if doc_published:
                    feature["properties"]["publishedAt"] = doc_published
                if doc_url:
                    feature["properties"]["url"] = doc_url
                if doc_geometry:
                    feature["properties"]["docGeometry"] = doc_geometry
                all_features.append(feature)

        return {"type": "FeatureCollection", "features": all_features}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
