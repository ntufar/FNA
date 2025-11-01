"""add_missing_columns_alerts_embeddings

Revision ID: ac636ac1bb29
Revises: 980f6b872ad4
Create Date: 2025-10-29 05:47:35.199838

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "ac636ac1bb29"
down_revision = "980f6b872ad4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Alerts: add columns introduced by updated model
    with op.batch_alter_table("alerts") as batch_op:
        batch_op.add_column(sa.Column("delta_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
        batch_op.add_column(sa.Column("actual_change_percentage", sa.Float, nullable=True))
        batch_op.add_column(sa.Column("alert_message", sa.Text, nullable=True))
        batch_op.add_column(sa.Column("is_read", sa.Boolean, nullable=False, server_default=sa.text("false")))
        batch_op.add_column(sa.Column("delivery_method", sa.String(20), nullable=True))
        batch_op.add_column(sa.Column("delivered_at", sa.TIMESTAMP, nullable=True))
        batch_op.create_index("idx_alerts_is_read", ["is_read"])
        # Optional FK to narrative_deltas if table exists
        try:
            batch_op.create_foreign_key(
                "fk_alerts_delta",
                referent_table="narrative_deltas",
                local_cols=["delta_id"],
                remote_cols=["id"],
                ondelete="CASCADE",
            )
        except Exception:
            # In case of existing constraint or missing table in some envs
            pass


def downgrade() -> None:
    with op.batch_alter_table("alerts") as batch_op:
        try:
            batch_op.drop_constraint("fk_alerts_delta", type_="foreignkey")
        except Exception:
            pass
        try:
            batch_op.drop_index("idx_alerts_is_read")
        except Exception:
            pass
        batch_op.drop_column("delivered_at")
        batch_op.drop_column("delivery_method")
        batch_op.drop_column("is_read")
        batch_op.drop_column("alert_message")
        batch_op.drop_column("actual_change_percentage")
        batch_op.drop_column("delta_id")
