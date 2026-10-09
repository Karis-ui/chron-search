from app.services import limits_service
from typing import Any
from app.core.security import get_current_user
from app.core.database import get_db
from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from typing import Dict
from typing import Optional
from pydantic import BaseModel
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from redis.asyncio import Redis

from app.api.v1.deps import get_current_active_user
from app.core.config import settings
from app.core.redis_client import get_redis
from app.models.domain import User
from app.services.ml_service import FaceRecognitionService
from app.workers.celery_app import celery_app
from app.services.limits_service import LimitsService

router = APIRouter(prefix="/search", tags=["Search"])


def get_face_service() -> FaceRecognitionService:
    return FaceRecognitionService()


@router.post("/initiate", status_code=status.HTTP_200_OK)
async def initiate_search(
    media_file: UploadFile = File(...),
    time_range_days: int = Form(180, ge=1, le=180),
    platforms: str = Form(""),
    min_confidence: float = Form(0.68, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_active_user),
    redis: Redis = Depends(get_redis),
    face_service: FaceRecognitionService = Depends(get_face_service),
    db: AsyncSession = Depends(get_db)
):
    limits_service = LimitsService(db)
    await limits_service.enforce_search_limit.check_time_range(current_user,time_range_days)

    allowed,clamped_days = await limits_service.check_time_range(current_user,time_range_days)
    time_range_days = clamped_days

    allowed, filtered_platforms = await limits_service.check_platforms_allowed(
    current_user, platform_list
)
    if not allowed:
        raise HTTPException(
        status_code=403,
        detail="None of the requested platforms are available on your tier",
    )
    platform_list = filtered_platforms

    allowed, clamped_results = await limits_service.check_results_limit(
        current_user, 1000 
    )

    await limits_service.increment_usage(
        str(current_user.id),
        "searches_count",
        1,
    )
    content_type = media_file.content_type or ""
    if not content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Image search requires an image upload.",
        )

    image_bytes = await media_file.read(settings.MAX_UPLOAD_SIZE + 1)
    if len(image_bytes) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Uploaded image exceeds the maximum allowed size.",
        )

    try:
        face = await run_in_threadpool(face_service.extract_face_embedding, image_bytes)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Image recognition is unavailable. Please try again later.",
        ) from exc

    if face is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No detectable face was found in the uploaded image.",
        )

    task_id = str(uuid.uuid4())
    selected_platforms = [platform.strip().lower() for platform in platforms.split(",") if platform.strip()]
    if not selected_platforms:
        selected_platforms = ["instagram", "facebook", "twitter", "tiktok", "telegram", "reddit", "youtube"]

    await redis.hset(
        f"search:task:{task_id}",
        mapping={
            "task_id": task_id,
            "user_id": str(current_user.id),
            "status": "queued",
            "progress": "0",
            "results_count": "0",
        },
    )
    try:
        await run_in_threadpool(
            celery_app.send_task,
            "app.workers.search_worker.run_search_task",
            kwargs={
                "task_id": task_id,
                "embedding_data": {"face_embedding": face.embedding.tolist()},
                "biometric_type": "face",
                "time_range_days": time_range_days,
                "platforms": selected_platforms,
                "min_confidence": min_confidence,
                "user_id": str(current_user.id),
            },
        )
    except Exception as exc:
        await redis.delete(f"search:task:{task_id}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search queue is unavailable. Please try again later.",
        ) from exc

    return {
        "task_id": task_id,
        "status": "queued",
        "message": "Image search queued successfully.",
        "websocket_url": f"/api/v1/ws/search/{task_id}",
        "estimated_time": "2-5 minutes",
        "biometric_type": "face",
        "platforms_searched": selected_platforms,
        "time_range_days": time_range_days,
    }

class UnifiedResult(BaseModel):
    source: str  
    similarity: float
    confidence_level: str
    rank: int
    final_score: float

    profile_id: Optional[str] = None
    user_id: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    occupation: Optional[str] = None
    company: Optional[str] = None
    social_links: Optional[Dict[str, str]] = None
    is_verified: Optional[bool] = None
    is_featured: Optional[bool] = None
    allow_direct_messages: Optional[bool] = None

    post_id: Optional[str] = None
    platform: Optional[str] = None
    url: Optional[str] = None
    posted_at: Optional[str] = None
    caption: Optional[str] = None
    author_username: Optional[str] = None
    likes: Optional[int] = None
    shares: Optional[int] = None
    comments: Optional[int] = None

    thumbnail: Optional[str] = None
    face_score: Optional[float] = None
    voice_score: Optional[float] = None
    match_type: Optional[str] = None

class UnifiedResultsResponse(BaseModel):
    task_id: str
    status: str
    consent_count: int
    social_count: int
    total_count: int
    results: List[UnifiedResult]
    duration_ms: float

@router.get("/unified-results/{task_id}",
    response_model=UnifiedResultsResponse,
    summary="Get unified results (consent + social)",
)
async def get_unified_results(
    task_id: str,
    limit: int = Query(200, ge=1, le=500),
    source: Optional[str] = Query(None, pattern="^(consent|social|all)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis),
):
    import json
    status_data = await redis.hgetall(f"search:task:{task_id}")
    if not status_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )
    
    if status_data.get("user_id") != str(current_user.id):
        if current_user.id not in ['admin','super_admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied.",
            )
    
    cached_key = f"search:unified:{task_id}"
    cached_data = await redis.get(cached_key)

    if cached_data:
        data = json.loads(cached_data)
        
    else:
        from sqlalchemy import select, desc
        from app.models.domain import SearchResult, SocialPost

        consent_cache = await redis.get(f"search:consent:{task_id}")
        consent_matches = json.loads(consent_cache) if consent_cache else []
        stat = (
            select(SearchResult, SocialPost)
            .join(SocialPost, SearchResult.post_id == SocialPost.id)
            .where(SearchResult.task_id == task_id)
            .order_by(desc(SearchResult.similarity_score))
        )
        result = await db.execute(stat)
        rows = result.all()
        social_matches = []
        for search_result, post in rows:
            social_matches.append({
                "source": "social",
                "post_id": str(post.id),
                "platform": post.platform.value,
                "url": post.platform_url,
                "thumbnail": post.thumbnail_url or post.media_url,
                "posted_at": post.posted_at.isoformat() if post.posted_at else None,
                "caption": post.caption,
                "author_username": post.author_username,
                "author_full_name": post.author_full_name,
                "location": post.location,
                "likes": post.likes or 0,
                "shares": post.shares or 0,
                "comments": post.comments or 0,
                "similarity": search_result.similarity_score,
                "confidence_level": (
                    search_result.confidence_level.value.capitalize()
                    if search_result.confidence_level
                    else "Unknown"
                ),
                "face_score": search_result.face_match_score or 0,
                "voice_score": search_result.voice_match_score or 0,
                "match_type": search_result.method_used or "face",
            })
        all_results = consent_matches + social_matches
        for result_data in all_results:
            result_data["final_score"] = result_data.get("similarity", 0) * (
                1.1 if result_data["source"] == "consent" else 1.0
            )
        all_results.sort(key=lambda result_data: result_data["final_score"], reverse=True)
        all_results = all_results[:200]
        for idx, result_data in enumerate(all_results):
            result_data["rank"] = idx + 1
        data = {
            "task_id": task_id,
            "status": status_data.get("status", "completed"),
            "consent_count": sum(result_data["source"] == "consent" for result_data in all_results),
            "social_count": sum(result_data["source"] == "social" for result_data in all_results),
            "total_count": len(all_results),
            "results": all_results,
            "duration_ms": 0,
        }
        await redis.setex(cached_key, 3600, json.dumps(data, default=str))
    
    all_results = data.get("results", [])
    if source and source != "all":
        all_results = [result for result in all_results if result.get("source") == source]

    results = all_results[:limit]
    return UnifiedResultsResponse(
        task_id=data["task_id"],
        status=data["status"],
        consent_count=data["consent_count"],
        social_count=data["social_count"],
        total_count=len(results),
        duration_ms=data.get("duration_ms", 0),
    )