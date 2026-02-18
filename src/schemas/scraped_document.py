from datetime import date
from typing import Optional, Any
from dataclasses import dataclass, field

from enums.document_type import DocumentType
from enums.document_category import DocumentCategory

from schemas.scraped_part import ScrapedPart

@dataclass
class ScrapedDocument:
    canonical_citation: str

    title: str
    category: DocumentCategory
    doc_type: DocumentType

    source_url: str

    short_title: Optional[str] = None

    date_promulgated: Optional[date] = None
    date_published: Optional[date] = None
    date_effectivity: Optional[date] = None

    metadata_fields: dict[str, Any] = field(default_factory=dict)
    parts: list[ScrapedPart] = field(default_factory=list)

    raw_html: Optional[str] = None