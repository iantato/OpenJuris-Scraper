from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator

from sqlmodel import SQLModel
from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession

from exceptions import DatabaseException

from config import Settings

class Database:

    def __init__(self, settings: Settings, echo: Optional[bool] = False):
        # Use the remote instance of Turso when production. Otherwise, just
        # use the normal local sqlite database to minimize request limits.
        if settings.is_production:
            self.engine = create_async_engine(
                settings.database_url,
                connect_args={
                    "auth_token": settings.turso_auth_token,
                    "secure": True
                },
                echo=echo,
                poolclass=AsyncAdaptedQueuePool
            )
        else:
            self.engine = create_async_engine(
                settings.database_url,
                echo=echo,
                poolclass=AsyncAdaptedQueuePool
            )

    async def create_tables(self) -> None:
        """
        Create all tables defined by SQLModel metadata. Make sure
        to import the models before creating the tables to add the
        model into the SQLModel metadata.
        """
        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Provides an asynchronous session as a context manager.
        """
        async with AsyncSession(self.engine, expire_on_commit=False) as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise DatabaseException(f"An error occured in the database: {e}")

    async def close(self):
        """
        Dispose of the engine connection pool.
        """
        await self.engine.dispose()