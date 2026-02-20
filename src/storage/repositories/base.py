from uuid import UUID
from typing import Generic, TypeVar, Optional, Sequence

from sqlmodel import SQLModel, select
from sqlalchemy.ext.asyncio.session import AsyncSession

T = TypeVar("T", bound=SQLModel)

class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations."""

    def __init__(self, session: AsyncSession, model: type[T]):
        self.session = session
        self.model = model

    async def get_by_id(self, id: UUID) -> Optional[T]:
        """
        Get a single record by ID.

        Args:
            id (UUID): The UUID of the specific data/row.

        Returns:
            Optional[SQLModel]: The SQLModel entity/document with that specific uuid.
        """
        return await self.session.get(self.model, id)

    async def get_all(self, limit: int = 100, offset: int = 0) -> Sequence[T]:
        """Get all records with pagination."""
        statement = select(self.model).offset(offset).limit(limit)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def create(self, obj: T) -> T:
        """Create a new record."""
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: T) -> T:
        """Update an existing record."""
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id: UUID) -> bool:
        """Delete a record by ID."""
        obj = await self.get_by_id(id)
        if obj:
            await self.session.delete(obj)
            await self.session.flush()
            return True
        return False