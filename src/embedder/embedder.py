from uuid import UUID
from typing import Optional

from loguru import logger
from sqlalchemy.ext.asyncio.session import AsyncSession

from embedder.providers.base import BaseEmbedder
from embedder.text_chunker import TextChunker

from schemas.scraped_document import ScrapedDocument

from models.vector import DocumentVector

from config.embedder import EmbedderSettings

class EmbeddingService:
    """Service to handle document embedding operations."""

    def __init__(self, embedder: BaseEmbedder, settings: EmbedderSettings):
        self.embedder = embedder
        self.settings = settings
        self.chunker = TextChunker(settings)

    async def embed_scraped_document(
        self,
        document: ScrapedDocument,
        document_id: UUID,
        session: AsyncSession,
    ) -> list[DocumentVector]:
        """
        Embed a scraped document and store vectors in the database.

        Args:
            document: The scraped document to embed
            document_id: The UUID of the saved Document
            session: Database session for storing vectors

        Returns:
            List of created DocumentVector records
        """
        # Get the full markdown content
        content = document.content_markdown or ""
        if not content:
            # Fallback to combining parts
            content = self._extract_text_from_parts(document)

        if not content.strip():
            logger.warning(f"No content to embed for document {document_id}")
            return []

        # Chunk the content
        chunks = self.chunker.chunk_text(content)

        if not chunks:
            logger.warning(f"No chunks generated for document {document_id}")
            return []

        logger.info(f"Embedding {len(chunks)} chunks for document {document_id}")

        # Generate embeddings in batch
        chunk_texts = [chunk.content for chunk in chunks]
        embeddings = await self.embedder.embed_batch(chunk_texts)

        # Create vector records
        vectors = []
        for chunk, embedding in zip(chunks, embeddings):
            vector = DocumentVector(
                document_id=document_id,
                chunk_index=chunk.index,
                content=chunk.content,
                section_title=chunk.section_title,
                embedding=embedding,
            )
            session.add(vector)
            vectors.append(vector)

        await session.flush()

        logger.info(f"Created {len(vectors)} vectors for document {document_id}")
        return vectors

    async def embed_text(self, text: str) -> list[float]:
        """Embed a single text string."""
        return await self.embedder.embed(text)

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple text strings."""
        return await self.embedder.embed_batch(texts)

    async def embed_document_by_id(
        self,
        document_id: UUID,
        content: str,
        session: AsyncSession,
        section_title: Optional[str] = None,
    ) -> list[DocumentVector]:
        """
        Embed content for an existing document by ID.

        Args:
            document_id: The document UUID
            content: Text content to embed
            session: Database session
            section_title: Optional section title for all chunks

        Returns:
            List of created DocumentVector records
        """
        chunks = self.chunker.chunk_text(content, section_title=section_title)

        if not chunks:
            return []

        chunk_texts = [chunk.content for chunk in chunks]
        embeddings = await self.embedder.embed_batch(chunk_texts)

        vectors = []
        for chunk, embedding in zip(chunks, embeddings):
            vector = DocumentVector(
                document_id=document_id,
                chunk_index=chunk.index,
                content=chunk.content,
                section_title=chunk.section_title,
                embedding=embedding,
            )
            session.add(vector)
            vectors.append(vector)

        await session.flush()
        return vectors

    def _extract_text_from_parts(self, document: ScrapedDocument) -> str:
        """Extract text content from document parts."""
        texts = []
        for part in document.parts:
            if part.content_markdown:
                texts.append(part.content_markdown)
            elif part.content_text:
                texts.append(part.content_text)

            # Recursively get children
            texts.extend(self._extract_text_from_children(part.children))

        return "\n\n".join(texts)

    def _extract_text_from_children(self, children: list) -> list[str]:
        """Recursively extract text from child parts."""
        texts = []
        for child in children:
            if child.content_markdown:
                texts.append(child.content_markdown)
            elif child.content_text:
                texts.append(child.content_text)

            if child.children:
                texts.extend(self._extract_text_from_children(child.children))

        return texts