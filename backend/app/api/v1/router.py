from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    oauth,
    websockets,
    admin,
    feedback,
    health,
    search,
    consent,
    billing,
    me,
    rewards,
    subscriptions,
)

router = APIRouter()

router.include_router(auth.router, tags=["Authentication"])
router.include_router(oauth.router, tags=["OAuth"])
router.include_router(websockets.router, tags=["WebSocket"])
router.include_router(admin.router, tags=["Administration"])
router.include_router(feedback.router, tags=["Feedback"])
router.include_router(search.router, tags=["Search"])
router.include_router(health.router, prefix="/health", tags=["Health Check"])
router.include_router(consent.router, prefix="/consent", tags=["Consent"])
router.include_router(billing.router, prefix="/billing", tags=["Billing"])
router.include_router(me.router, prefix="/me", tags=["Account"])
router.include_router(rewards.router, prefix="/rewards", tags=["Rewards"])
router.include_router(subscriptions.router, prefix="/subscriptions", tags=["Subscriptions"])
