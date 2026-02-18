from uuid import UUID, uuid7
from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from src.models.documents import Document

class Subject(SQLModel, table=True):
    """The taxonomy (e.g., 'Criminal Law', 'Taxation')"""
    __tablename__ = "subjects"

    id: UUID = Field(default_factory=uuid7, primary_key=True)
    name: str = Field(unique=True, index=True) # e.g. "Environmental Law"
    description: Optional[str]

    # Heirarchy support e.g. Criminal Law -> Crimes Against Property -> Theft
    parent_id: Optional[UUID] = Field(foreign_key="subjects.id", nullable=True)

    parent: Optional["Subject"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side", "Subject.id"}
    )

    children: list["Subject"] = Relationship(back_populates="parent")

    # Relationship to the Documents model.
    documents: list["Document"] = Relationship(
        back_populates="subjects",
        link_model="DocumentSubjectLink"
    )

class DocumentSubjectLink(SQLModel, table=True):
    """Many-to-Many table to link document to subject viceversa"""
    __tablename__ = "document_subjects"

    document_id: UUID = Field(foreign_key="documents.id", primary_key=True)
    subject_id: UUID = Field(foreign_key="subjects.id", primary_key=True)

    confidence: float = Field(default=1.0)              # If an AI tagged the subject, how sure is it?
                                                        # AI Confidence score (0.0 - 1.0)

    is_primary: Optional[bool] = Field(default=False)   # If the topic is the MAIN topic e.g. Criminal Law.