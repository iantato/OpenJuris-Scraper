from uuid import UUID

from uuid6 import uuid7
from sqlmodel import SQLModel, Field

from enums.issue_type import IssueType

class DocumentFlags(SQLModel, table=True):
    __tablename__ = "document_flags"

    id: UUID = Field(default_factory=uuid7, primary_key=True)
    document_id: UUID = Field(foreign_key="documents.id")

    issue_type: IssueType
    description: str