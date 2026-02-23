from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from api.dependencies import get_embed_service, get_document_repository

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
    DocumentVectorsResponse,
    DocumentVectorInfo,
)

from services.embed import EmbedService
from storage.repositories.document import DocumentRepository

router = APIRouter(prefix="/embeddings", tags=["Embeddings"])


@router.post("/text", response_model=EmbeddingResponse)
async def embed_text(
    request: EmbedTextRequest,
    service: EmbedService = Depends(get_embed_service),
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/texts", response_model=EmbeddingsResponse)
async def embed_texts(
    request: EmbedTextsRequest,
    service: EmbedService = Depends(get_embed_service),
):
    """Embed multiple text strings."""
    if not request.texts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No texts provided",
        )
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/document", response_model=DocumentEmbeddingResponse)
async def embed_document(
    request: EmbedDocumentRequest,
    service: EmbedService = Depends(get_embed_service),
    doc_repo: DocumentRepository = Depends(get_document_repository),
):
    """Embed a document by ID."""
    document = await doc_repo.get_by_id(request.document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Check for existing vectors
    existing = await service.get_document_vectors(request.document_id)
    if existing and not request.force:
        return DocumentEmbeddingResponse(
            document_id=request.document_id,
            chunks_created=len(existing),
            message="Document already embedded. Use force=true to re-embed.",
        )

    # Delete existing if force
    if existing and request.force:
        await service.delete_document_vectors(request.document_id)
        logger.info(f"Deleted {len(existing)} existing vectors for document {request.document_id}")

    content = document.content_markdown
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document has no content to embed",
        )

    try:
        vectors = await service.embed_document_by_id(
            document_id=request.document_id,
            content=content,
            force=True,  # Already handled deletion above
        )
        await service.session.commit()

        return DocumentEmbeddingResponse(
            document_id=request.document_id,
            chunks_created=len(vectors),
            message=f"Successfully created {len(vectors)} embeddings",
        )
    except Exception as e:
        logger.error(f"Failed to embed document {request.document_id}: {e}")
        await service.session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/search", response_model=SearchResponse)
async def search_similar(
    request: SearchRequest,
    service: EmbedService = Depends(get_embed_service),
):
    """Search for similar document chunks."""
    try:
        results = await service.search_similar(
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/document/{document_id}/vectors", response_model=DocumentVectorsResponse)
async def get_document_vectors(
    document_id: UUID,
    service: EmbedService = Depends(get_embed_service),
):
    """Get all vectors for a document."""
    vectors = await service.get_document_vectors(document_id)
    return DocumentVectorsResponse(
        document_id=document_id,
        count=len(vectors),
        chunks=[
            DocumentVectorInfo(
                id=str(v.id),
                chunk_index=v.chunk_index,
                content_preview=v.content[:200] + "..." if len(v.content) > 200 else v.content,
                section_title=v.section_title,
            )
            for v in vectors
        ],
    )


@router.delete("/document/{document_id}")
async def delete_document_vectors(
    document_id: UUID,
    service: EmbedService = Depends(get_embed_service),
):
    """Delete all vectors for a document."""
    count = await service.delete_document_vectors(document_id)
    await service.session.commit()
    return {
        "document_id": document_id,
        "deleted_count": count,
        "message": f"Deleted {count} vectors",
    }