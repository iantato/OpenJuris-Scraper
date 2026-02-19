from typing import Optional
from schemas.scraped_document import ScrapedDocument
from schemas.scraped_part import ScrapedPart
from enums.section_type import SectionType

class MarkdownTransformer:
    """Convert ScrapedDocument to readable Markdown."""

    def transform(self, document: ScrapedDocument) -> str:
        """
        Generate a complete Markdown document.

        Args:
            document: The scraped document to transform

        Returns:
            Formatted Markdown string
        """
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

        if document.metadata_fields.get("source_name", None):
            lines.append(f"**Source:** {document.metadata_fields.get("source_name", None)}")
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

    def _transform_part(
        self, part: ScrapedPart, depth: int = 0
    ) -> list[str]:
        """
        Recursively transform a ScrapedPart and its children.

        Args:
            part: The part to transform
            depth: Current nesting depth

        Returns:
            List of markdown lines
        """
        lines = []
        indent = "  " * depth

        # Handle different section types
        if part.section_type == SectionType.ARTICLE:
            lines.append(f"{indent}## {part.label or 'Article'}")
            if part.content_text:
                lines.append(f"{indent}{part.content_text}")
            lines.append("")

        elif part.section_type == SectionType.SECTION:
            lines.append(f"{indent}### {part.label or 'Section'}")
            if part.content_text:
                lines.append(f"{indent}{part.content_text}")
            lines.append("")

        elif part.section_type == SectionType.PARAGRAPH:
            if part.content_markdown:
                lines.append(f"{indent}{part.content_markdown}")
            elif part.content_text:
                lines.append(f"{indent}{part.content_text}")
            lines.append("")

        elif part.section_type == SectionType.BODY:
            # Tables or generic body content
            if part.content_markdown:
                lines.append(part.content_markdown)
            elif part.content_text:
                lines.append(part.content_text)
            lines.append("")

        else:
            # Generic handling
            if part.label:
                lines.append(f"{indent}**{part.label}**")
            if part.content_markdown:
                lines.append(f"{indent}{part.content_markdown}")
            elif part.content_text:
                lines.append(f"{indent}{part.content_text}")
            lines.append("")

        # Recursively process children
        for child in part.children:
            child_lines = self._transform_part(child, depth + 1)
            lines.extend(child_lines)

        return lines

    def save_to_file(self, document: ScrapedDocument, filepath: str) -> None:
        """
        Transform and save to a file.

        Args:
            document: The document to save
            filepath: Output file path
        """
        markdown = self.transform(document)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown)