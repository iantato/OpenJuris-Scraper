from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio.session import AsyncSession

from config import Settings

from storage.database import Database
from storage.repositories.document import DocumentRepository
from storage.repositories.source import SourceRepository
from storage.repositories.scrape_job import ScrapeJobRepository

from embedder.factory import get_embedder
from embedder.embedder import EmbeddingService

# Global instances
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


async def get_source_repository(
    session: AsyncSession = Depends(get_session),
) -> SourceRepository:
    """Get source repository."""
    return SourceRepository(session)


async def get_scrape_job_repository(
    session: AsyncSession = Depends(get_session),
) -> ScrapeJobRepository:
    """Get scrape job repository."""
    return ScrapeJobRepository(session)

async def get_embedding_service(
    settings: Settings = Depends(get_settings),
) -> EmbeddingService:
    """Get embedding service."""
    embedder = get_embedder(settings)
    return EmbeddingService(embedder, settings)