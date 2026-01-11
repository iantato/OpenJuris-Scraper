from typing import Any

# Token types for the parsers.
TOKEN_HEADER = "header"
TOKEN_NEWLINE = "newline"
TOKEN_CONTENT = "content"
TOKEN_ITALIC = "italic"
TOKEN_BOLD = "bold"
TOKEN_TABLE = "table"

def make_token(content: Any, tag: str, token_type: str) -> None:
    return {
        "type": token_type,
        "content": content,
        "tag": tag,
    }