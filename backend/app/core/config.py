"""
Configuration management using environment variables
"""
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # CORS Settings
    CORS_ORIGINS: List[str] = ["*"]
    
    # Model Paths
    MODELS_DIR: Path = Path(__file__).parent.parent / "models"
    DT_MODEL_PATH: Path = MODELS_DIR / "decision_tree_model.pkl"
    LSTM_MODEL_PATH: Path = MODELS_DIR / "lstm_model.pt"
    ENSEMBLE_MODEL_PATH: Path = MODELS_DIR / "ensemble_model.pkl"
    VOCAB_PATH: Path = MODELS_DIR / "vocab.json"
    
    # Inference Settings
    LSTM_MAX_LENGTH: int = 200
    CONFIDENCE_THRESHOLD: float = 0.5
    
    # Database Settings (for hash lookup)
    DATABASE_URL: str = "sqlite:///./phishing_detection.db"
    
    # Performance Settings
    USE_GPU: bool = True
    ENABLE_HASH_CACHE: bool = True
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }


settings = Settings()
