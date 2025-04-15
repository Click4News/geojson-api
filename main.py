from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import motor.motor_asyncio
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Add this section — CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # Local React/Vue/Angular dev
        "https://click4news-frontend-app.web.app",   # Your production frontend URL (Cloud Run)
    ],
    allow_credentials=True,
    allow_methods=["*"],   # Allow GET, POST, PUT, DELETE, OPTIONS...
    allow_headers=["*"],   # Allow Authorization, Content-Type, etc.
)

# Connect to MongoDB Atlas, make sure the connection string is correct
client = motor.motor_asyncio.AsyncIOMotorClient(
    "mongodb+srv://vasa2949:sandy@cluster0.j5gm2.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client.sqsMessagesDB1  # Ensure this is the correct database name

@app.get("/geojson")
async def get_geojson():
    try:
        # Fetch all documents from the raw_messages collection (each assumed to be a complete FeatureCollection)
        articles = await db.raw_messages.find({}).to_list(length=1000)

        # Prepare a list to collect features from all documents
        all_features = []

        for article in articles:
            # 1. Get the features array from the document
            doc_features = article.get("features", [])
            if not doc_features:
                logging.info(f"Document {article.get('_id')} has no features or unexpected structure")
                continue

            # 2. Extract other fields from the document
            doc_properties = article.get("properties", {})  # Document-level properties (if any)
            doc_title      = article.get("title")
            doc_published  = article.get("publishedAt")
            doc_url        = article.get("url")
            doc_geometry   = article.get("geometry", {})

            # 3. Merge document-level information into each feature
            for feature in doc_features:
                # If the feature has no properties, initialize an empty dict
                if "properties" not in feature:
                    feature["properties"] = {}

                # (a) Merge document's properties into the feature's properties
                #     Adjust as needed to merge all keys or only specific ones
                for key, value in doc_properties.items():
                    feature["properties"][key] = value

                # (b) Optionally add doc_title, doc_published, doc_url to feature.properties
                if doc_title:
                    feature["properties"]["title"] = doc_title
                if doc_published:
                    feature["properties"]["publishedAt"] = doc_published
                if doc_url:
                    feature["properties"]["url"] = doc_url

                # (c) If you want to include the document's geometry in feature.properties (or elsewhere)
                if doc_geometry:
                    feature["properties"]["docGeometry"] = doc_geometry

                # 4. Add the processed feature to all_features
                all_features.append(feature)

        # 5. Return the combined FeatureCollection
        return {
            "type": "FeatureCollection",
            "features": all_features
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Run the server, default at http://0.0.0.0:3000
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
