import re
from typing import Optional

from bs4 import BeautifulSoup, Tag

from schemas.scraped_document import ScrapedDocument
from schemas.statute_pattern import StatutePattern
from schemas.scraped_part import ScrapedPart

from enums.section_type import SectionType
from enums.document_type import DocumentType
from enums.document_category import DocumentCategory

from scrapers.lawphil.constants import STATUTE_PATTERNS

class LawphilStatuteParser:

    def __init__(self):
        self._title_terminators = re.compile(
            r'(?:'
            r'(?:^|\n)\s*(?:SEC(?:TION)?\.?\s*\d+)'  # Section 1, SEC. 1, etc.
            r'|(?:^|\n)\s*(?:ART(?:ICLE)?\.?\s*[IVXLCDM\d]+)'  # Article I, ART. 1
            r'|(?:^|\n)\s*(?:CHAPTER\s*[IVXLCDM\d]+)'  # Chapter I
            r'|(?:^|\n)\s*PRELIMINARY\s+TITLE'  # Preliminary Title
            r'|(?:^|\n)\s*GENERAL\s+PROVISIONS'  # General Provisions
            r'|(?:^|\n)\s*Be\s+it\s+enacted'  # Enacting clause
            r'|(?:^|\n)\s*WHEREAS'  # Whereas clauses (for EOs, PDs)
            r')',
            re.IGNORECASE | re.MULTILINE
        )

        # Section/Article patterns (shared across all statute types)
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
        """
        Parse a statute document and return a ScrapedDocument.

        Args:
            html: Raw HTML content
            url: Source URL
            doc_type: Document type (e.g., DocumentType.REPUBLIC_ACT)

        Returns:
            ScrapedDocument or None if parsing fails
        """
        soup = BeautifulSoup(html, "lxml")
        self._sort_counter = 0  # Reset counter for each document

        pattern_config = STATUTE_PATTERNS.get(doc_type)
        if not pattern_config:
            return None

        # Extract statute number
        statute_info = self._extract_statute_number(soup, pattern_config)
        if not statute_info:
            return None

        # Extract other components
        title = self._extract_title(soup, pattern_config)
        parts = self._extract_body_parts(soup)
        dates = self._extract_dates(soup, pattern_config)

        # Determine document category based on type
        category = self._get_category(doc_type)

        return ScrapedDocument(
            canonical_citation=statute_info,
            title=title or statute_info,
            category=category,
            doc_type=doc_type,
            source_url=url,
            date_promulgated=dates.get('approved') or dates.get('promulgated'),
            date_effectivity=dates.get('effectivity'),
            metadata_fields={
                'statute_number': self._extract_number(statute_info),
                'dates_raw': dates,
            },
            parts=parts,
            raw_html=html
        )

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

    def _extract_statute_number(
        self, soup: BeautifulSoup, config: StatutePattern
    ) -> Optional[str]:
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

    def _extract_number(self, citation: str) -> Optional[str]:
        """Extract just the number from citation."""
        match = re.search(r'No\.\s*(\d+)', citation)
        return match.group(1) if match else None

    def _extract_title(
        self,
        soup: BeautifulSoup,
        pattern_config: StatutePattern
    ) -> Optional[str]:
        """
        Extract document title.

        Title typically:
        - Starts with "AN ACT", "DECLARING", etc.
        - Ends before "Section 1", "Article I", or similar structural markers
        """
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
                        # Title is everything before the terminator
                        title = title_text[:terminator_match.start()]
                    else:
                        # No terminator found, try to find a reasonable end
                        # Look for double newline or excessive whitespace
                        double_newline = re.search(r'\n\s*\n', title_text)
                        if double_newline and double_newline.start() < 1000:
                            title = title_text[:double_newline.start()]
                        else:
                            # Fallback: take first 500 chars
                            title = title_text[:500]

                    # Clean up whitespace
                    title = ' '.join(title.split())

                    # Remove trailing punctuation issues
                    title = title.rstrip('.,;: ')

                    if len(title) > 500:
                        title = title[:500] + "..."

                    return title

        # Fallback: Look for standalone title elements
        for tag in soup.find_all(['p', 'div', 'center', 'b', 'i', 'em']):
            text = tag.get_text(strip=True)
            for prefix in pattern_config.title_prefixes:
                if text.upper().startswith(prefix):
                    # Check this element doesn't contain section markers
                    if not self._title_terminators.search(text):
                        return ' '.join(text.split())

        return None

    def _next_sort_order(self) -> int:
        """Get next sort order and increment counter."""
        order = self._sort_counter
        self._sort_counter += 1
        return order

    def _extract_body_parts(self, soup: BeautifulSoup) -> list[ScrapedPart]:
        """Extract document body with structure detection."""
        parts: list[ScrapedPart] = []

        current_article: Optional[ScrapedPart] = None
        current_section: Optional[ScrapedPart] = None
        current_content: list[str] = []

        body = soup.find('body') or soup

        for element in body.find_all(['p', 'div', 'blockquote', 'table', 'center', 'pre']):
            if self._is_boilerplate(element):
                continue

            # Handle tables
            if element.name == 'table':
                # Flush current content before table
                if current_content:
                    self._flush_content(
                        current_content, current_section, current_article, parts
                    )
                    current_content = []

                table_md = self._table_to_markdown(element)
                table_part = ScrapedPart(
                    section_type=SectionType.BODY,  # Tables are body content
                    content_text=element.get_text(strip=True),
                    content_markdown=table_md,
                    content_html=str(element),
                    sort_order=self._next_sort_order()
                )

                # Add table to current section/article or top-level
                if current_section:
                    current_section.children.append(table_part)
                elif current_article:
                    current_article.children.append(table_part)
                else:
                    parts.append(table_part)
                continue

            text = element.get_text(strip=True)
            if not text:
                continue

            # Check for article header
            article_match = self._article_pattern.match(text)
            if article_match:
                # Flush any pending content
                if current_content:
                    self._flush_content(
                        current_content, current_section, current_article, parts
                    )
                    current_content = []

                # Save previous article to parts
                if current_article:
                    parts.append(current_article)

                article_num = article_match.group(1)
                article_title = article_match.group(2).strip()

                current_article = ScrapedPart(
                    section_type=SectionType.ARTICLE,
                    label=f"Article {article_num}",
                    content_text=article_title,
                    content_markdown=f"## Article {article_num}\n\n{article_title}" if article_title else f"## Article {article_num}",
                    sort_order=self._next_sort_order()
                )
                current_section = None  # Reset section on new article
                continue

            # Check for section header
            section_match = self._section_pattern.match(text)
            if section_match:
                # Flush any pending content
                if current_content:
                    self._flush_content(
                        current_content, current_section, current_article, parts
                    )
                    current_content = []

                # Save previous section to article or parts
                if current_section:
                    if current_article:
                        current_article.children.append(current_section)
                    else:
                        parts.append(current_section)

                section_num = section_match.group(1)
                section_text = section_match.group(2).strip()

                current_section = ScrapedPart(
                    section_type=SectionType.SECTION,
                    label=f"Section {section_num}",
                    content_text=section_text,
                    content_markdown=f"### Section {section_num}\n\n{section_text}" if section_text else f"### Section {section_num}",
                    sort_order=self._next_sort_order()
                )
                continue

            # Regular content - accumulate
            current_content.append(text)

        # Flush remaining content
        if current_content:
            self._flush_content(
                current_content, current_section, current_article, parts
            )

        # Save last section
        if current_section:
            if current_article:
                current_article.children.append(current_section)
            else:
                parts.append(current_section)

        # Save last article
        if current_article:
            parts.append(current_article)

        return parts

    def _flush_content(
        self,
        content: list[str],
        current_section: Optional[ScrapedPart],
        current_article: Optional[ScrapedPart],
        parts: list[ScrapedPart]
    ) -> None:
        """Flush accumulated content to appropriate parent."""
        if not content:
            return

        text = '\n'.join(content)
        paragraph = ScrapedPart(
            section_type=SectionType.PARAGRAPH,
            content_text=text,
            content_markdown=text,
            sort_order=self._next_sort_order()
        )

        if current_section:
            current_section.children.append(paragraph)
        elif current_article:
            current_article.children.append(paragraph)
        else:
            parts.append(paragraph)

    def _extract_tables(self, soup: BeautifulSoup) -> list[ScrapedPart]:
        """Extract all tables as ScrapedPart objects."""
        tables: list[ScrapedPart] = []

        for table in soup.find_all('table'):
            table_md = self._table_to_markdown(table)
            tables.append(ScrapedPart(
                section_type=SectionType.BODY,
                content_text=table.get_text(strip=True),
                content_markdown=table_md,
                content_html=str(table),
                sort_order=self._next_sort_order()
            ))

        return tables

    def _table_to_markdown(self, table: Tag) -> str:
        """Convert HTML table to Markdown."""
        rows = table.find_all('tr')
        if not rows:
            return ''

        md_lines = []

        for i, row in enumerate(rows):
            cells = row.find_all(['td', 'th'])
            cell_texts = [
                cell.get_text(strip=True).replace('|', '\\|')
                for cell in cells
            ]
            md_lines.append('| ' + ' | '.join(cell_texts) + ' |')

            if i == 0:
                md_lines.append('| ' + ' | '.join(['---'] * len(cells)) + ' |')

        return '\n'.join(md_lines)

    def _extract_dates(self, soup: BeautifulSoup, config: StatutePattern) -> dict:
        """Extract dates and parse them."""
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
                    dates[date_field] = self._parse_date(date_str)

        return dates

    def _parse_date(self, date_str: str) -> Optional[str]:
        """
        Parse Philippine date format to ISO string.
        Example: "June 19, 1946" -> "1946-06-19"
        """
        try:
            from dateutil.parser import parse
            parsed = parse(date_str)
            return parsed.date().isoformat()
        except:
            # Return raw string if parsing fails
            return date_str

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