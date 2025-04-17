import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import motor.motor_asyncio
import uvicorn

from google.cloud import secretmanager
import google.auth

logging.basicConfig(level=logging.INFO)
app = FastAPI()

# CORS 设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://click4news-frontend-app.web.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_secret(secret_id: str, version: str = "latest") -> str:
    """
    从 Secret Manager 拿 secret 值。
    优先用环境变量，否则用 ADC 自动获取 project_id。
    """
    project_id = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        _, project_id = google.auth.default()
    if not project_id:
        raise RuntimeError(
            "无法取得 GCP 项目 ID，请设置 GCP_PROJECT 或 GOOGLE_CLOUD_PROJECT"
        )
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version}"
    resp = client.access_secret_version(name=name)
    return resp.payload.data.decode("UTF-8")

# 1. 从 Secret Manager 读出 Mongo URI
MONGODB_URI = get_secret("MONGO_URI")
# 2. DB 名称用 env 或默认
DB_NAME = os.getenv("DB_NAME", "sqsMessagesDB1")

# 3. 连接 MongoDB
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
db = client[DB_NAME]

@app.get("/geojson")
async def get_geojson():
    """
    把 raw_messages 集合里所有文档的 features 平铺合并，
    返回一个标准的 GeoJSON FeatureCollection。
    """
    try:
        # 拉取所有文档
        docs = await db.raw_messages.find({}).to_list(length=None)
        all_features = []
        for doc in docs:
            feats = doc.get("features", [])
            if not isinstance(feats, list):
                logging.warning(f"文档 {doc.get('_id')} 的 features 不是列表，已跳过")
                continue
            all_features.extend(feats)

        return {"type": "FeatureCollection", "features": all_features}

    except Exception as e:
        logging.error(f"获取 geojson 失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
