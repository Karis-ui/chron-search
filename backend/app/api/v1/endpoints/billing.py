from torch import return_types
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List
import json

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.logger import logger
from app.models.domain import User
from app.services.stripe_service import StripeService
from app.services.billing_service import BillingService


router = APIRouter(prefix="/billing", tags=["Billing"])

class CheckoutRequest(BaseModel):
    tier: str
    billing_cycle: str = "monthly"


class BoostCheckoutRequest(BaseModel):
    boost_type: str


class VerificationCheckoutRequest(BaseModel):
    level: str


class SubscriptionResponse(BaseModel):
    tier: str
    status: str
    current_period_end: Optional[str] = None
    cancel_at_period_end: bool = False
    amount: float = 0
    currency: str = "usd"

@router.post("/checkout/subscription")
async def create_subscription_checkout(
    data: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    price_map = {
        ("pro", "monthly"): settings.STRIPE_PRICE_PRO_MONTHLY,
        ("pro", "yearly"): settings.STRIPE_PRICE_PRO_YEARLY,
        ("ultra", "monthly"): settings.STRIPE_PRICE_ULTRA_MONTHLY,
        ("ultra", "yearly"): settings.STRIPE_PRICE_ULTRA_YEARLY,
    }
    price_id = price_map.get((data.tier.lower(),data.billing_cycle))
    if not price_id:
        raise HTTPException(status_code=400, detail="Invalid tier or billing cycle")
    
    trial_days = 14 if data.tier.lower() == "pro" else 0
    url = await StripeService.create_subscription_checkout(
        user=current_user,
        price_id=price_id,
        success_url=f"{settings.FRONTEND_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.FRONTEND_URL}/billing/cancel",
        trial_days=trial_days,
    )
    return {"checout_url":url}

@router.post("/checkout/boost")
async def create_boost_checkout(
    data: BoostCheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    
    service = StripeService(db)
    price_map = {
        "starter": settings.STRIPE_PRICE_BOOST_STARTER,
        "standard": settings.STRIPE_PRICE_BOOST_STANDARD,
        "premium": settings.STRIPE_PRICE_BOOST_PREMIUM,
    }
    price_id = price_map.get(data.boost_type.lower())
    if not price_id:
        raise HTTPException(status_code=400, detail="Invalid boost type")
    
    url = await service.create_checkout_session(
        user_id=current_user.id,
        payment_type="boost",
        boost_type=data.boost_type,
        price_id=price_id,
        success_url=f"{settings.FRONTEND_URL}/boosts/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.FRONTEND_URL}/boosts/cancel",
    )

    return {"checkout_url": url}

@router.post("/checkout/verification")
async def create_verification_checkout(
    data: VerificationCheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = StripeService(db)
    price_map = {
        "blue": settings.STRIPE_PRICE_VERIFY_BLUE,
        "purple": settings.STRIPE_PRICE_VERIFY_PURPLE,
        "gold": settings.STRIPE_PRICE_VERIFY_GOLD,
    }
    price_id = price_map.get(data.level.lower())
    if not price_id:
        raise HTTPException(status_code=400, detail="Invalid verification level")
    
    url = await service.create_checkout_session(
        user_id=current_user.id,
        payment_type="verification",
        verification_level=data.level,
        price_id=price_id,
        success_url=f"{settings.FRONTEND_URL}/verification/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.FRONTEND_URL}/verification/cancel",
    )

    return {"checkout_url": url}

@router.get("/subscription", response_model=SubscriptionResponse)
async def get_user_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = StripeService(db)
    sub = await service.get_subscription(current_user)
    if not sub:
        return SubscriptionResponse(
            tier="free",
            status="inactive",
            current_period_end=None,
            cancel_at_period_end=False,
            amount=0,
            currency="usd",
        )
    return SubscriptionResponse(
        tier=sub.tier,
        status=sub.status,
        current_period_end=(sub.current_period_end.isoformat() if sub.current_period_end else None),
        cancel_at_period_end=sub.cancel_at_period_end,
        amount=float(sub.amount or 0),
        currency=sub.currency,
    )

@router.post("/portal")
async def create_portal_session(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = StripeService(db)
    url = await service.create_customer_portal_session(current_user,return_url=f"{settings.FRONTEND_URL}/billing")
    return {"portal_url":url}

@router.post("/subscription/cancel")
async def cancel_subscription(
    immediate: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = StripeService(db)
    await service.cancel_subscription(current_user, immediate=immediate)
    return {"message": "Subscription cancelled"}


@router.post("/subscription/resume")
async def resume_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = StripeService(db)
    await service.resume_subscription(current_user)
    return {"message": "Subscription resumed"}


@router.get("/payments")
async def get_payments(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = StripeService(db)
    payments = await service.get_payment_history(current_user, limit=limit)

    return [
        {
            "id": str(p.id),
            "amount": float(p.amount),
            "currency": p.currency,
            "status": p.status,
            "type": p.payment_type,
            "description": p.description,
            "created_at": p.created_at.isoformat(),
        }
        for p in payments
    ]


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    db: AsyncSession = Depends(get_db),
):
    payload = await request.body()

    service = StripeService(db)

    try:
        event = service.verify_webhook(payload, stripe_signature)
    except Exception as e:
        logger.error(f"Webhook verification failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    from app.models.subscription import StripeWebhookEvent
    webhook_event = StripeWebhookEvent(
        stripe_event_id=event["id"],
        event_type=event["type"],
        data=event,
    )
    db.add(webhook_event)
    await db.commit()

    billing_service = BillingService(db)

    try:
        await billing_service.handle_webhook(event)
        webhook_event.processed = True
        webhook_event.processed_at = __import__("datetime").datetime.utcnow()
        await db.commit()

        logger.info(f"✅ Webhook processed: {event['type']}")

    except Exception as e:
        logger.error(f"Webhook handling failed: {e}", exc_info=True)
        webhook_event.processing_error = str(e)
        webhook_event.retry_count += 1
        await db.commit()
        return JSONResponse(status_code=200, content={"received": True})

    return {"received": True}