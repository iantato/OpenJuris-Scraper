from uuid import UUID

from uuid6 import uuid7
from sqlmodel import SQLModel, Column, LargeBinary, Field

class DocumentVector(SQLModel, table=True):
    """Vector Embeddings for a specific DocumentPart"""
    __tablename__ = "document_vectors"

    id: UUID = Field(default_factory=uuid7, primary_key=True)
    part_id: UUID = Field(foreign_key="document_parts.id", index=True)

    embedding: bytes = Field(sa_column=Column(LargeBinary))