from dataclasses import dataclass

from enums.document_type import DocumentType

@dataclass
class StatutePattern:
    """Configuration for a statute type."""
    document_type: DocumentType
    display_name: str
    abbreviation: str

    patterns: list[str]
    url_indicators: list[str]
    title_prefixes: list[str]

    date_fields: list[str]