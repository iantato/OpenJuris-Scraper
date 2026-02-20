from typing import Optional, Sequence

from sqlmodel import select
from sqlalchemy.ext.asyncio.session import AsyncSession

from storage.repositories.base import BaseRepository
from models.scrape_job import ScrapeJob
from enums.scraper_status import ScraperStatus


class ScrapeJobRepository(BaseRepository[ScrapeJob]):
    """Repository for ScrapeJob operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ScrapeJob)

    async def get_by_url(self, url: str) -> Optional[ScrapeJob]:
        """Get scrape job by URL."""
        statement = select(ScrapeJob).where(ScrapeJob.url == url)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_pending_jobs(self, limit: int = 100) -> Sequence[ScrapeJob]:
        """Get all pending scrape jobs."""
        statement = (
            select(ScrapeJob)
            .where(ScrapeJob.status == ScraperStatus.PENDING)
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_failed_jobs(self, limit: int = 100) -> Sequence[ScrapeJob]:
        """Get all failed scrape jobs for retry."""
        statement = (
            select(ScrapeJob)
            .where(ScrapeJob.status == ScraperStatus.FAILED)
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def mark_completed(self, job: ScrapeJob, document_id: Optional[str] = None) -> ScrapeJob:
        """Mark job as completed."""
        job.status = ScraperStatus.COMPLETED
        job.document_id = document_id
        return await self.update(job)

    async def mark_failed(self, job: ScrapeJob, error_message: str) -> ScrapeJob:
        """Mark job as failed."""
        job.status = ScraperStatus.FAILED
        job.error_message = error_message
        job.retry_count += 1
        return await self.update(job)