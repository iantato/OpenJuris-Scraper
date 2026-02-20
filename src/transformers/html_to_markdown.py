import re
from typing import Optional
from bs4 import BeautifulSoup, Tag, NavigableString


class HtmlToMarkdown:
    """Convert HTML elements to Markdown formatting."""

    def convert(self, html: str) -> str:
        """
        Convert HTML string to Markdown.

        Args:
            html: HTML string to convert

        Returns:
            Markdown formatted string
        """
        if not html:
            return ""

        soup = BeautifulSoup(html, "html.parser")
        return self._process_element(soup).strip()

    def convert_element(self, element: Tag) -> str:
        """
        Convert a BeautifulSoup element to Markdown.

        Args:
            element: BeautifulSoup Tag element

        Returns:
            Markdown formatted string
        """
        if element is None:
            return ""
        return self._process_element(element).strip()

    def _process_element(self, element) -> str:
        """Recursively process an element and its children."""
        if isinstance(element, NavigableString):
            text = str(element)
            # Normalize whitespace but preserve single spaces
            text = re.sub(r'\s+', ' ', text)
            return text

        if not isinstance(element, Tag):
            return ""

        # Get tag name
        tag = element.name.lower() if element.name else ""

        # Process children first
        children_text = ""
        for child in element.children:
            children_text += self._process_element(child)

        # Apply formatting based on tag
        if tag in ('b', 'strong'):
            return f"**{children_text.strip()}**" if children_text.strip() else ""

        elif tag in ('i', 'em'):
            return f"*{children_text.strip()}*" if children_text.strip() else ""

        elif tag in ('u', 'ins'):
            # Markdown doesn't have native underline, use HTML or emphasis
            return f"_{children_text.strip()}_" if children_text.strip() else ""

        elif tag in ('s', 'strike', 'del'):
            return f"~~{children_text.strip()}~~" if children_text.strip() else ""

        elif tag == 'sup':
            return f"^{children_text.strip()}^" if children_text.strip() else ""

        elif tag == 'sub':
            return f"~{children_text.strip()}~" if children_text.strip() else ""

        elif tag == 'code':
            return f"`{children_text.strip()}`" if children_text.strip() else ""

        elif tag == 'pre':
            return f"```\n{children_text.strip()}\n```" if children_text.strip() else ""

        elif tag == 'a':
            href = element.get('href', '')
            text = children_text.strip() or href
            return f"[{text}]({href})" if href else text

        elif tag == 'br':
            return "\n"

        elif tag == 'hr':
            return "\n---\n"

        elif tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            level = int(tag[1])
            prefix = '#' * level
            return f"\n{prefix} {children_text.strip()}\n" if children_text.strip() else ""

        elif tag == 'p':
            return f"\n{children_text.strip()}\n" if children_text.strip() else "\n"

        elif tag == 'blockquote':
            lines = children_text.strip().split('\n')
            quoted = '\n'.join(f"> {line}" for line in lines)
            return f"\n{quoted}\n"

        elif tag == 'ul':
            return f"\n{children_text}\n"

        elif tag == 'ol':
            return f"\n{children_text}\n"

        elif tag == 'li':
            # Check parent to determine list type
            parent = element.parent
            if parent and parent.name == 'ol':
                # Get index
                siblings = list(parent.find_all('li', recursive=False))
                try:
                    idx = siblings.index(element) + 1
                except ValueError:
                    idx = 1
                return f"{idx}. {children_text.strip()}\n"
            else:
                return f"- {children_text.strip()}\n"

        elif tag == 'img':
            alt = element.get('alt', '')
            src = element.get('src', '')
            return f"![{alt}]({src})"

        elif tag in ('div', 'span', 'font', 'center'):
            # Pass through content
            return children_text

        elif tag in ('table', 'thead', 'tbody', 'tfoot'):
            # Tables are handled separately
            return children_text

        elif tag == 'tr':
            return children_text + "\n"

        elif tag in ('td', 'th'):
            return children_text.strip() + " | "

        else:
            # Default: just return children text
            return children_text

    def clean_text(self, text: str) -> str:
        """
        Clean up markdown text by fixing common issues.

        Args:
            text: Markdown text to clean

        Returns:
            Cleaned markdown text
        """
        if not text:
            return ""

        # Fix multiple consecutive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Fix spaces around bold/italic markers
        text = re.sub(r'\*\*\s+', '**', text)
        text = re.sub(r'\s+\*\*', '**', text)
        text = re.sub(r'\*\s+', '*', text)
        text = re.sub(r'\s+\*', '*', text)

        # Remove empty formatting
        text = re.sub(r'\*\*\*\*', '', text)
        text = re.sub(r'\*\*', '', text.count('**') % 2 and text or text)

        # Normalize spaces
        text = re.sub(r' +', ' ', text)

        return text.strip()