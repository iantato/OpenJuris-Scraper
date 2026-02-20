from uuid import UUID
from typing import Optional, TYPE_CHECKING
from datetime import datetime

from uuid6 import uuid7
from sqlmodel import SQLModel, Field, Relationship

from enums.relation_type import RelationType

if TYPE_CHECKING:
    from models.document import Document

class DocumentRelation(SQLModel, table=True):
    """The universal link between documents"""
    __tablename__ = "document_relations"

    id: UUID = Field(default_factory=uuid7, primary_key=True)

    source_id: UUID = Field(foreign_key="documents.id", index=True) # The "Actor" or new/current law
    target_id: UUID = Field(foreign_key="documents.id", index=True) # The "Target" or old/referenced law

    target_part_id: Optional[UUID] = Field(default=None, foreign_key="document_parts.id")

    relation_type: RelationType     # e.g. "Amends"
    target_scope: str               # e.g. "Section 5" (Human Readable backup)

    verbatim_text: Optional[str] = None    # e.g. "Is hereby amended to read..."

    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships back to Document
    source_document: Optional["Document"] = Relationship(
        back_populates="relations_made",
        sa_relationship_kwargs={
            "primaryjoin": "DocumentRelation.source_id==Document.id",
            "lazy": "select",
        }
    )

    target_document: Optional["Document"] = Relationship(
        back_populates="relations_received",
        sa_relationship_kwargs={
            "primaryjoin": "DocumentRelation.target_id==Document.id",
            "lazy": "select",
            "overlaps": "relations_made,source_document",
        }
    )