import secrets
from datetime import datetime, timedelta
from typing import Any

import bcrypt as _bcrypt
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models.user import User
from app.models.subscription import Subscription
from app.models.wallet import Wallet


def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt(rounds=12)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def create_token(data: dict[str, Any], expires_delta: timedelta) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + expires_delta
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(data: dict[str, Any] | int) -> str:
    if isinstance(data, int):
        data = {"sub": str(data), "type": "access"}
    elif "type" not in data:
        data = {**data, "type": "access"}
    return create_token(data, timedelta(minutes=settings.access_token_expire_minutes))


def create_refresh_token(data: dict[str, Any] | int) -> str:
    if isinstance(data, int):
        data = {"sub": str(data), "type": "refresh"}
    elif "type" not in data:
        data = {**data, "type": "refresh"}
    return create_token(data, timedelta(days=settings.refresh_token_expire_days))


def create_email_verify_token(user_id: int) -> str:
    return create_token(
        {"sub": str(user_id), "type": "email_verify"},
        timedelta(hours=24),
    )


def decode_token(token: str, expected_type: str | None = None) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if expected_type and payload.get("type") != expected_type:
            return None
        return payload
    except JWTError:
        return None


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email.lower().strip())
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, email: str, password: str) -> User:
    user = User(
        email=email.lower().strip(),
        password_hash=hash_password(password),
    )
    db.add(user)
    await db.flush()

    # Create subscription record with free tier
    sub = Subscription(
        user_id=user.id,
        stripe_customer_id=f"cus_pending_{secrets.token_hex(8)}",
        tier="free",
        status="active",
    )
    db.add(sub)

    # Create wallet with 100 PC signup bonus
    wallet = Wallet(
        user_id=user.id,
        prediction_coins=100,
        real_credits_usd=0.0,
    )
    db.add(wallet)

    await db.flush()
    return user
