from uuid import UUID
from typing import Optional, TYPE_CHECKING

from uuid6 import uuid7
from sqlmodel import SQLModel, Field, Relationship

from enums.section_type import SectionType

if TYPE_CHECKING:
    from models.document import Document
    from models.document_part import DocumentPart

class DocumentPart(SQLModel, table=True):
    """Sections of the document"""
    __tablename__ = "document_parts"

    id: UUID = Field(default_factory=uuid7, primary_key=True)
    document_id: UUID = Field(foreign_key="documents.id", index=True)

    # For heirarchy or tree structures. A great example for this is
    # when we have multiple paragraphs for a Section in a Republic Act.
    # We would store all of those paragraph as a child of the original
    # section paragraph.
    parent_id: Optional[UUID] = Field(foreign_key="document_parts.id", nullable=True)

    section_type: SectionType                                   # e.g. "Section", "EnactingClause", "Ruling", etc.
    label: Optional[str] = Field(default=None, nullable=True)   # e.g. "Secton 1" or "Article III".

    content_text: str           # Plain text of the content.
    content_markdown: str       # Markdown version of the content.
    content_html: Optional[str] # Markdown to HTML conversion (sort of like a cache).

    sort_order: int

    document: "Document" = Relationship(back_populates="parts")

    # The parent relationship, e.g. the Article the Section belongs to.
    parent: Optional["DocumentPart"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side": "DocumentPart.id"}
    )

    # The children relationship, e.g. all the Sections inside an Article.
    children: list["DocumentPart"] = Relationship(back_populates="parent")