from uuid import UUID
from typing import Optional

from loguru import logger
from fastapi import APIRouter, HTTPException, Query, Depends

from api.dependencies import get_document_repository
from storage.repositories.document import DocumentRepository

from enums.document_type import DocumentType
from enums.document_category import DocumentCategory

from api.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
    DocumentViewResponse
)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    doc_type: Optional[DocumentType] = None,
    category: Optional[DocumentCategory] = None,
    repo: DocumentRepository = Depends(get_document_repository)
):
    """List documents with optional filtering."""
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


@router.get("/{document_id}", response_model=DocumentViewResponse)
async def get_document(
    document_id: UUID,
    repo: DocumentRepository = Depends(get_document_repository),
):
    """Get a specific document by ID."""
    document = await repo.get_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse.model_validate(document)


@router.get("/citation/{citation}", response_model=DocumentResponse)
async def get_document_by_citation(
    citation: str,
    repo: DocumentRepository = Depends(get_document_repository),
):
    """Get the first document by its canonical citation (returns one if multiple exist)."""
    document = await repo.get_by_citation(citation)
    if not document:
        raise HTTPException(
            status_code=404,
            detail=f"Document with citation '{citation}' not found"
        )
    return DocumentResponse.model_validate(document)


@router.get("/search/", response_model=DocumentListResponse)
async def search_documents(
    q: str = Query(..., min_length=2),
    limit: int = Query(default=20, le=100),
    repo: DocumentRepository = Depends(get_document_repository),
):
    """Search documents by title."""
    items = await repo.search_by_title(q, limit=limit)
    return DocumentListResponse(
        items=[DocumentResponse.model_validate(doc) for doc in items],
        total=len(items),
        limit=limit,
        offset=0,
    )


@router.get("/sorted/", response_model=DocumentListResponse)
async def get_sorted_documents(
    sort_field: str = Query(default="title"),
    ascending: bool = Query(default=True),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    repo: DocumentRepository = Depends(get_document_repository),
):
    """Get documents sorted by a specified field."""
    items = await repo.get_sorted(sort_field=sort_field, ascending=ascending, limit=limit, offset=offset)
    return DocumentListResponse(
        items=[DocumentResponse.model_validate(doc) for doc in items],
        total=len(items),
        limit=limit,
        offset=offset
    )


@router.get("/sorted/date/", response_model=DocumentListResponse)
async def get_sorted_documents_by_date(
    ascending: bool = Query(default=True),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    repo: DocumentRepository = Depends(get_document_repository),
):
    """Get documents sorted by date."""
    items = await repo.get_sorted_by_date(ascending=ascending, limit=limit, offset=offset)
    return DocumentListResponse(
        items=[DocumentResponse.model_validate(doc) for doc in items],
        total=len(items),
        limit=limit,
        offset=offset
    )


@router.get("/sorted/title/", response_model=DocumentListResponse)
async def get_sorted_documents_by_title(
    ascending: bool = Query(default=True),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    repo: DocumentRepository = Depends(get_document_repository),
):
    """Get documents sorted by title."""
    items = await repo.get_sorted_by_title(ascending=ascending, limit=limit, offset=offset)
    return DocumentListResponse(
        items=[DocumentResponse.model_validate(doc) for doc in items],
        total=len(items),
        limit=limit,
        offset=offset
    )