from uuid import UUID
from typing import Optional
from datetime import datetime
from dataclasses import dataclass, field

from uuid6 import uuid7
from sqlmodel import Session

from enums.document_type import DocumentType
from enums.source_name import SourceName

from config.scraper import ScraperSettings

@dataclass
class ScraperContext:
    """Passes dependencies, configuration, and state through the pipeline."""

    # Dependencies
    db: Session
    settings: ScraperSettings

    source: SourceName
    job_id: UUID = field(default_factory=uuid7)

    start_time: datetime = field(default_factory=datetime.now)

    # If None, scrape EVERYTHING.
    target_document_types: Optional[list[DocumentType]] = None

    # Date range filters. e.g., Only scrape documents from 2020 to 2024
    start_year: Optional[int]
    end_year: Optional[int]
