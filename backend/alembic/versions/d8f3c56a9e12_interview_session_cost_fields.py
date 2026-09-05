"""interview session cost fields (phase 4d)

Revision ID: d8f3c56a9e12
Revises: c4a7e19b2d3f
Create Date: 2026-08-24 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8f3c56a9e12'
down_revision: Union[str, None] = 'c4a7e19b2d3f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('interview_sessions', sa.Column('total_cost_usd', sa.Float(), nullable=True))
    op.add_column('interview_sessions', sa.Column('cost_cap_usd', sa.Float(), nullable=True))
    op.add_column('interview_sessions', sa.Column('stop_reason', sa.String(length=32), nullable=True))
    op.execute("UPDATE interview_sessions SET total_cost_usd = 0.0, cost_cap_usd = 2.0")
    op.alter_column('interview_sessions', 'total_cost_usd', nullable=False)
    op.alter_column('interview_sessions', 'cost_cap_usd', nullable=False)


def downgrade() -> None:
    op.drop_column('interview_sessions', 'stop_reason')
    op.drop_column('interview_sessions', 'cost_cap_usd')
    op.drop_column('interview_sessions', 'total_cost_usd')
