from pathlib import Path
from typing import Optional

from models.directory import Directory
from utils.constants import SUPREME_COURT_TITLE
from parser.elibrary.repact import RepublicActTokenizer
from storage.file_system import get_files_dir, get_file_dir

class SupremeCourtELibraryParser:

    def __init__(self):
        self.title = SUPREME_COURT_TITLE

        # Tokenizers
        self.repact = RepublicActTokenizer()

    def _list_all_html(self, dir: Directory) -> list[str]:
        return [file.name for file in dir.directory.iterdir() if ".html" in file.name]

    def _parse_based_on_category(self, category: str, file: Path) -> None:
        match category:
            case "republic_act":
                self.repact.tokenize(file)

    def crawl_local(self, category: str, start_year: Optional[int] = 1946, end_year: Optional[int] = 2025) -> None:

        # Get all the available directory for HTMLs.
        dirs = get_files_dir(self.title, category, "html", start_year, end_year)

        for dir in dirs:
            files = self._list_all_html(dir)

            # Skip if there are no files.
            if not files:
                continue

            for file in files:
                self.parse(category, file, dir=dir)

    def parse(self, category: str, html: str, month: Optional[str] = "", year: Optional[int] = "", dir: Optional[Directory] = None) -> None:
        if not dir:
            dir = get_file_dir(self.title, category, "html", month, year)
        file = f"{html}.html" if ".html" not in html else html

        self._parse_based_on_category(category, dir.directory / file)