from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.domain import User
from app.services.rewards_service import RewardsService
from app.services.stripe_service import StripeService


router = APIRouter(prefix="/rewards", tags=["Rewards"])

class PayoutRequest(BaseModel):
    amount:Optional[float] = Field(None,gt=0)

@router.get("/balance")
async def get_balance(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, float]:
    return await RewardsService.get_or_create_balance(db=db, user=user)

@router.get("/ledger")
async def get_ledger(
    user: User = Depends(get_current_user),
    limit:Optional[int]=50,
    offset:Optional[int]=0,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, float]:
    return await RewardsService.get_ledger( user=user,limit=limit,offset=offset)

@router.get("/earnings")
async def get_earnings(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, float]:
    return await RewardsService.get_earnings_summary( user=user)

@router.post("/confirm-pending")
async def confirm_pending_rewards(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, float]:
    return await RewardsService.confirm_pending(db=db, user_id=str(user.id))

@router.post("/connect/onboarding")
async def start_connect_onboarding(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, float]:
    service = StripeService(db=db)
    url = await service.create_connect_onboarding_link(
        user=user,
        return_url=f"{settings.FRONTEND_URL}/rewards/connect/success",
        refresh_url=f"{settings.FRONTEND_URL}/rewards/connect/refresh"
    )
    return {"onboarding_url": url}

@router.get("/connect/status")
async def get_connect_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, float]:
    service = RewardsService(db=db)
    balance = await service.get_or_create_balance(user)
    return{
        "has_account": bool(balance.stripe_account_id),
        "account_id": balance.stripe_account_id,
        "account_status": balance.stripe_account_status,
        "onboarding_complete": balance.stripe_onboarding_complete,
        "can_receive_payouts": balance.stripe_onboarding_complete,
    }

@router.post("/payouts")
async def request_payout(
    body:PayoutRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, float]:
    service = RewardsService(db=db)
    payout = await service.request_payout(
        user=user,amount=body.amount
    )
    return {
        "id": str(payout.id),
        "amount": float(payout.amount),
        "status": payout.status,
        "requested_at": payout.requested_at.isoformat(),
    }

@router.get("/payouts")
async def get_payouts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit:Optional[int]=50,
    offset:Optional[int]=0,
) -> Dict[str, float]:
    service = RewardsService(db=db)
    return await service.get_payouts(user=user,limit=limit,offset=offset)