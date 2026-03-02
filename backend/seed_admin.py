"""
Create a demo Enterprise account for local testing.

Run from the backend/ directory:
    python seed_admin.py

Credentials:
    Email:    demo@pokemarket.app
    Password: Demo1234!
"""
import asyncio
import secrets
import sys
from datetime import datetime, timezone, timedelta

import bcrypt as _bcrypt
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

DATABASE_URL = "sqlite+aiosqlite:///./data/prices.db"

engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt(rounds=12)).decode()

EMAIL = "demo@pokemarket.app"
PASSWORD = "Demo1234!"


async def main():
    # Import models so SQLAlchemy knows about all tables
    from app.models import user, subscription, wallet  # noqa: F401
    from app.models.user import User
    from app.models.subscription import Subscription
    from app.models.wallet import Wallet, KycVerification
    from app.database import Base

    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        # Check if user already exists
        result = await db.execute(select(User).where(User.email == EMAIL))
        existing = result.scalar_one_or_none()
        if existing:
            print(f"User {EMAIL} already exists (id={existing.id}). Updating tier to enterprise...")
            # Just upgrade the subscription
            sub_res = await db.execute(select(Subscription).where(Subscription.user_id == existing.id))
            sub = sub_res.scalar_one_or_none()
            if sub:
                sub.tier = "enterprise"
                sub.status = "active"
                sub.current_period_end = datetime.now(timezone.utc) + timedelta(days=365)

            wallet_res = await db.execute(select(Wallet).where(Wallet.user_id == existing.id))
            w = wallet_res.scalar_one_or_none()
            if w:
                w.prediction_coins = 10_000
                w.real_credits_usd = 500.0

            # Ensure KYC verified
            kyc_res = await db.execute(select(KycVerification).where(KycVerification.user_id == existing.id))
            kyc = kyc_res.scalar_one_or_none()
            if not kyc:
                db.add(KycVerification(
                    user_id=existing.id,
                    stripe_identity_session=f"idvs_demo_{secrets.token_hex(8)}",
                    status="verified",
                    verified_at=datetime.now(timezone.utc),
                ))
            else:
                kyc.status = "verified"
                kyc.verified_at = datetime.now(timezone.utc)

            await db.commit()
            print("Done — account upgraded.")
            return

        # Create new user
        user_obj = User(
            email=EMAIL,
            password_hash=hash_password(PASSWORD),
            email_verified=True,
            is_active=True,
        )
        db.add(user_obj)
        await db.flush()

        # Enterprise subscription
        sub = Subscription(
            user_id=user_obj.id,
            stripe_customer_id=f"cus_demo_{secrets.token_hex(8)}",
            stripe_subscription_id=f"sub_demo_{secrets.token_hex(8)}",
            tier="enterprise",
            status="active",
            current_period_end=datetime.now(timezone.utc) + timedelta(days=365),
        )
        db.add(sub)

        # Wallet with generous balances
        w = Wallet(
            user_id=user_obj.id,
            prediction_coins=10_000,
            real_credits_usd=500.0,
        )
        db.add(w)

        # KYC verified (required for real-money markets)
        kyc = KycVerification(
            user_id=user_obj.id,
            stripe_identity_session=f"idvs_demo_{secrets.token_hex(8)}",
            status="verified",
            verified_at=datetime.now(timezone.utc),
        )
        db.add(kyc)

        await db.commit()
        print(f"Enterprise demo account created!")
        print(f"  Email:    {EMAIL}")
        print(f"  Password: {PASSWORD}")
        print(f"  Tier:     enterprise")
        print(f"  Wallet:   10,000 PC + $500.00 USD")


if __name__ == "__main__":
    asyncio.run(main())
