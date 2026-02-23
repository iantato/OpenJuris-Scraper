from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from models.statistics import Statistics
from storage.repositories.base import BaseRepository

class StatisticsRepository(BaseRepository[Statistics]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Statistics)

    async def get_by_name(self, name: str) -> Sequence[Statistics]:
        result = await self.session.execute(select(Statistics).where(Statistics.stat_name == name))
        return result.scalars().all()

    async def update(self, stat_id: UUID, stat: int) -> Optional[Statistics]:
        db_stat = await self.get_by_id(stat_id)
        if db_stat is None:
            return None
        db_stat.stat = stat
        self.session.add(db_stat)
        await self.session.commit()
        await self.session.refresh(db_stat)
        return db_stat