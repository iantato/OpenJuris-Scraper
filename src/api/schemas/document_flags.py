from uuid import UUID

from pydantic import BaseModel

from enums.issue_type import IssueType

class DocumentFlagsResponse(BaseModel):
    id: UUID
    document_id: UUID
    issue_type: IssueType
    description: str

    class Config:
        from_attributes = True

class DocumentFlagsCreate(BaseModel):
    document_id: UUID
    issue_type: IssueType
    description: str