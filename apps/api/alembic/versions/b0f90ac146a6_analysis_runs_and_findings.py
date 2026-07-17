"""analysis_runs_and_findings

Revision ID: b0f90ac146a6
Revises: 786118880f25
Create Date: 2026-07-17 22:14:19.464543

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b0f90ac146a6'
down_revision: Union[str, None] = '786118880f25'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'analysis_runs',
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('repository_id', sa.UUID(), nullable=False),
        sa.Column('repository_index_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(), server_default='pending', nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('stats', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id']),
        sa.ForeignKeyConstraint(['repository_index_id'], ['repository_indexes.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "status in ('pending','running','completed','failed')",
            name='ck_analysis_runs_status',
        ),
    )
    op.create_table(
        'findings',
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('analysis_run_id', sa.UUID(), nullable=False),
        sa.Column('repository_index_id', sa.UUID(), nullable=False),
        sa.Column('file_id', sa.UUID(), nullable=False),
        sa.Column('symbol_id', sa.UUID(), nullable=True),
        sa.Column('check_id', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('confidence', sa.String(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('recommended_fix', sa.Text(), nullable=False),
        sa.Column('suggested_test', sa.Text(), nullable=True),
        sa.Column('execution_path', sa.Text(), nullable=True),
        sa.Column('start_line', sa.Integer(), nullable=False),
        sa.Column('end_line', sa.Integer(), nullable=False),
        sa.Column('evidence', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(), server_default='open', nullable=False),
        sa.Column('dismissed_reason', sa.Text(), nullable=True),
        sa.Column('dismissed_at', sa.DateTime(), nullable=True),
        sa.Column('dismissed_by', sa.UUID(), nullable=True),
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['analysis_run_id'], ['analysis_runs.id']),
        sa.ForeignKeyConstraint(['dismissed_by'], ['users.id']),
        sa.ForeignKeyConstraint(['file_id'], ['files.id']),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['repository_index_id'], ['repository_indexes.id']),
        sa.ForeignKeyConstraint(['symbol_id'], ['symbols.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("category in ('bug','security','performance')", name='ck_findings_category'),
        sa.CheckConstraint("severity in ('critical','high','medium','low')", name='ck_findings_severity'),
        sa.CheckConstraint("confidence in ('high','medium','low')", name='ck_findings_confidence'),
        sa.CheckConstraint("status in ('open','dismissed')", name='ck_findings_status'),
    )
    op.create_index('ix_findings_analysis_run_id', 'findings', ['analysis_run_id'])
    op.create_index(
        'ix_findings_repository_index_id_status', 'findings', ['repository_index_id', 'status']
    )


def downgrade() -> None:
    op.drop_index('ix_findings_repository_index_id_status', table_name='findings')
    op.drop_index('ix_findings_analysis_run_id', table_name='findings')
    op.drop_table('findings')
    op.drop_table('analysis_runs')
