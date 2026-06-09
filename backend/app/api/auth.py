from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, EmailStr
from passlib.context import CryptContext
from typing import Optional
from app.services.user_db import UserDB

MAX_PASSWORD_BYTES = 72


router = APIRouter()
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
user_db = UserDB()


class RegisterRequest(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(..., min_length=6, max_length=128)


class RegisterResponse(BaseModel):
    user_id: int
    email: EmailStr


class LoginRequest(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(..., min_length=6, max_length=128)


class LoginResponse(BaseModel):
    user_id: int
    email: EmailStr


@router.post("/auth/register", response_model=RegisterResponse)
async def register(req: RegisterRequest):
    password = req.password.strip()

    if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise HTTPException(
            status_code=400,
            detail="Password too long (max 72 bytes)"
        )

    password_hash = pwd_context.hash(password)
    user_id = user_db.create_user(req.email, password_hash)
    if not user_id:
        raise HTTPException(status_code=400, detail="User already exists or invalid")
    return RegisterResponse(user_id=user_id, email=req.email)


@router.post("/auth/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    user = user_db.get_user(req.email)
    if not user or not pwd_context.verify(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # Ensure user's table exists and is ready
    user_db.ensure_user_table(user["id"])
    return LoginResponse(user_id=user["id"], email=user["email"])
