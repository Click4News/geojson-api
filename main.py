# main.py

import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import motor.motor_asyncio
import uvicorn
from google.cloud import secretmanager

logging.basicConfig(level=logging.INFO)
app = FastAPI()

# CORS settings
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
    Fetch the payload of the given secret from GCP Secret Manager.
    """
    project_id = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        raise RuntimeError("Environment variable GCP_PROJECT is not set")
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version}"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")

# 1. Retrieve the MongoDB connection string from Secret Manager
MONGODB_URI = get_secret("MONGO_URI")

# 2. Database name from env (default to "sqsMessagesDB1")
DB_NAME = os.getenv("DB_NAME", "sqsMessagesDB1")

# Connect to MongoDB Atlas
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
db = client[DB_NAME]

@app.get("/geojson")
async def get_geojson():
    try:
        articles = await db.raw_messages.find({}).to_list(length=1000)
        all_features = []

        for article in articles:
            features = article.get("features", [])
            if not features:
                logging.info(f"Document {article.get('_id')} has no features")
                continue

            props     = article.get("properties", {})
            title     = article.get("title")
            published = article.get("publishedAt")
            url       = article.get("url")
            geom      = article.get("geometry", {})

            for feat in features:
                feat.setdefault("properties", {})
                # merge document-level properties
                for k, v in props.items():
                    feat["properties"][k] = v
                if title:
                    feat["properties"]["title"] = title
                if published:
                    feat["properties"]["publishedAt"] = published
                if url:
                    feat["properties"]["url"] = url
                if geom:
                    feat["properties"]["docGeometry"] = geom

                all_features.append(feat)

        return {"type": "FeatureCollection", "features": all_features}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
