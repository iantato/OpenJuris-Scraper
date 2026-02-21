from typing import Optional

from dataclasses import dataclass

@dataclass
class TextChunk:
    """A chunk of text with metadata"""
    content: str
    index: int
    start_char: int
    end_char: int
    section_title: Optional[str] = None