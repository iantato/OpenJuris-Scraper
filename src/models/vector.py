from typing import Optional, List
from uuid import UUID

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text
from uuid6 import uuid7

from models.types.vector import VectorType

# Default dimension, will be overridden at startup
_DEFAULT_EMBEDDING_DIM = 384


def _make_embedding_column(dim: int = _DEFAULT_EMBEDDING_DIM) -> Column:
    return Column(VectorType(dim=dim), nullable=True)


class DocumentVector(SQLModel, table=True):
    """Vector embeddings for document chunks."""
    __tablename__ = "document_vectors"

    id: UUID = Field(default_factory=uuid7, primary_key=True)
    document_id: UUID = Field(foreign_key="documents.id", index=True)
    chunk_index: int = Field(default=0)
    content: str = Field(sa_column=Column(Text))
    section_title: Optional[str] = Field(default=None)

    embedding: Optional[List[float]] = Field(
        default=None,
        sa_column=_make_embedding_column(_DEFAULT_EMBEDDING_DIM),
    )

    class Config:
        arbitrary_types_allowed = True


def configure_embedding_dimension(dim: int) -> None:
    """
    Reconfigure the embedding column dimension before table creation.
    Must be called before Database.create_tables().
    """
    table = DocumentVector.__table__
    table.c.embedding.type = VectorType(dim=dim)