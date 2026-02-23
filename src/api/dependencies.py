from typing import AsyncGenerator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio.session import AsyncSession

from config import Settings

from storage.database import Database
from storage.repositories.document import DocumentRepository
from storage.repositories.vector import VectorRepository
from storage.repositories.statistics import StatisticsRepository

_settings: Settings | None = None
_database: Database | None = None

def get_settings() -> Settings:
    """Get application settings."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


async def get_database(settings: Settings = Depends(get_settings)) -> Database:
    """Get database instance."""
    global _database
    if _database is None:
        _database = Database(settings)
        await _database.create_tables()
    return _database


async def get_session(
    db: Database = Depends(get_database),
) -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with db.session() as session:
        yield session


async def get_document_repository(
    session: AsyncSession = Depends(get_session),
) -> DocumentRepository:
    """Get document repository."""
    return DocumentRepository(session)


async def get_vector_repository(
    session: AsyncSession = Depends(get_session),
    request: Request = None,
) -> VectorRepository:
    """
    Dependency: yields a VectorRepository using the session and app embedder.
    """
    if request is None:
        raise RuntimeError("Request object is required for get_vector_repository")
    embedder = request.app.state.embedder
    return VectorRepository(session, embedder)

async def get_statistics_repository(
    session: AsyncSession = Depends(get_session),
) -> StatisticsRepository:
    return StatisticsRepository(session)