import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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
    project_id = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        _, project_id = google.auth.default()
    if not project_id:
        raise RuntimeError("Unable to determine GCP project ID")
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version}"
    resp = client.access_secret_version(name=name)
    return resp.payload.data.decode("UTF-8")

# Fetch Mongo URI and DB name
MONGODB_URI = get_secret("MONGO_URI")
DB_NAME     = os.getenv("DB_NAME", "sqsMessagesDB1")

# Connect to Mongo
client       = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
db           = client[DB_NAME]
raw_msgs_col = db.raw_messages
users_col    = db.users

# Pydantic model for POST body
class UserRequest(BaseModel):
    userid: str

@app.get("/geojson")
async def get_geojson():
    try:
        docs = await raw_msgs_col.find({}).to_list(length=None)
        all_features = []
        for doc in docs:
            feats = doc.get("features", [])
            if isinstance(feats, list):
                all_features.extend(feats)
        return {"type": "FeatureCollection", "features": all_features}
    except Exception as e:
        logging.error(f"get_geojson failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/user")
async def get_user_stats(req: UserRequest):
    user_doc = await users_col.find_one({"userid": req.userid})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

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
