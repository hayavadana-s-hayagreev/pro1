from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import List

from backend.auth import router as auth_router
from backend.predictor import predict_yield, determine_yield_level
from backend.recommender import get_recommendations
from backend.eda_service import get_eda_data
from backend.history_service import add_prediction, add_search, get_user_history

app = FastAPI(title="🌾 Crop Yield Estimator API")

# Setup CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

class PredictionRequest(BaseModel):
    crop: str
    country: str
    year: int
    rainfall: float
    pesticide: float
    temperature: float

class SearchRequest(BaseModel):
    query: str

@app.get("/")
def read_root():
    return {"message": "Welcome to Crop Yield Estimator API"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "api": "online"}

@app.post("/predict")
def make_prediction(req: PredictionRequest):
    try:
        # 1. Predict
        yield_pred = predict_yield(
            req.crop, req.country, req.year, req.rainfall, req.pesticide, req.temperature
        )
        yield_level = determine_yield_level(yield_pred)
        
        # 2. Recommend
        recommendations = get_recommendations(
            req.crop, req.country, yield_level, req.rainfall, req.temperature
        )
        
        result = {
            "predicted_yield_hg_ha": yield_pred,
            "predicted_yield_tonnes_ha": yield_pred / 10000,
            "yield_level": yield_level,
            "recommendations": recommendations,
            "inputs": req.dict()
        }
        
        # 3. Save to history
        add_prediction("anonymous_user", result)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/eda/{chart_type}")
def get_eda_chart(chart_type: str):
    data = get_eda_data(chart_type)
    if not data:
        raise HTTPException(status_code=404, detail="Data not found or chart type invalid")
    return {"data": data}

@app.get("/history")
def get_history():
    return get_user_history("anonymous_user")

@app.post("/history/search")
def log_search(req: SearchRequest):
    return add_search("anonymous_user", req.query)

import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# ... (rest of the file stays the same, I need to use multi_replace to be precise)
