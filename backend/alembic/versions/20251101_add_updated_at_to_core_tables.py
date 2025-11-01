"""add_updated_at_to_core_tables

Revision ID: 20251101
Revises: ac636ac1bb29
Create Date: 2025-11-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251101"
down_revision = "ac636ac1bb29"
branch_labels = None
depends_on = None


def upgrade() -> None:
    tables = [
        "financial_reports",
        "narrative_analyses",
        "narrative_deltas",
        "narrative_embeddings",
        "alerts",
    ]

    for table in tables:
        with op.batch_alter_table(table) as batch_op:
            batch_op.add_column(
                sa.Column("updated_at", sa.TIMESTAMP, nullable=False, server_default=sa.func.now())
            )


def downgrade() -> None:
    tables = [
        "financial_reports",
        "narrative_analyses",
        "narrative_deltas",
        "narrative_embeddings",
        "alerts",
    ]

    for table in tables:
        with op.batch_alter_table(table) as batch_op:
            batch_op.drop_column("updated_at")


