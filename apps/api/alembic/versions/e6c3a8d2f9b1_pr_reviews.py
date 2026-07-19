"""pr_reviews

Revision ID: e6c3a8d2f9b1
Revises: d5b2e9f1a4c7
Create Date: 2026-07-19 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e6c3a8d2f9b1'
down_revision: Union[str, None] = 'd5b2e9f1a4c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'pr_reviews',
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('owner', sa.String(), nullable=False),
        sa.Column('repo', sa.String(), nullable=False),
        sa.Column('pr_number', sa.Integer(), nullable=False),
        sa.Column('commit_sha', sa.String(), nullable=False),
        sa.Column('findings_count', sa.Integer(), nullable=False),
        sa.Column('comments_posted', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('review_url', sa.Text(), nullable=True),
        sa.Column('reviewed_by', sa.UUID(), nullable=False),
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("status in ('success','failure')", name='ck_pr_reviews_status'),
    )
    op.create_index('ix_pr_reviews_organization_id', 'pr_reviews', ['organization_id'])


def downgrade() -> None:
    op.drop_index('ix_pr_reviews_organization_id', table_name='pr_reviews')
    op.drop_table('pr_reviews')
