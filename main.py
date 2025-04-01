import os
from fastapi import FastAPI, HTTPException
import motor.motor_asyncio
import uvicorn
import logging
from mangum import Mangum  # 加入 Mangum

logging.basicConfig(level=logging.INFO)

app = FastAPI()

# 連接 MongoDB Atlas
client = motor.motor_asyncio.AsyncIOMotorClient(
    "mongodb+srv://vasa2949:sandy@cluster0.j5gm2.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client.newsDB

@app.get("/geojson")
async def get_geojson():
    try:
        cursor = db.news.find({})
        articles = await cursor.to_list(length=1000)
        features = []
        for article in articles:
            logging.info("hi")
            geo = article.get("geoJson")
            if not geo:
                continue
            feature = {
                "type": "Feature",
                "geometry": geo.get("geometry"),
                "properties": {
                    "title": article.get("title"),
                    "description": article.get("description"),
                    "url": article.get("url"),
                    "publishedAt": article.get("publishedAt"),
                }
            }
            features.append(feature)
        feature_collection = {
            "type": "FeatureCollection",
            "features": features
        }
        return feature_collection
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 新增 Lambda handler
handler = Mangum(app)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
