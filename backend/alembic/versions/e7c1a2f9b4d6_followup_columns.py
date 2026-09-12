"""CE-c follow-up question columns

Revision ID: e7c1a2f9b4d6
Revises: d3e9a7f2c5b1
Create Date: 2026-09-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7c1a2f9b4d6'
down_revision: Union[str, None] = 'd3e9a7f2c5b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'interview_sessions',
        sa.Column('topic_number', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column(
        'interview_turns',
        sa.Column('is_followup', sa.Boolean(), nullable=False, server_default='false'),
    )
    op.add_column('interview_turns', sa.Column('topic_number', sa.Integer(), nullable=True))
    op.add_column('interview_turns', sa.Column('followup_reason', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('interview_turns', 'followup_reason')
    op.drop_column('interview_turns', 'topic_number')
    op.drop_column('interview_turns', 'is_followup')
    op.drop_column('interview_sessions', 'topic_number')
