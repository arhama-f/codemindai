"""subscriptions

Revision ID: d37269c7c01c
Revises: 8e39503dfeb4
Create Date: 2026-08-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd37269c7c01c'
down_revision: Union[str, None] = '8e39503dfeb4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'subscriptions',
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('plan', sa.String(), server_default='free', nullable=False),
        sa.Column('status', sa.String(), server_default='active', nullable=False),
        sa.Column('stripe_customer_id', sa.String(), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(), nullable=True),
        sa.Column('current_period_end', sa.DateTime(), nullable=True),
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id'),
        sa.UniqueConstraint('stripe_subscription_id'),
        sa.CheckConstraint("plan in ('free','pro','team')", name='ck_subscriptions_plan'),
        sa.CheckConstraint(
            "status in ('active','past_due','canceled','trialing')", name='ck_subscriptions_status'
        ),
    )

    # Backfill a free subscription for every organization created before this
    # migration — new orgs get one inline at creation time going forward.
    op.execute(
        """
        INSERT INTO subscriptions (organization_id, plan, status)
        SELECT id, 'free', 'active' FROM organizations
        """
    )


def downgrade() -> None:
    op.drop_table('subscriptions')
