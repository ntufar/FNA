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
    from sqlalchemy import inspect
    
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('alerts')]
    
    with op.batch_alter_table("alerts") as batch_op:
        for col_name, col_type in [
            ("delta_id", sa.dialects.postgresql.UUID(as_uuid=True)),
            ("actual_change_percentage", sa.Float),
            ("alert_message", sa.Text),
            ("is_read", sa.Boolean),
            ("delivery_method", sa.String(20)),
            ("delivered_at", sa.TIMESTAMP),
        ]:
            if col_name not in columns:
                if col_name == "is_read":
                    batch_op.add_column(sa.Column(col_name, col_type, nullable=False, server_default=sa.text("false")))
                else:
                    batch_op.add_column(sa.Column(col_name, col_type, nullable=True))

        # Check if index exists
        indexes = [i['name'] for i in inspector.get_indexes('alerts')]
        if "idx_alerts_is_read" not in indexes:
            batch_op.create_index("idx_alerts_is_read", ["is_read"])

        # Check for FK
        fks = [f['name'] for f in inspector.get_foreign_keys('alerts')]
        if "fk_alerts_delta" not in fks:
            try:
                batch_op.create_foreign_key(
                    "fk_alerts_delta",
                    referent_table="narrative_deltas",
                    local_cols=["delta_id"],
                    remote_cols=["id"],
                    ondelete="CASCADE",
                )
            except Exception:
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
