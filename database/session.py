import os
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from database.models import Base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./omniforge.db")
if DATABASE_URL.startswith("sqlite+aiosqlite:///"):
    DATABASE_URL = DATABASE_URL.replace("sqlite+aiosqlite:///", "sqlite:///")

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

sync_session_factory = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)


async def init_db():
    def _create_all():
        Base.metadata.create_all(engine)
    await asyncio.to_thread(_create_all)


class AsyncSessionWrapper:
    """Provides async-compatible interface for standard SQLAlchemy session."""

    def __init__(self, sync_session: Session):
        self.session = sync_session

    async def execute(self, stmt):
        return await asyncio.to_thread(self.session.execute, stmt)

    async def commit(self):
        return await asyncio.to_thread(self.session.commit)

    async def rollback(self):
        return await asyncio.to_thread(self.session.rollback)

    async def close(self):
        return await asyncio.to_thread(self.session.close)

    def add(self, obj):
        self.session.add(obj)


@asynccontextmanager
async def async_session_factory():
    sync_session = sync_session_factory()
    wrapped = AsyncSessionWrapper(sync_session)
    try:
        yield wrapped
    finally:
        await wrapped.close()


async def get_db_session():
    async with async_session_factory() as session:
        yield session
