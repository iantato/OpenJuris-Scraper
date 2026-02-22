from api.routers.document import router as documents_router
from api.routers.scraper import router as scraper_router
from api.routers.embedding import router as embedding_router

__all__ = ["documents_router", "scraper_router", "embedding_router"]