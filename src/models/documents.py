from datetime import date, datetime
from typing import Optional, Any, TYPE_CHECKING

from uuid import UUID, uuid7
from sqlmodel import SQLModel, Column, JSON, Field, Relationship

from src.enums.document_category import DocumentCategory
from src.enums.document_type import DocumentType

if TYPE_CHECKING:
    from src.models.source import Source
    from src.models.subject import Subject, DocumentSubjectLink
    from src.models.document_part import DocumentPart
    from src.models.document_relation import DocumentRelation

class Document(SQLModel, table=True):
    """The Master Registry"""
    __tablename__ = "documents"

    id: UUID = Field(default_factory=uuid7, primary_key=True)
    canonical_citation: str = Field(unique=True)    # e.g. "G.R. No. 12345", "Republic Act No. 1"

    title: str
    short_title: Optional[str]
    category: DocumentCategory
    doc_type: DocumentType

    date_promulgated: Optional[date] = Field(index=True)    # Signed/Decided
    date_published: Optional[date]                          # Gazette
    date_effectivity: Optional[date]                        # Law is active

    source_id: Optional[UUID] = Field(foreign_key="sources.id")
    source_url: str     # Specific deep link (e.g. "/judjuris/juri2024/jul2024/gr_242296_2024.html")

    source: Optional["Source"] = Relationship(back_populates="documents")

    # Flexible Metadata. Instead of creating tables for different types of
    # documents, we instead store their metadatas through a JSON field.
    # For example, RAs get {congress, bills} while cases get {division, votes}.
    metadata_fields: dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    created_at: Optional[datetime] = Field(default_factory=datetime.now)

    parts: list["DocumentPart"] = Relationship(back_populates="document")

    # It answers the "Who do I cite/amend?" question.
    relations_made: list["DocumentRelation"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "DocumentRelation.target_id==Document.id",
            "lazy": "select"
        }
    )

    # It answers the "Who cites/amends me?" question.
    relations_receive: list["DocumentRelation"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "DocumentRelation.target_id==Document.id",
            "lazy": "select"
        }
    )

    subjects: list["Subject"] = Relationship(
        back_populates="documents",
        link_model=DocumentSubjectLink
    )