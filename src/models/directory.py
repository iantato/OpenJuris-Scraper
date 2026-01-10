from pathlib import Path
from dataclasses import dataclass

@dataclass
class Directory:
    month: str
    year: str
    source: str
    directory: Path