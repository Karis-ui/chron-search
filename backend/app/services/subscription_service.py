from google.protobuf import descriptor_pb2
from app.models.subscription import Payment
from app.core.tiers import get_all_tier_info
from typing import List
from app.core.tiers import compare_tiers
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from sqlalchemy import select, and_, func,and_,desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.core.tiers import Tier, TierLimits, get_tier_limits, is_tier_at_least
from app.core.exceptions import BadRequestException, ForbiddenException
from app.models.domain import User
from app.models.subscription import (
    Subscription, UsageRecord, SavedSearch, SearchAlert
)

class SubscriptionService:
    def __init__(self,db:AsyncSession):
        self.db = db
    
    async def get_subscription(self,user:User) -> Optional[Subscription]:
        stmt = select(Subscription).where(Subscription.user_id == user.id,Subscription.status == "active")
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()
    
    async def get_or_create_free(self,user:User) -> Optional[Subscription]:
        sub = await self.get_subscription(user)
        if sub:
            return sub
        
        sub = Subscription(
            user_id=user.id,
            tier="free",
            status="active"
        )
        self.db.add(sub)
        await self.db.commit()
        await self.db.refresh(sub)
        return sub
    
    async def get_subscription_summary(self,user:User)-> Dict[str,Any]:
        sub = await self.get_or_create_free(user)
        limits = get_tier_limits(sub.tier)
        return {
            "tier": sub.tier,
            "tier_name": limits.name,
            "status": sub.status,
            "billing_cycle": sub.billing_cycle,

            "current_period_start": (
                sub.current_period_start.isoformat() if sub.current_period_start else None
            ),
            "current_period_end": (
                sub.current_period_end.isoformat() if sub.current_period_end else None
            ),
            "cancel_at_period_end": sub.cancel_at_period_end,

            "amount": float(sub.amount or 0),
            "currency": sub.currency,

            "is_active": sub.status in ("active", "trialing"),
            "in_trial": sub.status == "trialing" and bool(sub.trial_end),
            "trial_end": sub.trial_end.isoformat() if sub.trial_end else None,

            "limits": {
                "searches_per_day": limits.searches_per_day,
                "searches_per_month": limits.searches_per_month,
                "results_per_search": limits.results_per_search,
                "time_range_days": limits.time_range_days,
                "platforms_count": len(limits.platforms_allowed) if limits.platforms_allowed else "all",
                "export_formats": limits.export_formats,
                "saved_searches": limits.saved_searches,
                "api_calls_per_month": limits.api_calls_per_month,
                "boosts_per_month": limits.profile_boosts_per_month,
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

            "created_at": sub.created_at.isoformat() if sub.created_at else None,
        }
    
    async def is_eligible_for_trial(self,user:User) -> bool:
        sub = await self.get_subscription(user)
        if not sub:
            return True

        if sub.trial_start or sub.trial_end:
            return False
        
        if sub.tier != 'free':
            return False
        return True

    async def start_trial(self, user: User, tier: str = "pro", days: int = 14) -> Subscription:
        if not await self.is_eligible_for_trial(user):
            raise BadRequestException(message="Not eligible for trial")

        sub = await self.get_or_create_free(user)
        sub.tier = tier
        sub.status = "trialing"
        sub.trial_start = datetime.utcnow()
        sub.trial_end = datetime.utcnow() + timedelta(days=days)
        sub.current_period_start = datetime.utcnow()
        sub.current_period_end = sub.trial_end

        await self.db.commit()
        await self.db.refresh(sub)

        logger.info(f"🎁 Trial started: {tier} for {user.email}")
        return sub
    
    async def can_upgrade(self,user:User,new_tier:str) -> bool:
        sub = await self.get_or_create_free(user)
        return compare_tiers(new_tier,sub.tier) > 0
    
    async def get_upgrade_options(self,user:User) -> List[Dict[str,Any]]:
        sub = await self.get_or_create_free(user)
        all_tiers = get_all_tier_info()
        return[
            tier for tier in all_tiers if compare_tiers(tier["id"],sub.tier) > 0
        ]
    
    async def get_subscription_stats(self,user:User) -> Dict[str,Any]:
        sub = await self.get_or_create_free(user)
        stmt = select(
            func.count(Payment.id),
            func.sum(Payment.amount)
        ).where(and_(
            Payment.user_id == user.id,
            Payment.status == "succeeded"
        ))

        res = await self.db.execute(stmt)
        row = res.first()
        total_payments = row[0] or 0
        total_amount = row[1] or 0

        stmt = (
            select(Payment)
            .where(
                and_(
                    Payment.user_id == user.id,
                    Payment.status == "succeeded"
                )
            )
            .order_by(desc(Payment.created_at)).limit(10)
        )
        result = await self.db.execute(stmt)
        recent = result.scalars().all()

        return {
            "tier": sub.tier,
            "status": sub.status,
            "member_since": sub.created_at.isoformat() if sub.created_at else None,
            "total_payments": total_payments,
            "total_spent": total_amount,
            "recent_payments": [
                {
                    "id": str(p.id),
                    "amount": float(p.amount),
                    "currency": p.currency,
                    "type": p.payment_type,
                    "status": p.status,
                    "description": p.description,
                    "created_at": p.created_at.isoformat(),
                }
                for p in recent
            ],
        }
    
    async def get_all_subscriptions(
        self,
        tier: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str,Any]:
        query = select(Subscription)
        if tier:
            query = query.where(Subscription.tier == tier)
        if status:
            query = query.where(Subscription.status == status)
        
        count_stmt = select(func.count()).select_from(query.subquery())
        count_res = await self.db.execute(count_stmt)
        total = count_res.scalar_one() or 0
        
        query = query.offset(offset).limit(limit).order_by(desc(Subscription.created_at))
        res = await self.db.execute(query)
        subs = res.scalars().all()

        return {
            "total": total,
            "subscriptions": [
                {
                    "user_id": str(s.user_id),
                    "tier": s.tier,
                    "status": s.status,
                    "amount": float(s.amount or 0),
                    "current_period_end": (
                        s.current_period_end.isoformat() if s.current_period_end else None
                    ),
                    "created_at": s.created_at.isoformat(),
                }
                for s in subs
            ],
        }
    
    async def get_revenue_stats(self,days:int=30) -> Dict[str,Any]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        stmt = (
            select(
                func.count(Payment.id),
                func.sum(Payment.amount),
            ).where(
                and_(
                    Payment.status == "succeeded",
                    Payment.created_at >= datetime.utcnow() - timedelta(days=days),
                )
            )
        )
        res = await self.db.execute(stmt)
        revenue = float(res.scalar() or 0)
        stmt = (
            select(Subscription.tier,func.count(Subscription.id))
            .where(Subscription.status == "active")
            .group_by(Subscription.tier)
        )

        res = await self.db.execute(stmt)
        by_tier = {row[0]: row[1] for row in res.all()}
        stmt = (
            select(func.sum(Subscription.amount))
            .where(
                and_(
                    Subscription.status == "active",
                    Subscription.billing_cycle == "monthly",
                )
            )
        )
        res = await self.db.execute(stmt)
        mrr = float(res.scalar() or 0)

        return {
            "revenue_period": revenue,
            "period_days": days,
            "mrr": mrr,
            "arr": mrr * 12,
            "subscriptions_by_tier": by_tier,
            "total_active": sum(by_tier.values()),
        }