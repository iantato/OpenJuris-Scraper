from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Depends, status

from api.dependencies import get_vector_repository

from api.schemas.vector import (
    VectorResponse,
    VectorSearchResult
)

from storage.repositories.vector import VectorRepository

router = APIRouter(prefix="/vectors", tags=["vectors"])


@router.get(
    "/search",
    response_model=list[VectorSearchResult],
    summary="Search similar vectors",
    description="Search for similar document chunks using semantic similarity"
)
async def search_vectors(
    q: str = Query(..., alias="query", description="Search query text"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    threshold: float = Query(0.7, ge=0.0, le=1.0, description="Minimum similarity threshold"),
    document_id: Optional[UUID] = Query(None, description="Filter by specific document ID"),
    repo: VectorRepository = Depends(get_vector_repository),
) -> list[VectorSearchResult]:
    """
    Search for similar document chunks using vector similarity.

    Returns chunks ordered by similarity score (highest first).
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
            detail=f"Error searching vectors: {str(exc)}"
        )


@router.get(
    "/document/{document_id}",
    response_model=list[VectorResponse],
    summary="Get document vectors",
    description="Retrieve all vector chunks for a specific document"
)
async def get_vectors_by_document(
    document_id: UUID,
    repo: VectorRepository = Depends(get_vector_repository)
) -> list[VectorResponse]:
    """
    Get all vector embeddings for a specific document.

    Returns chunks ordered by chunk_index.
    """
    try:
        vectors = await repo.get_by_document(document_id)
        if not vectors:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No vectors found for document {document_id}"
            )
        return vectors
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving vectors: {str(exc)}"
        )