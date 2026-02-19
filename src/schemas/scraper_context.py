from uuid import UUID
from typing import Optional
from datetime import datetime
from dataclasses import dataclass, field

from uuid6 import uuid7

from enums.document_type import DocumentType

from storage.database import Database

from config.scraper import ScraperSettings

@dataclass
class ScraperContext:
    """Passes dependencies, configuration, and state through the pipeline."""

    # Dependencies
    db: Database
    settings: ScraperSettings

    job_id: UUID = field(default_factory=uuid7)

    start_time: datetime = field(default_factory=datetime.now)

    # If None, scrape EVERYTHING.
    target_document_types: Optional[list[DocumentType]] = None