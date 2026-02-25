from typing import AsyncIterator, Optional, List, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from config import Settings
from embedder.providers.base import BaseEmbedder
from enums.document_type import DocumentType
from enums.source_name import SourceName
from enums.scraper_status import ScraperStatus
from models.document import Document
from models.scrape_job import ScrapeJob
from schemas.scraped_document import ScrapedDocument
from schemas.scraper_context import ScraperContext
from services.subject import SubjectExtractionService
from scrapers.base import BaseScraper
from scrapers.lawphil.scraper import LawphilScraper
from storage.repositories.document import DocumentRepository
from storage.repositories.source import SourceRepository
from storage.repositories.scrape_job import ScrapeJobRepository


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
        self.source_repo = SourceRepository(session)
        self.job_repo = ScrapeJobRepository(session)
        self.subject_service = SubjectExtractionService(session, embedder)

    def _get_scraper(self, source: SourceName, ctx: Optional[ScraperContext] = None) -> BaseScraper:
        """Get the appropriate scraper for a source."""
        if source == SourceName.LAWPHIL:
            return LawphilScraper(self.settings, ctx)
        else:
            raise ValueError(f"Unsupported source: {source}")

    async def get_supported_document_types(self, source: SourceName) -> List[DocumentType]:
        """Get the document types supported by a source."""
        scraper = self._get_scraper(source, None)
        return list(scraper.urls.keys())

    async def get_pending_jobs(self, limit: int = 100) -> List[ScrapeJob]:
        """Get pending scrape jobs."""
        return await self.job_repo.get_pending_jobs(limit=limit)

    async def get_failed_jobs(self, limit: int = 100) -> List[ScrapeJob]:
        """Get failed scrape jobs."""
        return await self.job_repo.get_failed_jobs(limit=limit)

    async def save_document(
        self,
        scraped_doc: ScrapedDocument,
        source_id: UUID,
        embed: bool = True,
    ) -> Document:
        """Save a scraped document to the database with optional embedding."""
        from converters.markdown_transformer import MarkdownTransformer
        from models.document_part import DocumentPart
        from uuid6 import uuid7

        transformer = MarkdownTransformer()
        content_markdown = transformer.transform(scraped_doc)

        document = Document(
            id=uuid7(),
            source_id=source_id,
            canonical_citation=scraped_doc.canonical_citation,
            title=scraped_doc.title,
            source_url=scraped_doc.source_url,
            doc_type=scraped_doc.doc_type,
            category=scraped_doc.category,
            date_published=scraped_doc.date_promulgated,
            content_markdown=content_markdown,
            metadata_fields=scraped_doc.metadata_fields or {},
        )

        document = await self.document_repo.create(document)

        # Build and save document parts
        parts = self._build_document_parts(scraped_doc.parts, document.id)
        for part in parts:
            self.session.add(part)

        # Embed if requested
        if embed and self.embedder:
            await self._embed_document(document)

        return document

    def _build_document_parts(
        self,
        scraped_parts: List[Any],
        document_id: UUID,
        parent_id: Optional[UUID] = None,
    ) -> List[Any]:
        """Recursively convert ScrapedPart trees into flat list of DocumentPart models."""
        from models.document_part import DocumentPart
        from uuid6 import uuid7

        result = []
        for idx, part in enumerate(scraped_parts):
            part_id = uuid7()
            doc_part = DocumentPart(
                id=part_id,
                document_id=document_id,
                parent_id=parent_id,
                section_type=part.section_type,
                label=part.label,
                content_text=part.content_text,
                content_markdown=part.content_markdown,
                content_html=part.content_html,
                sort_order=idx,
            )
            result.append(doc_part)

            if part.children:
                result.extend(
                    self._build_document_parts(part.children, document_id, part_id)
                )

        return result

    async def _embed_document(self, document: Document) -> None:
        """Generate and store embeddings for a document."""
        if not self.embedder:
            return

        try:
            from models.vector import DocumentVector
            from storage.repositories.vector import VectorRepository
            from uuid6 import uuid7

            vector_repo = VectorRepository(self.session)

            # Embed the full content
            content = document.content_markdown or ""
            if not content:
                return

            embedding = await self.embedder.embed(content)

            vector = DocumentVector(
                id=uuid7(),
                document_id=document.id,
                embedding=embedding,
                chunk_index=0,
                chunk_text=content[:1000],  # Store first 1000 chars as reference
            )
            await vector_repo.create(vector)

            logger.debug(f"Created embedding for document {document.id}")

        except Exception as e:
            logger.warning(f"Failed to embed document {document.id}: {e}")

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