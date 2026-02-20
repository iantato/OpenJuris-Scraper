from abc import ABC, abstractmethod
from typing import Optional, Any, AsyncIterator

from bs4 import BeautifulSoup
from loguru import logger

from config.scraper import ScraperSettings
from schemas.scraper_context import ScraperContext
from schemas.scraped_document import ScrapedDocument
from enums.document_type import DocumentType
from utils.http_client import HttpClient


class BaseScraper(ABC):
    """Abstract base class for all scrapers"""

    def __init__(self, settings: ScraperSettings, ctx: ScraperContext):
        self.settings = settings
        self.ctx = ctx
        self.http_client = HttpClient(
            rate_limit=settings.rate_limit,
            request_timeout=settings.request_timeout,
            max_retries=settings.max_retries,
            user_agent=settings.user_agent,
        )
        self.visited_links: list[str] = []

    @property
    @abstractmethod
    def source_name(self) -> Any:
        """Human-readable name of the source"""
        ...

    @property
    @abstractmethod
    def base_url(self) -> Any:
        """The base URL for this scraper. Must be defined by subclass."""
        ...

    @property
    @abstractmethod
    def urls(self) -> dict[DocumentType, str]:
        """URL registry for this scraper. Must be defined by subclass."""
        ...

    def _get_deep_links(
        self,
        target_document_types: list[DocumentType] | None
    ) -> dict[DocumentType, str]:
        """Get deep links for the target document types."""
        if target_document_types is None:
            return self.urls
        return {
            doc_type: url
            for doc_type, url in self.urls.items()
            if doc_type in target_document_types
        }

    @abstractmethod
    async def scrape_document(self, url: str, doc_type: DocumentType) -> Optional[ScrapedDocument]:
        """Scrape a single document. Must be implemented by subclass."""
        ...

    async def _extract_urls(self, soup: BeautifulSoup, current_url: Optional[str] = None) -> AsyncIterator[str]:
        """Extract all valid URLs from a soup object."""
        from urllib.parse import urljoin

        for link in soup.find_all('a', href=True):
            href = link['href']
            if current_url:
                href = urljoin(current_url, href)

            if href not in self.visited_links:
                yield href

    async def run(self) -> AsyncIterator[ScrapedDocument]:
        """Main entry point for crawling and scraping."""
        deep_links = self._get_deep_links(self.ctx.target_document_types)

        await self.http_client.start()
        try:
            for doc_type, index_url in deep_links.items():
                full_url = f"{self.base_url.value}{index_url}"
                logger.info(f"Crawling index: {full_url}")

                try:
                    html = await self.http_client.get_bytes(full_url)
                    soup = BeautifulSoup(html, "html.parser")

                    async for doc_url in self.crawl(soup, full_url):
                        if doc_url in self.visited_links:
                            continue

                        try:
                            document = await self.scrape_document(doc_url, doc_type)
                            if document:
                                yield document
                        except Exception as e:
                            logger.error(f"Failed to scrape {doc_url}: {e}")
                            continue

                except Exception as e:
                    logger.error(f"Failed to crawl index {full_url}: {e}")
                    continue
        finally:
            await self.http_client.close()

    @abstractmethod
    async def crawl(self, soup: BeautifulSoup, current_url: str) -> AsyncIterator[str]:
        """Crawl an index page and yield document URLs."""
        ...

    async def close(self):
        """Close the scraper and release resources."""
        await self.http_client.close()