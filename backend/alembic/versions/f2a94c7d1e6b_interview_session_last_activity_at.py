"""interview session last_activity_at (phase 4b)

Revision ID: f2a94c7d1e6b
Revises: e561ffb36d47
Create Date: 2026-08-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2a94c7d1e6b'
down_revision: Union[str, None] = 'e561ffb36d47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('interview_sessions', sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE interview_sessions SET last_activity_at = COALESCE(completed_at, created_at)")
    op.alter_column('interview_sessions', 'last_activity_at', nullable=False)


def downgrade() -> None:
    op.drop_column('interview_sessions', 'last_activity_at')
