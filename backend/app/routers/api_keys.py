import secrets
import hashlib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.middleware.tier_guard import require_tier
from app.models.user import User
from app.models.subscription import ApiKey

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.get("")
async def list_api_keys(
    current_user: User = Depends(require_tier("enterprise")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ApiKey).where(ApiKey.user_id == current_user.id)
    )
    keys = result.scalars().all()
    return [
        {
            "id": k.id,
            "prefix": k.prefix,
            "created_at": k.created_at.isoformat(),
            "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
        }
        for k in keys
    ]


@router.post("", status_code=201)
async def create_api_key(
    current_user: User = Depends(require_tier("enterprise")),
    db: AsyncSession = Depends(get_db),
):
    # Limit to 5 keys per user
    result = await db.execute(select(ApiKey).where(ApiKey.user_id == current_user.id))
    existing = result.scalars().all()
    if len(existing) >= 5:
        raise HTTPException(400, "Maximum 5 API keys allowed per account")

    raw_key = f"pk_{secrets.token_hex(32)}"
    prefix = raw_key[:12]
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    key = ApiKey(user_id=current_user.id, key_hash=key_hash, prefix=prefix)
    db.add(key)
    await db.commit()
    await db.refresh(key)

    # Return the raw key only once — it cannot be recovered later
    return {
        "id": key.id,
        "key": raw_key,
        "prefix": prefix,
        "message": "Store this key securely. It will not be shown again.",
    }


@router.delete("/{key_id}", status_code=204)
async def revoke_api_key(
    key_id: int,
    current_user: User = Depends(require_tier("enterprise")),
    db: AsyncSession = Depends(get_db),
):
    key = await db.get(ApiKey, key_id)
    if not key or key.user_id != current_user.id:
        raise HTTPException(404, "API key not found")
    await db.delete(key)
    await db.commit()
