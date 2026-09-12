"""soft delete interview sessions

Revision ID: a2f6c9e1b8d4
Revises: e7c1a2f9b4d6
Create Date: 2026-09-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2f6c9e1b8d4'
down_revision: Union[str, None] = 'e7c1a2f9b4d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('interview_sessions', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('interview_sessions', 'deleted_at')
