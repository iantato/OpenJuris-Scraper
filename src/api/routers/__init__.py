from api.routers.document import router as documents_router
from api.routers.statistics import router as statistics_router
from api.routers.vector import router as vector_router
from api.routers.document_flags import router as document_flags_router
from api.routers.scraper import router as scraper_router
from api.routers.embedding import router as embedding_router
from api.routers.public import router as public_router
from api.routers.export import router as export_router

__all__ = [
    "documents_router",
    "statistics_router",
    "vector_router",
    "document_flags_router",
    "scraper_router",
    "embedding_router",
    "public_router",
    "export_router",
]