import hashlib
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from app.database import get_db
from app.models.user import User
from app.models.subscription import ApiKey
from app.services.auth_service import decode_token, get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = await get_user_by_id(db, int(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if not token:
        return None
    try:
        return await get_current_user(token=token, db=db)
    except HTTPException:
        return None


async def get_user_from_api_key(api_key: str, db: AsyncSession) -> User | None:
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    result = await db.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))
    record = result.scalar_one_or_none()
    if not record:
        return None
    record.last_used_at = datetime.now(timezone.utc)
    user = await get_user_by_id(db, record.user_id)
    return user if user and user.is_active else None


async def get_current_user_or_apikey(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    from fastapi import Request
    if token:
        try:
            return await get_current_user(token=token, db=db)
        except HTTPException:
            pass
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
