from api.routers.document import router as documents_router
from api.routers.statistics import router as statistics_router
from api.routers.vector import router as vector_router
from api.routers.document_flags import router as document_flags_router

__all__ = [
    "documents_router",
    "statistics_router",
    "vector_router",
    "document_flags_router"
]