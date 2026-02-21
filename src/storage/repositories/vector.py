import json
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlmodel import select
from loguru import logger

from storage.repositories.base import BaseRepository
from models.vector import DocumentVector
from embedder.providers.base import BaseEmbedder


class VectorRepository(BaseRepository[DocumentVector]):
    """Repository for vector operations."""

    def __init__(self, session: AsyncSession, embedder: BaseEmbedder):
        super().__init__(session, DocumentVector)
        self.embedder = embedder

    async def create_vector(
        self,
        document_id: UUID,
        chunk_index: int,
        content: str,
        section_title: Optional[str] = None,
    ) -> DocumentVector:
        """Create a vector embedding for a document chunk."""
        embedding = await self.embedder.embed(content)

        vector = DocumentVector(
            document_id=document_id,
            chunk_index=chunk_index,
            content=content,
            section_title=section_title,
            embedding=embedding,
        )

        return await self.create(vector)

    async def create_vectors_batch(
        self,
        document_id: UUID,
        chunks: list[dict],
    ) -> list[DocumentVector]:
        """Create vector embeddings for multiple chunks."""
        if not chunks:
            return []

        contents = [chunk["content"] for chunk in chunks]
        embeddings = await self.embedder.embed_batch(contents)

        vectors = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            vector = DocumentVector(
                document_id=document_id,
                chunk_index=chunk.get("index", i),
                content=chunk["content"],
                section_title=chunk.get("section_title"),
                embedding=embedding,
            )
            self.session.add(vector)
            vectors.append(vector)

        await self.session.flush()

        for vector in vectors:
            await self.session.refresh(vector)

        return vectors

    async def search_similar(
        self,
        query: str,
        limit: int = 10,
        threshold: float = 0.7,
        document_id: Optional[UUID] = None,
    ) -> Sequence[dict]:
        """Search for similar vectors using cosine similarity."""
        query_embedding = await self.embedder.embed(query)
        embedding_json = json.dumps(query_embedding)

        if document_id:
            sql = text("""
                SELECT
                    id, document_id, chunk_index, content, section_title,
                    (1 - vector_distance_cos(embedding, vector(:query_embedding))) as similarity
                FROM document_vectors
                WHERE document_id = :doc_id
                AND (1 - vector_distance_cos(embedding, vector(:query_embedding))) >= :threshold
                ORDER BY similarity DESC
                LIMIT :limit
            """)
            params = {
                "query_embedding": embedding_json,
                "doc_id": str(document_id),
                "threshold": threshold,
                "limit": limit,
            }
        else:
            sql = text("""
                SELECT
                    id, document_id, chunk_index, content, section_title,
                    (1 - vector_distance_cos(embedding, vector(:query_embedding))) as similarity
                FROM document_vectors
                WHERE (1 - vector_distance_cos(embedding, vector(:query_embedding))) >= :threshold
                ORDER BY similarity DESC
                LIMIT :limit
            """)
            params = {
                "query_embedding": embedding_json,
                "threshold": threshold,
                "limit": limit,
            }

        result = await self.session.execute(sql, params)
        rows = result.fetchall()

        return [
            {
                "id": row.id,
                "document_id": row.document_id,
                "chunk_index": row.chunk_index,
                "content": row.content,
                "section_title": row.section_title,
                "similarity": row.similarity,
            }
            for row in rows
        ]

    async def get_by_document(self, document_id: UUID) -> Sequence[DocumentVector]:
        """Get all vectors for a document."""
        statement = (
            select(DocumentVector)
            .where(DocumentVector.document_id == document_id)
            .order_by(DocumentVector.chunk_index)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def delete_by_document(self, document_id: UUID) -> int:
        """Delete all vectors for a document."""
        from sqlalchemy import delete

        statement = delete(DocumentVector).where(
            DocumentVector.document_id == document_id
        )
        result = await self.session.execute(statement)
        await self.session.flush()
        return result.rowcount