"""Add performance indexes for query optimization

Revision ID: 20251102_add_performance_indexes
Revises: efab533a171f
Create Date: 2025-11-02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251102_add_performance_indexes'
down_revision = 'efab533a171f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Additional performance indexes for common query patterns
    
    # Composite index for reports by company and filing date (most common query)
    op.create_index(
        'idx_financial_reports_company_filing_date',
        'financial_reports',
        ['company_id', sa.text('filing_date DESC')],
        unique=False
    )
    
    # Index for narrative analyses by report (frequently joined)
    op.create_index(
        'idx_narrative_analyses_report_id',
        'narrative_analyses',
        ['report_id'],
        unique=False
    )
    
    # Composite index for narrative deltas by company and date
    op.create_index(
        'idx_narrative_deltas_company_created',
        'narrative_deltas',
        ['company_id', sa.text('created_at DESC')],
        unique=False
    )
    
    # Composite index for alerts by user, read status, and date
    op.create_index(
        'idx_alerts_user_read_created',
        'alerts',
        ['user_id', 'is_read', sa.text('created_at DESC')],
        unique=False
    )
    
    # Index for narrative embeddings by analysis and section type
    op.create_index(
        'idx_narrative_embeddings_analysis_section',
        'narrative_embeddings',
        ['analysis_id', 'section_type'],
        unique=False
    )
    
    # Index for users by subscription tier (for admin queries)
    op.create_index(
        'idx_users_subscription_tier',
        'users',
        ['subscription_tier'],
        unique=False
    )
    
    # Index for users by active status (for admin queries)
    op.create_index(
        'idx_users_is_active',
        'users',
        ['is_active'],
        unique=False
    )
    
    # Index for reports by processing status (for monitoring)
    op.create_index(
        'idx_financial_reports_processing_status',
        'financial_reports',
        ['processing_status'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index('idx_financial_reports_processing_status', table_name='financial_reports')
    op.drop_index('idx_users_is_active', table_name='users')
    op.drop_index('idx_users_subscription_tier', table_name='users')
    op.drop_index('idx_narrative_embeddings_analysis_section', table_name='narrative_embeddings')
    op.drop_index('idx_alerts_user_read_created', table_name='alerts')
    op.drop_index('idx_narrative_deltas_company_created', table_name='narrative_deltas')
    op.drop_index('idx_narrative_analyses_report_id', table_name='narrative_analyses')
    op.drop_index('idx_financial_reports_company_filing_date', table_name='financial_reports')

