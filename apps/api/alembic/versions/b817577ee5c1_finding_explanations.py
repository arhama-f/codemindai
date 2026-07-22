"""finding_explanations

Revision ID: b817577ee5c1
Revises: e6c3a8d2f9b1
Create Date: 2026-07-20 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b817577ee5c1'
down_revision: Union[str, None] = 'e6c3a8d2f9b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'finding_explanations',
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('finding_id', sa.UUID(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('generated_by', sa.String(), nullable=False),
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['finding_id'], ['findings.id']),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("generated_by in ('mock','claude')", name='ck_finding_explanations_generated_by'),
    )
    op.create_index('ix_finding_explanations_finding_id', 'finding_explanations', ['finding_id'])


def downgrade() -> None:
    op.drop_index('ix_finding_explanations_finding_id', table_name='finding_explanations')
    op.drop_table('finding_explanations')
