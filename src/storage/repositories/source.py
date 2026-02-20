from typing import Optional

from sqlmodel import select
from sqlalchemy.ext.asyncio.session import AsyncSession

from storage.repositories.base import BaseRepository
from models.source import Source
from enums.source_name import SourceName


class SourceRepository(BaseRepository[Source]):
    """Repository for Source operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Source)

    async def get_by_name(self, name: SourceName) -> Optional[Source]:
        """Get source by name."""
        statement = select(Source).where(Source.name == name)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_or_create(
        self, name: SourceName, short_code: str, base_url: str, source_type: str
    ) -> Source:
        """Get existing source or create new one."""
        existing = await self.get_by_name(name)
        if existing:
            return existing

        source = Source(
            name=name,
            short_code=short_code,
            base_url=base_url,
            type=source_type
        )
        return await self.create(source)