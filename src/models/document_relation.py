from typing import Optional
from uuid import UUID, uuid7
from datetime import datetime

from sqlmodel import SQLModel, Field

from src.enums.relation_type import RelationType

class DocumentRelation(SQLModel, table=True):
    """The universal link between documents"""
    __tablename__ = "document_relations"

    id: UUID = Field(default_factory=uuid7, primary_key=True)

    source_id: UUID = Field(foreign_key="documents.id", index=True) # The "Actor" or new/current law
    target_id: UUID = Field(foreign_key="documents.id", index=True) # The "Target" or old/referenced law

    target_part_id: Optional[UUID] = Field(foreign_key="document_parts.id")

    relation_type: RelationType     # e.g. "Amends"
    target_scope: str               # e.g. "Section 5" (Human Readable backup)

    verbatim_text: Optional[str]    # e.g. "Is hereby amended to read..."

    created_at: datetime = Field(default_factory=datetime.now)