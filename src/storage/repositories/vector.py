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
        embedding_str = json.dumps(query_embedding)

        # Get raw connection from SQLAlchemy session
        conn = await self.session.connection()
        raw_conn = await conn.get_raw_connection()

        # aiolibsql execute returns cursor synchronously, but driver is async
        if document_id:
            cursor = raw_conn.execute(  # No await here
                """
                SELECT id, document_id, chunk_index, content, section_title,
                       vector_distance_cos(embedding, ?) as distance
                FROM document_vectors
                WHERE document_id = ?
                ORDER BY distance ASC
                LIMIT ?
                """,
                (embedding_str, str(document_id), limit)
            )
        else:
            cursor = raw_conn.execute(  # No await here
                """
                SELECT id, document_id, chunk_index, content, section_title,
                       vector_distance_cos(embedding, ?) as distance
                FROM document_vectors
                ORDER BY distance ASC
                LIMIT ?
                """,
                (embedding_str, limit)
            )

        # fetchall() is also synchronous
        rows = cursor.fetchall()

        results = []
        for row in rows:
            similarity = 1 - float(row[5])  # Convert distance to similarity
            if similarity >= threshold:
                results.append({
                    "id": str(row[0]),
                    "document_id": str(row[1]),
                    "chunk_index": int(row[2]),
                    "content": str(row[3]),
                    "section_title": str(row[4]) if row[4] else None,
                    "similarity": similarity,
                })

        return results

    async def get_by_document(self, document_id: UUID) -> Sequence[DocumentVector]:
        statement = (
            select(DocumentVector)
            .where(DocumentVector.document_id == document_id)
            .order_by(DocumentVector.chunk_index)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def delete_by_document(self, document_id: UUID) -> int:
        """Delete all vectors for a document."""
        statement = select(DocumentVector).where(
            DocumentVector.document_id == document_id
        )
        result = await self.session.execute(statement)
        vectors = result.scalars().all()

        for vector in vectors:
            await self.session.delete(vector)

        await self.session.commit()
        return len(vectors)