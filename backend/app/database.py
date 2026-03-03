from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event, text
from app.config import settings

_db_url = settings.database_url
# Railway provides postgres:// or postgresql:// — SQLAlchemy async needs postgresql+asyncpg://
if _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif _db_url.startswith("postgresql://"):
    _db_url = _db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

_is_sqlite = _db_url.startswith("sqlite")

_engine_kwargs: dict = {"echo": False}
if _is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_async_engine(_db_url, **_engine_kwargs)


if _is_sqlite:
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragmas(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()


AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def create_tables():
    from app.models import user, subscription, card, product, price, watchlist, portfolio, notification, shipping, message  # noqa
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def migrate_schema():
    """Add new columns to existing tables without losing data."""
    async with engine.begin() as conn:
        if not _is_sqlite:
            await conn.execute(text("ALTER TABLE cards ADD COLUMN IF NOT EXISTS set_release_date DATE"))
            await conn.execute(text("ALTER TABLE listings ADD COLUMN IF NOT EXISTS image_url VARCHAR(500)"))
        else:
            rows = await conn.execute(text("PRAGMA table_info(cards)"))
            cols = [r[1] for r in rows.fetchall()]
            if "set_release_date" not in cols:
                await conn.execute(text("ALTER TABLE cards ADD COLUMN set_release_date DATE"))
            rows = await conn.execute(text("PRAGMA table_info(listings)"))
            cols = [r[1] for r in rows.fetchall()]
            if "image_url" not in cols:
                await conn.execute(text("ALTER TABLE listings ADD COLUMN image_url VARCHAR(500)"))
