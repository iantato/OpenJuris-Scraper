from uuid import UUID
from typing import Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from config.embedder import EmbedderSettings
from embedder.providers.base import BaseEmbedder
from embedder.text_chunker import TextChunker
from embedder.factory import get_embedder

from schemas.scraped_document import ScrapedDocument

from models.vector import DocumentVector

from storage.repositories.vector import VectorRepository
from storage.repositories.document import DocumentRepository


class EmbedService:
    """Service to handle document embedding operations."""

    def __init__(
        self,
        session: AsyncSession,
        embedder: BaseEmbedder,
        settings: EmbedderSettings
    ):
        self.session = session
        self.embedder = embedder
        self.settings = settings
        self.chunker = TextChunker(settings)

    async def embed_text(self, text: str) -> list[float]:
        """Embed a single text string."""
        return await self.embedder.embed(text)

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple text strings."""
        return await self.embedder.embed_batch(texts)

    async def embed_scraped_document(
        self,
        document: ScrapedDocument,
        document_id: UUID,
    ) -> list[DocumentVector]:
        """
        Embed a scraped document and store vectors in the database.

        Args:
            document: The scraped document to embed
            document_id: The UUID of the saved Document

        Returns:
            List of created DocumentVector records
        """
        content = document.content_markdown or ""
        if not content:
            content = self._extract_text_from_parts(document)

        if not content.strip():
            logger.warning(f"No content to embed for document {document_id}")
            return []

        chunks = self.chunker.chunk_text(content)

        if not chunks:
            logger.warning(f"No chunks generated for document {document_id}")
            return []

        logger.info(f"Embedding {len(chunks)} chunks for document {document_id}")

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
            self.session.add(vector)
            vectors.append(vector)

        await self.session.flush()

        logger.info(f"Created {len(vectors)} vectors for document {document_id}")
        return vectors

    async def embed_document_by_id(
        self,
        document_id: UUID,
        content: str,
        section_title: Optional[str] = None,
        force: bool = False,
    ) -> list[DocumentVector]:
        """
        Embed content for an existing document by ID.

        Args:
            document_id: The document UUID
            content: Text content to embed
            section_title: Optional section title for all chunks
            force: If True, delete existing vectors and re-embed

        Returns:
            List of created DocumentVector records
        """
        vector_repo = VectorRepository(self.session, self.embedder)

        # Check for existing vectors
        existing = await vector_repo.get_by_document(document_id)
        if existing and not force:
            logger.info(f"Document {document_id} already has {len(existing)} vectors")
            return existing

        # Delete existing if forcing re-embed
        if existing and force:
            await vector_repo.delete_by_document(document_id)
            logger.info(f"Deleted {len(existing)} existing vectors for document {document_id}")

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
            self.session.add(vector)
            vectors.append(vector)

        await self.session.flush()
        return vectors

    async def search_similar(
        self,
        query: str,
        limit: int = 10,
        threshold: float = 0.7,
        document_id: Optional[UUID] = None,
    ) -> list[dict]:
        """
        Search for similar document chunks.

        Args:
            query: Search query text
            limit: Maximum number of results
            threshold: Minimum similarity threshold
            document_id: Optional filter by specific document

        Returns:
            List of similar chunks with similarity scores
        """
        vector_repo = VectorRepository(self.session, self.embedder)
        return await vector_repo.search_similar(
            query=query,
            limit=limit,
            threshold=threshold,
            document_id=document_id,
        )

    async def get_document_vectors(self, document_id: UUID) -> list[DocumentVector]:
        """Get all vectors for a document."""
        vector_repo = VectorRepository(self.session, self.embedder)
        return await vector_repo.get_by_document(document_id)

    async def delete_document_vectors(self, document_id: UUID) -> int:
        """Delete all vectors for a document."""
        vector_repo = VectorRepository(self.session, self.embedder)
        return await vector_repo.delete_by_document(document_id)

    def _extract_text_from_parts(self, document: ScrapedDocument) -> str:
        """Extract text content from document parts."""
        texts = []
        for part in document.parts:
            if part.content_markdown:
                texts.append(part.content_markdown)
            elif part.content_text:
                texts.append(part.content_text)

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