from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from storage.repositories.document_flags import DocumentFlagsRepository
from api.dependencies import get_session
from sqlalchemy.ext.asyncio import AsyncSession

from models.document_flags import DocumentFlags

from api.schemas.document_flags import (
    DocumentFlagsCreate,
    DocumentFlagsResponse
)

router = APIRouter(prefix="/document-flags", tags=["DocumentFlags"])

@router.get("/", response_model=List[DocumentFlagsResponse])
async def get_all_flags(
    session: AsyncSession = Depends(get_session)
):
    repo = DocumentFlagsRepository(session)
    flags = await repo.get_all()
    return [DocumentFlagsResponse.model_validate(flag) for flag in flags]

@router.get("/document/{document_id}", response_model=List[DocumentFlagsResponse])
async def get_flags_by_document(
    document_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    repo = DocumentFlagsRepository(session)
    flags = await repo.get_by_document(document_id)
    return [DocumentFlagsResponse.model_validate(flag) for flag in flags]

@router.post("/", response_model=DocumentFlagsResponse, status_code=status.HTTP_201_CREATED)
async def create_flag(
    flag: DocumentFlagsCreate,
    session: AsyncSession = Depends(get_session)
):
    repo = DocumentFlagsRepository(session)
    flag_obj = DocumentFlags(**flag.model_dump())
    created = await repo.create(flag_obj)
    return DocumentFlagsResponse.model_validate(created)

@router.delete("/{flag_id}", response_model=dict)
async def delete_flag(
    flag_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    repo = DocumentFlagsRepository(session)
    deleted = await repo.delete(flag_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flag not found")
    return {"deleted": True}