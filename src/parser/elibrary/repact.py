from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup

from utils.tokens import make_token
from utils.tokens import (TOKEN_NEWLINE, TOKEN_CONTENT, TOKEN_HEADER,
                          TOKEN_ITALIC, TOKEN_BOLD, TOKEN_TABLE)
from utils.cleaner import clean_text, clean_table

class RepublicActTokenizer:
    def __init__(self):
        pass

    def _get_children(self, element: BeautifulSoup) -> list[BeautifulSoup]:
        return [i for i in element.children]

    def metadata(self, soup: BeautifulSoup) -> dict[str, str]:

        # The Republic Act Number (e.g. Republic Act No. 1) and the Date are normally enclosed
        # within the <h2>...</h2> tags. It is normally within a format of [ REPUBLIC ACT... ]
        # hence we remove the brackets ([ ]).
        number_and_date = soup.find("h2").get_text().replace("[", "").replace("]", "").split(",")

        # The title of the Republic Act is normally enclosed after the <h2>...</h2> tags and
        # instead are in the <h3>...</h3> tags.
        title = soup.find("h3").get_text().strip()

        return {
            "document_type": "Republic Act",
            "ra_no": "".join([char for char in number_and_date[0].title().strip() if char.isdigit()]),
            "ra_title": " ".join(filter(None, title.split())).title(),
            "approved_date": ",".join(number_and_date[1:]).strip(),
            "source": "Supreme Court E-Library"
        }

    def _is_centered(self, element: BeautifulSoup) -> None:

        # To reduce \n and empty strings.
        if not hasattr(element, "name") or element.name is None:
            return False

        # If the tag is <center>.
        if element.name == "center":
            return True

        # If the tag is something else but instead has
        # an alignment of center e.g. <p align="center">.
        align = element.get("align", "")
        if "center" in align.lower():
            return True

        # If the tag is something else but instead
        # has a text-alignment of center e.g.
        # <p style="text-align: center;".
        style = element.get("style", "")
        if "text-align" in style.lower() and "center" in style.lower():
            return True

        return False

    def _get_list_marker(self, ol_type: str, index: int) -> str:
        match ol_type:
            case "a":
                # Lowercase letters: (a), (b), (c), ...
                return f"({chr(ord('a') + index)})"
            case "A":
                # Uppercase letters: (A), (B), (C), ...
                return f"({chr(ord('A') + index)})"
            case "i":
                # Lowercase roman numerals
                numerals = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"]
                return f"({numerals[index] if index < len(numerals) else index + 1})"
            case "I":
                # Uppercase roman numerals
                numerals = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
                return f"({numerals[index] if index < len(numerals) else index + 1})"
            case _:
                # Default numeric: (1), (2), (3), ...
                return f"({index + 1})"

    def process_html_blocks(self, children: Optional[list[BeautifulSoup]] = None, soup: Optional[BeautifulSoup] = None,
                            recursion: Optional[bool] = False) -> list[dict[str, str]]:
        # The <center>...</center> tag normally holds the Republic Act title and
        # is followed by two <br> tags before the actual content. We only get this
        # element if we're only just starting the processing and not when recursively
        # processing other elements.
        if not recursion:
            starting_element = soup.find("center")
            children = starting_element.next_siblings

        tokens = []
        for element in children:
            tag = element.name

            if not element:
                continue

            # If the tag is a <br/>, we add a newline token.
            if tag == "br":
                tokens.append(make_token("\n", tag, TOKEN_NEWLINE))

            # If the text is centered in the HTML file. There are a few
            # ways they center a text hence we use an internal function
            # to check whether a text has been centered. It usually means
            # it's a sub-header if the text was centered.
            elif self._is_centered(element):
                text = element.get_text(separator=" ", strip=True)
                tokens += [make_token(text, tag, TOKEN_HEADER), make_token("\n", None, TOKEN_NEWLINE)]

            # If the tag is in one of the following containers, we need
            # to re-process it as normally it has other contents and
            # elements inside of it.
            if tag in ("div", "blockquote", "p", "font"):
                tokens += self.process_html_blocks(self._get_children(element), recursion=True)

            # If the tag is a <table> container, usually it contains
            # a bunch of rows and columns but it is completely unsure
            # as to what other table looks like apart from the reference
            # of "Republic Act 1".
            elif tag == "table":
                rows = element.find_all("tr")
                table_data = []

                # Get the text of all the rows.
                for row in rows:
                    cells = row.find_all(["td", "th"])
                    row_data = []

                    for cell in cells:
                        cell_tokens = self.process_html_blocks(self._get_children(cell), recursion=True)
                        # Get all the text that is inside
                        cell_text = "".join(token["content"] for token in cell_tokens if token["type"] != TOKEN_NEWLINE)
                        row_data.append(cell_text)

                    if row_data:
                        table_data.append(row_data)

                # Create tokenized table data using a 2D list (e.g. [["a", "b"], ["c", "d"]]).
                if table_data:
                    tokens.append(make_token(table_data, tag, TOKEN_TABLE))

            # If the tag is <ol>, which does not include the marker/numbering
            # when parsing it normally. Thus, we get the type of the markers and
            # then re-place it back to the content.
            elif tag == "ol":
                ol_type = element.get("type", "1")
                items = element.find_all("li")

                for idx, item in enumerate(items):
                    marker = self._get_list_marker(ol_type, idx)

                    item_content = self.process_html_blocks(self._get_children(item))
                    if item_content:
                        item_content["content"] = f"{marker} {item_content[0]['content']}"

                    tokens += item_content + [make_token("\n", None, TOKEN_NEWLINE)]

            # If the tag is an <i> which means italic text.
            elif tag == "i" or tag == "em":
                text = element.get_text(strip=True)
                tokens.append(make_token(text, tag, TOKEN_ITALIC))

            # If the tag is a <b> which means bold text.
            elif tag == "b":
                text = element.get_text(separator=" ", strip=True)
                tokens.append(make_token(text, tag, TOKEN_BOLD))

            elif tag in ("span", "font"):
                tokens += self.process_html_blocks(self._get_children(element), recursion=True)

            # Edge case to collect text from the container if there is nothing else we can do.
            elif hasattr(element, "get_text"):
                text = element.get_text(separator=" ", strip=True)
                tokens += [make_token(text, None, TOKEN_CONTENT), make_token("\n", None, TOKEN_NEWLINE)]

            # Another edge case to collect text if "get_text" is not available
            # and the element is a string.
            elif isinstance(element, str) and element.strip():
                text = element.strip()
                tokens += [make_token(text, None, TOKEN_CONTENT), make_token("\n", None, TOKEN_NEWLINE)]

        return tokens

    def clean_tokens(self, tokens: list[dict[str, str]], max_consecutive: Optional[int] = 1) -> list[dict[str, str]]:
        consecutive_newlines = 0

        cleaned_tokens = []
        for token in tokens:

            # Skip empty content.
            if not token["content"]:
                continue

            # Removes the empty rows by checking
            # whether the list just contains a bunch of
            # empty strings ("").
            if token["type"] == TOKEN_TABLE:
                table_data = token["content"]
                new_table_data = []

                for data in table_data:
                    if "".join(data).strip():
                        new_table_data.append(data)

                token["content"] = new_table_data

            # Clean the content text to iron out any sort
            # of buggy formatting or strings.
            if token["type"] is not TOKEN_TABLE:
                token["content"] = clean_text(token["content"])
            else:
                token["content"] = clean_table(token["content"])

            # Each time there are consecutive newlines ("\n"),
            # we increase the newline counter until the
            # maximum amount that we allow. Otherwise, the
            # counter goes back to 0 if we are no longer
            # within a newline chain.
            if token["type"] == TOKEN_NEWLINE:
                consecutive_newlines += 1

                if consecutive_newlines <= max_consecutive:
                    cleaned_tokens.append(token)
            else:
                consecutive_newlines = 0
                cleaned_tokens.append(token)

        return cleaned_tokens

    def tokenize(self, file: Path) -> None:
        html_content = file.read_text(encoding="utf-8")
        soup = BeautifulSoup(html_content, "html.parser")

        content = {
            "metadata": self.metadata(soup),
            "blocks": self.process_html_blocks(soup=soup)
        }

        content["blocks"] = self.clean_tokens(content["blocks"])

        return content