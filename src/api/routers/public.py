from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Query, Depends, HTTPException, status

from api.dependencies import get_document_repository, get_vector_repository
from storage.repositories.document import DocumentRepository
from storage.repositories.vector import VectorRepository

from enums.document_type import DocumentType
from enums.document_category import DocumentCategory

from api.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
    DocumentViewResponse
)
from api.schemas.vector import VectorSearchResult

router = APIRouter(prefix="/public", tags=["Public API"])

# Maximum limits for public API
MAX_PUBLIC_LIMIT = 50
DEFAULT_PUBLIC_LIMIT = 10


@router.get(
    "/",
    summary="Public API Information",
    description="Information about the public API endpoints and rate limits"
)
async def public_api_info():
    """Get information about the public API."""
    return {
        "name": "OpenJuris Public API",
        "version": "1.0",
        "description": "Read-only API for Philippine Legal Documents",
        "rate_limits": {
            "requests_per_minute": 60,
            "requests_per_hour": 1000
        },
        "query_limits": {
            "max_results_per_query": MAX_PUBLIC_LIMIT,
            "default_results": DEFAULT_PUBLIC_LIMIT
        },
        "endpoints": {
            "documents": "/api/public/documents",
            "document_by_id": "/api/public/documents/{id}",
            "document_by_citation": "/api/public/documents/citation/{citation}",
            "search_documents": "/api/public/documents/search",
            "vector_search": "/api/public/vectors/search"
        },
        "documentation": "/docs"
    }


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    limit: int = Query(default=DEFAULT_PUBLIC_LIMIT, le=MAX_PUBLIC_LIMIT, ge=1),
    offset: int = Query(default=0, ge=0),
    doc_type: Optional[DocumentType] = None,
    category: Optional[DocumentCategory] = None,
    repo: DocumentRepository = Depends(get_document_repository)
):
    """
    List documents with optional filtering.

    Rate Limits:
    - 60 requests per minute
    - 1000 requests per hour

    Query Limits:
    - Maximum 50 results per query
    - Default 10 results
    """
    items = None
    if doc_type:
        items = await repo.get_by_type(doc_type, limit=limit, offset=offset)
    elif category:
        items = await repo.get_by_category(category, limit=limit, offset=offset)
    else:
        items = await repo.get_all(limit=limit, offset=offset)

    return DocumentListResponse(
        items=[DocumentResponse.model_validate(doc) for doc in items],
        total=len(items),
        limit=limit,
        offset=offset
    )


@router.get("/documents/{document_id}", response_model=DocumentViewResponse)
async def get_document(
    document_id: UUID,
    repo: DocumentRepository = Depends(get_document_repository),
):
    """
    Get a specific document by ID.

    Returns the full document including content.
    """
    document = await repo.get_by_id(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    return DocumentViewResponse.model_validate(document)


@router.get("/documents/citation/{citation}", response_model=DocumentResponse)
async def get_document_by_citation(
    citation: str,
    repo: DocumentRepository = Depends(get_document_repository),
):
    """
    Get a document by its canonical citation.

    Example: R.A. No. 12313
    """
    document = await repo.get_by_citation(citation)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with citation '{citation}' not found"
        )
    return DocumentResponse.model_validate(document)


@router.get("/documents/search", response_model=DocumentListResponse)
async def search_documents(
    q: str = Query(..., min_length=2, description="Search query (minimum 2 characters)"),
    limit: int = Query(default=DEFAULT_PUBLIC_LIMIT, le=MAX_PUBLIC_LIMIT, ge=1),
    repo: DocumentRepository = Depends(get_document_repository),
):
    """
    Search documents by title.

    Maximum 50 results per query.
    """
    items = await repo.search_by_title(q, limit=limit)
    return DocumentListResponse(
        items=[DocumentResponse.model_validate(doc) for doc in items],
        total=len(items),
        limit=limit,
        offset=0,
    )


@router.get(
    "/vectors/search",
    response_model=list[VectorSearchResult],
    summary="Semantic search",
    description="Search for similar document chunks using AI-powered semantic similarity"
)
async def search_vectors(
    q: str = Query(..., alias="query", min_length=3, description="Search query text (minimum 3 characters)"),
    limit: int = Query(default=DEFAULT_PUBLIC_LIMIT, ge=1, le=MAX_PUBLIC_LIMIT, description="Maximum number of results"),
    threshold: float = Query(0.7, ge=0.0, le=1.0, description="Minimum similarity threshold (0.0-1.0)"),
    document_id: Optional[UUID] = Query(None, description="Filter by specific document ID"),
    repo: VectorRepository = Depends(get_vector_repository),
) -> list[VectorSearchResult]:
    """
    Search for similar document chunks using vector similarity.

    Returns chunks ordered by similarity score (highest first).
    Maximum 50 results per query.
    """
    try:
        results = await repo.search_similar(
            query=q,
            limit=limit,
            threshold=threshold,
            document_id=document_id
        )
        return results
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(exc)}"
        )