from typing import Optional, AsyncIterator

from bs4 import BeautifulSoup

from scrapers.base import BaseScraper

from schemas.scraper_context import ScraperContext
from schemas.scraped_document import ScrapedDocument

from enums.source_url import SourceBaseURL
from enums.source_name import SourceName
from enums.document_type import DocumentType

from scrapers.lawphil.constants import LAWPHIL_PATHS

from config import Settings

class LawphilScraper(BaseScraper):

    def __init__(self, settings: Settings, ctx: ScraperContext):
        super().__init__(settings, ctx)
        self.ctx = ctx

    @property
    def source_name(self) -> SourceName:
        """Human-readable name of the source"""
        return SourceName.LAWPHIL

    @property
    def base_url(self) -> SourceBaseURL:
        """The base URL for this scraper. Must be defined by subclass."""
        return SourceBaseURL.LAWPHIL

    @property
    def urls(self) -> dict[DocumentType, str]:
        """URL registry for this scraper. Must be defined by subclass."""
        return LAWPHIL_PATHS

    async def crawl(self, soup: BeautifulSoup) -> None:
        async for statute in self._extract_urls(soup.find("table", id="s-menu")):
            html = await self.http_client.get_bytes(statute)
            soup = BeautifulSoup(html, "html.parser")
            self.visited_links.append(statute)

            yield statute

    async def scrape_document(self, doc_url: str) -> Optional[ScrapedDocument]:
        html = await self.http_client.get_bytes(doc_url)