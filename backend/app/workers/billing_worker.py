from celery import Task
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select, and_, update
from decimal import Decimal

from app.workers.celery_app import celery_app
from app.core.logger import logger
from app.core.database import get_async_db
from app.core.config import settings
from app.models.subscription import (
    Subscription, RewardPayout, PayoutStatus,
    UserBalance, UsageRecord, StripeWebhookEvent
)
from app.models.domain import User, RewardLedger

@celery_app.task(bind=True,name="app.workers.billing_worker.confirm_pending_rewards")
def confirm_pending_rewards(kself) -> bool:
    logger.info("Confirming pending rewards...")
    async def run():
        async with get_async_db() as db:
            from app.services.rewards_service import RewardsService
            cutoff = datetime.utcnow() - timedelta(hours=24)
            stmt = select(RewardLedger).where(
                and_(
                    RewardLedger.status == "pending",
                    RewardLedger.created_at < cutoff
                )
            ).distinct()
            result = await db.execute(stmt)
            user_ids = [row[0].user_id for row in result.all()]
            total_confirmed = 0

            for user_id in user_ids:
                service = RewardsService(db)
                result = await service.confirm_pending_rewards(str(user_id))
                total_confirmed += result.get("confirmed")
            
            return {
                "users_processed": len(user_ids),
                "total_confirmed": total_confirmed,
                "timestamp": datetime.utcnow().isoformat(),
            }
        
        try:
            result = asyncio.run(run())
            logger.info(f"Confirmed {result['total_confirmed']} pending rewards across {result['users_processed']} users")
            return result
        except Exception as e:
            logger.error(f"Error confirming pending rewards: {e}")
            raise

@celery_app.task(bind=True, name="app.workers.billing_worker.reset_monthly_usage")
def reset_monthly_usage(self) -> dict:
    logger.info("Resetting monthly usage...")
    async def run():
        async with get_async_db() as db:
            now = datetime.utcnow()
            month_start = now.replace(day=1,hour=0,minute=0,second=0,microsecond=0)
            stmt = update(UserBalance).where(UserBalance.monthly_reset_at < month_start).values(
                monthly_earned=0,
                monthly_withdrawals=0,
                monthly_reset_at=now
            )
            await db.execute(stmt)
            await db.commit()

            return {
                "status": "success",
                "balance_reset": result.rowcount,
                "timestamp": datetime.utcnow().isoformat(),
            }
    
    try:
        result = asyncio.run(run())
        logger.info(f"Monthly usage reset complete: {result}")
        return result
    except Exception as e:
        logger.error(f"Error resetting monthly usage: {e}")
        raise

@celery_app.task(bind=True, name="app.workers.billing_worker.process_payouts")
def process_payouts(self) -> dict:
    logger.info("Processing payouts...")
    async def run():
        from app.models.domain import User
        from app.services.stripe_service import StripeService
        async with get_async_db() as db:
            from app.services.rewards_service import RewardsService
            stmt = select(RewardPayout).where(
                RewardPayout.status == "pending"
            )
            result = await db.execute(stmt)
            payouts = result.scalars().all()
            processed = 0
            failed = 0

            for payout in payouts:
                try:
                    stmt = select(User).where(User.id == payout.user_id)
                    user_result = await db.execute(stmt)
                    user = user_result.scalar_one_or_none()
                    if not user:
                        payout.status = "failed"
                        payout.failure_reason = "User not found"
                        failed += 1
                        continue
                    await db.execute(stmt)
                    await db.commit()
                    service = StripeService()
                    await service.create_transfer(user=user,amount_cents=int(float(payout.amount) * 100),description=f"Chronos Rewards Payout - {payout.id}")
                    payout.status = "processed"
                    payout.processed_at = datetime.utcnow()
                    payout.processed_at = datetime.utcnow()
                    processed += 1
                    await db.execute(payout)
                    await db.commit()
                    processed += 1
                except Exception as e:
                    logger.error(f"Failed to process payout {payout.id}: {e}")
                    failed += 1
            logger.info(f"Processed {processed} payouts")
            await db.commit()
            return {
                "processed": processed,
                "failed": failed,
                "total": len(payouts),
                "timestamp": datetime.utcnow().isoformat(),
            }
        
        try:
            result = asyncio.run(run())
            logger.info(f"Processed {result['processed']} payouts")
            return result
        except Exception as e:
            logger.error(f"Error processing payouts: {e}")
            raise

@celery_app.task(bind=True, name="app.workers.billing_worker.retry_failed_webhooks")
def retry_failed_webhooks(self) -> dict:
    logger.info("Retrying failed webhooks...")
    async def run():
        async with get_async_db() as db:
            from app.services.billing_service import BillingService

            cutoff = datetime.utcnow() - timedelta(hours=24)
            stmt = select(StripeWebhookEvent).where(
                and_(
                    StripeWebhookEvent.processed == False,
                    StripeWebhookEvent.retry_count < 3,
                    StripeWebhookEvent.created_at > cutoff,
                )
            ).limit(20)
            result = await db.execute(stmt)
            events = result.scalars().all()
            succeeded = 0
            retried = 0

            for event in events:
                try:
                    service = BillingService(db)
                    await service.handle_webhook(event.data)
                    event.processed = True
                    event.processed_at = datetime.utcnow()
                    event.retry_count += 1
                    succeeded += 1
                    await db.execute(event)
                    await db.commit()
                except Exception as e:
                    event.retry_count += 1
                    event.failure_reason = str(e)
                    logger.error(f"Failed to process webhook {event.id}: {e}")
                    await db.execute(event)
                    retried += 1
                    await db.commit()

            return {
                "succeeded": succeeded,
                "retried": retried,
                "failed": len(events) - succeeded - retried,
                "total": len(events),
                "timestamp": datetime.utcnow().isoformat(),
            }
        
        try:
            result = asyncio.run(run())
            logger.info(f"Processed {result['processed']} webhooks")
            return result
        except Exception as e:
            logger.error(f"Error processing webhooks: {e}")
            raise

@celery_app.task(bind=True, name="app.workers.billing_worker.check_expired_trials")
def check_expired_trials(self) -> dict:
    logger.info("⏰ Checking expired trials...")

    async def _run():
        async with get_async_db() as db:
            now = datetime.utcnow()

            stmt = select(Subscription).where(
                and_(
                    Subscription.status == "trialing",
                    Subscription.trial_end < now,
                    Subscription.stripe_subscription_id.is_(None),  # No Stripe sub
                )
            )

            result = await db.execute(stmt)
            trials = result.scalars().all()

            downgraded = 0
            for sub in trials:
                sub.tier = "free"
                sub.status = "active"
                downgraded += 1

            await db.commit()

            return {
                "downgraded": downgraded,
                "timestamp": now.isoformat(),
            }

    try:
        result = asyncio.run(_run())
        logger.info(f"✅ Trials checked: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ Trial check failed: {e}", exc_info=True)
        raise


@celery_app.task(bind=True, name="app.workers.billing_worker.expire_boosts")
def expire_boosts(self) -> dict:
    logger.info("⚡ Expiring old boosts...")

    async def _run():
        async with get_async_db() as db:
            from app.models.subscription import ProfileBoost

            now = datetime.utcnow()

            stmt = (
                update(ProfileBoost)
                .where(
                    and_(
                        ProfileBoost.is_active == True,
                        ProfileBoost.ends_at < now,
                    )
                )
                .values(is_active=False)
            )
            result = await db.execute(stmt)
            await db.commit()

            return {
                "expired": result.rowcount,
                "timestamp": now.isoformat(),
            }

    try:
        result = asyncio.run(_run())
        logger.info(f"✅ Boosts expired: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ Boost expiry failed: {e}", exc_info=True)
        raise