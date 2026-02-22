from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from models.document_flags import DocumentFlags
from storage.repositories.base import BaseRepository

class DocumentFlagsRepository(BaseRepository[DocumentFlags]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, DocumentFlags)

    async def get_by_document(self, document_id: UUID) -> Sequence[DocumentFlags]:
        result = await self.session.execute(
            select(DocumentFlags).where(DocumentFlags.document_id == document_id)
        )
        return result.scalars().all()