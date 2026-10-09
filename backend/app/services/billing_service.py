from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.models.domain import User
from app.models.subscription import (
    Subscription, Payment, PaymentStatus, PaymentType,
    SubscriptionStatus, UserBalance, ProfileBoost, ProfileVerification,
)


class BillingService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def handle_webhook(self, event: Dict[str, Any]) -> None:
        event_type = event["type"]
        data = event["data"]["object"]

        handlers = {
            "checkout.session.completed": self._handle_checkout_completed,
            "customer.subscription.created": self._handle_subscription_created,
            "customer.subscription.updated": self._handle_subscription_updated,
            "customer.subscription.deleted": self._handle_subscription_deleted,
            "invoice.payment_succeeded": self._handle_payment_succeeded,
            "invoice.payment_failed": self._handle_payment_failed,
            "account.updated": self._handle_account_updated,
        }

        handler = handlers.get(event_type)
        if handler:
            await handler(data)
        else:
            logger.info(f"Unhandled webhook: {event_type}")


    async def _handle_checkout_completed(self, session: Dict[str, Any]) -> None:
        metadata = session.get("metadata", {})
        user_id = metadata.get("user_id")
        checkout_type = metadata.get("type")

        if not user_id:
            return

        logger.info(f"✅ Checkout completed: {checkout_type} for user {user_id}")

        if checkout_type == "subscription":
            pass

        elif checkout_type == "boost":
            await self._process_boost_purchase(user_id, metadata, session)

        elif checkout_type == "verification":
            await self._process_verification_purchase(user_id, metadata, session)
        payment = Payment(
            user_id=user_id,
            stripe_payment_intent_id=session.get("payment_intent"),
            amount=(session.get("amount_total") or 0) / 100,
            currency=session.get("currency", "usd"),
            status="succeeded",
            payment_type=checkout_type or "unknown",
            description=f"Stripe Checkout: {checkout_type}",
            metadata_json=session,
        )
        self.db.add(payment)
        await self.db.commit()

    async def _handle_subscription_created(self, subscription: Dict[str, Any]) -> None:
        metadata = subscription.get("metadata", {})
        user_id = metadata.get("user_id")

        if not user_id:
            logger.warning("Subscription created without user_id")
            return

        stmt = select(Subscription).where(Subscription.user_id == user_id)
        result = await self.db.execute(stmt)
        sub = result.scalar_one_or_none()

        price_id = subscription["items"]["data"][0]["price"]["id"]
        tier = self._get_tier_from_price(price_id)

        if not sub:
            sub = Subscription(user_id=user_id)
            self.db.add(sub)

        sub.stripe_subscription_id = subscription["id"]
        sub.stripe_customer_id = subscription["customer"]
        sub.stripe_price_id = price_id
        sub.tier = tier
        sub.status = subscription["status"]
        sub.current_period_start = datetime.fromtimestamp(subscription["current_period_start"])
        sub.current_period_end = datetime.fromtimestamp(subscription["current_period_end"])
        sub.amount = subscription["items"]["data"][0]["price"]["unit_amount"] / 100
        sub.currency = subscription["currency"]

        if subscription.get("trial_end"):
            sub.trial_end = datetime.fromtimestamp(subscription["trial_end"])

        await self.db.commit()

        logger.info(f"✅ Subscription created: {tier} for user {user_id}")

    async def _handle_subscription_updated(self, subscription: Dict[str, Any]) -> None:
        stmt = select(Subscription).where(
            Subscription.stripe_subscription_id == subscription["id"]
        )
        result = await self.db.execute(stmt)
        sub = result.scalar_one_or_none()

        if not sub:
            return

        sub.status = subscription["status"]
        sub.current_period_end = datetime.fromtimestamp(subscription["current_period_end"])
        sub.cancel_at_period_end = subscription.get("cancel_at_period_end", False)

        if subscription["status"] == "canceled":
            sub.canceled_at = datetime.utcnow()

        await self.db.commit()

    async def _handle_subscription_deleted(self, subscription: Dict[str, Any]) -> None:
        stmt = select(Subscription).where(
            Subscription.stripe_subscription_id == subscription["id"]
        )
        result = await self.db.execute(stmt)
        sub = result.scalar_one_or_none()

        if not sub:
            return

        sub.status = "cancelled"
        sub.tier = "free"
        sub.canceled_at = datetime.utcnow()

        await self.db.commit()

        logger.info(f"❌ Subscription cancelled: user {sub.user_id}")

    async def _handle_payment_succeeded(self, invoice: Dict[str, Any]) -> None:
        customer_id = invoice.get("customer")

        stmt = select(Subscription).where(Subscription.stripe_customer_id == customer_id)
        result = await self.db.execute(stmt)
        sub = result.scalar_one_or_none()

        if sub:
            sub.status = "active"
            await self.db.commit()

    async def _handle_payment_failed(self, invoice: Dict[str, Any]) -> None:
        customer_id = invoice.get("customer")

        stmt = select(Subscription).where(Subscription.stripe_customer_id == customer_id)
        result = await self.db.execute(stmt)
        sub = result.scalar_one_or_none()

        if sub:
            sub.status = "past_due"
            await self.db.commit()

    async def _handle_account_updated(self, account: Dict[str, Any]) -> None:
        account_id = account["id"]

        stmt = select(UserBalance).where(UserBalance.stripe_account_id == account_id)
        result = await self.db.execute(stmt)
        balance = result.scalar_one_or_none()

        if not balance:
            return

        if account.get("charges_enabled") and account.get("payouts_enabled"):
            balance.stripe_onboarding_complete = True
            balance.stripe_account_status = "verified"
        elif account.get("requirements", {}).get("disabled_reason"):
            balance.stripe_account_status = "restricted"

        await self.db.commit()

    async def _process_boost_purchase(
        self,
        user_id: str,
        metadata: Dict[str, Any],
        session: Dict[str, Any],
    ) -> None:
        from app.core.config import settings

        boost_type = metadata.get("boost_type", "starter")
        config = {
            "starter": {"days": 7, "pct": 25, "amount": 4.99},
            "standard": {"days": 30, "pct": 50, "amount": 14.99},
            "premium": {"days": 90, "pct": 100, "amount": 49.99},
            "employer": {"days": 30, "pct": 200, "amount": 199.99},
        }[boost_type]

        from app.models.domain import ConsentProfile
        stmt = select(ConsentProfile).where(ConsentProfile.user_id == user_id)
        result = await self.db.execute(stmt)
        profile = result.scalar_one_or_none()

        if not profile:
            logger.warning(f"Boost purchased but no consent profile: {user_id}")
            return

        boost = ProfileBoost(
            user_id=user_id,
            profile_id=profile.id,
            boost_type=boost_type,
            boost_percentage=config["pct"],
            amount_paid=config["amount"],
            ends_at=datetime.utcnow() + timedelta(days=config["days"]),
        )
        self.db.add(boost)
        await self.db.commit()

        logger.info(f"⚡ Boost activated: {boost_type} for {user_id}")

    async def _process_verification_purchase(
        self,
        user_id: str,
        metadata: Dict[str, Any],
        session: Dict[str, Any],
    ) -> None:
        level = metadata.get("level", "blue")

        config = {
            "blue": {"amount": 9.99},
            "purple": {"amount": 29.99},
            "gold": {"amount": 99.99},
        }[level]

        from app.models.domain import ConsentProfile
        stmt = select(ConsentProfile).where(ConsentProfile.user_id == user_id)
        result = await self.db.execute(stmt)
        profile = result.scalar_one_or_none()

        if not profile:
            return

        verification = ProfileVerification(
            user_id=user_id,
            profile_id=profile.id,
            level=level,
            amount_paid=config["amount"],
            verified_by="auto",
            expires_at=datetime.utcnow() + timedelta(days=365),
        )
        self.db.add(verification)

        profile.is_verified = True

        await self.db.commit()

        logger.info(f"✅ Verification: {level} for {user_id}")

    def _get_tier_from_price(self, price_id: str) -> str:
        from app.core.config import settings

        if price_id in [
            settings.STRIPE_PRICE_PRO_MONTHLY,
            settings.STRIPE_PRICE_PRO_YEARLY,
        ]:
            return "pro"
        if price_id in [
            settings.STRIPE_PRICE_ULTRA_MONTHLY,
            settings.STRIPE_PRICE_ULTRA_YEARLY,
        ]:
            return "ultra"
        return "free"