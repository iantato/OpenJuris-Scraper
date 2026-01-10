from pathlib import Path
from dataclasses import dataclass

@dataclass
class HTMLDirectory:
    month: str
    year: str
    source: str
    directory: Path

@dataclass
class MDDirectory:
    month: str
    year: str
    source: str
    directory: Path