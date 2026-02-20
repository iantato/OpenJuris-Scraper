from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from loguru import logger
from uuid6 import uuid7

from api.schemas.scraper import (
    ScrapeRequest,
    ScrapeJobResponse,
    BulkScrapeRequest,
    CrawlRequest,
    CrawlResponse,
    ScrapeStatusResponse,
)
from api.dependencies import (
    get_settings,
    get_database,
    get_document_repository,
    get_scrape_job_repository,
    get_source_repository,
)
from config import Settings
from config.scraper import ScraperSettings
from storage.database import Database
from storage.repositories.document import DocumentRepository
from storage.repositories.scrape_job import ScrapeJobRepository
from storage.repositories.source import SourceRepository
from schemas.scraper_context import ScraperContext
from schemas.scraped_document import ScrapedDocument
from schemas.scraped_part import ScrapedPart
from scrapers.lawphil.scraper import LawphilScraper
from scrapers.sc_elibrary.scraper import SCELibraryScraper
from models.scrape_job import ScrapeJob
from models.document import Document
from models.document_part import DocumentPart
from enums.source_name import SourceName
from enums.scraper_status import ScraperStatus
from enums.document_type import DocumentType

from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/scraper", tags=["Scraper"])

def _get_scraper(source: SourceName, settings: ScraperSettings, ctx: ScraperContext):
    """Factory to get the appropriate scraper based on source."""
    if source == SourceName.LAWPHIL:
        return LawphilScraper(settings, ctx)
    elif source == SourceName.SC_ELIBRARY:
        return SCELibraryScraper(settings, ctx)
    else:
        raise ValueError(f"Unsupported source: {source}")


def _build_document_parts(
    scraped_parts: list[ScrapedPart],
    document_id: UUID,
    parent_id: Optional[UUID] = None,
) -> list[DocumentPart]:
    """
    Recursively convert ScrapedPart trees into flat list of DocumentPart models.
    """
    result: list[DocumentPart] = []

    for part in scraped_parts:
        doc_part = DocumentPart(
            document_id=document_id,
            parent_id=parent_id,
            section_type=part.section_type,
            label=part.label,
            content_text=part.content_text or "",
            content_markdown=part.content_markdown or "",
            content_html=part.content_html,
            sort_order=part.sort_order,
        )

        result.append(doc_part)

        # Recursively process children
        if part.children:
            children = _build_document_parts(
                part.children,
                document_id,
                parent_id=doc_part.id,
            )
            result.extend(children)

    return result


async def _save_document(
    session: AsyncSession,
    scraped_doc: ScrapedDocument,
    source_id: UUID,
) -> Document:
    """Save a ScrapedDocument as a Document with all its parts."""
    document = Document(
        canonical_citation=scraped_doc.canonical_citation,
        title=scraped_doc.title,
        short_title=scraped_doc.short_title,
        category=scraped_doc.category,
        doc_type=scraped_doc.doc_type,
        source_id=source_id,
        source_url=scraped_doc.source_url,
        date_promulgated=scraped_doc.date_promulgated,
        date_published=scraped_doc.date_published,
        date_effectivity=scraped_doc.date_effectivity,
        metadata_fields=scraped_doc.metadata_fields,
        content_markdown=scraped_doc.content_markdown,
    )

    session.add(document)
    await session.flush()  # Flush to get the document.id

    # Build and save all document parts
    if scraped_doc.parts:
        doc_parts = _build_document_parts(scraped_doc.parts, document.id)
        for part in doc_parts:
            session.add(part)

        logger.info(f"Created {len(doc_parts)} document parts for {scraped_doc.canonical_citation}")

    return document


async def _crawl_source_task(
    job_id: UUID,
    source: SourceName,
    document_types: list[DocumentType],
    scraper_settings: ScraperSettings,
    db: Database,
):
    """Background task to crawl a source for specific document types."""
    ctx = ScraperContext(
        db=db,
        settings=scraper_settings,
        job_id=job_id,
        target_document_types=document_types,
    )

    scraper = _get_scraper(source, scraper_settings, ctx)

    documents_scraped = 0
    errors = 0

    try:
        async for scraped_doc in scraper.run():
            async with db.session() as session:
                job_repo = ScrapeJobRepository(session)
                source_repo = SourceRepository(session)

                source_record = await source_repo.get_by_name(source)
                if not source_record:
                    logger.warning(f"Source {source} not found in database")
                    continue

                try:
                    doc_repo = DocumentRepository(session)
                    existing = await doc_repo.get_by_url(scraped_doc.source_url)
                    if existing:
                        logger.debug(f"Document already exists: {scraped_doc.source_url}")
                        continue

                    document = await _save_document(session, scraped_doc, source_record.id)

                    job = ScrapeJob(
                        source_id=source_record.id,
                        url=scraped_doc.source_url,
                        status=ScraperStatus.COMPLETED,
                        document_id=document.id,
                    )
                    await job_repo.create(job)

                    documents_scraped += 1
                    logger.info(f"Scraped: {scraped_doc.canonical_citation}")

                    await session.commit()

                except Exception as e:
                    logger.error(f"Failed to save document {scraped_doc.source_url}: {e}")
                    logger.exception(e)
                    errors += 1
                    await session.rollback()

    except Exception as e:
        logger.error(f"Crawl task failed: {e}")
        logger.exception(e)

    finally:
        await scraper.close()

    logger.info(f"Crawl completed. Documents: {documents_scraped}, Errors: {errors}")


async def _scrape_document_task(
    job_id: UUID,
    url: str,
    doc_type: DocumentType,
    source: SourceName,
    scraper_settings: ScraperSettings,
    db: Database,
):
    """Background task to scrape a single document."""
    logger.info(f"Starting scrape task for {url}")

    ctx = ScraperContext(
        db=db,
        settings=scraper_settings,
        target_document_types=[doc_type],
    )

    source_id: Optional[UUID] = None

    try:
        # Step 1: Update job to IN_PROGRESS and get source_id
        async with db.session() as session:
            job_repo = ScrapeJobRepository(session)
            source_repo = SourceRepository(session)

            job = await job_repo.get_by_id(job_id)
            if not job:
                logger.error(f"Job {job_id} not found!")
                return

            source_record = await source_repo.get_by_name(source)
            if not source_record:
                logger.error(f"Source {source} not found")
                await job_repo.mark_failed(job, f"Source {source} not found")
                await session.commit()
                return

            source_id = source_record.id

            job.status = ScraperStatus.IN_PROGRESS
            await job_repo.update(job)
            await session.commit()

        # Step 2: Scrape the document (outside transaction)
        scraper = _get_scraper(source, scraper_settings, ctx)

        await scraper.http_client.start()
        try:
            logger.info(f"Scraping document from {url}")
            scraped_doc = await scraper.scrape_document(url, doc_type)
        finally:
            await scraper.http_client.close()

        if not scraped_doc:
            logger.error(f"Failed to parse document from {url}")
            async with db.session() as session:
                job_repo = ScrapeJobRepository(session)
                job = await job_repo.get_by_id(job_id)
                if job:
                    await job_repo.mark_failed(job, "Failed to parse document")
                    await session.commit()
            return

        logger.info(f"Parsed document: {scraped_doc.canonical_citation}")

        # Step 3: Save document + parts in one transaction
        async with db.session() as session:
            doc_repo = DocumentRepository(session)
            job_repo = ScrapeJobRepository(session)

            existing = await doc_repo.get_by_url(scraped_doc.source_url)
            if existing:
                logger.info(f"Document already exists: {scraped_doc.source_url}")
                job = await job_repo.get_by_id(job_id)
                if job:
                    await job_repo.mark_completed(job, existing.id)
                    await session.commit()
                return

            document = await _save_document(session, scraped_doc, source_id)

            job = await job_repo.get_by_id(job_id)
            if job:
                await job_repo.mark_completed(job, document.id)

            await session.commit()
            logger.info(f"Successfully scraped and saved: {scraped_doc.canonical_citation}")

    except Exception as e:
        logger.error(f"Scrape task failed for {url}: {e}")
        logger.exception(e)

        try:
            async with db.session() as session:
                job_repo = ScrapeJobRepository(session)
                job = await job_repo.get_by_id(job_id)
                if job:
                    await job_repo.mark_failed(job, str(e))
                    await session.commit()
        except Exception as e2:
            logger.error(f"Failed to mark job as failed: {e2}")


@router.post("/crawl", response_model=CrawlResponse)
async def crawl_source(
    request: CrawlRequest,
    background_tasks: BackgroundTasks,
    db: Database = Depends(get_database),
):
    """Crawl a source for specific document types."""
    job_id = uuid7()
    scraper_settings = ScraperSettings()

    scraper = _get_scraper(request.source, scraper_settings, ScraperContext(
        db=db,
        settings=scraper_settings,
        target_document_types=request.document_types,
    ))

    available_types = set(scraper.urls.keys())
    requested_types = set(request.document_types)
    unsupported = requested_types - available_types

    if unsupported:
        raise HTTPException(
            status_code=400,
            detail=f"Source {request.source} does not support document types: {[t.value for t in unsupported]}"
        )

    background_tasks.add_task(
        _crawl_source_task,
        job_id,
        request.source,
        request.document_types,
        scraper_settings,
        db,
    )

    return CrawlResponse(
        job_id=job_id,
        source=request.source,
        document_types=request.document_types,
        status="crawling",
    )


@router.get("/sources/{source}/document-types")
async def get_supported_document_types(
    source: SourceName,
    db: Database = Depends(get_database),
):
    """Get the document types supported by a source."""
    scraper_settings = ScraperSettings()
    ctx = ScraperContext(
        db=db,
        settings=scraper_settings,
        target_document_types=None,
    )

    try:
        scraper = _get_scraper(source, scraper_settings, ctx)
        return {
            "source": source,
            "document_types": [dt.value for dt in scraper.urls.keys()],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/scrape", response_model=ScrapeJobResponse)
async def scrape_document(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: Database = Depends(get_database),
):
    """Queue a single document URL for scraping."""
    async with db.session() as session:
        job_repo = ScrapeJobRepository(session)
        source_repo = SourceRepository(session)

        existing = await job_repo.get_by_url(request.url)
        if existing:
            logger.info(f"Job already exists for URL: {request.url}")
            return ScrapeJobResponse.model_validate(existing)

        source_record = await source_repo.get_by_name(request.source)
        if not source_record:
            raise HTTPException(
                status_code=400,
                detail=f"Source {request.source} not found in database. Please seed the database first."
            )

        job_id = uuid7()
        job = ScrapeJob(
            id=job_id,
            source_id=source_record.id,
            url=request.url,
            status=ScraperStatus.PENDING,
        )
        job = await job_repo.create(job)
        await session.commit()

        logger.info(f"Created scrape job {job_id} for {request.url}")

    scraper_settings = ScraperSettings()
    background_tasks.add_task(
        _scrape_document_task,
        job_id,
        request.url,
        request.doc_type,
        request.source,
        scraper_settings,
        db,
    )

    return ScrapeJobResponse.model_validate(job)


@router.get("/jobs/{job_id}", response_model=ScrapeJobResponse)
async def get_scrape_job(
    job_id: UUID,
    db: Database = Depends(get_database),
):
    """Get status of a scrape job."""
    async with db.session() as session:
        job_repo = ScrapeJobRepository(session)
        job = await job_repo.get_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return ScrapeJobResponse.model_validate(job)


@router.get("/status", response_model=ScrapeStatusResponse)
async def get_scrape_status(
    db: Database = Depends(get_database),
):
    """Get overall scraping status."""
    async with db.session() as session:
        job_repo = ScrapeJobRepository(session)
        pending = await job_repo.get_pending_jobs(limit=10000)
        failed = await job_repo.get_failed_jobs(limit=10000)

        return ScrapeStatusResponse(
            pending=len(pending),
            in_progress=0,
            completed=0,
            failed=len(failed),
        )


@router.post("/retry-failed")
async def retry_failed_jobs(
    background_tasks: BackgroundTasks,
    source: Optional[SourceName] = None,
    limit: int = 10,
    db: Database = Depends(get_database),
):
    """Retry failed scrape jobs."""
    scraper_settings = ScraperSettings()
    queued = 0

    async with db.session() as session:
        job_repo = ScrapeJobRepository(session)
        failed_jobs = await job_repo.get_failed_jobs(limit=limit)

        for job in failed_jobs:
            job.status = ScraperStatus.PENDING
            job.retry_count += 1
            await job_repo.update(job)

            background_tasks.add_task(
                _scrape_document_task,
                job.id,
                job.url,
                DocumentType.REPUBLIC_ACT,
                source or SourceName.LAWPHIL,
                scraper_settings,
                db,
            )
            queued += 1

        await session.commit()

    return {"queued": queued}