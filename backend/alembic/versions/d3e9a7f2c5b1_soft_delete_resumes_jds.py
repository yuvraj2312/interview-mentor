"""soft delete resumes and job_descriptions

Revision ID: d3e9a7f2c5b1
Revises: c1a6f2b9e4d7
Create Date: 2026-09-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3e9a7f2c5b1'
down_revision: Union[str, None] = 'c1a6f2b9e4d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('resumes', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('job_descriptions', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('job_descriptions', 'deleted_at')
    op.drop_column('resumes', 'deleted_at')
