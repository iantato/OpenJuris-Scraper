from typing import AsyncIterator, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from config import Settings
from embedder.providers.base import BaseEmbedder
from enums.document_type import DocumentType
from enums.source_name import SourceName
from enums.scraper_status import ScraperStatus
from models.document import Document
from schemas.scraped_document import ScrapedDocument
from schemas.scraper_context import ScraperContext
from services.subject import SubjectExtractionService
from scrapers.base import BaseScraper
from scrapers.lawphil.scraper import LawphilScraper
from storage.repositories.document import DocumentRepository


class ScraperService:
    """Service for managing scraping operations with optional subject extraction."""

    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        embedder: Optional[BaseEmbedder] = None,
    ):
        self.session = session
        self.settings = settings
        self.embedder = embedder
        self.document_repo = DocumentRepository(session)
        self.subject_service = SubjectExtractionService(session, embedder)

    def _get_scraper(self, source: SourceName, ctx: Optional[ScraperContext] = None) -> BaseScraper:
        """Get the appropriate scraper for a source."""
        if source == SourceName.LAWPHIL:
            return LawphilScraper(self.settings, ctx)
        else:
            raise ValueError(f"Unsupported source: {source}")

    async def scrape_single(
        self,
        url: str,
        source: SourceName,
        document_type: DocumentType,
        extract_subjects: bool = True,
        use_llm_for_subjects: bool = True,
    ) -> Optional[Document]:
        """
        Scrape a single document.

        Args:
            url: URL to scrape
            source: Source name
            document_type: Type of document
            extract_subjects: Whether to extract and link subjects
            use_llm_for_subjects: Whether to use LLM for subject extraction

        Returns:
            Saved Document model or None if failed
        """
        try:
            scraper = self._get_scraper(source)
            scraped_doc = await scraper.scrape_document(url, document_type)

            if not scraped_doc:
                logger.error(f"Failed to scrape document from {url}")
                return None

            # Save document
            document = await self._save_document(scraped_doc)

            # Extract and link subjects if requested
            if extract_subjects:
                await self.subject_service.extract_and_link_subjects(
                    document_id=document.id,
                    scraped_document=scraped_doc,
                    use_llm=use_llm_for_subjects
                )

            await self.session.commit()
            logger.info(f"Successfully scraped document: {scraped_doc.canonical_citation}")
            return document

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            await self.session.rollback()
            return None

    async def scrape_batch(
        self,
        source: SourceName,
        document_types: Optional[List[DocumentType]] = None,
        extract_subjects: bool = True,
        use_llm_for_subjects: bool = True,
        max_documents: Optional[int] = None,
    ) -> AsyncIterator[Document]:
        """
        Crawl and scrape documents from a source.

        Args:
            source: Source to scrape
            document_types: Types of documents to scrape (None for all)
            extract_subjects: Whether to extract and link subjects
            use_llm_for_subjects: Whether to use LLM for subject extraction
            max_documents: Maximum number of documents to scrape

        Yields:
            Saved Document models
        """
        count = 0
        scraper = self._get_scraper(source)

        async for scraped_doc in scraper.run():
            # Filter by document type if specified
            if document_types and scraped_doc.document_type not in document_types:
                continue

            try:
                # Save document
                document = await self._save_document(scraped_doc)

                # Extract and link subjects
                if extract_subjects:
                    await self.subject_service.extract_and_link_subjects(
                        document_id=document.id,
                        scraped_document=scraped_doc,
                        use_llm=use_llm_for_subjects
                    )

                await self.session.commit()
                count += 1
                yield document

                if max_documents and count >= max_documents:
                    break

            except Exception as e:
                logger.error(f"Error processing document {scraped_doc.canonical_citation}: {e}")
                await self.session.rollback()
                continue

    async def _save_document(self, scraped_doc: ScrapedDocument) -> Document:
        """Save a scraped document to the database."""
        # Build content from parts
        content = ""
        if scraped_doc.parts:
            content = "\n\n".join(
                part.content for part in scraped_doc.parts if part.content
            )

        document = Document(
            canonical_citation=scraped_doc.canonical_citation,
            title=scraped_doc.title,
            url=scraped_doc.url,
            document_type=scraped_doc.document_type,
            content=content,
            abstract=scraped_doc.abstract,
            date_published=scraped_doc.date,
        )

        self.session.add(document)
        await self.session.flush()  # Get the ID
        return document