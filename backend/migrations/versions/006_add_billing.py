from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '006_add_billing'
down_revision = '005_add_consent'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'subscriptions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('stripe_customer_id', sa.String(255), unique=True),
        sa.Column('stripe_subscription_id', sa.String(255), unique=True),
        sa.Column('stripe_price_id', sa.String(255)),
        sa.Column('stripe_product_id', sa.String(255)),
        sa.Column('tier', sa.String(20), nullable=False, server_default='free'),
        sa.Column('status', sa.String(30), nullable=False, server_default='active'),
        sa.Column('billing_cycle', sa.String(20), server_default='monthly'),
        sa.Column('current_period_start', sa.DateTime(timezone=True)),
        sa.Column('current_period_end', sa.DateTime(timezone=True)),
        sa.Column('trial_start', sa.DateTime(timezone=True)),
        sa.Column('trial_end', sa.DateTime(timezone=True)),
        sa.Column('canceled_at', sa.DateTime(timezone=True)),
        sa.Column('cancel_at_period_end', sa.Boolean, server_default='false'),
        sa.Column('amount', sa.Numeric(10, 2), server_default='0'),
        sa.Column('currency', sa.String(3), server_default='usd'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_sub_tier_status', 'subscriptions', ['tier', 'status'])
    op.create_index('idx_sub_period_end', 'subscriptions', ['current_period_end'])

    op.create_table(
        'payments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('stripe_payment_intent_id', sa.String(255), unique=True),
        sa.Column('stripe_charge_id', sa.String(255)),
        sa.Column('stripe_invoice_id', sa.String(255)),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), server_default='usd'),
        sa.Column('status', sa.String(30), nullable=False),
        sa.Column('payment_type', sa.String(30), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('metadata_json', JSONB, server_default='{}'),
        sa.Column('reference_id', UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_payment_user_status', 'payments', ['user_id', 'status'])
    op.create_index('idx_payment_type_date', 'payments', ['payment_type', 'created_at'])

    op.create_table(
        'profile_boosts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('profile_id', UUID(as_uuid=True), nullable=False),
        sa.Column('boost_type', sa.String(30), nullable=False),
        sa.Column('boost_percentage', sa.Integer, nullable=False),
        sa.Column('payment_id', UUID(as_uuid=True)),
        sa.Column('amount_paid', sa.Numeric(10, 2), nullable=False),
        sa.Column('starts_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('ends_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('impressions', sa.Integer, server_default='0'),
        sa.Column('clicks', sa.Integer, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['profile_id'], ['consent_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id']),
    )
    op.create_index('idx_boost_active_end', 'profile_boosts', ['is_active', 'ends_at'])
    op.create_index('idx_boost_profile', 'profile_boosts', ['profile_id', 'is_active'])

    op.create_table(
        'profile_verifications',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('profile_id', UUID(as_uuid=True), nullable=False),
        sa.Column('level', sa.String(20), nullable=False),
        sa.Column('verified_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('verified_by', sa.String(100)),
        sa.Column('payment_id', UUID(as_uuid=True)),
        sa.Column('amount_paid', sa.Numeric(10, 2), nullable=False),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['profile_id'], ['consent_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id']),
    )
    op.create_index('idx_verify_profile_active', 'profile_verifications', ['profile_id', 'is_active'])
    op.create_index('idx_verify_level', 'profile_verifications', ['level'])

    op.create_table(
        'reward_payouts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), server_default='usd'),
        sa.Column('status', sa.String(30), nullable=False, server_default='pending'),
        sa.Column('stripe_transfer_id', sa.String(255), unique=True),
        sa.Column('stripe_payout_id', sa.String(255)),
        sa.Column('stripe_account_id', sa.String(255)),
        sa.Column('payout_method', sa.String(50), server_default='stripe'),
        sa.Column('failure_reason', sa.Text),
        sa.Column('requested_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('processed_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_payout_user_status', 'reward_payouts', ['user_id', 'status'])
    op.create_index('idx_payout_completed', 'reward_payouts', ['completed_at'])

    op.create_table(
        'user_balances',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('available', sa.Numeric(10, 2), server_default='0'),
        sa.Column('pending', sa.Numeric(10, 2), server_default='0'),
        sa.Column('lifetime_earned', sa.Numeric(10, 2), server_default='0'),
        sa.Column('lifetime_paid', sa.Numeric(10, 2), server_default='0'),
        sa.Column('lifetime_searches', sa.Integer, server_default='0'),
        sa.Column('monthly_earned', sa.Numeric(10, 2), server_default='0'),
        sa.Column('monthly_reset_at', sa.DateTime(timezone=True)),
        sa.Column('stripe_account_id', sa.String(255)),
        sa.Column('stripe_account_status', sa.String(30)),
        sa.Column('stripe_onboarding_complete', sa.Boolean, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_balance_available', 'user_balances', ['available'])

    op.create_table(
        'stripe_webhook_events',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('stripe_event_id', sa.String(255), unique=True, nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('data', JSONB, nullable=False),
        sa.Column('processed', sa.Boolean, server_default='false'),
        sa.Column('processed_at', sa.DateTime(timezone=True)),
        sa.Column('processing_error', sa.Text),
        sa.Column('retry_count', sa.Integer, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_webhook_type_processed', 'stripe_webhook_events', ['event_type', 'processed'])
    op.create_index('idx_webhook_created', 'stripe_webhook_events', ['created_at'])


def downgrade() -> None:
    op.drop_table('stripe_webhook_events')
    op.drop_table('user_balances')
    op.drop_table('reward_payouts')
    op.drop_table('profile_verifications')
    op.drop_table('profile_boosts')
    op.drop_table('payments')
    op.drop_table('subscriptions')