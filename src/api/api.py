from contextlib import asynccontextmanager

from loguru import logger
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from config import Settings

from storage.database import Database
from storage.seed import seed_all
from embedder.factory import get_embedder

from api.dependencies import verify_internal_api_key

# Import models to register with SQLModel
from models.source import Source                        # noqa: F401
from models.subject import Subject                      # noqa: F401
from models.document import Document                    # noqa: F401
from models.scrape_job import ScrapeJob                 # noqa: F401
from models.vector import DocumentVector                # noqa: F401
from models.document_part import DocumentPart           # noqa: F401
from models.subject_link import DocumentSubjectLink     # noqa: F401
from models.document_relation import DocumentRelation   # noqa: F401
from models.document_flags import DocumentFlags         # noqa: F401
from models.statistics import Statistics                # noqa: F401

from models.vector import configure_embedding_dimension

from api.middleware.rate_limit import RateLimitMiddleware

from api.routers import (
    statistics_router,
    documents_router,
    vector_router,
    document_flags_router,
    scraper_router,
    embedding_router,
    public_router,
    export_router
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info("Starting OpenJuris API...")

    settings = Settings()
    db = Database(settings)

    # Initialize embedder to get the Embedder's dimensions
    embedder = get_embedder(settings)
    dim = embedder.dimensions
    logger.info(f"Embedding dimensions: {dim}")
    configure_embedding_dimension(dim)

    await db.create_tables()

    # Initialize some data to the database.
    await seed_all(db)

    app.state.settings = settings
    app.state.database = db
    app.state.embedder = embedder

    logger.info("Database initialized")

    yield

    await db.close()
    logger.info("OpenJuris API shutdown complete.")

def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = Settings()

    app = FastAPI(
        title=settings.app_name,
        description="API for Philippine Legal Documents Archive",
        version="0.1.0",
        lifespan=lifespan
    )

    if settings.is_production:
        app.add_middleware(
            RateLimitMiddleware,
            requests_per_minute=100,
            requests_per_hour=50000
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(documents_router, prefix="/api/v1", dependencies=[Depends(verify_internal_api_key)])
    app.include_router(statistics_router, prefix="/api/v1", dependencies=[Depends(verify_internal_api_key)])
    app.include_router(vector_router, prefix="/api/v1", dependencies=[Depends(verify_internal_api_key)])
    app.include_router(document_flags_router, prefix="/api/v1", dependencies=[Depends(verify_internal_api_key)])
    app.include_router(embedding_router, prefix="/api/v1", dependencies=[Depends(verify_internal_api_key)])
    app.include_router(scraper_router, prefix="/api/v1", dependencies=[Depends(verify_internal_api_key)])
    app.include_router(export_router, prefix="/api/v1", dependencies=[Depends(verify_internal_api_key)])

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "name": settings.app_name,
            "version": "0.1.0",
            "docs": "/docs"
        }

    # Public API Endpoint for public users.
    public_app = FastAPI(root_path="/api/public")

    public_app.add_middleware(
        CORSMiddleware,
        allow_origins=getattr(settings, "public_cors_origins", ["*"]),
        allow_credentials=True,
        allow_methods=["GET", "OPTIONS"],
        allow_headers=["*"]
    )

    if settings.is_production:
        public_app.add_middleware(
            RateLimitMiddleware,
            requests_per_minute=60,
            requests_per_hour=1000
        )

    public_app.include_router(public_router, prefix="/api/public")

    app.mount("/api/public", public_app)

    return app

app = create_app()