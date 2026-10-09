from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.exceptions import NotFoundException
from app.models.domain import User
from app.models.subscription import SavedSearch, SearchAlert
from app.services.limits_service import LimitsService
from app.services.subscription_service import SubscriptionService


router = APIRouter(prefix="/me", tags=["Account"])

class SavedSearchCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    time_range_days: int = 180
    platforms: List[str] = []
    min_confidence: float = 0.68
    biometric_type: str = "face"


class AlertCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    saved_search_id: Optional[str] = None
    min_confidence: float = 0.75
    platforms: List[str] = []
    notify_email: bool = True
    notify_push: bool = True

@router.get("/overview")
async def get_account_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    limits_service = LimitsService(db)
    sub_service = SubscriptionService(db)

    subscription = await sub_service.get_subscription_summary(current_user)

    capabilities = await limits_service.get_user_capabilities(current_user)

    return {
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "username": current_user.username,
            "full_name": current_user.full_name,
            "avatar_url": current_user.avatar_url,
            "role": current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role),
            "is_premium": current_user.is_premium,
        },
        "subscription": subscription,
        "capabilities": capabilities,
    }


@router.get("/usage")
async def get_my_usage(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    service = LimitsService(db)
    return await service.get_usage_summary(str(current_user.id))

@router.get("/saved-searches")
async def list_saved_searches(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    stmt = (
        select(SavedSearch)
        .where(SavedSearch.user_id == current_user.id)
        .order_by(desc(SavedSearch.created_at))
    )
    result = await db.execute(stmt)
    searches = result.scalars().all()

    return [
        {
            "id": str(s.id),
            "name": s.name,
            "description": s.description,
            "time_range_days": s.time_range_days,
            "platforms": s.platforms,
            "min_confidence": s.min_confidence,
            "times_run": s.times_run,
            "last_run_at": s.last_run_at.isoformat() if s.last_run_at else None,
            "created_at": s.created_at.isoformat(),
        }
        for s in searches
    ]


@router.post("/saved-searches")
async def create_saved_search(
    data: SavedSearchCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    service = LimitsService(db)
    allowed, remaining = await service.check_saved_search_limit(current_user)

    if not allowed:
        raise HTTPException(
            status_code=403,
            detail=f"Saved search limit reached ({remaining})",
        )

    saved = SavedSearch(
        user_id=current_user.id,
        name=data.name,
        description=data.description,
        time_range_days=data.time_range_days,
        platforms=data.platforms,
        min_confidence=data.min_confidence,
        biometric_type=data.biometric_type,
    )
    db.add(saved)
    await db.commit()
    await db.refresh(saved)

    return {
        "id": str(saved.id),
        "name": saved.name,
        "created_at": saved.created_at.isoformat(),
    }


@router.delete("/saved-searches/{search_id}")
async def delete_saved_search(
    search_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    stmt = select(SavedSearch).where(
        SavedSearch.id == search_id,
        SavedSearch.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    saved = result.scalar_one_or_none()

    if not saved:
        raise NotFoundException(message="Saved search not found")

    await db.delete(saved)
    await db.commit()

    return {"message": "Deleted"}


@router.get("/alerts")
async def list_alerts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    stmt = (
        select(SearchAlert)
        .where(SearchAlert.user_id == current_user.id)
        .order_by(desc(SearchAlert.created_at))
    )
    result = await db.execute(stmt)
    alerts = result.scalars().all()

    return [
        {
            "id": str(a.id),
            "name": a.name,
            "saved_search_id": str(a.saved_search_id) if a.saved_search_id else None,
            "min_confidence": a.min_confidence,
            "notify_email": a.notify_email,
            "notify_push": a.notify_push,
            "is_active": a.is_active,
            "trigger_count": a.trigger_count,
            "last_triggered_at": (
                a.last_triggered_at.isoformat() if a.last_triggered_at else None
            ),
            "created_at": a.created_at.isoformat(),
        }
        for a in alerts
    ]


@router.post("/alerts")
async def create_alert(
    data: AlertCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    service = LimitsService(db)
    has_alerts = await service.check_feature(current_user, "alerts_enabled")

    if not has_alerts:
        raise HTTPException(
            status_code=403,
            detail="Alerts require Pro tier or higher",
        )

    alert = SearchAlert(
        user_id=current_user.id,
        saved_search_id=data.saved_search_id,
        name=data.name,
        min_confidence=data.min_confidence,
        platforms=data.platforms,
        notify_email=data.notify_email,
        notify_push=data.notify_push,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    return {
        "id": str(alert.id),
        "name": alert.name,
        "is_active": alert.is_active,
        "created_at": alert.created_at.isoformat(),
    }


@router.delete("/alerts/{alert_id}")
async def delete_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    stmt = select(SearchAlert).where(
        SearchAlert.id == alert_id,
        SearchAlert.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    alert = result.scalar_one_or_none()

    if not alert:
        raise NotFoundException(message="Alert not found")

    await db.delete(alert)
    await db.commit()

    return {"message": "Deleted"}