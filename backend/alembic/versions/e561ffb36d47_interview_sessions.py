"""interview sessions (phase 4a)

Revision ID: e561ffb36d47
Revises: b7e2d4f6a1c8
Create Date: 2026-08-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e561ffb36d47'
down_revision: Union[str, None] = 'b7e2d4f6a1c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('interview_sessions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('interview_plan_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('current_turn_index', sa.Integer(), nullable=False),
    sa.Column('total_questions', sa.Integer(), nullable=False),
    sa.Column('current_difficulty', sa.Integer(), nullable=False),
    sa.Column('topic_queue', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('asked_questions', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['interview_plan_id'], ['interview_plans.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_interview_sessions_interview_plan_id'), 'interview_sessions', ['interview_plan_id'], unique=False)
    op.create_index(op.f('ix_interview_sessions_user_id'), 'interview_sessions', ['user_id'], unique=False)

    op.create_table('interview_turns',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('session_id', sa.UUID(), nullable=False),
    sa.Column('idx', sa.Integer(), nullable=False),
    sa.Column('topic', sa.String(length=255), nullable=False),
    sa.Column('difficulty', sa.Integer(), nullable=False),
    sa.Column('question_text', sa.Text(), nullable=False),
    sa.Column('answer_text', sa.Text(), nullable=True),
    sa.Column('technical_score', sa.Float(), nullable=True),
    sa.Column('communication_score', sa.Float(), nullable=True),
    sa.Column('completeness_score', sa.Float(), nullable=True),
    sa.Column('rationale', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['session_id'], ['interview_sessions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_interview_turns_session_id'), 'interview_turns', ['session_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_interview_turns_session_id'), table_name='interview_turns')
    op.drop_table('interview_turns')
    op.drop_index(op.f('ix_interview_sessions_user_id'), table_name='interview_sessions')
    op.drop_index(op.f('ix_interview_sessions_interview_plan_id'), table_name='interview_sessions')
    op.drop_table('interview_sessions')
