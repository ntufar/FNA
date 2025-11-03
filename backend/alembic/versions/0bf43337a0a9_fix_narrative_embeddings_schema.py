"""fix_narrative_embeddings_schema

Revision ID: 0bf43337a0a9
Revises: 20251101b
Create Date: 2025-11-03 14:29:13.925216

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0bf43337a0a9"
down_revision = "20251101b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum type for section_type
    section_type_enum = postgresql.ENUM(
        "MD_A",
        "CEO_LETTER",
        "RISK_FACTORS",
        "OTHER",
        name="sectiontype",
        create_type=True,
    )
    section_type_enum.create(op.get_bind(), checkfirst=True)

    # Drop old foreign key constraint
    op.drop_constraint(
        "narrative_embeddings_report_id_fkey",
        "narrative_embeddings",
        type_="foreignkey",
    )

    # Drop old indexes
    op.drop_index("idx_narrative_embeddings_chunk", table_name="narrative_embeddings")
    op.drop_index("idx_narrative_embeddings_report", table_name="narrative_embeddings")

    # Drop old columns
    op.drop_column("narrative_embeddings", "text_chunk")
    op.drop_column("narrative_embeddings", "report_id")
    op.drop_column("narrative_embeddings", "model_version")

    # Add new columns
    op.add_column(
        "narrative_embeddings",
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), nullable=False),
    )
    op.add_column(
        "narrative_embeddings",
        sa.Column("section_type", section_type_enum, nullable=False),
    )
    op.add_column(
        "narrative_embeddings", sa.Column("text_content", sa.Text(), nullable=False)
    )

    # Create new indexes
    op.create_index(
        op.f("ix_narrative_embeddings_analysis_id"),
        "narrative_embeddings",
        ["analysis_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_narrative_embeddings_section_type"),
        "narrative_embeddings",
        ["section_type"],
        unique=False,
    )

    # Create new foreign key constraint
    op.create_foreign_key(
        None,
        "narrative_embeddings",
        "narrative_analyses",
        ["analysis_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    # Drop new foreign key
    op.drop_constraint(None, "narrative_embeddings", type_="foreignkey")

    # Drop new indexes
    op.drop_index(
        op.f("ix_narrative_embeddings_section_type"), table_name="narrative_embeddings"
    )
    op.drop_index(
        op.f("ix_narrative_embeddings_analysis_id"), table_name="narrative_embeddings"
    )

    # Drop new columns
    op.drop_column("narrative_embeddings", "text_content")
    op.drop_column("narrative_embeddings", "section_type")
    op.drop_column("narrative_embeddings", "analysis_id")

    # Re-add old columns
    op.add_column(
        "narrative_embeddings",
        sa.Column("model_version", sa.String(length=50), nullable=False),
    )
    op.add_column(
        "narrative_embeddings",
        sa.Column("report_id", postgresql.UUID(as_uuid=True), nullable=False),
    )
    op.add_column(
        "narrative_embeddings", sa.Column("text_chunk", sa.Text(), nullable=False)
    )

    # Re-create old indexes
    op.create_index(
        "idx_narrative_embeddings_report",
        "narrative_embeddings",
        ["report_id"],
        unique=False,
    )
    op.create_index(
        "idx_narrative_embeddings_chunk",
        "narrative_embeddings",
        ["chunk_index"],
        unique=False,
    )

    # Re-create old foreign key
    op.create_foreign_key(
        "narrative_embeddings_report_id_fkey",
        "narrative_embeddings",
        "financial_reports",
        ["report_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Drop enum type
    sa.Enum(name="sectiontype").drop(op.get_bind(), checkfirst=True)
