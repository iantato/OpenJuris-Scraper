from uuid import UUID

from pydantic import BaseModel

from enums.source_name import SourceName
from enums.source_type import SourceType

class SourceCreate(BaseModel):
    name: SourceName
    short_code: str
    base_url: str
    type: SourceType
    description: str | None = None

class SourceResponse(BaseModel):
    id: UUID
    name: SourceName
    short_code: str
    base_url: str
    type: SourceType
    description: str | None

    class Config:
        from_attributes = True