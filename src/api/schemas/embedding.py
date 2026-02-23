from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class EmbedTextRequest(BaseModel):
    """Request to embed a single text."""
    text: str


class EmbedTextsRequest(BaseModel):
    """Request to embed multiple texts."""
    texts: list[str]


class EmbedDocumentRequest(BaseModel):
    """Request to embed a document by ID."""
    document_id: UUID
    force: bool = False


class EmbeddingResponse(BaseModel):
    """Response containing embedding vector."""
    embedding: list[float]
    dimension: int


class EmbeddingsResponse(BaseModel):
    """Response containing multiple embedding vectors."""
    embeddings: list[list[float]]
    count: int
    dimension: int


class DocumentEmbeddingResponse(BaseModel):
    """Response for document embedding operation."""
    document_id: UUID
    chunks_created: int
    message: str


class SimilarChunk(BaseModel):
    """A similar document chunk from search."""
    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    section_title: Optional[str]
    similarity: float


class SearchRequest(BaseModel):
    """Request to search for similar content."""
    query: str
    limit: int = 10
    threshold: float = 0.7
    document_id: Optional[UUID] = None


class SearchResponse(BaseModel):
    """Response containing similar chunks."""
    results: list[SimilarChunk]
    query: str
    count: int


class DocumentVectorInfo(BaseModel):
    """Summary info about a document's vector chunk."""
    id: str
    chunk_index: int
    content_preview: str
    section_title: Optional[str]


class DocumentVectorsResponse(BaseModel):
    """Response listing vectors for a document."""
    document_id: UUID
    count: int
    chunks: list[DocumentVectorInfo]