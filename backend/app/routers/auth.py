from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr

from app.database import get_db
from app.services import auth_service
from app.middleware.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await auth_service.get_user_by_email(db, body.email)
    if existing:
        raise HTTPException(400, "Email already registered")
    user = await auth_service.create_user(db, body.email, body.password)
    access = auth_service.create_access_token({"sub": str(user.id)})
    refresh = auth_service.create_refresh_token({"sub": str(user.id)})
    return {"access_token": access, "refresh_token": refresh}


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.authenticate_user(db, body.email, body.password)
    if not user:
        raise HTTPException(401, "Invalid email or password")
    if not user.is_active:
        raise HTTPException(403, "Account is deactivated")
    access = auth_service.create_access_token({"sub": str(user.id)})
    refresh = auth_service.create_refresh_token({"sub": str(user.id)})
    return {"access_token": access, "refresh_token": refresh}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = auth_service.decode_token(body.refresh_token, expected_type="refresh")
    if not payload:
        raise HTTPException(401, "Invalid or expired refresh token")
    user_id = int(payload["sub"])
    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(401, "User not found")
    access = auth_service.create_access_token({"sub": str(user_id)})
    refresh = auth_service.create_refresh_token({"sub": str(user_id)})
    return {"access_token": access, "refresh_token": refresh}


@router.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "email_verified": current_user.email_verified,
        "created_at": current_user.created_at.isoformat(),
    }
