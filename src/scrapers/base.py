from typing import Optional, Any
from abc import ABC, abstractmethod
from urllib.parse import urljoin
from typing import AsyncIterator
from dataclasses import asdict

from bs4 import BeautifulSoup

from utils.http_client import HTTPClient
from enums.document_type import DocumentType
from schemas.scraper_context import ScraperContext
from schemas.scraped_document import ScrapedDocument
from schemas.date_range import DateRange

from config.scraper import ScraperSettings

class BaseScraper(ABC):
    """Abstract base class for all scrapers"""

    def __init__(self, settings: ScraperSettings, ctx: ScraperContext):
        self.ctx = ctx
        self.settings = settings
        self.http_client = HTTPClient(settings)
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
        """
        Get filtered deep links based on target document types.

        Args:
            target_document_types (list[DocumentType] | None): A list of all the document types to be
                                                               scraped. Defaults to None.

        Returns:
            dict[DocumentType, str]: A dictionary of all the deep links of specified document types.
        """
        # If the target_document_types has any sort of value, we filter the
        # deep link/urls to instead just include the target document types.
        # Otherwise, we crawl all the document types.
        if target_document_types:
            return {
                doc_type: url
                for doc_type, url in self.urls.items()
                if doc_type in target_document_types
            }
        return self.urls

    @abstractmethod
    async def scrape_document(self, url: str) -> Optional[ScrapedDocument]:
        ...

    async def _extract_urls(self, soup: BeautifulSoup) -> AsyncIterator[str]:
        for link in soup.find_all("a", href=True):
            href = link["href"]

            full_url = urljoin(self.base_url, href)

            if not full_url.startswith(self.base_url):
                continue

            yield full_url

    async def run(self) -> AsyncIterator[ScrapedDocument]:

        async with self.http_client:
            deep_links = self._get_deep_links(self.ctx.target_document_types)

            for _, url in deep_links.items():
                full_url = urljoin(self.base_url, url)

                html = await self.http_client.get_bytes(full_url)
                soup = BeautifulSoup(html, "html.parser")

                async for doc in self.crawl(soup):
                    document = await self.scrape_document(doc)

                    if document:
                        yield document

    async def close(self):
        """Cleanup resources"""
        await self.http_client.close()
