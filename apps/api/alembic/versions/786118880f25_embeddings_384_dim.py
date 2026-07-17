"""embeddings_384_dim

Revision ID: 786118880f25
Revises: c2da1df6d998
Create Date: 2026-07-17 02:32:55.476009

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '786118880f25'
down_revision: Union[str, None] = 'c2da1df6d998'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # `embeddings.vector` has never had a row written to it — this is a pure
    # schema change (no data migration needed) to match the real embedding
    # model's dimension (all-MiniLM-L6-v2, 384) instead of the placeholder
    # 1536 chosen before any provider was picked.
    op.drop_column('embeddings', 'vector')
    op.add_column('embeddings', sa.Column('vector', Vector(384), nullable=True))


def downgrade() -> None:
    op.drop_column('embeddings', 'vector')
    op.add_column('embeddings', sa.Column('vector', Vector(1536), nullable=True))
