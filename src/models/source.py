from datetime import datetime
from typing import Optional, TYPE_CHECKING

from uuid import UUID, uuid7

from sqlmodel import SQLModel, Field, Relationship

from src.enums.source_type import SourceType

if TYPE_CHECKING:
    from src.models.documents import Document

class Source(SQLModel, table=True):
    """Registry of where we get data (e.g., Lawphil, SC Library)"""
    __tablename__ = "sources"

    id: UUID = Field(default_factory=uuid7, primary_key=True)
    name: str = Field(unique=True)              # e.g. "Supreme Court E-Library"
    short_code: str = Field(unique=True)        # e.g. "SC-ELIB"

    base_url: str       # e.g. "https://elibrary.judiciary.gov.ph"
    type: SourceType

    created_at: Optional[datetime] = Field(default_factory=datetime.now)    # Date when the source was added to the registry.
                                                                            # This is specifically to know when we started
                                                                            # scraping the certain website.

    documents: list["Document"] = Relationship(back_populates="source")