from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy.ext.asyncio.session import AsyncSession

from api.schemas.embedding import (
    EmbedTextRequest,
    EmbedTextsRequest,
    EmbedDocumentRequest,
    EmbeddingResponse,
    EmbeddingsResponse,
    DocumentEmbeddingResponse,
    SearchRequest,
    SearchResponse,
    SimilarChunk,
)
from api.dependencies import get_session, get_settings
from config import Settings
from config.embedder import EmbedderSettings
from embedder.factory import get_embedder
from embedder.embedder import EmbeddingService
from storage.repositories.document import DocumentRepository
from storage.repositories.vector import VectorRepository

router = APIRouter(prefix="/embeddings", tags=["Embeddings"])


def get_embedding_service(settings: Settings = Depends(get_settings)) -> EmbeddingService:
    """Get embedding service with configured embedder."""
    embedder = get_embedder(settings)
    return EmbeddingService(embedder, settings)


@router.post("/text", response_model=EmbeddingResponse)
async def embed_text(
    request: EmbedTextRequest,
    service: EmbeddingService = Depends(get_embedding_service),
):
    """Embed a single text string."""
    try:
        embedding = await service.embed_text(request.text)
        return EmbeddingResponse(
            embedding=embedding,
            dimension=len(embedding),
        )
    except Exception as e:
        logger.error(f"Failed to embed text: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/texts", response_model=EmbeddingsResponse)
async def embed_texts(
    request: EmbedTextsRequest,
    service: EmbeddingService = Depends(get_embedding_service),
):
    """Embed multiple text strings."""
    if not request.texts:
        raise HTTPException(status_code=400, detail="No texts provided")

    try:
        embeddings = await service.embed_texts(request.texts)
        dimension = len(embeddings[0]) if embeddings else 0
        return EmbeddingsResponse(
            embeddings=embeddings,
            count=len(embeddings),
            dimension=dimension,
        )
    except Exception as e:
        logger.error(f"Failed to embed texts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/document", response_model=DocumentEmbeddingResponse)
async def embed_document(
    request: EmbedDocumentRequest,
    session: AsyncSession = Depends(get_session),
    service: EmbeddingService = Depends(get_embedding_service),
):
    """Embed a document by ID."""
    doc_repo = DocumentRepository(session)
    document = await doc_repo.get_by_id(request.document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Check if vectors already exist
    embedder = get_embedder(EmbedderSettings())
    vector_repo = VectorRepository(session, embedder)
    existing_vectors = await vector_repo.get_by_document(request.document_id)

    if existing_vectors and not request.force:
        return DocumentEmbeddingResponse(
            document_id=request.document_id,
            chunks_created=len(existing_vectors),
            message="Document already embedded. Use force=true to re-embed.",
        )

    # Delete existing vectors if forcing re-embed
    if existing_vectors and request.force:
        await vector_repo.delete_by_document(request.document_id)
        logger.info(f"Deleted {len(existing_vectors)} existing vectors for document {request.document_id}")

    # Get content to embed
    content = document.content_markdown
    if not content:
        raise HTTPException(
            status_code=400,
            detail="Document has no content to embed",
        )

    try:
        vectors = await service.embed_document_by_id(
            document_id=request.document_id,
            content=content,
            session=session,
        )

        await session.commit()

        return DocumentEmbeddingResponse(
            document_id=request.document_id,
            chunks_created=len(vectors),
            message=f"Successfully created {len(vectors)} embeddings",
        )
    except Exception as e:
        logger.error(f"Failed to embed document {request.document_id}: {e}")
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=SearchResponse)
async def search_similar(
    request: SearchRequest,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
):
    """Search for similar document chunks."""
    embedder = get_embedder(settings)
    vector_repo = VectorRepository(session, embedder)

    try:
        results = await vector_repo.search_similar(
            query=request.query,
            limit=request.limit,
            threshold=request.threshold,
            document_id=request.document_id,
        )

        return SearchResponse(
            results=[
                SimilarChunk(
                    id=r["id"],
                    document_id=r["document_id"],
                    chunk_index=r["chunk_index"],
                    content=r["content"],
                    section_title=r["section_title"],
                    similarity=r["similarity"],
                )
                for r in results
            ],
            query=request.query,
            count=len(results),
        )
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/document/{document_id}/vectors")
async def get_document_vectors(
    document_id: UUID,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
):
    """Get all vectors for a document."""
    embedder = get_embedder(settings)
    vector_repo = VectorRepository(session, embedder)

    vectors = await vector_repo.get_by_document(document_id)

    return {
        "document_id": document_id,
        "count": len(vectors),
        "chunks": [
            {
                "id": str(v.id),
                "chunk_index": v.chunk_index,
                "content": v.content[:200] + "..." if len(v.content) > 200 else v.content,
                "section_title": v.section_title,
            }
            for v in vectors
        ],
    }


@router.delete("/document/{document_id}")
async def delete_document_vectors(
    document_id: UUID,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
):
    """Delete all vectors for a document."""
    embedder = get_embedder(settings)
    vector_repo = VectorRepository(session, embedder)

    count = await vector_repo.delete_by_document(document_id)
    await session.commit()

    return {
        "document_id": document_id,
        "deleted_count": count,
        "message": f"Deleted {count} vectors",
    }