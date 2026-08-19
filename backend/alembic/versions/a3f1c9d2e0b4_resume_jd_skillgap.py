"""resume jd skillgap

Revision ID: a3f1c9d2e0b4
Revises: 07833fa47b18
Create Date: 2026-08-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a3f1c9d2e0b4'
down_revision: Union[str, None] = '07833fa47b18'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('resumes',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('original_filename', sa.String(length=255), nullable=False),
    sa.Column('content_type', sa.String(length=100), nullable=False),
    sa.Column('storage_key', sa.String(length=512), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('extracted_text', sa.Text(), nullable=True),
    sa.Column('structured_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('low_confidence_fields', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resumes_user_id'), 'resumes', ['user_id'], unique=False)

    op.create_table('job_descriptions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('raw_text', sa.Text(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('structured_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('low_confidence_fields', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_job_descriptions_user_id'), 'job_descriptions', ['user_id'], unique=False)

    op.create_table('skill_gap_analyses',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('resume_id', sa.UUID(), nullable=False),
    sa.Column('job_description_id', sa.UUID(), nullable=False),
    sa.Column('matched_skills', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('missing_required_skills', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('missing_preferred_skills', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('match_score', sa.Float(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['job_description_id'], ['job_descriptions.id'], ),
    sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_skill_gap_analyses_job_description_id'), 'skill_gap_analyses', ['job_description_id'], unique=False)
    op.create_index(op.f('ix_skill_gap_analyses_resume_id'), 'skill_gap_analyses', ['resume_id'], unique=False)
    op.create_index(op.f('ix_skill_gap_analyses_user_id'), 'skill_gap_analyses', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_skill_gap_analyses_user_id'), table_name='skill_gap_analyses')
    op.drop_index(op.f('ix_skill_gap_analyses_resume_id'), table_name='skill_gap_analyses')
    op.drop_index(op.f('ix_skill_gap_analyses_job_description_id'), table_name='skill_gap_analyses')
    op.drop_table('skill_gap_analyses')

    op.drop_index(op.f('ix_job_descriptions_user_id'), table_name='job_descriptions')
    op.drop_table('job_descriptions')

    op.drop_index(op.f('ix_resumes_user_id'), table_name='resumes')
    op.drop_table('resumes')
