from typing import Optional

from models.directory import Directory
from storage.file_system import get_files_dir
from utils.constants import SUPREME_COURT_TITLE
from parser.elibrary.repact import RepublicActTokenizer

class SupremeCourtELibraryParser:

    def __init__(self):
        self.title = SUPREME_COURT_TITLE

        # Tokenizers
        self.repact = RepublicActTokenizer()

    def _list_all_html(self, dir: Directory) -> list[str]:
        return [file.name for file in dir.directory.iterdir() if ".html" in file.name]

    def convert_based_on_category(self, category: str, dir: Directory, htmls: list[str]) -> None:
        match category:
            case "republic_act":
                self.repact.tokenize(dir, htmls)

    def crawl_local(self, category: str, start_year: Optional[int] = 1946, end_year: Optional[int] = 2025) -> None:

        dirs = get_files_dir(self.title, category, "html", start_year, end_year)

        for dir in dirs:
            files = self._list_all_html(dir)

            if not files:
                continue

            self.convert_based_on_category(category, dir, files)