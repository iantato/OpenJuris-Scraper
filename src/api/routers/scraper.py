from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, status
from loguru import logger
from uuid6 import uuid7

from api.dependencies import (
    get_scraper_service,
)

from api.schemas.scraper import (
    ScrapeRequest,
    ScrapeJobResponse,
    CrawlRequest,
    CrawlResponse,
    ScrapeStatusResponse,
    SupportedDocumentTypesResponse,
)

from config import Settings
from config.scraper import ScraperSettings

from services.scraper import ScraperService

from schemas.scraper_context import ScraperContext

from storage.database import Database
from storage.repositories.scrape_job import ScrapeJobRepository
from storage.repositories.source import SourceRepository
from storage.repositories.document import DocumentRepository

from scrapers.lawphil.scraper import LawphilScraper
from scrapers.sc_elibrary.scraper import SCELibraryScraper

from embedder.providers.base import BaseEmbedder

from models.scrape_job import ScrapeJob

from enums.source_name import SourceName
from enums.document_type import DocumentType
from enums.scraper_status import ScraperStatus

router = APIRouter(prefix="/scraper", tags=["Scraper"])


# ---------------------------------------------------------------------------
# Background task helpers (run outside the request's session/transaction)
# ---------------------------------------------------------------------------

def _get_scraper(source: SourceName, settings: ScraperSettings, ctx: ScraperContext):
    """Factory to get the appropriate scraper based on source."""
    if source == SourceName.LAWPHIL:
        return LawphilScraper(settings, ctx)
    elif source == SourceName.SC_ELIBRARY:
        return SCELibraryScraper(settings, ctx)
    else:
        raise ValueError(f"Unsupported source: {source}")


async def _scrape_document_task(
    job_id: UUID,
    url: str,
    doc_type: DocumentType,
    source: SourceName,
    db: Database,
    embedder: Optional[BaseEmbedder],
    settings: Settings,
    embed_documents: bool = True,
):
    """Background task to scrape a single document."""
    logger.info(f"Starting scrape task for {url}")

    ctx = ScraperContext(
        db=db,
        settings=settings,
        target_document_types=[doc_type],
    )

    try:
        # Step 1: Mark job as in-progress, resolve source_id
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

        # Step 2: Scrape (outside transaction)
        scraper = _get_scraper(source, settings, ctx)
        await scraper.http_client.start()
        try:
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

        # Step 3: Save document + embed in one transaction
        async with db.session() as session:
            scraper_service = ScraperService(
                session=session,
                settings=settings,
                embedder=embedder if embed_documents else None,
            )
            job_repo = ScrapeJobRepository(session)
            doc_repo = DocumentRepository(session)

            # Check for existing
            existing = await doc_repo.get_by_url(scraped_doc.source_url)
            if existing:
                logger.info(f"Document already exists: {scraped_doc.source_url}")
                job = await job_repo.get_by_id(job_id)
                if job:
                    await job_repo.mark_completed(job, existing.id)
                    await session.commit()
                return

            document = await scraper_service.save_document(
                scraped_doc=scraped_doc,
                source_id=source_id,
                embed=embed_documents,
            )

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


async def _crawl_source_task(
    job_id: UUID,
    source: SourceName,
    document_types: list[DocumentType],
    db: Database,
    embedder: Optional[BaseEmbedder],
    settings: Settings,
    embed_documents: bool = True,
):
    """Background task to crawl a source for specific document types."""
    ctx = ScraperContext(
        db=db,
        settings=settings,
        job_id=job_id,
        target_document_types=document_types,
    )

    scraper = _get_scraper(source, settings, ctx)
    documents_scraped = 0
    errors = 0

    try:
        async for scraped_doc in scraper.run():
            async with db.session() as session:
                try:
                    source_repo = SourceRepository(session)
                    doc_repo = DocumentRepository(session)
                    job_repo = ScrapeJobRepository(session)

                    source_record = await source_repo.get_by_name(source)
                    if not source_record:
                        logger.warning(f"Source {source} not found in database")
                        continue

                    existing = await doc_repo.get_by_url(scraped_doc.source_url)
                    if existing:
                        logger.debug(f"Document already exists: {scraped_doc.source_url}")
                        continue

                    scraper_service = ScraperService(
                        session=session,
                        settings=settings,
                        embedder=embedder if embed_documents else None,
                    )

                    document = await scraper_service.save_document(
                        scraped_doc=scraped_doc,
                        source_id=source_record.id,
                        embed=embed_documents,
                    )

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


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/scrape", response_model=ScrapeJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def scrape_document(
    request_body: ScrapeRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    service: ScraperService = Depends(get_scraper_service),
):
    """Queue a single document URL for scraping."""
    # Check if job already exists
    source_record = await service.source_repo.get_by_name(request_body.source)
    if not source_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Source {request_body.source} not found. Seed the database first.",
        )

    job_id = uuid7()
    job = ScrapeJob(
        id=job_id,
        source_id=source_record.id,
        url=request_body.url,
        status=ScraperStatus.PENDING,
    )
    job = await service.job_repo.create(job)
    await service.session.commit()

    db: Database = request.app.state.database
    embedder: BaseEmbedder = request.app.state.embedder
    settings: Settings = request.app.state.settings

    background_tasks.add_task(
        _scrape_document_task,
        job_id,
        request_body.url,
        request_body.doc_type,
        request_body.source,
        db,
        embedder if request_body.embed else None,
        settings,
        request_body.embed,
    )

    return ScrapeJobResponse.model_validate(job)


@router.post("/crawl", response_model=CrawlResponse, status_code=status.HTTP_202_ACCEPTED)
async def crawl_source(
    request_body: CrawlRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    service: ScraperService = Depends(get_scraper_service),
):
    """Crawl a source for specific document types."""
    # Validate document types are supported
    supported = await service.get_supported_document_types(request_body.source)
    unsupported = set(request_body.document_types) - set(supported)
    if unsupported:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Source {request_body.source} does not support: {[t.value for t in unsupported]}",
        )

    job_id = uuid7()
    db: Database = request.app.state.database
    embedder: BaseEmbedder = request.app.state.embedder
    settings: Settings = request.app.state.settings

    background_tasks.add_task(
        _crawl_source_task,
        job_id,
        request_body.source,
        request_body.document_types,
        db,
        embedder if request_body.embed else None,
        settings,
        request_body.embed,
    )

    return CrawlResponse(
        job_id=job_id,
        source=request_body.source,
        document_types=request_body.document_types,
        status="crawling",
    )


@router.get(
    "/sources/{source}/document-types",
    response_model=SupportedDocumentTypesResponse,
)
async def get_supported_document_types(
    source: SourceName,
    service: ScraperService = Depends(get_scraper_service),
):
    """Get the document types supported by a source."""
    try:
        types = await service.get_supported_document_types(source)
        return SupportedDocumentTypesResponse(
            source=source,
            document_types=[dt.value for dt in types],
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/jobs/{job_id}", response_model=ScrapeJobResponse)
async def get_scrape_job(
    job_id: UUID,
    service: ScraperService = Depends(get_scraper_service),
):
    """Get status of a scrape job."""
    job = await service.job_repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return ScrapeJobResponse.model_validate(job)


@router.get("/status", response_model=ScrapeStatusResponse)
async def get_scrape_status(
    service: ScraperService = Depends(get_scraper_service),
):
    """Get overall scraping status."""
    pending = await service.get_pending_jobs(limit=10_000)
    failed = await service.get_failed_jobs(limit=10_000)
    return ScrapeStatusResponse(
        pending=len(pending),
        in_progress=0,  # Could be tracked with a query on IN_PROGRESS status
        completed=0,
        failed=len(failed),
    )


@router.post("/retry-failed")
async def retry_failed_jobs(
    background_tasks: BackgroundTasks,
    request: Request,
    source: Optional[SourceName] = None,
    limit: int = 10,
    service: ScraperService = Depends(get_scraper_service),
):
    """Retry failed scrape jobs."""
    failed_jobs = await service.get_failed_jobs(limit=limit)

    db: Database = request.app.state.database
    embedder: BaseEmbedder = request.app.state.embedder
    settings: Settings = request.app.state.settings

    queued = 0
    for job in failed_jobs:
        job.status = ScraperStatus.PENDING
        job.retry_count += 1
        await service.job_repo.update(job)

        background_tasks.add_task(
            _scrape_document_task,
            job.id,
            job.url,
            DocumentType.REPUBLIC_ACT,  # Default; ideally store doc_type on the job
            source or SourceName.LAWPHIL,
            db,
            embedder,
            settings,
        )
        queued += 1

    await service.session.commit()
    return {"queued": queued}