from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_source_repository
from api.schemas.source import SourceCreate, SourceResponse

from models.source import Source

from storage.repositories.source import SourceRepository


router = APIRouter(prefix="/sources", tags=["Sources"])

@router.get("/", response_model=list[SourceResponse])
async def list_sources(
    repo: SourceRepository = Depends(get_source_repository),
):
    """List all sources."""
    sources = await repo.get_all()
    return [SourceResponse.model_validate(s) for s in sources]


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: UUID,
    repo: SourceRepository = Depends(get_source_repository),
):
    """Get a specific source."""
    source = await repo.get_by_id(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return SourceResponse.model_validate(source)


@router.post("/", response_model=SourceResponse, status_code=201)
async def create_source(
    data: SourceCreate,
    repo: SourceRepository = Depends(get_source_repository),
):
    """Create a new source."""
    # Check if already exists
    existing = await repo.get_by_name(data.name)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Source '{data.name.value}' already exists"
        )

    source = Source(
        name=data.name,
        short_code=data.short_code,
        base_url=data.base_url,
        type=data.type,
        description=data.description,
    )
    source = await repo.create(source)
    return SourceResponse.model_validate(source)


@router.delete("/{source_id}")
async def delete_source(
    source_id: UUID,
    repo: SourceRepository = Depends(get_source_repository),
):
    """Delete a source."""
    deleted = await repo.delete(source_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Source not found")
    return {"message": "Source deleted"}