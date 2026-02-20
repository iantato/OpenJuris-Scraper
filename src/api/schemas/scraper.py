from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from enums.document_type import DocumentType
from enums.source_name import SourceName
from enums.scraper_status import ScraperStatus


class ScrapeRequest(BaseModel):
    """Request to scrape a specific URL."""
    url: str
    doc_type: DocumentType
    source: SourceName = SourceName.LAWPHIL


class ScrapeJobResponse(BaseModel):
    """Response for scrape job status."""
    id: UUID
    url: str
    status: ScraperStatus
    document_id: Optional[UUID] = None
    error_message: Optional[str] = None
    retry_count: int = 0

    class Config:
        from_attributes = True


class BulkScrapeRequest(BaseModel):
    """Request to scrape multiple document types."""
    source: SourceName = SourceName.LAWPHIL
    document_types: list[DocumentType]


class CrawlRequest(BaseModel):
    """Request to crawl and scrape all documents of certain types from a source."""
    source: SourceName
    document_types: list[DocumentType]


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