from typing import Optional
from schemas.scraped_document import ScrapedDocument
from schemas.scraped_part import ScrapedPart
from enums.section_type import SectionType
from transformers.html_to_markdown import HtmlToMarkdown


class MarkdownTransformer:
    """Convert ScrapedDocument to readable Markdown."""

    def __init__(self):
        self.html_converter = HtmlToMarkdown()

    def transform(self, document: ScrapedDocument) -> str:
        """Generate a complete Markdown document."""
        lines = []

        # Header
        lines.append(f"# {document.canonical_citation}")
        lines.append("")

        if document.title:
            lines.append(f"## {document.title}")
            lines.append("")

        # Metadata section
        lines.append("---")
        lines.append("")

        if document.date_promulgated:
            lines.append(f"**Promulgated:** {document.date_promulgated}")
        if document.date_effectivity:
            lines.append(f"**Effectivity:** {document.date_effectivity}")

        if document.metadata_fields.get("source_name"):
            lines.append(f"**Source:** {document.metadata_fields.get('source_name')}")
        if document.source_url:
            lines.append(f"**URL:** {document.source_url}")

        lines.append("")
        lines.append("---")
        lines.append("")

        # Body parts
        for part in document.parts:
            lines.extend(self._transform_part(part, depth=0))
            lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append(f"*Document Type: {document.doc_type.value}*")

        return "\n".join(lines)

    def _transform_part(self, part: ScrapedPart, depth: int = 0) -> list[str]:
        """Recursively transform a ScrapedPart and its children."""
        lines = []
        indent = "  " * depth

        # Prefer content_markdown, fall back to content_text
        content = part.content_markdown or part.content_text or ""

        if part.section_type == SectionType.ARTICLE:
            label = part.label or "Article"
            lines.append(f"{indent}## {label}")
            if content:
                lines.append(f"{indent}{content}")
            lines.append("")

        elif part.section_type == SectionType.SECTION:
            label = part.label or "Section"
            lines.append(f"{indent}### {label}")
            if content:
                lines.append(f"{indent}{content}")
            lines.append("")

        elif part.section_type == SectionType.SUBSECTION:
            label = part.label or ""
            if label:
                lines.append(f"{indent}#### {label}")
            if content:
                lines.append(f"{indent}{content}")
            lines.append("")

        elif part.section_type == SectionType.PARAGRAPH:
            if content:
                lines.append(f"{indent}{content}")
            lines.append("")

        elif part.section_type == SectionType.BODY:
            if content:
                lines.append(content)
            lines.append("")

        elif part.section_type == SectionType.TABLE:
            if content:
                lines.append(content)
            lines.append("")

        elif part.section_type == SectionType.PREAMBLE:
            if content:
                lines.append(f"> {content}")
            lines.append("")

        elif part.section_type == SectionType.ENACTING_CLAUSE:
            if content:
                lines.append(f"*{content}*")
            lines.append("")

        elif part.section_type == SectionType.TITLE:
            if content:
                lines.append(f"# {content}")
            lines.append("")

        elif part.section_type == SectionType.FOOTNOTE:
            if content:
                lines.append(f"{indent}> *{content}*")
            lines.append("")

        else:
            # Generic handling for all other types
            if part.label:
                lines.append(f"{indent}**{part.label}**")
            if content:
                lines.append(f"{indent}{content}")
            lines.append("")

        # Recursively process children
        for child in part.children:
            lines.extend(self._transform_part(child, depth + 1))

        return lines

    def save_to_file(self, document: ScrapedDocument, filepath: str) -> None:
        """Transform and save to a file."""
        markdown = self.transform(document)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown)