"""
API endpoint for URL analysis
FIXED VERSION - Addresses 422 validation errors
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict
import logging

from app.core.security import compute_url_hash, normalize_url, validate_url, sanitize_url_for_display
from app.services.hash_lookup import HashLookup
from app.services.inference import ModelInference
from app.services.user_db import UserDB

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize hash lookup service
hash_lookup = HashLookup()
user_db = UserDB()


class URLRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2048, description="URL to analyze")
    user_id: Optional[int] = Field(default=None, description="Optional user id for user DB lookup")
    @validator('url')
    def validate_url_format(cls, v):
        if not v or not v.strip():
            raise ValueError("URL cannot be empty")
        try:
            from app.core.security import normalize_url
            normalized = normalize_url(v.strip())
            return normalized
        except Exception as e:
            raise ValueError(f"Invalid URL format: {str(e)}")
    model_config = {
        "json_schema_extra": {
            "example": {
                "url": "https://www.example.com",
                "user_id": 1
            }
        }
    }


class URLResponse(BaseModel):
    is_phishing: bool
    confidence: float
    url: str
    details: Optional[Dict] = None
    source: str = "ml_inference"
    found_in_main_db: bool = False
    found_in_user_db: bool = False

class LookupResponse(BaseModel):
    url: str
    url_hash: str
    found_in_main_db: bool
    found_in_user_db: bool
    source: str = "lookup"

@router.post("/analyze", response_model=URLResponse)
async def analyze_url(request: URLRequest):
    """
    Analyze URL for phishing
    
    **Fixed to handle 422 errors properly**
    
    Args:
        request: URLRequest with URL to analyze
        
    Returns:
        URLResponse with analysis result
        
    Raises:
        400: Invalid URL format
        503: Service unavailable
        500: Internal server error
    """
    try:
        # URL is already normalized by the validator
        normalized_url = request.url
        
        logger.info(f"Analyzing URL: {sanitize_url_for_display(normalized_url)}")
        
        # Compute hash
        url_hash = compute_url_hash(normalized_url)
        
        cached_result = hash_lookup.lookup(url_hash)
        if cached_result:
            val = cached_result.get('is_phishing')
            found_main = (
                (val is True) or
                (val == 1) or
                (isinstance(val, str) and val.strip().lower() in ('1', 'true', 't', 'yes', 'y'))
            )
            found_user = bool(request.user_id and user_db.is_flagged(request.user_id, url_hash))
            is_phish = bool(found_user or found_main)
            src = "user_db" if found_user else "cache"
            return URLResponse(
                is_phishing=is_phish,
                confidence=cached_result['confidence'],
                url=normalized_url,
                details=cached_result.get('details'),
                source=src,
                found_in_main_db=found_main,
                found_in_user_db=found_user
            )
        
        # Slow path: Run ML inference
        logger.info(f"Running ML inference for URL hash: {url_hash[:16]}...")
        
        # Get model inference instance from app state
        from app.main import get_model_inference
        inference = get_model_inference()
        
        if not inference:
            raise HTTPException(
                status_code=503, 
                detail="Model inference service not available"
            )
        
        result = inference.predict(normalized_url)
        found_main = user_db.exists_phishing_in_main_db(url_hash)
        found_user = bool(request.user_id and user_db.is_flagged(request.user_id, url_hash))
        is_phish = bool(result['is_phishing'] or found_user)
        return URLResponse(
            is_phishing=is_phish,
            confidence=result['confidence'],
            url=normalized_url,
            details=result.get('details'),
            source="user_db" if found_user else "ml_inference",
            found_in_main_db=found_main,
            found_in_user_db=found_user
        )
        
    except ValueError as e:
        # Validation errors
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Unexpected errors
        logger.error(f"Analysis error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@router.get("/analyze/check", response_model=LookupResponse)
async def check_lookup(url: str, user_id: Optional[int] = None):
    """
    Quick check if a URL exists in main DB and user DB
    """
    try:
        normalized = normalize_url(url.strip())
        url_hash = compute_url_hash(normalized)
        found_main = user_db.exists_phishing_in_main_db(url_hash)
        found_user = bool(user_id and user_db.is_flagged(user_id, url_hash))
        return LookupResponse(
            url=normalized,
            url_hash=url_hash,
            found_in_main_db=found_main,
            found_in_user_db=found_user,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Lookup failed: {e}")

@router.get("/stats")
async def get_stats():
    """
    Get database statistics
    
    Returns:
        Statistics about cached URLs
    """
    try:
        stats = hash_lookup.get_stats()
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve statistics"
        )
