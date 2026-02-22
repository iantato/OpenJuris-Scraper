from uuid import UUID

from pydantic import BaseModel

class StatisticsResponse(BaseModel):
    id: UUID
    stat_name: str
    stat: int

    class Config:
        from_attributes = True

class StatisticsCreate(BaseModel):
    id: UUID
    stat_name: str
    stat: int

class StatisticsUpdate(BaseModel):
    stat: int