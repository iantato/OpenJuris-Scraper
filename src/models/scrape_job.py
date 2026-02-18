from uuid import UUID
from typing import Optional
from datetime import datetime

from uuid6 import uuid7
from sqlmodel import SQLModel, Field

from enums.scraper_status import ScraperStatus

class ScrapeJob(SQLModel, table=True):
    """Track scraping progress and avoid re-scraping"""
    __tablename__ = "scrape_jobs"

    id: UUID = Field(default_factory=uuid7, primary_key=True)
    source_id: UUID = Field(foreign_key="sources.id", index=True)

    url: str = Field(unique=True, index=True)   # The full URL of the website that is being
                                                # scraped.
    status: ScraperStatus = Field(default=ScraperStatus.PENDING)

    document_id: Optional[UUID] = Field(foreign_key="documents.id", nullable=True)

    error_message: Optional[str] = None
    retry_count: int = Field(default=0)

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)