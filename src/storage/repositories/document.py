from typing import Optional, Sequence
from uuid import UUID

from sqlmodel import select
from sqlalchemy.ext.asyncio.session import AsyncSession

from storage.repositories.base import BaseRepository
from models.document import Document
from enums.document_type import DocumentType
from enums.document_category import DocumentCategory


class DocumentRepository(BaseRepository[Document]):
    """Repository for Document operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Document)

    async def get_by_citation(self, citation: str) -> Optional[Document]:
        """Get document by canonical citation."""
        statement = select(Document).where(Document.canonical_citation == citation)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_type(
        self, doc_type: DocumentType, limit: int = 100, offset: int = 0
    ) -> Sequence[Document]:
        """Get documents by type."""
        statement = (
            select(Document)
            .where(Document.doc_type == doc_type)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_by_category(
        self, category: DocumentCategory, limit: int = 100, offset: int = 0
    ) -> Sequence[Document]:
        """Get documents by category."""
        statement = (
            select(Document)
            .where(Document.category == category)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def search_by_title(
        self, query: str, limit: int = 100
    ) -> Sequence[Document]:
        """Search documents by title."""
        statement = (
            select(Document)
            .where(Document.title.ilike(f"%{query}%"))
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def exists_by_url(self, url: str) -> bool:
        """Check if document exists by source URL."""
        statement = select(Document.id).where(Document.source_url == url)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none() is not None

    async def get_by_url(self, url: str) -> Optional[Document]:
        """Get document by source URL."""
        statement = select(Document).where(Document.source_url == url)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()