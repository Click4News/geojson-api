# main.py
from fastapi import FastAPI, HTTPException
import motor.motor_asyncio
import uvicorn
import logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Connect to MongoDB Atlas (ensure your credentials and cluster details are correct)
client = motor.motor_asyncio.AsyncIOMotorClient(
    "mongodb+srv://vasa2949:sandy@cluster0.j5gm2.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client.newsDB  # Use your database name; you may also set it here if it's different

@app.get("/geojson")
async def get_geojson():
    try:
        # Retrieve all documents from the articles collection
        cursor = db.news.find({})
        articles = await cursor.to_list(length=1000)
        
        # Convert each document to a GeoJSON Feature
        features = []
        for article in articles:
            logging.info("hi")
            geo = article.get("geoJson")
            if not geo:
                continue  # Skip if no geoJson field is present
            
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
        
        # Assemble the FeatureCollection
        feature_collection = {
            "type": "FeatureCollection",
            "features": features
        }
        
        return feature_collection
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Run the server on port 3000 (or change as needed)
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
