from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator

from loguru import logger
from sqlmodel import SQLModel
from sqlalchemy.pool import StaticPool, AsyncAdaptedQueuePool
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession

from exceptions import DatabaseException

from config import Settings


class Database:

    def __init__(self, settings: Settings, echo: Optional[bool] = False):
        if settings.is_production:
            self.engine = create_async_engine(
                f"{settings.database_url}?secure=true",
                connect_args={
                    "auth_token": settings.turso_auth_token
                },
                echo=echo,
                poolclass=AsyncAdaptedQueuePool
            )
        else:
            self.engine = create_async_engine(
                settings.database_url,
                echo=echo,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )

    async def create_tables(self) -> None:
        """
        Create all tables defined by SQLModel metadata.
        The VectorType handles F32_BLOB column creation automatically.
        """
        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("All tables created successfully")

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Provides an asynchronous session as a context manager."""
        async with AsyncSession(self.engine, expire_on_commit=False) as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise DatabaseException(f"An error occurred in the database: {e}")

    async def close(self):
        """Dispose of the engine connection pool."""
        await self.engine.dispose()