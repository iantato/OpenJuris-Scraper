import re
from typing import Optional

from schemas.text_chunk import TextChunk

from config.embedder import EmbedderSettings

class TextChunker:
    """Service to split documents into chunks for embedding"""

    def __init__(self, settings: EmbedderSettings):
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.overlap

    def chunk_text(
        self,
        text: str,
        section_title: Optional[str] = None,
    ) -> list[TextChunk]:
        """Split text into overlapping chunks."""
        if not text or not text.strip():
            return []

        # Clean the text
        text = self._clean_text(text)

        # Try to split on sentence boundaries first
        sentences = self._split_sentences(text)
        chunks = self._merge_sentences_to_chunks(sentences)

        return [
            TextChunk(
                content=chunk["content"],
                index=i,
                start_char=chunk["start"],
                end_char=chunk["end"],
                section_title=section_title,
            )
            for i, chunk in enumerate(chunks)
        ]

    def chunk_document_parts(
        self,
        parts: list[dict],
    ) -> list[TextChunk]:
        """Chunk document parts (sections) individually."""
        all_chunks = []
        chunk_index = 0

        for part in parts:
            title = part.get("title")
            content = part.get("content", "")

            part_chunks = self.chunk_text(content, section_title=title)

            # Update global indices
            for chunk in part_chunks:
                chunk.index = chunk_index
                chunk_index += 1
                all_chunks.append(chunk)

        return all_chunks

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def _split_sentences(self, text: str) -> list[dict]:
        """Split text into sentences with positions."""
        # Simple sentence splitting - handles common legal citation patterns
        pattern = r'(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])\s*\n'

        sentences = []
        last_end = 0

        for match in re.finditer(pattern, text):
            sentence = text[last_end:match.start() + 1].strip()
            if sentence:
                sentences.append({
                    "content": sentence,
                    "start": last_end,
                    "end": match.start() + 1,
                })
            last_end = match.end()

        # Add remaining text
        if last_end < len(text):
            remaining = text[last_end:].strip()
            if remaining:
                sentences.append({
                    "content": remaining,
                    "start": last_end,
                    "end": len(text),
                })

        return sentences

    def _merge_sentences_to_chunks(
        self,
        sentences: list[dict],
    ) -> list[dict]:
        """Merge sentences into chunks of appropriate size."""
        if not sentences:
            return []

        chunks = []
        current_chunk = {
            "content": "",
            "start": sentences[0]["start"],
            "end": sentences[0]["end"],
        }

        for sentence in sentences:
            potential_content = (
                current_chunk["content"] + " " + sentence["content"]
                if current_chunk["content"]
                else sentence["content"]
            )

            if len(potential_content) <= self.chunk_size:
                current_chunk["content"] = potential_content.strip()
                current_chunk["end"] = sentence["end"]
            else:
                # Save current chunk if it has content
                if current_chunk["content"]:
                    chunks.append(current_chunk)

                # Start new chunk, potentially with overlap
                if chunks and self.chunk_overlap > 0:
                    # Get overlap from previous chunk
                    overlap_text = self._get_overlap_text(
                        chunks[-1]["content"],
                        self.chunk_overlap,
                    )
                    current_chunk = {
                        "content": overlap_text + " " + sentence["content"],
                        "start": sentence["start"],
                        "end": sentence["end"],
                    }
                else:
                    current_chunk = {
                        "content": sentence["content"],
                        "start": sentence["start"],
                        "end": sentence["end"],
                    }

        # Add final chunk
        if current_chunk["content"]:
            chunks.append(current_chunk)

        return chunks

    def _get_overlap_text(self, text: str, target_chars: int) -> str:
        """Get the last N characters of text, breaking at word boundary."""
        if len(text) <= target_chars:
            return text

        # Find word boundary
        overlap_start = len(text) - target_chars
        space_pos = text.find(' ', overlap_start)

        if space_pos != -1:
            return text[space_pos + 1:]
        return text[overlap_start:]