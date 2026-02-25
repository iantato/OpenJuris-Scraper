from typing import AsyncGenerator

from loguru import logger
from fastapi import Depends, Request, HTTPException, Header
from sqlalchemy.ext.asyncio.session import AsyncSession

from config import Settings

from storage.database import Database
from storage.repositories.document import DocumentRepository
from storage.repositories.vector import VectorRepository
from storage.repositories.statistics import StatisticsRepository

from embedder.providers.base import BaseEmbedder

from services.scraper import ScraperService
from services.embed import EmbedService

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


def _get_embedder_from_request(request: Request) -> BaseEmbedder:
    """Extract embedder from app state."""
    return request.app.state.embedder


def _get_db_from_request(request: Request) -> Database:
    """Extract database from app state."""
    return request.app.state.database


async def get_embed_service(
    session: AsyncSession = Depends(get_session),
    request: Request = None,
    settings: Settings = Depends(get_settings),
) -> EmbedService:
    """Get embedding service."""
    embedder = _get_embedder_from_request(request)
    return EmbedService(
        session=session,
        embedder=embedder,
        settings=settings,
    )


async def get_scraper_service(
    session: AsyncSession = Depends(get_session),
    request: Request = None,
    settings: Settings = Depends(get_settings),
) -> ScraperService:
    """Get scraper service."""
    embedder = _get_embedder_from_request(request)
    return ScraperService(
        session=session,
        settings=settings,
        embedder=embedder,
    )

async def verify_internal_api_key(x_api_key: str = Header(..., description="Internal API Key")):
    """Verify internal API key for /api/v1 endpoints."""
    settings = Settings()
    internal_key = getattr(settings, "internal_api_key", None)

    if not internal_key:
        logger.error("Internal API key not configured in settings")
        raise HTTPException(status_code=500, detail="Server misconfiguration")

    if x_api_key != internal_key:
        logger.warning(f"Invalid API key attempt: {x_api_key[:10]}...")
        raise HTTPException(status_code=401, detail="Invalid API key")

    return True