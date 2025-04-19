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
    Retrieve a secret from Google Secret Manager.
    Falls back to ADC if GCP_PROJECT/GOOGLE_CLOUD_PROJECT not set.
    """
    project_id = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        _, project_id = google.auth.default()
    if not project_id:
        raise RuntimeError(
            "Unable to determine GCP project ID; set GCP_PROJECT or GOOGLE_CLOUD_PROJECT"
        )
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version}"
    resp = client.access_secret_version(name=name)
    return resp.payload.data.decode("UTF-8")

# 1. Fetch MongoDB URI from Secret Manager
MONGODB_URI = get_secret("MONGO_URI")
# 2. Database name via env or default
DB_NAME = os.getenv("DB_NAME", "sqsMessagesDB1")

# 3. Connect to MongoDB
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
db = client[DB_NAME]

# Collections
raw_msgs_col = db.raw_messages
users_col    = db.users  # ← New: user statistics stored here

@app.get("/geojson")
async def get_geojson():
    """
    Flatten all 'features' arrays in raw_messages into
    a single GeoJSON FeatureCollection.
    """
    try:
        docs = await raw_msgs_col.find({}).to_list(length=None)
        all_features = []
        for doc in docs:
            feats = doc.get("features", [])
            if not isinstance(feats, list):
                logging.warning(f"Doc {doc.get('_id')} features not a list, skipping")
                continue
            all_features.extend(feats)

        return {"type": "FeatureCollection", "features": all_features}

    except Exception as e:
        logging.error(f"Failed to fetch geojson: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user/{user_id}")
async def get_user_stats(user_id: str):
    """
    Retrieve aggregated statistics for a given user_id
    directly from the 'users' collection.
    """
    # 1. Fetch the user document
    user_doc = await users_col.find_one({"userid": user_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Return only the fields we care about
    return {
        "userid":                   user_doc.get("userid"),
        "credibility_score":        user_doc.get("credibility_score", 0),
        "total_likes_received":     user_doc.get("total_likes_received", 0),
        "total_fakeflags_received": user_doc.get("total_fakeflags_received", 0),
        "total_articles":           user_doc.get("total_articles", 0),
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
