from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from sqlalchemy import select, and_, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.core.tiers import Tier, TierLimits, get_tier_limits, is_tier_at_least
from app.core.exceptions import BadRequestException, ForbiddenException
from app.models.domain import User
from app.models.subscription import (
    Subscription, UsageRecord, SavedSearch, SearchAlert
)


class LimitsService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_tier(self, user: User) -> Tier:
        if user.role in ("admin", "super_admin"):
            return Tier.ENTERPRISE

        stmt = select(Subscription).where(Subscription.user_id == user.id)
        result = await self.db.execute(stmt)
        subscription = result.scalar_one_or_none()

        if not subscription:
            return Tier.FREE

        if subscription.status not in ("active", "trialing"):
            if (
                subscription.current_period_end
                and subscription.current_period_end > datetime.utcnow()
            ):
                pass 
            else:
                return Tier.FREE

        try:
            return Tier(subscription.tier)
        except ValueError:
            return Tier.FREE

    async def get_user_limits(self, user: User) -> TierLimits:
        tier = await self.get_user_tier(user)
        return get_tier_limits(tier)

    async def get_or_create_usage(
        self,
        user_id: str,
        period_type: str = "daily",
    ) -> UsageRecord:
        now = datetime.utcnow()

        if period_type == "daily":
            period_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else: 
            period_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        stmt = select(UsageRecord).where(
            and_(
                UsageRecord.user_id == user_id,
                UsageRecord.period_date == period_date,
                UsageRecord.period_type == period_type,
            )
        )
        result = await self.db.execute(stmt)
        usage = result.scalar_one_or_none()

        if not usage:
            usage = UsageRecord(
                user_id=user_id,
                period_date=period_date,
                period_type=period_type,
            )
            self.db.add(usage)
            await self.db.commit()
            await self.db.refresh(usage)

        return usage

    async def increment_usage(
        self,
        user_id: str,
        counter: str, 
        amount: int = 1,
    ) -> None:
        daily = await self.get_or_create_usage(user_id, "daily")
        monthly = await self.get_or_create_usage(user_id, "monthly")

        setattr(daily, counter, getattr(daily, counter) + amount)
        setattr(monthly, counter, getattr(monthly, counter) + amount)

        await self.db.commit()

    async def get_usage_summary(self, user_id: str) -> Dict[str, Any]:
        daily = await self.get_or_create_usage(user_id, "daily")
        monthly = await self.get_or_create_usage(user_id, "monthly")

        return {
            "daily": {
                "date": daily.period_date.isoformat(),
                "searches": daily.searches_count,
                "results": daily.results_count,
                "api_calls": daily.api_calls_count,
            },
            "monthly": {
                "month": monthly.period_date.isoformat(),
                "searches": monthly.searches_count,
                "results": monthly.results_count,
                "api_calls": monthly.api_calls_count,
            },
        }

    async def check_search_limit(self, user: User) -> Tuple[bool, Dict[str, Any]]:
        limits = await self.get_user_limits(user)

        if limits.searches_per_day == -1:
            return True, {"unlimited": True}

        daily_usage = await self.get_or_create_usage(user.id, "daily")
        if daily_usage.searches_count >= limits.searches_per_day:
            return False, {
                "reason": "daily_limit_reached",
                "limit": limits.searches_per_day,
                "used": daily_usage.searches_count,
                "resets_at": (daily_usage.period_date + timedelta(days=1)).isoformat(),
            }

        monthly_usage = await self.get_or_create_usage(user.id, "monthly")
        if (
            limits.searches_per_month != -1
            and monthly_usage.searches_count >= limits.searches_per_month
        ):
            return False, {
                "reason": "monthly_limit_reached",
                "limit": limits.searches_per_month,
                "used": monthly_usage.searches_count,
                "resets_at": (
                    monthly_usage.period_date.replace(day=1) + timedelta(days=32)
                ).replace(day=1).isoformat(),
            }

        return True, {
            "daily_remaining": limits.searches_per_day - daily_usage.searches_count,
            "monthly_remaining": (
                limits.searches_per_month - monthly_usage.searches_count
                if limits.searches_per_month != -1
                else -1
            ),
        }

    async def check_platforms_allowed(
        self,
        user: User,
        requested_platforms: list,
    ) -> Tuple[bool, list]:
        limits = await self.get_user_limits(user)

        if not limits.platforms_allowed:
            return True, requested_platforms

        filtered = [p for p in requested_platforms if p in limits.platforms_allowed]

        if not filtered:
            return False, []

        return True, filtered

    async def check_time_range(self, user: User, requested_days: int) -> Tuple[bool, int]:
        limits = await self.get_user_limits(user)
        allowed = min(requested_days, limits.time_range_days)
        return requested_days <= limits.time_range_days, allowed

    async def check_results_limit(self, user: User, requested: int) -> Tuple[bool, int]:
        limits = await self.get_user_limits(user)
        if limits.results_per_search == -1:
            return True, requested
        allowed = min(requested, limits.results_per_search)
        return requested <= limits.results_per_search, allowed

    async def check_export_format(self, user: User, format: str) -> bool:
        limits = await self.get_user_limits(user)
        return format.lower() in limits.export_formats

    async def check_feature(self, user: User, feature: str) -> bool:
        limits = await self.get_user_limits(user)
        return getattr(limits, feature, False)

    async def check_api_limit(self, user: User) -> Tuple[bool, Dict[str, Any]]:
        limits = await self.get_user_limits(user)

        if limits.api_calls_per_month == -1:
            return True, {"unlimited": True}

        if limits.api_calls_per_month == 0:
            return False, {"reason": "api_not_available"}

        monthly_usage = await self.get_or_create_usage(user.id, "monthly")
        if monthly_usage.api_calls_count >= limits.api_calls_per_month:
            return False, {
                "reason": "api_limit_reached",
                "limit": limits.api_calls_per_month,
                "used": monthly_usage.api_calls_count,
            }

        return True, {
            "remaining": limits.api_calls_per_month - monthly_usage.api_calls_count,
        }

    async def check_saved_search_limit(self, user: User) -> Tuple[bool, int]:
        limits = await self.get_user_limits(user)

        stmt = select(func.count(SavedSearch.id)).where(SavedSearch.user_id == user.id)
        result = await self.db.execute(stmt)
        count = result.scalar() or 0

        if limits.saved_searches == -1:
            return True, -1

        if count >= limits.saved_searches:
            return False, count

        return True, limits.saved_searches - count

    async def enforce_search_limit(self, user: User) -> None:
        allowed, info = await self.check_search_limit(user)
        if not allowed:
            raise ForbiddenException(
                message="Search limit reached",
                details=info,
            )

    async def enforce_feature(self, user: User, feature: str, friendly_name: str = None) -> None:
        has_access = await self.check_feature(user, feature)
        if not has_access:
            tier = await self.get_user_tier(user)
            raise ForbiddenException(
                message=f"{friendly_name or feature} requires a higher subscription tier",
                details={
                    "feature": feature,
                    "current_tier": tier.value,
                    "upgrade_url": "/pricing",
                },
            )

    async def enforce_tier(self, user: User, required_tier: str) -> None:
        tier = await self.get_user_tier(user)
        if not is_tier_at_least(tier.value, required_tier):
            raise ForbiddenException(
                message=f"This feature requires {required_tier} tier or higher",
                details={
                    "current_tier": tier.value,
                    "required_tier": required_tier,
                    "upgrade_url": "/pricing",
                },
            )

    async def cleanup_old_usage(self, days: int = 90) -> int:
        cutoff = datetime.utcnow() - timedelta(days=days)
        stmt = delete(UsageRecord).where(UsageRecord.period_date < cutoff)
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount

    async def get_user_capabilities(self, user: User) -> Dict[str, Any]:
        tier = await self.get_user_tier(user)
        limits = await self.get_user_limits(user)

        daily = await self.get_or_create_usage(user.id, "daily")
        monthly = await self.get_or_create_usage(user.id, "monthly")

        return {
            "tier": tier.value,
            "tier_name": limits.name,

            "limits": {
                "searches_per_day": limits.searches_per_day,
                "searches_per_month": limits.searches_per_month,
                "results_per_search": limits.results_per_search,
                "time_range_days": limits.time_range_days,
                "platforms_allowed": limits.platforms_allowed or "all",
                "export_formats": limits.export_formats,
                "saved_searches": limits.saved_searches,
                "api_calls_per_month": limits.api_calls_per_month,
                "profile_boosts_per_month": limits.profile_boosts_per_month,
                "history_retention_days": limits.history_retention_days,
            },

            "features": {
                "voice_recognition": limits.voice_recognition,
                "batch_search": limits.batch_search,
                "advanced_filters": limits.advanced_filters,
                "alerts_enabled": limits.alerts_enabled,
                "priority_support": limits.priority_support,
                "analytics_access": limits.analytics_access,
            },

            "usage": {
                "searches_today": daily.searches_count,
                "searches_this_month": monthly.searches_count,
                "api_calls_this_month": monthly.api_calls_count,
                "daily_remaining": (
                    limits.searches_per_day - daily.searches_count
                    if limits.searches_per_day != -1
                    else -1
                ),
                "monthly_remaining": (
                    limits.searches_per_month - monthly.searches_count
                    if limits.searches_per_month != -1
                    else -1
                ),
            },

            "rewards": {
                "multiplier": limits.reward_multiplier,
                "monthly_cap": limits.monthly_reward_cap,
            },
        }