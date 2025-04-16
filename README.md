# click4news-geojson-api

> **GeoJSON aggregation service**  
> Fetch raw news messages (each containing a GeoJSON FeatureCollection) from MongoDB Atlas, merge all features, and expose a single combined FeatureCollection at `/geojson`.

---

## Table of Contents

- [Features](#features)  
- [Prerequisites](#prerequisites)  
- [Getting Started](#getting-started)  
  - [Clone the repo](#clone-the-repo)  
  - [Install dependencies](#install-dependencies)  
  - [Configuration](#configuration)  
  - [Run locally](#run-locally)  
- [Docker](#docker)  
- [Google Cloud Build & Run](#google-cloud-build--run)  
- [API Reference](#api-reference)  
- [CORS](#cors)  
- [Logging](#logging)  
- [Contributing](#contributing)  
- [License](#license)  

---

## Features

- **FastAPI**‑powered HTTP server  
-  **Motor** (async MongoDB client)  
-  Single endpoint: **GET** `/geojson`  
-  CORS configured for both local dev and your production frontend  
-  Runs in Docker & deploys easily to Cloud Run  

---

## Prerequisites

- **Python** ≥ 3.9  
- **MongoDB Atlas** cluster & connection URI  
- **Docker** (optional, for containerized runs)  
- **Google Cloud** project with Cloud Build & Cloud Run (optional)

