from uuid import UUID
from typing import Optional, TYPE_CHECKING

from uuid6 import uuid7
from sqlmodel import SQLModel, Field, Relationship

from models.subject_link import DocumentSubjectLink

if TYPE_CHECKING:
    from models.document import Document

class Subject(SQLModel, table=True):
    """The taxonomy (e.g., 'Criminal Law', 'Taxation')"""
    __tablename__ = "subjects"

    id: UUID = Field(default_factory=uuid7, primary_key=True)
    name: str = Field(unique=True, index=True) # e.g. "Environmental Law"
    description: Optional[str] = None

    # Heirarchy support e.g. Criminal Law -> Crimes Against Property -> Theft
    parent_id: Optional[UUID] = Field(foreign_key="subjects.id", nullable=True)

    parent: Optional["Subject"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side": "Subject.id"}
    )

    children: list["Subject"] = Relationship(back_populates="parent")

    # Relationship to the Documents model.
    documents: list["Document"] = Relationship(
        back_populates="subjects",
        link_model=DocumentSubjectLink
    )