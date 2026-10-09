from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from decimal import Decimal
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logger import logger
from app.core.tiers import get_tier_limits
from app.core.exceptions import BadRequestException, NotFoundException
from app.models.domain import User, ConsentProfile, RewardLedger
from app.models.subscription import (
    UserBalance, RewardPayout, PayoutStatus
)

REWARD_RATES = {
    "search_appearance": 0.20,
    "profile_click": 0.50,
    "premium_search": 2.00,
    "enterprise_search": 1.00,
    "verification_bonus": 2.00,
    "referral_bonus": 5.00,
}


class RewardsService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_balance(self, user: User) -> UserBalance:
        stmt = select(UserBalance).where(UserBalance.user_id == user.id)
        result = await self.db.execute(stmt)
        balance = result.scalar_one_or_none()

        if not balance:
            balance = UserBalance(
                user_id=user.id,
                available=0,
                pending=0,
                lifetime_earned=0,
                lifetime_paid=0,
                monthly_earned=0,
                monthly_reset_at=datetime.utcnow(),
            )
            self.db.add(balance)
            await self.db.commit()
            await self.db.refresh(balance)

        if (
            balance.monthly_reset_at
            and balance.monthly_reset_at.month != datetime.utcnow().month
        ):
            balance.monthly_earned = 0
            balance.monthly_reset_at = datetime.utcnow()
            await self.db.commit()

        return balance

    async def get_balance_summary(self, user: User) -> Dict[str, Any]:
        balance = await self.get_or_create_balance(user)

        return {
            "available": float(balance.available),
            "pending": float(balance.pending),
            "lifetime_earned": float(balance.lifetime_earned),
            "lifetime_paid": float(balance.lifetime_paid),
            "lifetime_searches": balance.lifetime_searches,
            "monthly_earned": float(balance.monthly_earned),
            "monthly_cap": settings.REWARDS_MONTHLY_CAP,
            "minimum_payout": settings.REWARDS_MIN_PAYOUT,
            "can_withdraw": float(balance.available) >= settings.REWARDS_MIN_PAYOUT,
            "stripe_onboarding_complete": balance.stripe_onboarding_complete,
            "stripe_account_status": balance.stripe_account_status,
        }

    async def add_reward(
        self,
        user_id: str,
        amount: float,
        reward_type: str,
        description: str,
        searcher_tier: str = "free",
        search_log_id: Optional[str] = None,
    ) -> Decimal:
        from app.models.subscription import Subscription
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundException(message="User not found")

        stmt = select(Subscription).where(Subscription.user_id == user_id)
        result = await self.db.execute(stmt)
        sub = result.scalar_one_or_none()
        tier = sub.tier if sub else "free"
        limits = get_tier_limits(tier)

        base_amount = Decimal(str(amount))
        if reward_type == "search_appearance":
            if searcher_tier in ("pro", "ultra"):
                base_amount = Decimal(str(REWARD_RATES["premium_search"]))
            elif searcher_tier == "enterprise":
                base_amount = Decimal(str(REWARD_RATES["enterprise_search"]))

        final_amount = base_amount * Decimal(str(limits.reward_multiplier))

        balance = await self.get_or_create_balance(user)

        new_monthly = Decimal(str(balance.monthly_earned)) + final_amount
        if new_monthly > Decimal(str(limits.monthly_reward_cap)):
            final_amount = Decimal(str(limits.monthly_reward_cap)) - Decimal(str(balance.monthly_earned))
            if final_amount <= 0:
                logger.info(f"⚠️ Monthly cap reached for user {user_id}")
                return Decimal("0")

        ledger = RewardLedger(
            user_id=user_id,
            amount=final_amount,
            reward_type=reward_type,
            description=description,
            status="pending",
            search_log_id=search_log_id,
        )
        self.db.add(ledger)

        balance.pending = Decimal(str(balance.pending)) + final_amount
        balance.lifetime_earned = Decimal(str(balance.lifetime_earned)) + final_amount
        balance.monthly_earned = new_monthly
        balance.lifetime_searches = (balance.lifetime_searches or 0) + 1

        await self.db.commit()

        return final_amount

    async def confirm_pending_rewards(self, user_id: str) -> Dict[str, Any]:
        stmt = select(RewardLedger).where(
            and_(
                RewardLedger.user_id == user_id,
                RewardLedger.status == "pending",
                RewardLedger.created_at < datetime.utcnow() - timedelta(hours=24),
            )
        )
        result = await self.db.execute(stmt)
        pending = result.scalars().all()

        total_confirmed = Decimal("0")

        for ledger in pending:
            ledger.status = "confirmed"
            total_confirmed += Decimal(str(ledger.amount))

        if total_confirmed > 0:
            stmt = select(UserBalance).where(UserBalance.user_id == user_id)
            result = await self.db.execute(stmt)
            balance = result.scalar_one_or_none()

            if balance:
                balance.pending = Decimal(str(balance.pending)) - total_confirmed
                balance.available = Decimal(str(balance.available)) + total_confirmed

            await self.db.commit()

        return {
            "confirmed": float(total_confirmed),
            "count": len(pending),
        }

    async def get_ledger(
        self,
        user: User,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        stmt = select(func.count(RewardLedger.id)).where(RewardLedger.user_id == user.id)
        result = await self.db.execute(stmt)
        total = result.scalar() or 0

        stmt = (
            select(RewardLedger)
            .where(RewardLedger.user_id == user.id)
            .order_by(desc(RewardLedger.created_at))
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        entries = result.scalars().all()

        return {
            "total": total,
            "entries": [
                {
                    "id": str(e.id),
                    "amount": float(e.amount),
                    "type": e.reward_type,
                    "description": e.description,
                    "status": e.status,
                    "created_at": e.created_at.isoformat(),
                }
                for e in entries
            ],
        }

    async def get_earnings_summary(self, user: User) -> Dict[str, Any]:
        """Get earnings breakdown by type"""
        # By type
        stmt = (
            select(
                RewardLedger.reward_type,
                func.count(RewardLedger.id),
                func.sum(RewardLedger.amount),
            )
            .where(RewardLedger.user_id == user.id)
            .group_by(RewardLedger.reward_type)
        )
        result = await self.db.execute(stmt)

        breakdown = {
            row[0]: {
                "count": row[1],
                "total": float(row[2] or 0),
            }
            for row in result.all()
        }

        # By day (last 30 days)
        cutoff = datetime.utcnow() - timedelta(days=30)
        stmt = (
            select(
                func.date(RewardLedger.created_at).label("date"),
                func.sum(RewardLedger.amount),
            )
            .where(
                and_(
                    RewardLedger.user_id == user.id,
                    RewardLedger.created_at >= cutoff,
                )
            )
            .group_by(func.date(RewardLedger.created_at))
            .order_by(func.date(RewardLedger.created_at))
        )
        result = await self.db.execute(stmt)

        daily = [
            {"date": str(row[0]), "amount": float(row[1] or 0)}
            for row in result.all()
        ]

        return {
            "breakdown": breakdown,
            "daily": daily,
        }

    async def request_payout(
        self,
        user: User,
        amount: Optional[float] = None,
    ) -> RewardPayout:
        balance = await self.get_or_create_balance(user)

        if amount is None:
            amount = float(balance.available)

        if amount < settings.REWARDS_MIN_PAYOUT:
            raise BadRequestException(
                message=f"Minimum payout is ${settings.REWARDS_MIN_PAYOUT}",
                details={"minimum": settings.REWARDS_MIN_PAYOUT},
            )

        if amount > float(balance.available):
            raise BadRequestException(
                message="Insufficient balance",
                details={"available": float(balance.available)},
            )

        if not balance.stripe_account_id:
            raise BadRequestException(
                message="Set up payout account first",
                details={"action": "connect_stripe"},
            )

        if not balance.stripe_onboarding_complete:
            raise BadRequestException(
                message="Complete payout account onboarding",
                details={"action": "complete_onboarding"},
            )

        payout = RewardPayout(
            user_id=user.id,
            amount=amount,
            status="pending",
            payout_method="stripe",
            stripe_account_id=balance.stripe_account_id,
        )
        self.db.add(payout)

        balance.available = Decimal(str(balance.available)) - Decimal(str(amount))
        balance.lifetime_paid = Decimal(str(balance.lifetime_paid)) + Decimal(str(amount))

        await self.db.commit()
        await self.db.refresh(payout)

        logger.info(f"💰 Payout requested: ${amount} for {user.email}")
        return payout

    async def get_payout_history(
        self,
        user: User,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        stmt = (
            select(RewardPayout)
            .where(RewardPayout.user_id == user.id)
            .order_by(desc(RewardPayout.requested_at))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        payouts = result.scalars().all()

        return [
            {
                "id": str(p.id),
                "amount": float(p.amount),
                "currency": p.currency,
                "status": p.status,
                "payout_method": p.payout_method,
                "requested_at": p.requested_at.isoformat(),
                "completed_at": p.completed_at.isoformat() if p.completed_at else None,
                "failure_reason": p.failure_reason,
            }
            for p in payouts
        ]