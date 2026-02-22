from typing import Optional, Sequence

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

    async def get_sorted(
        self,
        sort_field: str = "title",
        ascending: bool = True,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[Document]:
        """Get documents sorted by a specified field."""
        order_by = getattr(Document, sort_field)
        if not ascending:
            order_by = order_by.desc()
        statement = (
            select(Document)
            .order_by(order_by)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_sorted_by_date(
        self,
        ascending: bool = True,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[Document]:
        """Get documents sorted by date field (assumes 'date' exists)."""
        order_by = Document.date.asc() if ascending else Document.date.desc()
        statement = (
            select(Document)
            .order_by(order_by)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_sorted_by_title(
        self,
        ascending: bool = True,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[Document]:
        """Get documents sorted by title."""
        order_by = Document.title.asc() if ascending else Document.title.desc()
        statement = (
            select(Document)
            .order_by(order_by)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()
