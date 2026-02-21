import re
from typing import Optional
from datetime import date

from bs4 import BeautifulSoup, Tag

from schemas.scraped_document import ScrapedDocument
from schemas.statute_pattern import StatutePattern
from schemas.scraped_part import ScrapedPart

from enums.section_type import SectionType
from enums.document_type import DocumentType
from enums.document_category import DocumentCategory

from scrapers.lawphil.constants import STATUTE_PATTERNS
from converters.html_to_markdown import HtmlToMarkdown
from converters.markdown_transformer import MarkdownTransformer


class LawphilStatuteParser:

    def __init__(self):
        # Initialize converters
        self.html_converter = HtmlToMarkdown()
        self.markdown_transformer = MarkdownTransformer()

        self._title_terminators = re.compile(
            r'(?:'
            r'(?:^|\n)\s*(?:SEC(?:TION)?\.?\s*\d+)'
            r'|(?:^|\n)\s*(?:ART(?:ICLE)?\.?\s*[IVXLCDM\d]+)'
            r'|(?:^|\n)\s*(?:CHAPTER\s*[IVXLCDM\d]+)'
            r'|(?:^|\n)\s*PRELIMINARY\s+TITLE'
            r'|(?:^|\n)\s*GENERAL\s+PROVISIONS'
            r'|(?:^|\n)\s*Be\s+it\s+enacted'
            r'|(?:^|\n)\s*WHEREAS'
            r')',
            re.IGNORECASE | re.MULTILINE
        )

        self._header_pattern = re.compile(
            r'^\s*\[?\s*(?:REPUBLIC\s+ACT|PRESIDENTIAL\s+DECREE|EXECUTIVE\s+ORDER|'
            r'BATAS\s+PAMBANSA|COMMONWEALTH\s+ACT|ACT)\s+NO\.?\s*\d+',
            re.IGNORECASE
        )

        self._enacting_clause_pattern = re.compile(
            r'Be\s+it\s+enacted\s+by\s+the\s+Senate\s+and\s+House\s+of\s+Representatives',
            re.IGNORECASE
        )

        self._section_pattern = re.compile(
            r'^(?:SEC(?:TION)?\.?\s*(\d+)\.?\s*[-–—.]?\s*(.*))',
            re.IGNORECASE
        )

        self._article_pattern = re.compile(
            r'^(?:ART(?:ICLE)?\.?\s*([IVXLCDM\d]+)\.?\s*[-–—.]?\s*(.*))',
            re.IGNORECASE
        )
        self._chapter_pattern = re.compile(
            r'^(?:CHAPTER\s*([IVXLCDM\d]+)\.?\s*[-–—.]?\s*(.*))',
            re.IGNORECASE
        )

        self._sort_counter = 0

    def parse(self, html: str, url: str, doc_type: DocumentType) -> Optional[ScrapedDocument]:
        """Parse a LawPhil statute page."""
        self._reset_sort_counter()

        soup = BeautifulSoup(html, "html.parser")

        config = self._get_pattern_for_type(doc_type)
        if not config:
            return None

        statute_info = self._extract_info(soup, config)
        if not statute_info:
            return None

        title = self._extract_title(soup, config)
        dates = self._extract_dates(soup, config)
        parts = self._extract_body_parts(soup)
        category = self._get_category(doc_type)

        # Convert date objects to ISO strings for JSON storage in metadata_fields
        dates_raw_json = {
            key: val.isoformat() if isinstance(val, date) else val
            for key, val in dates.items()
        }

        # Create the scraped document
        document = ScrapedDocument(
            canonical_citation=statute_info,
            title=title or statute_info,
            category=category,
            doc_type=doc_type,
            source_url=url,
            date_promulgated=dates.get('approved') or dates.get('promulgated'),
            date_effectivity=dates.get('effectivity'),
            metadata_fields={
                'statute_number': self._extract_number(statute_info),
                'dates_raw': dates_raw_json,  # Use JSON-serializable version
            },
            parts=parts,
            raw_html=html
        )

        # Generate full markdown representation using the transformer
        document.content_markdown = self.markdown_transformer.transform(document)

        return document

    def _get_pattern_for_type(self, doc_type: DocumentType) -> Optional[StatutePattern]:
        """Get the pattern configuration for a document type."""
        return STATUTE_PATTERNS.get(doc_type)

    def _extract_info(self, soup: BeautifulSoup, config: StatutePattern) -> Optional[str]:
        """Extract canonical citation (e.g., 'Republic Act No. 1')."""
        full_text = soup.get_text()

        # Try title first
        if soup.title:
            for pattern_str in config.patterns:
                match = re.search(pattern_str, soup.title.get_text(), re.IGNORECASE)
                if match:
                    number = match.group(2)
                    return f"{config.display_name} No. {number}"

        # Try patterns in body
        for pattern_str in config.patterns:
            match = re.search(pattern_str, full_text[:2000], re.IGNORECASE)
            if match:
                number = match.group(2)
                return f"{config.display_name} No. {number}"

        return None

    def _get_category(self, doc_type: DocumentType) -> DocumentCategory:
        """Map document type to category."""
        statute_types = [
            DocumentType.REPUBLIC_ACT,
            DocumentType.PRESIDENTIAL_DECREE,
            DocumentType.BATAS_PAMBANSA,
            DocumentType.COMMONWEALTH_ACT,
            DocumentType.ACT,
        ]

        executive_types = [
            DocumentType.EXECUTIVE_ORDER,
            DocumentType.ADMINISTRATIVE_ORDER,
            DocumentType.MEMORANDUM_ORDER,
            DocumentType.MEMORANDUM_CIRCULAR,
            DocumentType.GENERAL_ORDER,
        ]

        if doc_type in statute_types:
            return DocumentCategory.STATUTE
        elif doc_type in executive_types:
            return DocumentCategory.EXECUTIVE
        elif doc_type == DocumentType.CONSTITUTION:
            return DocumentCategory.CONSTITUTION
        else:
            return DocumentCategory.STATUTE  # Default

    def _extract_number(self, citation: str) -> Optional[str]:
        """Extract just the number from citation."""
        match = re.search(r'No\.\s*(\d+)', citation)
        return match.group(1) if match else None

    def _extract_title(
        self,
        soup: BeautifulSoup,
        pattern_config: StatutePattern
    ) -> Optional[str]:
        """Extract document title."""
        if pattern_config.title_prefixes:
            prefix_pattern = "|".join(re.escape(p) for p in pattern_config.title_prefixes)
        else:
            prefix_pattern = r'AN\s+ACT|DECLARING|PROVIDING|DIRECTING|CREATING|ORDERING'

        full_text = soup.get_text()

        # Find statute citation in text, then extract title after it
        for pattern_str in pattern_config.patterns:
            statute_match = re.search(pattern_str, full_text, re.IGNORECASE)
            if statute_match:
                # Look for title in text after the citation
                after_citation = full_text[statute_match.end():statute_match.end() + 5000]

                # Find where the title starts (prefix match)
                title_start_match = re.search(
                    rf'({prefix_pattern})',
                    after_citation,
                    re.IGNORECASE
                )

                if title_start_match:
                    # Get text from title start
                    title_text = after_citation[title_start_match.start():]

                    # Find where the title ends (section/article/chapter starts)
                    terminator_match = self._title_terminators.search(title_text)

                    if terminator_match:
                        title = title_text[:terminator_match.start()]
                    else:
                        # No terminator found, try to find a reasonable end
                        double_newline = re.search(r'\n\s*\n', title_text)
                        if double_newline and double_newline.start() < 1000:
                            title = title_text[:double_newline.start()]
                        else:
                            # Fallback: take first 500 chars
                            title = title_text[:500]

                    # Clean up whitespace
                    title = ' '.join(title.split())
                    title = title.rstrip('.,;: ')

                    if len(title) > 500:
                        title = title[:500] + "..."

                    return title

        # Fallback: Look for standalone title elements
        for tag in soup.find_all(['p', 'div', 'center', 'b', 'i', 'em']):
            text = tag.get_text(strip=True)
            for prefix in pattern_config.title_prefixes:
                if text.upper().startswith(prefix):
                    if not self._title_terminators.search(text):
                        return ' '.join(text.split())

        return None

    def _next_sort_order(self) -> int:
        """Get next sort order number."""
        self._sort_counter += 1
        return self._sort_counter

    def _reset_sort_counter(self):
        """Reset sort counter for new document."""
        self._sort_counter = 0

    def _element_to_markdown(self, element: Tag) -> str:
        """Convert an HTML element to Markdown."""
        if element is None:
            return ""
        return self.html_converter.convert_element(element)

    def _html_to_markdown(self, html: str) -> str:
        """Convert HTML string to Markdown."""
        if not html:
            return ""
        return self.html_converter.convert(html)

    def _get_text_with_formatting(self, element: Tag) -> tuple[str, str]:
        """
        Extract both plain text and markdown from an element.

        Returns:
            Tuple of (plain_text, markdown_text)
        """
        if element is None:
            return "", ""

        plain_text = element.get_text(separator=' ', strip=True)
        markdown_text = self._element_to_markdown(element)

        return plain_text, markdown_text

    def _extract_body_parts(self, soup: BeautifulSoup) -> list[ScrapedPart]:
        """Extract document body with structure detection and markdown conversion."""
        parts: list[ScrapedPart] = []

        current_article: Optional[ScrapedPart] = None
        current_section: Optional[ScrapedPart] = None
        current_content: list[tuple[str, str]] = []

        passed_header = False

        body = soup.find('body') or soup

        for element in body.find_all(['p', 'div', 'blockquote', 'table', 'center', 'pre']):
            if self._is_boilerplate(element):
                continue

            # Handle tables
            if element.name == 'table':
                if current_content:
                    self._flush_content(
                        current_content, current_section, current_article, parts
                    )
                    current_content = []

                table_md = self._table_to_markdown(element)
                table_text = element.get_text(separator=' ', strip=True)

                table_part = ScrapedPart(
                    section_type=SectionType.TABLE,
                    content_text=table_text,
                    content_markdown=table_md,
                    content_html=str(element),
                    sort_order=self._next_sort_order()
                )

                if current_section:
                    current_section.children.append(table_part)
                elif current_article:
                    current_article.children.append(table_part)
                else:
                    parts.append(table_part)
                continue

            text, markdown = self._get_text_with_formatting(element)

            if not text:
                continue

            # Check for article markers
            article_match = re.match(
                r'^(ARTICLE|ART\.?)\s+([IVXLCDM]+|\d+)\.?\s*(.*)',
                text, re.IGNORECASE
            )
            if article_match:
                passed_header = True
                if current_content:
                    self._flush_content(
                        current_content, current_section, current_article, parts
                    )
                    current_content = []

                if current_section and current_article:
                    current_article.children.append(current_section)
                    current_section = None

                if current_article:
                    parts.append(current_article)

                label = f"Article {article_match.group(2)}"
                title_text = article_match.group(3).strip() if article_match.group(3) else ""

                current_article = ScrapedPart(
                    section_type=SectionType.ARTICLE,
                    label=label,
                    content_text=title_text,
                    content_markdown=title_text,
                    sort_order=self._next_sort_order()
                )
                current_section = None
                continue

            # Check for section markers
            section_match = re.match(
                r'^(SECTION|SEC\.?)\s+(\d+)\.?\s*(.*)',
                text, re.IGNORECASE
            )
            if section_match:
                passed_header = True
                if current_content:
                    self._flush_content(
                        current_content, current_section, current_article, parts
                    )
                    current_content = []

                if current_section:
                    if current_article:
                        current_article.children.append(current_section)
                    else:
                        parts.append(current_section)

                label = f"Section {section_match.group(2)}"
                title_text = section_match.group(3).strip() if section_match.group(3) else ""

                current_section = ScrapedPart(
                    section_type=SectionType.SECTION,
                    label=label,
                    content_text=title_text,
                    content_markdown=title_text,
                    sort_order=self._next_sort_order()
                )
                continue

            if not passed_header and self._is_header_content(text):
                continue

            current_content.append((text, markdown))

        if current_content:
            self._flush_content(
                current_content, current_section, current_article, parts
            )

        if current_section:
            if current_article:
                current_article.children.append(current_section)
            else:
                parts.append(current_section)

        if current_article:
            parts.append(current_article)

        return parts

    def _is_header_content(self, text: str) -> bool:
        """Check if text is part of the document header/preamble to skip."""
        if self._header_pattern.search(text):
            return True

        title_starters = [
            'AN ACT', 'DECLARING', 'PROVIDING', 'DIRECTING', 'CREATING',
            'ORDERING', 'ESTABLISHING', 'AMENDING', 'REPEALING'
        ]
        text_upper = text.upper().strip()
        for starter in title_starters:
            if text_upper.startswith(starter):
                return True

        return False

    def _flush_content(
        self,
        content: list[tuple[str, str]],
        current_section: Optional[ScrapedPart],
        current_article: Optional[ScrapedPart],
        parts: list[ScrapedPart]
    ) -> None:
        """Flush accumulated content to appropriate parent."""
        if not content:
            return

        text_parts = [t for t, m in content]
        markdown_parts = [m for t, m in content]

        text = '\n'.join(text_parts)
        markdown = '\n\n'.join(markdown_parts)

        paragraph = ScrapedPart(
            section_type=SectionType.PARAGRAPH,
            content_text=text,
            content_markdown=markdown,
            sort_order=self._next_sort_order()
        )

        if current_section:
            current_section.children.append(paragraph)
        elif current_article:
            current_article.children.append(paragraph)
        else:
            parts.append(paragraph)

    def _table_to_markdown(self, table: Tag) -> str:
        """Convert HTML table to Markdown."""
        rows = table.find_all('tr')
        if not rows:
            return ""

        md_lines = []

        for i, row in enumerate(rows):
            cells = row.find_all(['td', 'th'])
            if not cells:
                continue

            cell_texts = []
            for cell in cells:
                cell_md = self._element_to_markdown(cell)
                cell_md = re.sub(r'\s+', ' ', cell_md).strip()
                cell_texts.append(cell_md)

            md_lines.append("| " + " | ".join(cell_texts) + " |")

            if i == 0:
                separator = "| " + " | ".join(["---"] * len(cells)) + " |"
                md_lines.append(separator)

        return "\n".join(md_lines)

    def _extract_dates(self, soup: BeautifulSoup, config: StatutePattern) -> dict:
        """Extract dates and parse them to date objects."""
        dates = {}
        text = soup.get_text()

        date_patterns = {
            'approved': r'(?:Approved|Signed)[:\s]+([A-Za-z]+\s+\d{1,2},?\s*\d{4})',
            'effectivity': r'(?:Effectiv(?:e|ity)[:\s]+|take\s+effect\s+(?:on\s+)?|shall\s+take\s+effect\s+)([A-Za-z]+\s+\d{1,2},?\s*\d{4})',
            'promulgated': r'(?:Promulgated|Done)[:\s]+([A-Za-z]+\s+\d{1,2},?\s*\d{4})',
        }

        for date_field in config.date_fields:
            if date_field in date_patterns:
                pattern = date_patterns[date_field]
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    date_str = match.group(1)
                    parsed_date = self._parse_date(date_str)
                    if parsed_date:
                        dates[date_field] = parsed_date

        return dates

    def _parse_date(self, date_str: str) -> Optional[date]:
        """
        Parse Philippine date format to date object.
        Example: "June 19, 1946" -> date(1946, 6, 19)
        """
        from dateutil import parser
        from loguru import logger

        try:
            parsed = parser.parse(date_str)
            return parsed.date()
        except Exception as e:
            logger.warning(f"Failed to parse date '{date_str}': {e}")
            return None

    def _is_boilerplate(self, element: Tag) -> bool:
        """Detect boilerplate elements to skip."""
        classes = element.get('class', [])
        element_id = element.get('id', '')

        boilerplate_keywords = [
            'nav', 'menu', 'footer', 'header', 'sidebar',
            'banner', 'ad', 'copyright'
        ]

        for keyword in boilerplate_keywords:
            if keyword in element_id.lower():
                return True
            for cls in classes:
                if keyword in cls.lower():
                    return True

        text = element.get_text(strip=True).lower()
        boilerplate_texts = [
            'lawphil project',
            'chan robles',
            'copyright',
            'all rights reserved',
            'arellano law foundation',
        ]

        if any(x in text for x in boilerplate_texts):
            return True

        return False