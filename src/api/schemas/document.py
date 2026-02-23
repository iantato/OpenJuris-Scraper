from uuid import UUID
from datetime import date
from typing import Optional, Any

from pydantic import BaseModel

from enums.document_type import DocumentType
from enums.document_category import DocumentCategory

class DocumentBase(BaseModel):
    title: str
    short_title: Optional[str] = None
    canonical_citation: str

    category: DocumentCategory
    doc_type: DocumentType

    source_url: str

    date_promulgated: Optional[date] = None
    date_published: Optional[date] = None
    date_effectivity: Optional[date] = None

class DocumentResponse(DocumentBase):
    id: UUID
    metadata_fields: dict[str, Any] = {}

    model_config = {"from_attributes": True}

class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
    limit: int
    offset: int

class DocumentViewResponse(DocumentResponse):
    content_markdown: str