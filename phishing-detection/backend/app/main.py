
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.api import analyze
from app.api import auth
from app.api import flags

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global model inference instance
model_inference = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    
    global model_inference

    logger.info("Starting Phishing Detection API...")

    try:
        
        from app.services.inference import ModelInference

        model_inference = ModelInference(
            dt_model_path=settings.DT_MODEL_PATH,
            lstm_model_path=settings.LSTM_MODEL_PATH,
            ensemble_model_path=settings.ENSEMBLE_MODEL_PATH,
            vocab_path=settings.VOCAB_PATH
        )

        logger.info("✓ All models loaded successfully")
        logger.info(f"✓ Using device: {model_inference.device}")

    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        raise

    yield

    logger.info("Shutting down Phishing Detection API...")



app = FastAPI(
    title="Phishing Detection API",
    description="Real-time phishing URL detection using ensemble ML/DL models",
    version="1.0.0",
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(analyze.router, prefix="/api", tags=["analysis"])
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(flags.router, prefix="/api", tags=["flags"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Phishing Detection API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "models_loaded": model_inference is not None,
        "device": str(model_inference.device) if model_inference else "unknown"
    }


def get_model_inference():
    """Dependency injection for model inference"""
    if model_inference is None:
        raise RuntimeError("ModelInference not initialized")
    return model_inference
