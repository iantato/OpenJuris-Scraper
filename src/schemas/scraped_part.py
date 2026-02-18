from typing import Optional
from dataclasses import dataclass, field

from enums.section_type import SectionType

@dataclass
class ScrapedPart:
    section_type: SectionType

    content_text: str
    content_markdown: str

    sort_order: int

    label: Optional[str] = None
    content_html: Optional[str] = None
    children: list["ScrapedPart"] = field(default_factory=list)