from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker
)
from .models import Base

engine = create_async_engine('sqlite+aiosqlite:///./lectures.db', echo=True)
async_session = async_sessionmaker(bind=engine, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@asynccontextmanager
async def get_db():
    async with async_session() as session:
        yield session
