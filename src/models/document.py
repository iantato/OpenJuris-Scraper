from uuid import UUID
from datetime import date, datetime
from typing import Optional, Any, TYPE_CHECKING

from uuid6 import uuid7
from pydantic import field_validator
from sqlmodel import SQLModel, Column, JSON, Field, Relationship, Text

from enums.document_category import DocumentCategory
from enums.document_type import DocumentType

from models.subject_link import DocumentSubjectLink

if TYPE_CHECKING:
    from models.source import Source
    from models.subject import Subject, DocumentSubjectLink
    from models.document_part import DocumentPart
    from models.document_relation import DocumentRelation

class Document(SQLModel, table=True):
    """The Master Registry"""
    __tablename__ = "documents"

    id: UUID = Field(default_factory=uuid7, primary_key=True)
    canonical_citation: str = Field(unique=True)    # e.g. "G.R. No. 12345", "Republic Act No. 1"

    title: str
    short_title: Optional[str] = None
    category: DocumentCategory
    doc_type: DocumentType

    date_promulgated: Optional[date] = Field(default=None, index=True)    # Signed/Decided
    date_published: Optional[date] = None                                  # Gazette
    date_effectivity: Optional[date] = None                                # Law is active

    source_id: Optional[UUID] = Field(default=None, foreign_key="sources.id")
    source_url: str     # Specific deep link

    source: Optional["Source"] = Relationship(back_populates="documents")

    # Full markdown representation of the entire document
    content_markdown: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))

    # Flexible Metadata
    metadata_fields: dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    created_at: Optional[datetime] = Field(default_factory=datetime.now)

    parts: list["DocumentPart"] = Relationship(back_populates="document")

    # "Who do I cite/amend?" — this document is the source (actor)
    relations_made: list["DocumentRelation"] = Relationship(
        back_populates="source_document",
        sa_relationship_kwargs={
            "primaryjoin": "Document.id==DocumentRelation.source_id",
            "lazy": "select",
        }
    )

    # "Who cites/amends me?" — this document is the target
    relations_received: list["DocumentRelation"] = Relationship(
        back_populates="target_document",
        sa_relationship_kwargs={
            "primaryjoin": "Document.id==DocumentRelation.target_id",
            "lazy": "select",
            "overlaps": "relations_made,source_document",
        }
    )

    subjects: list["Subject"] = Relationship(
        back_populates="documents",
        link_model=DocumentSubjectLink
    )

    @field_validator('date_promulgated', 'date_published', 'date_effectivity', mode='before')
    @classmethod
    def parse_date_fields(cls, value):
        """Convert string dates to date objects, allowing None."""
        if value is None or isinstance(value, date):
            return value
        if isinstance(value, str):
            from dateutil import parser
            try:
                parsed = parser.parse(value)
                return parsed.date()
            except (ValueError, TypeError):
                return None
        return None