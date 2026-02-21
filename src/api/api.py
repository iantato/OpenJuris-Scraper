from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from config import Settings
from config.embedder import EmbedderSettings

from storage.database import Database
from storage.seed import seed_all
from api.routers import documents_router, scraper_router, embedding_router

from embedder.factory import get_embedder

# Import models to register with SQLModel
from models.source import Source                        # noqa: F401
from models.subject import Subject                      # noqa: F401
from models.document import Document                    # noqa: F401
from models.scrape_job import ScrapeJob                 # noqa: F401
from models.vector import DocumentVector                # noqa: F401
from models.document_part import DocumentPart           # noqa: F401
from models.subject_link import DocumentSubjectLink     # noqa: F401
from models.document_relation import DocumentRelation   # noqa: F401

from models.vector import configure_embedding_dimension


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info("Starting OpenJuris API...")

    settings = Settings()
    db = Database(settings)

    embedder_settings = EmbedderSettings()
    embedder = get_embedder(embedder_settings)

    # Configure the vector column dimension BEFORE creating tables
    dim = embedder.dimensions
    logger.info(f"Embedding dimension: {dim}")
    configure_embedding_dimension(dim)

    await db.create_tables()

    # Seed initial data
    await seed_all(db)

    # Store in app state
    app.state.settings = settings
    app.state.database = db
    app.state.embedder_settings = embedder_settings
    app.state.embedder = embedder

    logger.info("Database initialized")

    yield

    # Cleanup
    await db.close()
    logger.info("OpenJuris API shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = Settings()

    app = FastAPI(
        title=settings.app_name,
        description="API for Philippine Legal Documents Archive",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(documents_router, prefix="/api/v1")
    app.include_router(scraper_router, prefix="/api/v1")
    app.include_router(embedding_router, prefix="/api/v1")

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "name": settings.app_name,
            "version": "0.1.0",
            "docs": "/docs",
        }

    return app


app = create_app()