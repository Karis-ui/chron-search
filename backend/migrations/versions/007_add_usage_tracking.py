from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '007_add_usage_tracking'
down_revision = '006_add_billing'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'usage_records',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('period_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_type', sa.String(20), server_default='daily'),
        sa.Column('searches_count', sa.Integer, server_default='0'),
        sa.Column('results_count', sa.Integer, server_default='0'),
        sa.Column('api_calls_count', sa.Integer, server_default='0'),
        sa.Column('exports_count', sa.Integer, server_default='0'),
        sa.Column('boosts_used', sa.Integer, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'period_date', 'period_type', name='uq_usage_user_period'),
    )
    op.create_index('idx_usage_user_date', 'usage_records', ['user_id', 'period_date'])

    op.create_table(
        'saved_searches',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('time_range_days', sa.Integer, server_default='180'),
        sa.Column('platforms', JSONB, server_default='[]'),
        sa.Column('min_confidence', sa.Float, server_default='0.68'),
        sa.Column('biometric_type', sa.String(20), server_default='face'),
        sa.Column('query_media_url', sa.Text),
        sa.Column('query_media_hash', sa.String(64)),
        sa.Column('times_run', sa.Integer, server_default='0'),
        sa.Column('last_run_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_saved_search_user', 'saved_searches', ['user_id'])

    op.create_table(
        'search_alerts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('saved_search_id', UUID(as_uuid=True)),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('min_confidence', sa.Float, server_default='0.75'),
        sa.Column('platforms', JSONB, server_default='[]'),
        sa.Column('notify_email', sa.Boolean, server_default='true'),
        sa.Column('notify_push', sa.Boolean, server_default='true'),
        sa.Column('notify_webhook', sa.Text),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('last_triggered_at', sa.DateTime(timezone=True)),
        sa.Column('trigger_count', sa.Integer, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['saved_search_id'], ['saved_searches.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_alert_user_active', 'search_alerts', ['user_id', 'is_active'])


def downgrade() -> None:
    op.drop_table('search_alerts')
    op.drop_table('saved_searches')
    op.drop_table('usage_records')