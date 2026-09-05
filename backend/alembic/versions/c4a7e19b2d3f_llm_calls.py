"""llm calls (phase 4d)

Revision ID: c4a7e19b2d3f
Revises: f2a94c7d1e6b
Create Date: 2026-08-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4a7e19b2d3f'
down_revision: Union[str, None] = 'f2a94c7d1e6b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('llm_calls',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('agent_name', sa.String(length=64), nullable=False),
    sa.Column('session_id', sa.UUID(), nullable=True),
    sa.Column('model', sa.String(length=64), nullable=False),
    sa.Column('prompt', sa.Text(), nullable=False),
    sa.Column('response', sa.Text(), nullable=True),
    sa.Column('input_tokens', sa.Integer(), nullable=True),
    sa.Column('output_tokens', sa.Integer(), nullable=True),
    sa.Column('latency_ms', sa.Integer(), nullable=False),
    sa.Column('cost_usd', sa.Float(), nullable=True),
    sa.Column('temperature', sa.Float(), nullable=False),
    sa.Column('max_tokens', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['session_id'], ['interview_sessions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_llm_calls_agent_name'), 'llm_calls', ['agent_name'], unique=False)
    op.create_index(op.f('ix_llm_calls_created_at'), 'llm_calls', ['created_at'], unique=False)
    op.create_index(op.f('ix_llm_calls_session_id'), 'llm_calls', ['session_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_llm_calls_session_id'), table_name='llm_calls')
    op.drop_index(op.f('ix_llm_calls_created_at'), table_name='llm_calls')
    op.drop_index(op.f('ix_llm_calls_agent_name'), table_name='llm_calls')
    op.drop_table('llm_calls')
