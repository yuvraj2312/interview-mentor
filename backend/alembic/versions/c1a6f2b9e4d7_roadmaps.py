"""roadmaps (phase 6c)

Revision ID: c1a6f2b9e4d7
Revises: 9b1d4e7c5a3f
Create Date: 2026-09-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c1a6f2b9e4d7'
down_revision: Union[str, None] = '9b1d4e7c5a3f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('roadmaps',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('session_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('summary', sa.Text(), nullable=True),
    sa.Column('strengths', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('growth_areas', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['session_id'], ['interview_sessions.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_roadmaps_user_id'), 'roadmaps', ['user_id'], unique=False)
    op.create_index(op.f('ix_roadmaps_session_id'), 'roadmaps', ['session_id'], unique=True)

    op.create_table('roadmap_items',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('roadmap_id', sa.UUID(), nullable=False),
    sa.Column('topic', sa.String(length=255), nullable=False),
    sa.Column('gap_description', sa.Text(), nullable=False),
    sa.Column('priority', sa.String(length=10), nullable=False),
    sa.Column('recommended_action', sa.Text(), nullable=False),
    sa.Column('matched_resources', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.ForeignKeyConstraint(['roadmap_id'], ['roadmaps.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_roadmap_items_roadmap_id'), 'roadmap_items', ['roadmap_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_roadmap_items_roadmap_id'), table_name='roadmap_items')
    op.drop_table('roadmap_items')
    op.drop_index(op.f('ix_roadmaps_session_id'), table_name='roadmaps')
    op.drop_index(op.f('ix_roadmaps_user_id'), table_name='roadmaps')
    op.drop_table('roadmaps')
