from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.tiers import get_all_tier_info
from app.models.domain import User
from app.services.subscription_service import SubscriptionService
from app.services.limits_service import LimitsService


router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])

@router.get("/tiers")
async def list_tiers() -> List[Dict[str,Any]]:
    return get_all_tier_info()

@router.get("/me")
async def get_my_subscriptions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:

    service = SubscriptionService(db)
    return await service.get_subscription_summary(current_user)

@router.get("/capabilities")
async def get_my_capabilities(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str,Any]:

    limits_service = LimitsService(db)
    tier = await limits_service.get_user_tier(current_user)
    limits = await limits_service.get_user_limits(current_user)
    daily = await limits_service.get_or_create_usage(current_user.id, "daily")
    monthly = await limits_service.get_or_create_usage(current_user.id, "monthly")
    return {
        "tier": tier.value,
        "limits": limits,
        "daily_usage": {
            "current": daily.current,
            "daily": daily.quota,
            "next_reset": daily.next_reset.isoformat() if daily.next_reset else None,
            "quota_percentage": daily.get_quota_percentage(),
        },
        "monthly_usage": {
            "current": monthly.current,
            "monthly": monthly.quota,
            "next_reset": monthly.next_reset.isoformat() if monthly.next_reset else None,
            "quota_percentage": monthly.get_quota_percentage(),
        },
        "available_features": limits_service.get_available_features(tier),
    }

@router.get("/stats")
async def get_subscription_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str,Any]]:
    
    service = SubscriptionService(db)
    stats = await service.get_subscription_stats()
    return stats

@router.get("/upgrade-options")
async def get_upgrade_options(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:

    service = SubscriptionService(db)
    return await service.get_upgrade_options(current_user)

@router.get("/trial/eligible")
async def check_trial_eligibility(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:

    service = SubscriptionService(db)
    return await service.is_eligible_for_trial(current_user)