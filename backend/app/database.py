from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event
from app.config import settings

_is_sqlite = settings.database_url.startswith("sqlite")

_engine_kwargs: dict = {"echo": False}
if _is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_async_engine(settings.database_url, **_engine_kwargs)


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
    from app.models import user, subscription, card, product, price, watchlist, portfolio, notification  # noqa
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
