import stripe
from typing import Optional,Dict,Any,List
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import BadRequestException, NotFoundException
from app.models.domain import User
from app.models.subscription import (
    Subscription, Payment, PaymentStatus, PaymentType,
    SubscriptionTier, SubscriptionStatus, RewardPayout,
    UserBalance, ProfileBoost, ProfileVerification
)

stripe.api_key = settings.STRIPE_SECRET_KEY.get_secret_value()
class StripeService:
    def __init__(self,db:AsyncSession):
        self.db = db
    
    async def get_or_create_customer(self,user:User) -> str:
        stmt = select(Subscription).where(Subscription.user_id == user.id)
        result = await self.db.execute(stmt)
        sub = result.scalar_one_or_none()
        if sub and sub.stripe_customer_id:
            return sub.stripe_customer_id
        
        logger.info("Creating new Stripe customer for user %s", user.id)
        try:
            customer = stripe.Customer.create(
                email = user.email,
                name = user.display_name or user.name,
                metadata = {
                    "user_id": str(user.id),
                    "type": "user"
                }
            )
            if not sub:
                sub = Subscription(
                    user_id=user.id,
                    status=SubscriptionStatus.active,
                    tier=SubscriptionTier.free,
                    stripe_customer_id = customer.id
                )
                self.db.add(sub)
            else:
                sub.stripe_customer_id = customer.id
            await self.db.commit()
            await self.db.refresh(sub)
            return customer.id
        except stripe.error.StripeError as e:
            logger.error("Stripe customer creation failed for user %s: %s", user.id, e)
            raise
    
    async def create_subscription_checkout(
        self,
        user: User,
        price_id: str,
        success_url: str,
        cancel_url: str,
        trial_days: int = 0,
    ) -> Dict[str,str]:
            customer_id = await self.get_or_create_customer(user)
            try:
                session_params = {
                "customer": customer_id,
                "mode": "subscription",
                "payment_method_types": ["card"],
                "line_items": [
                    {
                        "price": price_id,
                        "quantity": 1,
                    }
                ],
                "success_url": success_url,
                "cancel_url": cancel_url,
                "metadata": {
                    "user_id": str(user.id),
                    "type": "subscription",
                },
                "subscription_data": {
                    "metadata": {
                        "user_id": str(user.id),
                    }
                },
                "allow_promotion_codes": True,
                "billing_address_collection": "auto",
                }
                if trial_days > 0:
                    session_params["subscription_data"]["trial_end"] = int((datetime.utcnow() + timedelta(days=trial_days)).timestamp())
                session = stripe.checkout.Session.create(**session_params)
                return {
                    "checkout_url": session.url
                }
            except stripe.error.StripeError as e:
                logger.error("Stripe checkout creation failed for user %s: %s", user.id, e)
                raise

    
    async def create_boost_checkout(
        self,
        user: User,
        boost_type: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
    ) -> str:
        customer_id = await self.get_or_create_customer(user)
        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                mode="payment",
                payment_method_options=[{"type":"card"}],
                line_items=[{"price": price_id, "quantity": 1}],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "user_id": str(user.id),
                    "type": "boost",
                    "boost_type": boost_type,
                },
            )
            logger.info(f"Stripe checkout session created for user {user.id} : {session.id}")
            return {
                "checkout_url": session.url
            }
        except stripe.error.StripeError as e:
            logger.error("Stripe checkout creation failed for user %s: %s", user.id, e)
            raise BadRequestException(message=f"Boost checkout failed: {str(e)}")
    
    async def create_verification_checkout(
        self,
        user: User,
        level: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
    ) -> str:
        customer_id = await self.get_or_create_customer(user)
        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                mode="payment",
                payment_method_options=[{"type":"card"}],
                line_items=[{"price": price_id, "quantity": 1}],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "user_id": str(user.id),
                    "type": "verification",
                    "level": level,
                },
            )
            logger.info(f"Stripe checkout session created for user {user.id} : {session.id}")
            return {
                "checkout_url": session.url
            }
        except stripe.error.StripeError as e:
            logger.error("Stripe checkout creation failed for user %s: %s", user.id, e)
            raise BadRequestException(message=f"Verification checkout failed: {str(e)}")
    
    async def create_customer_portal_session(
        self,user:User,return_url:str
    ) -> str:
        customer_id = await self.get_or_create_customer(user)
        try:
            session = stripe.billing.Portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            logger.info(f"Stripe customer portal session created for user {user.id} : {session.id}")
            return {
                "portal_url": session.url
            }
        except stripe.error.StripeError as e:
            logger.error("Stripe customer portal session creation failed for user %s: %s", user.id, e)
            raise BadRequestException(message=f"Customer portal session creation failed: {str(e)}")
    
    async def cancel_subscription(
        self,user:User,immediate:bool = False
    )-> bool:
        stmt = select(Subscription).where(Subscription.user_id == user.id)
        result = await self.db.execute(stmt)
        sub = result.scalar_one_or_none()

        if not sub or not sub.stripe_subscription_id:
            return NotFoundException("No active subscription found for user")
        
        try:
            if immediate:
                stripe.Subscription.delete(sub.stripe_subscription_id)
                sub.status = SubscriptionStatus.cancelled
                sub.cancelled_at = datetime.utcnow()
                await self.db.commit()
                return True
            else:
                stripe.Subscription.modify(
                    sub.stripe_subscription_id,
                    cancel_at_period_end = True,
                )
                sub.cancelled_at = datetime.utcnow()
                await self.db.commit()
                return True
        except stripe.error.StripeError as e:
            logger.error("Stripe subscription cancellation failed for user %s: %s", user.id, e)
            raise BadRequestException(message=f"Subscription cancellation failed: {str(e)}")
    
    async def resume_subscription(self,user:User) -> bool:
        stmt = select(Subscription).where(Subscription.user_id == user.id)
        result = await self.db.execute(stmt)
        sub = result.scalar_one_or_none()

        if not sub or not sub.stripe_subscription_id:
            return False
        
        try:
            stripe.Subscription.resume(sub.stripe_subscription_id)
            sub.status = SubscriptionStatus.active
            sub.cancelled_at = None
            await self.db.commit()
            return True
        except stripe.error.StripeError as e:
            logger.error("Stripe subscription resumption failed for user %s: %s", user.id, e)
            raise BadRequestException(message=f"Subscription resumption failed: {str(e)}")
        
    async def create_connect_account(self,user:User) -> str:
        stmt = select(UserBalance).where(UserBalance.user_id == user.id)
        result = await self.db.execute(stmt)
        balance = result.scalar_one_or_none()

        if balance and balance.stripe_account_id:
            return balance.stripe_account_id
        try:
            account = stripe.Account.create(
                type="express",
                email=user.email,
                capabilities={
                    "transfers":{"requested":True}
                },
                metadata={"user_id":str(user.id)}
            )
            if balance:
                balance.stripe_account_id = account.id
                balance.stripe_account_status = "pending"
            else:
                balance = UserBalance(user_id=user.id,stripe_account_id=account.id)
            await self.db.commit()
            return account.id
        except stripe.error.StripeError as e:
            logger.error("Stripe connect account creation failed for user %s: %s", user.id, e)
            raise BadRequestException(message=f"Connect account creation failed: {str(e)}")
    
    async def create_connect_onboarding_link(
        self,
        user: User,
        return_url: str,
        refresh_url: str,
    ) -> str:
        account_id = await self.create_connect_account(user)

        try:
            link = stripe.AccountLink.create(
                account=account_id,
                return_url=return_url,
                refresh_url=refresh_url,
                type="account_onboarding",
            )
            return link.url

        except stripe.error.StripeError as e:
            raise BadRequestException(message=f"Onboarding link failed: {str(e)}")

    async def create_transfer(
        self,
        user: User,
        amount_cents: int,
        description: str,
    ) -> Dict[str, Any]:
        stmt = select(UserBalance).where(UserBalance.user_id == user.id)
        result = await self.db.execute(stmt)
        balance = result.scalar_one_or_none()

        if not balance or not balance.stripe_account_id:
            raise BadRequestException(message="No Connect account found")

        if not balance.stripe_onboarding_complete:
            raise BadRequestException(message="Complete Stripe onboarding first")

        try:
            transfer = stripe.Transfer.create(
                amount=amount_cents,
                currency="usd",
                destination=balance.stripe_account_id,
                description=description,
                metadata={"user_id": str(user.id)},
            )

            logger.info(f"✅ Transfer created: {transfer.id}")
            return {
                "transfer_id": transfer.id,
                "amount": amount_cents / 100,
                "status": "completed",
            }

        except stripe.error.StripeError as e:
            raise BadRequestException(message=f"Transfer failed: {str(e)}")

    def verify_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                settings.STRIPE_WEBHOOK_SECRET.get_secret_value(),
            )
            return event

        except ValueError as e:
            raise BadRequestException(message="Invalid webhook payload")
        except stripe.error.SignatureVerificationError as e:
            raise BadRequestException(message="Invalid webhook signature")

    async def get_subscription(self, user: User) -> Optional[Subscription]:
        stmt = select(Subscription).where(Subscription.user_id == user.id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_payment_history(
        self,
        user: User,
        limit: int = 50,
    ) -> List[Payment]:
        stmt = (
            select(Payment)
            .where(Payment.user_id == user.id)
            .order_by(Payment.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())