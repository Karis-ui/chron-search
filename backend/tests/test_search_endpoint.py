import asyncio
import json
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient
import numpy as np

from app.api.v1 import deps
from app.api.v1.endpoints import search as search_endpoint
from app.api.v1.router import router as api_v1_router
from app.core.redis_client import get_redis
from app.core.security import create_access_token


class FakeResult:
    def scalar_one_or_none(self):
        return SimpleNamespace(id="test-user", is_active=True, role=SimpleNamespace(value="user"))


class FakeRedis:
    def __init__(self):
        self.hashes = {}
        self.values = {}

    async def hset(self, key, mapping):
        self.key = key
        self.mapping = mapping

    async def hgetall(self, key):
        return self.hashes.get(key, {})

    async def get(self, key):
        return self.values.get(key)

    async def setex(self, key, ttl, value):
        self.values[key] = value

    async def delete(self, key):
        return 1


class FakeFaceService:
    def extract_face_embedding(self, image_bytes):
        return SimpleNamespace(embedding=np.array([0.1, 0.2], dtype=np.float32))


class FakeSession:
    async def execute(self, statement):
        return FakeResult()


class FakeRowsResult:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows


class FakeRowsSession:
    def __init__(self, rows):
        self.rows = rows

    async def execute(self, statement):
        return FakeRowsResult(self.rows)


def create_test_client():
    app = FastAPI()
    app.include_router(api_v1_router, prefix="/api/v1")

    async def fake_get_db():
        yield FakeSession()

    app.dependency_overrides[deps.get_db] = fake_get_db
    app.dependency_overrides[get_redis] = lambda: FakeRedis()
    app.dependency_overrides[search_endpoint.get_face_service] = FakeFaceService
    return TestClient(app)


def test_search_initiate_queues_image_search(monkeypatch):
    dispatched = {}
    monkeypatch.setattr(
        search_endpoint.celery_app,
        "send_task",
        lambda name, kwargs: dispatched.update(name=name, kwargs=kwargs),
    )

    with create_test_client() as client:
        response = client.post(
            "/api/v1/search/initiate",
            files={"media_file": ("query.jpg", b"image-bytes", "image/jpeg")},
            data={"time_range_days": "180", "platforms": "instagram,twitter", "min_confidence": "0.68"},
            headers={"Authorization": f"Bearer {create_access_token({'sub': 'test-user'})}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"
    assert data["task_id"]
    assert data["websocket_url"].endswith(data["task_id"])
    assert dispatched["kwargs"]["embedding_data"]["face_embedding"] == [
        0.10000000149011612,
        0.20000000298023224,
    ]


def test_search_route_rejects_malformed_token_without_500():
    with create_test_client() as client:
        response = client.post(
            "/api/v1/search/initiate",
            files={"media_file": ("query.jpg", b"image-bytes", "image/jpeg")},
            headers={"Authorization": "Bearer malformed-token"},
        )

    assert response.status_code == 401


def test_search_route_requires_bearer_authentication():
    with create_test_client() as client:
        response = client.post(
            "/api/v1/search/initiate",
            files={"media_file": ("query.jpg", b"image-bytes", "image/jpeg")},
        )

    assert response.status_code in (401, 403)


def test_search_initiate_rejects_non_media_upload():
    with create_test_client() as client:
        response = client.post(
            "/api/v1/search/initiate",
            files={"media_file": ("notes.txt", b"not media", "text/plain")},
            headers={"Authorization": f"Bearer {create_access_token({'sub': 'test-user'})}"},
        )

    assert response.status_code == 415


def test_unified_results_stay_in_sync_between_database_and_cache():
    redis = FakeRedis()
    redis.hashes["search:task:task-1"] = {
        "user_id": "test-user",
        "status": "completed",
    }
    consent_result = {
        "source": "consent",
        "profile_id": "profile-1",
        "user_id": "profile-user",
        "display_name": "Example",
        "similarity": 0.95,
        "confidence_level": "High",
        "face_score": 0.95,
        "voice_score": 0,
        "match_type": "face",
    }
    redis.values["search:consent:task-1"] = json.dumps([consent_result])

    search_result = SimpleNamespace(
        similarity_score=0.9,
        confidence_level=SimpleNamespace(value="High"),
        face_match_score=0.9,
        voice_match_score=0,
        method_used="face",
    )
    post = SimpleNamespace(
        id="post-1",
        platform=SimpleNamespace(value="instagram"),
        platform_url="https://example.com/post-1",
        thumbnail_url=None,
        media_url=None,
        posted_at=None,
        caption="Example post",
        author_username="example",
        likes=1,
        shares=2,
        comments=3,
    )

    async def fetch(source, db):
        return await search_endpoint.get_unified_results(
            task_id="task-1",
            limit=10,
            source=source,
            current_user=SimpleNamespace(id="test-user"),
            db=db,
            redis=redis,
        )

    database_response = asyncio.run(
        fetch("social", FakeRowsSession([(search_result, post)]))
    )

    assert database_response.total_count == 1
    assert database_response.social_count == 1
    assert database_response.results[0].post_id == "post-1"

    cached_data = json.loads(redis.values["search:unified:task-1"])
    assert cached_data["total_count"] == 2
    assert len(cached_data["results"]) == 2
    assert cached_data["results"][0]["profile_id"] == "profile-1"

    cache_social_response = asyncio.run(fetch("social", FakeRowsSession([])))

    assert cache_social_response.total_count == 1
    assert cache_social_response.results[0].post_id == "post-1"

    cache_response = asyncio.run(fetch("consent", FakeRowsSession([])))

    assert cache_response.total_count == 1
    assert cache_response.consent_count == 1
    assert cache_response.results[0].profile_id == "profile-1"