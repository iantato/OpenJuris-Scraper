from typing import Optional

from config import Settings
from enums.source_name import SourceName
from schemas.scraper_context import ScraperContext
from scrapers.base import BaseScraper
from scrapers.lawphil.scraper import LawphilScraper
from scrapers.sc_elibrary.scraper import SCELibraryScraper


def get_scraper(
    source: SourceName,
    settings: Settings,
    ctx: Optional[ScraperContext]
) -> BaseScraper:
    """Factory function to get the appropriate scraper for a source."""
    if source == SourceName.LAWPHIL:
        return LawphilScraper(settings, ctx)
    # elif source == SourceName.SC_ELIBRARY:
    #     return SCELibraryScraper(settings, ctx)
    else:
        raise ValueError(f"Unsupported source: {source}")