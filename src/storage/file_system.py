import os
import winreg
import platform
from pathlib import Path
from typing import Optional

from utils.constants import MONTHS
from models.directory import Directory

def _get_documents_path() -> Path:
    """Get the Documents directory for any os/system.

    Returns:
        Path: The path to the Documents directory.
    """
    if platform.system() == "Windows":
        try:
            # Access the Windows Registry for the user's shell folders (e.g. Downloads, Documents).
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
            )

            # Get the Data from the specified Name of the registry.
            # Side Note: The name for Documents is "Personal".
            value, _ = winreg.QueryValueEx(key, "Personal")
            winreg.CloseKey(key)

            expanded = os.path.expandvars(value)

            return Path(expanded).expanduser().resolve()

        except Exception:
            return (Path.home() / "Documents").expanduser().resolve()

    else:
        return (Path.home() / "Documents").expanduser().resolve()

def get_data_dir() -> Path:
    """Get the Data directory.
    Also creates the directory if has not been created yet.

    Returns:
        Path: the path to the Data save directory relative to the Document directory.
    """
    document_dir = _get_documents_path()

    data_dir = document_dir / "OpenJuris"
    data_dir.mkdir(exist_ok=True)

    return data_dir

def get_files_dir(source: str, category: str, file_type: str, start_year: Optional[int] = 1946, end_year: Optional[int] = 2025) -> list[Directory]:
    """Get the HTML directory.
    Also creates all the folders for the HTMLs if not created yet.

    Args:
        source (str): The website that the HTML has come from.
        category (str): The category of HTML that will be saved (e.g. Republic Act).
        file_type (str): The type of the file you'd like to access (e.g. html, markdown).
        start_year (Optional [int]): The first year folder to create.
        end_year (Optional [int]): The last year folder to create.

    Returns:
        list (HTMLDirectory): A list of all the HTML directory model that includes
                              month, year, source, and the html's directory.

    """
    html_dir =  get_data_dir() / source / file_type / category
    all_dir = []

    for year in range(start_year, end_year+1):
        year_dir = html_dir / str(year)

        for month in MONTHS:
            month_dir = year_dir / month
            month_dir.mkdir(parents=True, exist_ok=True)

            all_dir.append(Directory(
                month=month,
                year=year,
                source=source,
                directory=month_dir
            ))

    return all_dir

def get_file_dir(source: str, category: str, file_type: str, month: str, year: int) -> Directory:
    """Get a specific file directory without iterating through all directories.

    Args:
        source (str): The website that the file has come from.
        category (str): The category of file (e.g. Republic Act).
        file_type (str): The type of the file (e.g. html, markdown).
        year (int): The specific year.
        month (str): The specific month name.

    Returns:
        Directory: The directory model for the specified path.
    """

    html_dir = get_data_dir() / source / file_type / category / str(year) / month

    return Directory(
        month=month,
        year=year,
        source=source,
        directory=html_dir
    )