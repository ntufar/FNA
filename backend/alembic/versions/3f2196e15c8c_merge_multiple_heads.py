"""merge multiple heads

Revision ID: 3f2196e15c8c
Revises: 20251102_add_performance_indexes, 2d307d8695a5
Create Date: 2025-12-24 12:53:30.032101

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3f2196e15c8c"
down_revision = ("20251102_add_performance_indexes", "2d307d8695a5")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
