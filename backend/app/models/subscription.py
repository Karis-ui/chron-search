from sqlalchemy import (
    Column, String, DateTime, Float, Integer, Boolean,
    ForeignKey, UniqueConstraint, Index, Text, Numeric
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base

class SubscriptionTier(str,enum.Enum):
    FREE = "free"
    PRO = "pro"
    ULTRA = "ultra"
    ENTERPRISE = "enterprise"

class SubscriptionStatus(str,enum.Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    UNPAID = "unpaid"

class PaymentStatus(str,enum.Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"

class PaymentType(str,enum.Enum):
    SUBSCRIPTION = "subscription"
    BOOST = "boost"
    VERIFICATION = "verification"
    API_CREDITS = "api_credits"
    REWARD_PAYOUT = "reward_payout"

class UsageRecord(Base):
    __tablename__ = "usage_records"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    period_date = Column(DateTime(timezone=True), nullable=False, index=True)
    period_type = Column(String(20), default="daily")  

    searches_count = Column(Integer, default=0)
    results_count = Column(Integer, default=0)
    api_calls_count = Column(Integer, default=0)
    exports_count = Column(Integer, default=0)
    boosts_used = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'period_date', 'period_type', name='uq_usage_user_period'),
        Index('idx_usage_user_date', 'user_id', 'period_date'),
    )

class SavedSearch(Base):
    __tablename__ = "saved_searches"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    description = Column(Text)
    time_range_days = Column(Integer, default=180)
    platforms = Column(JSONB, default=list)
    min_confidence = Column(Float, default=0.68)
    biometric_type = Column(String(20), default="face")

    query_media_url = Column(Text)
    query_media_hash = Column(String(64))

    times_run = Column(Integer, default=0)
    last_run_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class SearchAlert(Base):
    __tablename__ = "search_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    saved_search_id = Column(
        UUID(as_uuid=True),
        ForeignKey("saved_searches.id", ondelete="CASCADE"),
        nullable=True,
    )
    name = Column(String(255), nullable=False)
    min_confidence = Column(Float, default=0.75)
    platforms = Column(JSONB, default=list)
    notify_email = Column(Boolean, default=True)
    notify_push = Column(Boolean, default=True)
    notify_webhook = Column(Text)
    is_active = Column(Boolean, default=True, index=True)
    last_triggered_at = Column(DateTime(timezone=True))
    trigger_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class BoostType(str,enum.Enum):
    STARTER = "starter" 
    STANDARD = "standard" 
    PREMIUM = "premium" 
    EMPLOYER = "employer" 

class VerificationLevel(str,enum.Enum):
    NONE = "none"
    BLUE = "blue"            
    PURPLE = "purple"        
    GOLD = "gold"

class PayoutStatus(str,enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PAID = "paid"
    FAILED = "failed"

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user = relationship("User",back_populates="subscription")
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    stripe_customer_id = Column(String(255), unique=True, index=True)
    stripe_subscription_id = Column(String(255), unique=True, index=True)
    stripe_price_id = Column(String(255))
    stripe_product_id = Column(String(255))
    tier = Column(String(20), nullable=False, default="free", index=True)
    status = Column(String(30), nullable=False, default="active", index=True)
    billing_cycle = Column(String(20), default="monthly")
    current_period_start = Column(DateTime(timezone=True))
    current_period_end = Column(DateTime(timezone=True))
    trial_start = Column(DateTime(timezone=True))
    trial_end = Column(DateTime(timezone=True))
    canceled_at = Column(DateTime(timezone=True))
    cancel_at_period_end = Column(Boolean, default=False)
    amount = Column(Numeric(10, 2), default=0)
    currency = Column(String(3), default="usd")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_sub_tier_status', 'tier', 'status'),
        Index('idx_sub_period_end', 'current_period_end'),
    )

class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user = relationship("User",back_populates="payments")

    stripe_payment_intent_id = Column(String(255), unique=True, index=True)
    stripe_charge_id = Column(String(255), index=True)
    stripe_invoice_id = Column(String(255), index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="usd")
    status = Column(String(30), nullable=False, index=True)
    payment_type = Column(String(30), nullable=False, index=True)
    description = Column(Text)
    metadata_json = Column(JSONB, default=dict)
    reference_id = Column(UUID(as_uuid=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_payment_user_status', 'user_id', 'status'),
        Index('idx_payment_type_date', 'payment_type', 'created_at'),
    )

class ProfileBoost(Base):
    __tablename__ = "profile_boosts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user = relationship("User",back_populates="boosts")
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("consent_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    boost_type = Column(String(30), nullable=False)  
    boost_percentage = Column(Integer, nullable=False)  

    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"))
    amount_paid = Column(Numeric(10, 2), nullable=False)

    starts_at = Column(DateTime(timezone=True), server_default=func.now())
    ends_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True, index=True)

    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_boost_active_end', 'is_active', 'ends_at'),
        Index('idx_boost_profile', 'profile_id', 'is_active'),
    )

class ProfileVerification(Base):
    __tablename__ = "profile_verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user = relationship("User",back_populates="verifications")
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("consent_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    level = Column(String(20), nullable=False)  
    verified_at = Column(DateTime(timezone=True), server_default=func.now())
    verified_by = Column(String(100))  

    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"))
    amount_paid = Column(Numeric(10, 2), nullable=False)

    is_active = Column(Boolean, default=True, index=True)
    expires_at = Column(DateTime(timezone=True))  

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_verify_profile_active', 'profile_id', 'is_active'),
        Index('idx_verify_level', 'level'),
    )

class RewardPayout(Base):
    __tablename__ = "reward_payouts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user = relationship("User",back_populates="payouts")

    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="usd")
    status = Column(String(20), nullable=False) 
    payment_method = Column(String(50),default="Stripe")  
    last_4_digits = Column(String(4))   
    stripe_account_id = Column(String(255),unique=True)
    stripe_transfer_id = Column(String(255),unique=True,index=True)
    stripe_payout_id = Column(String(255), unique=True, index=True)
    failure_reason = Column(Text)
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    __table_args__ = (
        Index('idx_payout_user_status', 'user_id', 'status'),
        Index('idx_payout_date', 'requested_at'),
    )

class UserBalance(Base):
    __tablename__ = "user_balances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    user = relationship("User",back_populates="balance")

    available = Column(Numeric(10, 2), default=0)
    pending = Column(Numeric(10, 2), default=0)
    lifetime_earned = Column(Numeric(10, 2), default=0)
    lifetime_paid = Column(Numeric(10, 2), default=0)
    lifetime_searches = Column(Integer, default=0)
    monthly_earned = Column(Numeric(10, 2), default=0)
    monthly_reset_at = Column(DateTime(timezone=True))
    stripe_account_id = Column(String(255))
    stripe_account_status = Column(String(30)) 
    stripe_onboarding_complete = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_balance_available', 'available'),
    )

class StripeWebhookEvent(Base):
    __tablename__ = "stripe_webhook_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stripe_event_id = Column(String(255), unique=True, nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    data = Column(JSONB, nullable=False)
    processed = Column(Boolean, default=False, index=True)
    processed_at = Column(DateTime(timezone=True))
    processing_error = Column(Text)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        Index('idx_webhook_type_processed', 'event_type', 'processed'),
        Index('idx_webhook_created', 'created_at'),
    )