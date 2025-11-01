"""update_narrative_analyses_to_model

Revision ID: 20251101b
Revises: 20251101
Create Date: 2025-11-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20251101b"
down_revision = "20251101"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("narrative_analyses") as batch_op:
        # Drop legacy columns not present in current model
        for col in [
            "overall_sentiment_score",
            "key_insights",
            "narrative_excerpts",
            "analysis_model_version",
        ]:
            try:
                batch_op.drop_column(col)
            except Exception:
                pass

        # Add columns matching current model
        batch_op.add_column(sa.Column("key_themes", postgresql.JSONB, nullable=False, server_default='[]'))
        batch_op.add_column(sa.Column("risk_indicators", postgresql.JSONB, nullable=False, server_default='[]'))
        batch_op.add_column(sa.Column("narrative_sections", postgresql.JSONB, nullable=False, server_default='{}'))
        batch_op.add_column(sa.Column("financial_metrics", postgresql.JSONB, nullable=True))
        batch_op.add_column(sa.Column("processing_time_seconds", sa.Integer, nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("model_version", sa.String(length=100), nullable=False, server_default="unknown"))

    # Remove server defaults after backfilling
    with op.batch_alter_table("narrative_analyses") as batch_op:
        batch_op.alter_column("key_themes", server_default=None)
        batch_op.alter_column("risk_indicators", server_default=None)
        batch_op.alter_column("narrative_sections", server_default=None)
        batch_op.alter_column("processing_time_seconds", server_default=None)
        batch_op.alter_column("model_version", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("narrative_analyses") as batch_op:
        for col in [
            "model_version",
            "processing_time_seconds",
            "financial_metrics",
            "narrative_sections",
            "risk_indicators",
            "key_themes",
        ]:
            try:
                batch_op.drop_column(col)
            except Exception:
                pass

        # Recreate legacy columns (best-effort)
        batch_op.add_column(sa.Column("analysis_model_version", sa.String(length=50), nullable=False, server_default="unknown"))
        batch_op.add_column(sa.Column("narrative_excerpts", postgresql.JSONB, nullable=True))
        batch_op.add_column(sa.Column("key_insights", postgresql.JSONB, nullable=True))
        batch_op.add_column(sa.Column("overall_sentiment_score", sa.Float, nullable=False, server_default="0"))


