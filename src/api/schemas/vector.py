from uuid import UUID
from typing import Optional

from pydantic import BaseModel, Field

class VectorSearchResult(BaseModel):
    """Response model for vector similarity search results."""
    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    section_title: Optional[str] = None
    similarity: float = Field(..., ge=0.0, le=1.0)

    model_config = {"from_attributes": True}


class VectorResponse(BaseModel):
    """Response model for vector data."""
    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    section_title: Optional[str] = None

    model_config = {"from_attributes": True}