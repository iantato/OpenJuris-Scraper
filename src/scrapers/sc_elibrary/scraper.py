from typing import Optional, AsyncIterator

from bs4 import BeautifulSoup

from scrapers.base import BaseScraper

from config import Settings

from schemas.scraper_context import ScraperContext
from schemas.scraped_document import ScrapedDocument

from enums.document_type import DocumentType
from enums.source_url import SourceBaseURL
from enums.source_name import SourceName

from scrapers.sc_elibrary.constants import SC_ELIB_PATHS
from scrapers.sc_elibrary.parsers.statute_parser import SCELibStatuteParser

class SCELibraryScraper(BaseScraper):

    def __init__(self, settings: Settings, ctx: ScraperContext):
        super().__init__(settings, ctx)
        self.ctx = ctx
        self.statute_parser = SCELibStatuteParser()

    @property
    def source_name(self) -> SourceName:
        """Human-readable name of the source"""
        return SourceName.SC_ELIBRARY

    @property
    def base_url(self) -> SourceBaseURL:
        """The base URL for this scraper. Must be defined by subclass."""
        return SourceBaseURL.SC_ELIBRARY

    @property
    def urls(self) -> dict[DocumentType, str]:
        """URL registry for this scraper. Must be defined by subclass."""
        return SC_ELIB_PATHS

    async def crawl(self, soup: BeautifulSoup) -> AsyncIterator[str]:
        async for month in self._extract_urls(soup.find("div", id="container_date")):
            html = await self.http_client.get(month)
            soup = BeautifulSoup(html, "html.parser")
            self.visited_links.append(month)

            async for doc in self._extract_urls(soup.find("div", id="left")):
                yield doc

    async def scrape_document(self, doc_url: str) -> Optional[ScrapedDocument]:
        html = await self.http_client.get(doc_url)

        self.statute_parser.parse(html, doc_url)