"""skill profiles (phase 6b)

Revision ID: 9b1d4e7c5a3f
Revises: d8f3c56a9e12
Create Date: 2026-09-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b1d4e7c5a3f'
down_revision: Union[str, None] = 'd8f3c56a9e12'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('skill_profiles',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('sessions_completed', sa.Integer(), nullable=False),
    sa.Column('overall_avg_technical_score', sa.Float(), nullable=True),
    sa.Column('overall_avg_communication_score', sa.Float(), nullable=True),
    sa.Column('overall_avg_completeness_score', sa.Float(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_skill_profiles_user_id'), 'skill_profiles', ['user_id'], unique=True)

    op.create_table('skill_profile_topic_stats',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('skill_profile_id', sa.UUID(), nullable=False),
    sa.Column('topic_key', sa.String(length=255), nullable=False),
    sa.Column('topic_label', sa.String(length=255), nullable=False),
    sa.Column('sessions_count', sa.Integer(), nullable=False),
    sa.Column('turns_count', sa.Integer(), nullable=False),
    sa.Column('avg_technical_score', sa.Float(), nullable=False),
    sa.Column('avg_communication_score', sa.Float(), nullable=False),
    sa.Column('avg_completeness_score', sa.Float(), nullable=False),
    sa.Column('last_session_score', sa.Float(), nullable=False),
    sa.Column('previous_session_score', sa.Float(), nullable=True),
    sa.Column('trend', sa.String(length=20), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['skill_profile_id'], ['skill_profiles.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('skill_profile_id', 'topic_key', name='uq_skill_profile_topic')
    )
    op.create_index(op.f('ix_skill_profile_topic_stats_skill_profile_id'), 'skill_profile_topic_stats', ['skill_profile_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_skill_profile_topic_stats_skill_profile_id'), table_name='skill_profile_topic_stats')
    op.drop_table('skill_profile_topic_stats')
    op.drop_index(op.f('ix_skill_profiles_user_id'), table_name='skill_profiles')
    op.drop_table('skill_profiles')
