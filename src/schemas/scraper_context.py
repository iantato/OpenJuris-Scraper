from uuid import UUID
from typing import Optional
from datetime import datetime

from uuid6 import uuid7
from sqlmodel import Session
from pydantic import dataclasses, Field

from enums.document_type import DocumentType
from enums.source_name import SourceName

from config.scraper import ScraperSettings

@dataclasses.dataclass
class ScraperContext:
    """Passes dependencies, configuration, and state through the pipeline."""

    # Dependencies
    db: Session
    settings: ScraperSettings

    source: SourceName
    job_id: UUID = Field(default_factory=uuid7)

    # Runetime Configurations
    dry_run: bool = False   # If True, do not commit to DB

    # If None, scrape EVERYTHING.
    target_document_types: Optional[list[DocumentType]] = None

    # Date range filters. e.g., Only scrape documents from 2020 to 2024
    start_year: Optional[int]
    end_year: Optional[int]

    start_time: datetime = Field(default_factory=datetime.now)