"""Settings API — user preference endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.responses import Envelope

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])

DEFAULT_PRIORITY_SETTINGS = {"high": 30, "medium": 60, "low": 180}


class PrioritySettingsInput(BaseModel):
    high: int
    medium: int
    low: int

    @field_validator("high", "medium", "low")
    @classmethod
    def validate_range(cls, v: int) -> int:
        if v < 7 or v > 365:
            raise ValueError("Interval must be between 7 and 365 days")
        return v


class PrioritySettingsData(BaseModel):
    high: int
    medium: int
    low: int


def get_priority_settings(user: User) -> dict:
    """Return priority settings with defaults fallback."""
    if user.priority_settings:
        return {**DEFAULT_PRIORITY_SETTINGS, **user.priority_settings}
    return dict(DEFAULT_PRIORITY_SETTINGS)


@router.get("/priority", response_model=Envelope[PrioritySettingsData])
async def get_priority(
    current_user: User = Depends(get_current_user),
) -> Envelope[PrioritySettingsData]:
    settings = get_priority_settings(current_user)
    return {"data": settings, "error": None}


@router.put("/priority", response_model=Envelope[PrioritySettingsData])
async def update_priority(
    body: PrioritySettingsInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Envelope[PrioritySettingsData]:
    current_user.priority_settings = body.model_dump()
    await db.flush()
    await db.refresh(current_user)
    settings = get_priority_settings(current_user)
    return {"data": settings, "error": None}
