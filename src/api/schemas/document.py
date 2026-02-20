from datetime import date
from typing import Optional, Any
from uuid import UUID

from pydantic import BaseModel

from enums.document_type import DocumentType
from enums.document_category import DocumentCategory


class DocumentBase(BaseModel):
    canonical_citation: str
    title: str
    category: DocumentCategory
    doc_type: DocumentType
    source_url: str
    short_title: Optional[str] = None
    date_promulgated: Optional[date] = None
    date_published: Optional[date] = None
    date_effectivity: Optional[date] = None


class DocumentCreate(DocumentBase):
    metadata_fields: dict[str, Any] = {}


class DocumentResponse(DocumentBase):
    id: UUID
    metadata_fields: dict[str, Any] = {}

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
    limit: int
    offset: int