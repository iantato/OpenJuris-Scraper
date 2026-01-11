import time
from pathlib import Path
from typing import Optional
from dataclasses import astuple

from tqdm import tqdm
from bs4 import BeautifulSoup

from utils.https import request_html
from storage.file_system import get_files_dir
from crawler.elibrary.constants import BASE_URL, PAGES

class SupremeCourtELibraryCrawler:

    def __init__(self, frequency: Optional[int] = 1):
        self.title = "supreme_court_elibrary"
        self.sleep_freuqency = frequency

    def _get_urls(self, soup: BeautifulSoup) -> list[str]:
        """Gets all the URL in the page of the month.

        Args:
            soup (BeautifulSoup): The page with the list of all the data we need to collect.

        Returns:
            list (str): The list of all the URLs.
        """
        return [url.get("href") for url in soup.find(attrs={"id": "left"}).find_all("a")]

    def crawl(self, category: str, start_year: Optional[int] = 1946, end_year: Optional[int] = 2025) -> None:
        """Crawls the Supreme Court E-Library and downloads the HTML.
        Downloading the HTML makes it easier for us to parse the data later on.

        Args:
            category (str): The category of which we'll be scraping (e.g. Republic Acts, Jurisprudence, etc.).
            start_year (Optional int): The start year to scrape. Defaults to 1946.
            end_year (Optional int): The last year to scrape. Defaults to 2025.
        """
        FILE_TYPE = "html"
        dirs = get_files_dir(
            source=self.title,
            category=category,
            file_type=FILE_TYPE,
            start_year=start_year,
            end_year=end_year
        )

        for dir in tqdm(dirs, desc="Month", position=0):
            time.sleep(self.sleep_freuqency)

            month, year, source, save_dir = astuple(dir)

            soup = BeautifulSoup(request_html(BASE_URL.format(
                month=month,
                year=year,
                page=PAGES.get(category)
            )), "html.parser")

            self._save_based_on_category(category, self._get_urls(soup), save_dir)

    def _save_based_on_category(self, category: str, urls: list[str], save_dir: Path) -> None:
        """Match the category of which we're scraping.
        This is because each of the category has their own different
        nuances for the file naming.

        Args:
            category (str): The category of which we'll be scraping (e.g. Republic Acts, Jurisprudence, etc.).
            urls (list[str]): List of all the url to save.
            save_dir (Path): The directory to save the file.
        """
        match category:
            case "republic_act":
                self.save_repact_htmls(urls, save_dir)

    def _get_repact_title(self, soup: BeautifulSoup) -> str:
        """Gets the title of Republic Act from the page.

        Args:
            soup (BeautifulSoup): The page of the republic act.

        Returns:
            str: Cleaned title of the Republic Act.
                    - Removed the brackets ( [] ) which is from the initial part of the page.
                    - Made the title from complete UPPERCASE to Title Case.
                    - Removed the dates which is from the initial part of the page.
        """
        raw_title = soup.find("h2").get_text().strip().split(",")[0]
        title = raw_title.replace("[", "").title().strip()

        return title

    def save_repact_htmls(self, urls: list[str], save_dir: Path) -> None:
        """Saves the parsed HTML into an HTML file.

        Args:
            urls (list[str]): List of all the url to save.
            save_dir (Path): The directory to save the file.
        """
        for url in tqdm(urls, desc="URL", position=1, leave=False):
            time.sleep(self.sleep_freuqency)

            soup = BeautifulSoup(request_html(url), "html.parser")
            title = self._get_repact_title(soup)
            ra_no = ''.join(char for char in title.split(" ")[-1] if char.isdigit())

            file = save_dir / f"ra_{ra_no}.html"
            file.write_text(soup.find(attrs={"id": "left"}).prettify(), encoding="utf-8")