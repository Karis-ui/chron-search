import pytest
import asyncio
from datetime import datetime, timedelta

from httpx import AsyncClient

@pytest.mark.asyncio
async def test_list_tiers(async_client: AsyncClient):
    response = await async_client.get("/api/v1/subscriptions/tiers")

    assert response.status_code == 200
    tiers = response.json()

    assert len(tiers) == 4
    assert tiers[0]["id"] == "free"
    assert tiers[3]["id"] == "enterprise"

    # Verify structure
    for tier in tiers:
        assert "limits" in tier
        assert "searches_per_day" in tier["limits"]


@pytest.mark.asyncio
async def test_get_capabilities(async_client: AsyncClient, auth_headers):
    response = await async_client.get(
        "/api/v1/subscriptions/capabilities",
        headers=auth_headers,
    )

    assert response.status_code == 200
    caps = response.json()

    assert "tier" in caps
    assert "limits" in caps
    assert "features" in caps
    assert "usage" in caps


@pytest.mark.asyncio
async def test_free_tier_limits(async_client: AsyncClient, auth_headers):
    caps_response = await async_client.get(
        "/api/v1/subscriptions/capabilities",
        headers=auth_headers,
    )
    caps = caps_response.json()

    assert caps["tier"] == "free"
    assert caps["limits"]["searches_per_day"] == 3
    assert caps["limits"]["results_per_search"] == 5
    assert caps["limits"]["time_range_days"] == 30


@pytest.mark.asyncio
async def test_subscription_checkout_creates_session(
    async_client: AsyncClient, auth_headers
):
    response = await async_client.post(
        "/api/v1/billing/checkout/subscription",
        headers=auth_headers,
        json={"tier": "pro", "billing_cycle": "monthly"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "checkout_url" in data
    assert "stripe.com" in data["checkout_url"]


@pytest.mark.asyncio
async def test_boost_checkout(async_client: AsyncClient, auth_headers):
    response = await async_client.post(
        "/api/v1/billing/checkout/boost",
        headers=auth_headers,
        json={"boost_type": "starter"},
    )

    assert response.status_code == 200
    assert "checkout_url" in response.json()


@pytest.mark.asyncio
async def test_verification_checkout(async_client: AsyncClient, auth_headers):
    response = await async_client.post(
        "/api/v1/billing/checkout/verification",
        headers=auth_headers,
        json={"level": "blue"},
    )

    assert response.status_code == 200
    assert "checkout_url" in response.json()


@pytest.mark.asyncio
async def test_balance_endpoint(async_client: AsyncClient, auth_headers):
    response = await async_client.get(
        "/api/v1/rewards/balance",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert "available" in data
    assert "pending" in data
    assert "lifetime_earned" in data
    assert data["available"] == 0


@pytest.mark.asyncio
async def test_payout_requires_minimum(async_client: AsyncClient, auth_headers):
    response = await async_client.post(
        "/api/v1/rewards/payouts",
        headers=auth_headers,
        json={"amount": 5.00},
    )

    assert response.status_code == 400
    assert "minimum" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_account_overview(async_client: AsyncClient, auth_headers):
    response = await async_client.get(
        "/api/v1/me/overview",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert "user" in data
    assert "subscription" in data
    assert "capabilities" in data

    assert data["user"]["email"]
    assert data["subscription"]["tier"] in ["free", "pro", "ultra", "enterprise"]