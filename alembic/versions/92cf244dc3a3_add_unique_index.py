"""add_unique_index

Revision ID: 92cf244dc3a3
Revises: ac170e07a776
Create Date: 2026-09-03 19:36:26.482502

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '92cf244dc3a3'
down_revision: Union[str, Sequence[str], None] = 'ac170e07a776'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE UNIQUE INDEX uq_booking_active_slot 
        ON bookings(booking_date, booking_time) 
        WHERE status = 'active'
        """
    )

def downgrade() -> None:
    op.execute("DROP INDEX uq_booking_active_slot")
