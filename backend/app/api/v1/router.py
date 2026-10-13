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
router.include_router(consent.router)
router.include_router(billing.router)
router.include_router(me.router)
router.include_router(rewards.router)
router.include_router(subscriptions.router)
