from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from storage.repositories.statistics import StatisticsRepository
from api.dependencies import get_statistics_repository

from models.statistics import Statistics

from api.schemas.statistics import (
    StatisticsResponse,
    StatisticsCreate,
    StatisticsUpdate
)

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/", response_model=List[StatisticsResponse])
async def get_all_statistics(
    repo: StatisticsRepository = Depends(get_statistics_repository)
):
    stats = await repo.get_all()
    return [StatisticsResponse.model_validate(stat) for stat in stats]


@router.get("/{stat_id}", response_model=StatisticsResponse)
async def get_statistic(
    stat_id: UUID,
    repo: StatisticsRepository = Depends(get_statistics_repository)
):
    stat = await repo.get_by_id(stat_id)
    if not stat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Statistic not found")
    return StatisticsResponse.model_validate(stat)


@router.post("/", response_model=StatisticsResponse, status_code=status.HTTP_201_CREATED)
async def create_statistic(
    stat: StatisticsCreate,
    repo: StatisticsRepository = Depends(get_statistics_repository)
):
    stat_obj = Statistics(**stat.model_dump())
    created = await repo.create(stat_obj)
    return StatisticsResponse.model_validate(created)


@router.put("/{stat_id}", response_model=StatisticsResponse)
async def update_statistic(
    stat_id: UUID,
    update: StatisticsUpdate,
    repo: StatisticsRepository = Depends(get_statistics_repository)
):
    updated = await repo.update(stat_id, update.stat)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Statistic not found")
    return StatisticsResponse.model_validate(updated)


@router.delete("/{stat_id}", response_model=dict)
async def delete_statistic(
    stat_id: UUID,
    repo: StatisticsRepository = Depends(get_statistics_repository)
):
    deleted = await repo.delete(stat_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Statistic not found")
    return {"deleted": True}