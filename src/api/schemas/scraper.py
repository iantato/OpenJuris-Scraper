from typing import Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel

from enums.document_type import DocumentType
from enums.source_name import SourceName
from enums.scraper_status import ScraperStatus


class ScrapeRequest(BaseModel):
    """Request to scrape a specific URL."""
    url: str
    doc_type: DocumentType
    source: SourceName = SourceName.LAWPHIL
    embed: bool = True


class ScrapeJobResponse(BaseModel):
    """Response for scrape job status."""
    id: UUID
    url: str
    status: ScraperStatus
    document_id: Optional[UUID] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CrawlRequest(BaseModel):
    """Request to crawl and scrape all documents of certain types from a source."""
    source: SourceName
    document_types: list[DocumentType]
    embed: bool = True


class CrawlResponse(BaseModel):
    """Response for crawl request."""
    job_id: UUID
    source: SourceName
    document_types: list[DocumentType]
    status: str


class ScrapeStatusResponse(BaseModel):
    """Overall scrape status."""
    pending: int
    in_progress: int
    completed: int
    failed: int


class ScrapeResultResponse(BaseModel):
    """Response after a synchronous scrape completes."""
    document_id: Optional[UUID] = None
    canonical_citation: Optional[str] = None
    url: str
    status: str
    error: Optional[str] = None


class SupportedDocumentTypesResponse(BaseModel):
    """Response listing supported document types for a source."""
    source: SourceName
    document_types: list[str]