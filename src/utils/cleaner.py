import ftfy

# Unicodes that may appear in the scraped HTML.
UNICODE_REPLACEMENTS = {
    '\u2026': '...',     # … ellipsis
    '\u2013': '-',       # – en dash
    '\u201c': '"',       # " left double quote
    '\u201d': '"',       # " right double quote
    '\u2018': "'",       # ' left single quote
    '\u2019': "'",       # ' right single quote
    '\xa0': ' ',         # non-breaking space
}

def _replace_unicode(text: str) -> str:
    for bad, good in UNICODE_REPLACEMENTS.items():
        text = text.replace(bad, good)

    return text

def clean_text(text: str) -> None:
    text = ftfy.fix_text(text)
    text = _replace_unicode(text)