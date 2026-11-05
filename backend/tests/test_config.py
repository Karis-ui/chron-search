import pytest
from fastapi.testclient import TestClient
from app.core.config import settings,Settings
from app.main import create_app

def test_settings_loaded():
    assert settings is not None
    assert settings.PROJECT_NAME == "Chromos Search engine"
    assert settings.VERSION == "3.0.0-masterpiece"

def test_database_url():
    url = settings.DATABASE_URL
    assert "postgresql+asyncpg://" in url
    assert settings.POSTGRES_USER in url

def test_trusted_hosts_are_extracted_from_urls():
    configured = Settings(
        HOST="0.0.0.0",
        ALLOWED_ORIGINS=["http://localhost:5173", "https://chron-search-pjkxhigpr-karis-projects1.vercel.app"],
        BACKEND_URL="https://chron-search.up.railway.app",
    )

    assert {"localhost", "127.0.0.1", "chron-search.up.railway.app"}.issubset(
        set(configured.TRUSTED_HOSTS)
    )
    assert all("://" not in host for host in configured.TRUSTED_HOSTS)

def test_health_route_accepts_localhost_host_header():
    response = TestClient(create_app()).get(
        "/api/v1/health/",
        headers={"host": "localhost:8000"},
    )

    assert response.status_code == 200

def test_registration_cors_allows_current_vercel_frontend():
    origin = "https://chron-search-pjkxhigpr-karis-projects1.vercel.app"
    response = TestClient(create_app()).options(
        "/api/v1/auth/register",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin

def test_redis_rl():
    url = settings.REDIS_URL
    assert "redis://" in url
    assert str(settings.REDIS_PORT) in url

def test_secret_key():
    assert settings.SECRET_KEY is not None
    assert len(settings.SECRET_KEY.get_secret_value()) > 0

def test_data_retention():
    assert settings.DATA_RETENTION_DAYS == 180
    assert settings.DATA_RETENTION_DAYS > 0