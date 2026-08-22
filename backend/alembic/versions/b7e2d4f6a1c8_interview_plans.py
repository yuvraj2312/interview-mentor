"""interview plans

Revision ID: b7e2d4f6a1c8
Revises: a3f1c9d2e0b4
Create Date: 2026-08-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b7e2d4f6a1c8'
down_revision: Union[str, None] = 'a3f1c9d2e0b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('interview_plans',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('resume_id', sa.UUID(), nullable=False),
    sa.Column('job_description_id', sa.UUID(), nullable=False),
    sa.Column('skill_gap_analysis_id', sa.UUID(), nullable=False),
    sa.Column('format', sa.String(length=20), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('question_count', sa.Integer(), nullable=True),
    sa.Column('topic_mix', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('difficulty_min', sa.Integer(), nullable=True),
    sa.Column('difficulty_max', sa.Integer(), nullable=True),
    sa.Column('candidate_level', sa.String(length=20), nullable=True),
    sa.Column('rationale', sa.Text(), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['job_description_id'], ['job_descriptions.id'], ),
    sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ),
    sa.ForeignKeyConstraint(['skill_gap_analysis_id'], ['skill_gap_analyses.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_interview_plans_job_description_id'), 'interview_plans', ['job_description_id'], unique=False)
    op.create_index(op.f('ix_interview_plans_resume_id'), 'interview_plans', ['resume_id'], unique=False)
    op.create_index(op.f('ix_interview_plans_skill_gap_analysis_id'), 'interview_plans', ['skill_gap_analysis_id'], unique=False)
    op.create_index(op.f('ix_interview_plans_user_id'), 'interview_plans', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_interview_plans_user_id'), table_name='interview_plans')
    op.drop_index(op.f('ix_interview_plans_skill_gap_analysis_id'), table_name='interview_plans')
    op.drop_index(op.f('ix_interview_plans_resume_id'), table_name='interview_plans')
    op.drop_index(op.f('ix_interview_plans_job_description_id'), table_name='interview_plans')
    op.drop_table('interview_plans')
