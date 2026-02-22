from uuid import UUID

from uuid6 import uuid7
from sqlmodel import SQLModel, Field

class Statistics(SQLModel, table=True):
    __tablename__ = "statistics"

    id: UUID = Field(default_factory=uuid7, primary_key=True)
    stat_name: str
    stat: int