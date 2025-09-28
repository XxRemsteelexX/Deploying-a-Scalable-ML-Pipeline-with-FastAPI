import os
import logging
import time
from datetime import datetime
from typing import Dict, Any

import pandas as pd
import numpy as np
from fastapi import FastAPI, APIRouter, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from ml.data import apply_label, process_data
from ml.model import inference, load_model

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables for metrics
request_count = 0
model_predictions = {'>50K': 0, '<=50K': 0}
start_time = time.time()

# Pydantic models
class Data(BaseModel):
    """Input data model for census income prediction."""
    age: int = Field(..., example=37, description="Age of the individual")
    workclass: str = Field(..., example="Private", description="Type of work class")
    fnlgt: int = Field(..., example=178356, description="Final weight")
    education: str = Field(..., example="HS-grad", description="Education level")
    education_num: int = Field(..., example=10, alias="education-num", description="Numeric education level")
    marital_status: str = Field(
        ..., example="Married-civ-spouse", alias="marital-status",
        description="Marital status"
    )
    occupation: str = Field(..., example="Prof-specialty", description="Occupation type")
    relationship: str = Field(..., example="Husband", description="Relationship status")
    race: str = Field(..., example="White", description="Race")
    sex: str = Field(..., example="Male", description="Gender")
    capital_gain: int = Field(..., example=0, alias="capital-gain", description="Capital gains")
    capital_loss: int = Field(..., example=0, alias="capital-loss", description="Capital losses")
    hours_per_week: int = Field(..., example=40, alias="hours-per-week", description="Hours worked per week")
    native_country: str = Field(..., example="United-States", alias="native-country", description="Native country")

class PredictionResponse(BaseModel):
    """Response model for predictions."""
    prediction: str = Field(..., description="Income prediction: '>50K' or '<=50K'")
    confidence: float = Field(..., description="Model confidence score")
    model_version: str = Field(..., description="Version of the model used")
    timestamp: str = Field(..., description="Timestamp of the prediction")

class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Service health status")
    timestamp: str = Field(..., description="Current timestamp")
    model_loaded: bool = Field(..., description="Whether model is loaded successfully")
    version: str = Field(..., description="API version")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")

class MetricsResponse(BaseModel):
    """Response model for metrics."""
    model_performance: Dict[str, float] = Field(..., description="Model performance metrics")
    request_count: int = Field(..., description="Total number of requests processed")
    prediction_distribution: Dict[str, int] = Field(..., description="Distribution of predictions")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    last_updated: str = Field(..., description="Last update timestamp")

# Load models
try:
    encoder_path = os.path.join('.', 'model', 'encoder.pkl')
    model_path = os.path.join('.', 'model', 'model.pkl')
    
    encoder = load_model(encoder_path)
    model = load_model(model_path)
    model_loaded = True
    logger.info("Models loaded successfully")
except Exception as e:
    logger.error(f"Failed to load models: {e}")
    model_loaded = False
    encoder = None
    model = None

# FastAPI app configuration
app = FastAPI(
    title="Census Income Prediction API",
    description="A production-ready ML API for predicting income levels based on census data",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create API router for versioned endpoints
api_v1 = APIRouter(prefix="/v1", tags=["v1"])

# Middleware for request logging and metrics
@app.middleware("http")
async def log_requests(request: Request, call_next):
    global request_count
    start_time_req = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url}")
    request_count += 1
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time_req
    logger.info(f"Response: {response.status_code} - Time: {process_time:.4f}s")
    
    return response

# Root endpoint
@app.get("/", response_model=Dict[str, Any])
async def get_root():
    """Welcome message and API information."""
    return {
        "message": "Welcome to the Census Income Prediction API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_check": "/v1/health",
        "metrics": "/v1/metrics"
    }

# Health check endpoint
@api_v1.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring."""
    current_time = datetime.utcnow().isoformat() + "Z"
    uptime = time.time() - start_time
    
    return HealthResponse(
        status="healthy" if model_loaded else "unhealthy",
        timestamp=current_time,
        model_loaded=model_loaded,
        version="1.0.0",
        uptime_seconds=uptime
    )

# Metrics endpoint
@api_v1.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get model performance metrics and API statistics."""
    current_time = datetime.utcnow().isoformat() + "Z"
    uptime = time.time() - start_time
    
    # Mock performance metrics (in production, these would come from model evaluation)
    model_performance = {
        "precision": 0.7369,
        "recall": 0.6294,
        "f1_score": 0.6789
    }
    
    return MetricsResponse(
        model_performance=model_performance,
        request_count=request_count,
        prediction_distribution=model_predictions.copy(),
        uptime_seconds=uptime,
        last_updated=current_time
    )

# Model info endpoint
@api_v1.get("/model/info")
async def get_model_info():
    """Get information about the loaded model."""
    if not model_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    return {
        "model_type": "RandomForestClassifier",
        "features": [
            "age", "workclass", "fnlgt", "education", "education-num",
            "marital-status", "occupation", "relationship", "race", "sex",
            "capital-gain", "capital-loss", "hours-per-week", "native-country"
        ],
        "target_classes": [">50K", "<=50K"],
        "model_version": "v1.0.0",
        "trained_on": "1994 US Census data"
    }

# Prediction endpoint
@api_v1.post("/predict", response_model=PredictionResponse)
async def predict_income(data: Data):
    """Predict income category based on individual characteristics."""
    global model_predictions
    
    if not model_loaded:
        raise HTTPException(status_code=503, detail="Model not available")
    
    try:
        # Convert Pydantic model to dict and then to DataFrame
        data_dict = data.dict(by_alias=True)
        data_df = pd.DataFrame([data_dict])
        
        # Define categorical features
        cat_features = [
            "workclass",
            "education",
            "marital-status",
            "occupation",
            "relationship",
            "race",
            "sex",
            "native-country",
        ]
        
        # Process data
        data_processed, _, _, _ = process_data(
            X=data_df,
            categorical_features=cat_features,
            training=False,
            encoder=encoder
        )
        
        # Make prediction
        prediction_proba = model.predict_proba(data_processed)
        prediction = inference(model, data_processed)
        
        # Get prediction label and confidence
        prediction_label = apply_label(prediction)
        confidence = float(np.max(prediction_proba))
        
        # Update prediction metrics
        model_predictions[prediction_label] += 1
        
        # Create response
        response = PredictionResponse(
            prediction=prediction_label,
            confidence=confidence,
            model_version="v1.0.0",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
        logger.info(f"Prediction made: {prediction_label} (confidence: {confidence:.4f})")
        return response
        
    except Exception as e:
        logger.error(f"Error during prediction: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

# Legacy endpoint for backward compatibility
@app.post("/data/")
async def legacy_inference(data: Data):
    """Legacy endpoint for backward compatibility."""
    logger.warning("Legacy endpoint /data/ used. Consider migrating to /v1/predict")
    
    # Redirect to new endpoint logic
    try:
        result = await predict_income(data)
        return {"result": result.prediction}
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"error": e.detail})

# Include the API router
app.include_router(api_v1)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
