from typing import Optional, AsyncIterator

from loguru import logger
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper

from schemas.scraper_context import ScraperContext
from schemas.scraped_document import ScrapedDocument

from enums.source_url import SourceBaseURL
from enums.source_name import SourceName
from enums.document_type import DocumentType

from scrapers.lawphil.parsers.statute_parser import LawphilStatuteParser

from scrapers.lawphil.constants import LAWPHIL_PATHS

from config import Settings

class LawphilScraper(BaseScraper):

    def __init__(self, settings: Settings, ctx: ScraperContext):
        super().__init__(settings, ctx)
        self.ctx = ctx
        self.statute_parser = LawphilStatuteParser()

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

    async def crawl(self, soup: BeautifulSoup, current_url: str) -> AsyncIterator[str]:

        async for statute in self._extract_urls(soup.find("table", id="s-menu"), current_url):
            logger.debug(f"Getting HTML for {statute}")
            try:
                html = await self.http_client.get_bytes(statute)
            except Exception:
                logger.debug(f"HTML extraction failed for {statute}")
                continue

            if ".pdf" in statute:
                logger.warning(f"Skipping {statute} because of PDF")
                continue

            soup = BeautifulSoup(html, "html.parser")
            self.visited_links.append(statute)

            yield statute

    async def scrape_document(self, doc_url: str, doc_type: DocumentType) -> Optional[ScrapedDocument]:
        logger.debug(f"Scraping {doc_type} from: {doc_url}")

        html = await self.http_client.get_bytes(doc_url)

        if "/statutes/" in doc_url:
            document = self.statute_parser.parse(html, doc_url, doc_type)
            document.metadata_fields["source_name"] = self.source_name.value

            return document

        return None