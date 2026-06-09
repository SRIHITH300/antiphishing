from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.core.security import compute_url_hash, normalize_url
from app.services.user_db import UserDB
from app.services.hash_lookup import HashLookup

router = APIRouter()
user_db = UserDB()
hash_lookup = HashLookup()


class FlagRequest(BaseModel):
    user_id: int = Field(...)
    url: str = Field(..., min_length=1, max_length=2048)


class FlagResponse(BaseModel):
    success: bool
    found_in_main_db: bool
    found_in_user_db: bool
    message: str


@router.post("/flags/flag", response_model=FlagResponse)
async def flag_url(req: FlagRequest):
    normalized = normalize_url(req.url)
    url_hash = compute_url_hash(normalized)
    found_main = user_db.exists_phishing_in_main_db(url_hash)
    if found_main:
        return FlagResponse(
            success=False,
            found_in_main_db=True,
            found_in_user_db=False,
            message="URL exists in main database",
        )
    already = user_db.is_flagged(req.user_id, url_hash)
    if already:
        return FlagResponse(
            success=False,
            found_in_main_db=False,
            found_in_user_db=True,
            message="URL already flagged by user",
        )
    inserted = user_db.flag_url(req.user_id, url_hash, normalized)
    if not inserted:
        raise HTTPException(status_code=500, detail="Failed to flag URL")
    return FlagResponse(
        success=True,
        found_in_main_db=False,
        found_in_user_db=True,
        message="URL flagged",
    )
