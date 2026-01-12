import re

import ftfy

# Unicodes that may appear in the scraped HTML.
UNICODE_REPLACEMENTS = {
    '\u2026': '...',     # … ellipsis
    '\u2013': '-',       # – en dash
    '\u2014': '-',       # — em dash
    '\u201c': '"',       # " left double quote
    '\u201d': '"',       # " right double quote
    '\u2018': "'",       # ' left single quote
    '\u2019': "'",       # ' right single quote
    '\xa0': ' ',         # non-breaking space
    '\u200b': '',        # zero-width space
    '\u200c': '',        # zero-width non-joiner
    '\u200d': '',        # zero-width joiner
    '\ufeff': '',        # BOM
}

def _replace_unicode(text: str) -> str:
    for bad, good in UNICODE_REPLACEMENTS.items():
        text = text.replace(bad, good)

    return text

def _fix_broken_list_markers(text: str) -> str:
    """Fix broken list markers like 'a)' to '(a)' or '(a' to '(a)'."""

    # Fix stray characters after letter in marker: "(f0" -> "(f)", "(a1" -> "(a)"
    # Matches: (a0, (b1, (c2, etc. where a digit follows the letter incorrectly
    text = re.sub(r'\(([a-zA-Z])[0-9]+\)', r'(\1)', text)  # with closing paren
    text = re.sub(r'\(([a-zA-Z])[0-9]+(?=\s|$)', r'(\1)', text)  # without closing paren

    # Fix missing opening parenthesis: "a)" -> "(a)" at start of line or after newline
    # Matches: a), b), c), ... z), A), B), ... Z), 1), 2), etc.
    text = re.sub(r'(^|\n)([a-zA-Z0-9])\)', r'\1(\2)', text)

    # Fix missing closing parenthesis: "(a" -> "(a)" when followed by space/content
    # Matches: (a , (b , (1 , etc.
    text = re.sub(r'\(([a-zA-Z0-9])(?=\s)', r'(\1)', text)

    # Fix missing opening parenthesis mid-line (after space): " a)" -> " (a)"
    text = re.sub(r'(\s)([a-zA-Z0-9])\)', r'\1(\2)', text)

    return text

def _normalize_ellipsis(text: str) -> str:
    # Match dots separated by spaces: ". . . . ." -> "..."
    text = re.sub(r'(\.\s*){3,}', '...', text)

   # Multiple consecutive dots: "......" -> "..."
    text = re.sub(r'\.{3,}', '...', text)

    return text

def _normalize_space(text: str) -> str:
    return re.sub(r" +", " ", text)

def clean_text(text: str) -> None:
    text = ftfy.fix_text(text)
    text = _replace_unicode(text)
    text = _normalize_ellipsis(text)
    text = _normalize_space(text)
    text = _fix_broken_list_markers(text)

    return text