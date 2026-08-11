"""github installation access token

Revision ID: f1a2b3c4d5e6
Revises: d37269c7c01c
Create Date: 2026-08-10 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'd37269c7c01c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('github_installations', sa.Column('access_token', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('github_installations', 'access_token')
