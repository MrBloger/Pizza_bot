"""rename aactivity_date to activity_date

Revision ID: 124b7d0d02c9
Revises: bc7280a62069
Create Date: 2025-10-15 15:53:13.060336

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '124b7d0d02c9'
down_revision: Union[str, Sequence[str], None] = 'bc7280a62069'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.alter_column(
        "activity",
        "aactivity_date",
        new_column_name="activity_date"
    )


def downgrade():
    op.alter_column(
        "activity",
        "activity_date",
        new_column_name="aactivity_date"
    )
