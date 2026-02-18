from uuid import UUID
from typing import Optional

from sqlmodel import SQLModel, Field

class DocumentSubjectLink(SQLModel, table=True):
    """Many-to-Many table to link document to subject viceversa"""
    __tablename__ = "document_subjects"

    document_id: UUID = Field(foreign_key="documents.id", primary_key=True)
    subject_id: UUID = Field(foreign_key="subjects.id", primary_key=True)

    confidence: float = Field(default=1.0)              # If an AI tagged the subject, how sure is it?
                                                        # AI Confidence score (0.0 - 1.0)

    is_primary: Optional[bool] = Field(default=False)   # If the topic is the MAIN topic e.g. Criminal Law.