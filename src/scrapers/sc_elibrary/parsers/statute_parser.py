from typing import Optional

from bs4 import BeautifulSoup

from schemas.scraped_part import ScrapedPart
from schemas.scraped_document import ScrapedDocument

class SCELibStatuteParser:

    def __init__(self):
        pass

    def parse(self, html: str, url: str, recursion: Optional[bool] = False) -> Optional[ScrapedDocument]:
        """Parse the statute page"""
        soup = BeautifulSoup(html, "html.parser")

        content_div = soup.find("div", id="left")
        print(content_div)