"""symbol_relationships_confidence

Revision ID: c4a1f7d8e2b3
Revises: b0f90ac146a6
Create Date: 2026-07-17 22:20:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c4a1f7d8e2b3'
down_revision: Union[str, None] = 'b0f90ac146a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('symbol_relationships', sa.Column('confidence', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('symbol_relationships', 'confidence')
