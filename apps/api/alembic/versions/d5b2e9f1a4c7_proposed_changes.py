"""proposed_changes

Revision ID: d5b2e9f1a4c7
Revises: c4a1f7d8e2b3
Create Date: 2026-07-18 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd5b2e9f1a4c7'
down_revision: Union[str, None] = 'c4a1f7d8e2b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'proposed_changes',
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('finding_id', sa.UUID(), nullable=False),
        sa.Column('file_id', sa.UUID(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('updated_content', sa.Text(), nullable=False),
        sa.Column('test_file_path', sa.Text(), nullable=True),
        sa.Column('test_file_content', sa.Text(), nullable=True),
        sa.Column('generated_by', sa.String(), nullable=False),
        sa.Column('status', sa.String(), server_default='draft', nullable=False),
        sa.Column('pr_url', sa.Text(), nullable=True),
        sa.Column('pr_number', sa.Integer(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('published_by', sa.UUID(), nullable=True),
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['file_id'], ['files.id']),
        sa.ForeignKeyConstraint(['finding_id'], ['findings.id']),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['published_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("generated_by in ('mock','claude')", name='ck_proposed_changes_generated_by'),
        sa.CheckConstraint("status in ('draft','published')", name='ck_proposed_changes_status'),
    )
    op.create_index('ix_proposed_changes_finding_id', 'proposed_changes', ['finding_id'])


def downgrade() -> None:
    op.drop_index('ix_proposed_changes_finding_id', table_name='proposed_changes')
    op.drop_table('proposed_changes')
