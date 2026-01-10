from pathlib import Path
from dataclasses import dataclass

@dataclass
class HTMLDirectory:
    month: str
    year: str
    source: str
    html_directory: Path

@dataclass
class MDDirectory:
    month: str
    year: str
    source: str
    html_directory: Path