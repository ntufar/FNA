"""add_company_id_to_narrative_deltas

Revision ID: 980f6b872ad4
Revises: efab533a171f
Create Date: 2025-10-29 05:11:11.852057

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "980f6b872ad4"
down_revision = "efab533a171f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the enum type first
    shift_significance_enum = sa.Enum('MINOR', 'MODERATE', 'MAJOR', 'CRITICAL', name='shift_significance_enum')
    shift_significance_enum.create(op.get_bind())
    
    # Add company_id column to narrative_deltas table
    op.add_column(
        'narrative_deltas',
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False)
    )
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_narrative_deltas_company_id',
        'narrative_deltas', 'companies',
        ['company_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Add index for company_id
    op.create_index('idx_narrative_deltas_company_id', 'narrative_deltas', ['company_id'])
    
    # Add missing theme evolution columns
    op.add_column(
        'narrative_deltas',
        sa.Column('themes_added', sa.JSON, nullable=False, server_default='[]')
    )
    op.add_column(
        'narrative_deltas',
        sa.Column('themes_removed', sa.JSON, nullable=False, server_default='[]')
    )
    op.add_column(
        'narrative_deltas',
        sa.Column('themes_evolved', sa.JSON, nullable=False, server_default='{}')
    )
    
    # Add shift significance column using the created enum
    op.add_column(
        'narrative_deltas',
        sa.Column('shift_significance', shift_significance_enum, nullable=False, server_default='MINOR')
    )
    
    # Add index for shift_significance
    op.create_index('idx_narrative_deltas_shift_significance', 'narrative_deltas', ['shift_significance'])
    
    # Remove server defaults after adding columns
    op.alter_column('narrative_deltas', 'themes_added', server_default=None)
    op.alter_column('narrative_deltas', 'themes_removed', server_default=None)
    op.alter_column('narrative_deltas', 'themes_evolved', server_default=None)
    op.alter_column('narrative_deltas', 'shift_significance', server_default=None)


def downgrade() -> None:
    # Remove indexes
    op.drop_index('idx_narrative_deltas_shift_significance', 'narrative_deltas')
    op.drop_index('idx_narrative_deltas_company_id', 'narrative_deltas')
    
    # Remove foreign key constraint
    op.drop_constraint('fk_narrative_deltas_company_id', 'narrative_deltas', type_='foreignkey')
    
    # Remove columns
    op.drop_column('narrative_deltas', 'shift_significance')
    op.drop_column('narrative_deltas', 'themes_evolved')
    op.drop_column('narrative_deltas', 'themes_removed')
    op.drop_column('narrative_deltas', 'themes_added')
    op.drop_column('narrative_deltas', 'company_id')
    
    # Drop the enum type
    op.execute('DROP TYPE IF EXISTS shift_significance_enum')
