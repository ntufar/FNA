"""Create initial FNA database schema

Revision ID: 0001
Revises: 
Create Date: 2025-10-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid


# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Note: pgvector extension not available in PostgreSQL 17 standard installation
    # Using JSONB for embeddings as fallback - can be upgraded later
    # Using VARCHAR instead of ENUM types for simpler implementation
    
    # Create companies table
    op.create_table(
        'companies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('ticker_symbol', sa.String(5), nullable=False, unique=True),
        sa.Column('company_name', sa.String(255), nullable=False),
        sa.Column('sector', sa.String(100), nullable=True),
        sa.Column('industry', sa.String(100), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now())
    )
    
    # Create indexes for companies
    op.create_index('idx_companies_ticker', 'companies', ['ticker_symbol'])
    op.create_index('idx_companies_sector', 'companies', ['sector'])
    op.create_index('idx_companies_industry', 'companies', ['industry'])
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('subscription_tier', sa.String(20), nullable=False, server_default='Basic'),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column('last_login', sa.TIMESTAMP, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true')
    )
    
    # Create indexes for users
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_subscription_tier', 'users', ['subscription_tier'])
    
    # Create financial_reports table
    op.create_table(
        'financial_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('report_type', sa.String(20), nullable=False),
        sa.Column('fiscal_period', sa.String(20), nullable=False),
        sa.Column('filing_date', sa.Date, nullable=False),
        sa.Column('report_url', sa.String(500), nullable=True),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_format', sa.String(20), nullable=False),
        sa.Column('file_size_bytes', sa.Integer, nullable=False),
        sa.Column('download_source', sa.String(20), nullable=False),
        sa.Column('processing_status', sa.String(20), nullable=False, server_default='PENDING'),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column('processed_at', sa.TIMESTAMP, nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE')
    )
    
    # Create indexes for financial_reports
    op.create_index('idx_financial_reports_company', 'financial_reports', ['company_id'])
    op.create_index('idx_financial_reports_type', 'financial_reports', ['report_type'])
    op.create_index('idx_financial_reports_filing_date', 'financial_reports', ['filing_date'])
    op.create_index('idx_financial_reports_status', 'financial_reports', ['processing_status'])
    
    # Create narrative_analyses table
    op.create_table(
        'narrative_analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('optimism_score', sa.Float, nullable=False),
        sa.Column('optimism_confidence', sa.Float, nullable=False),
        sa.Column('risk_score', sa.Float, nullable=False),
        sa.Column('risk_confidence', sa.Float, nullable=False),
        sa.Column('uncertainty_score', sa.Float, nullable=False),
        sa.Column('uncertainty_confidence', sa.Float, nullable=False),
        sa.Column('overall_sentiment_score', sa.Float, nullable=False),
        sa.Column('key_insights', sa.JSON, nullable=True),
        sa.Column('narrative_excerpts', sa.JSON, nullable=True),
        sa.Column('analysis_model_version', sa.String(50), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['report_id'], ['financial_reports.id'], ondelete='CASCADE')
    )
    
    # Create indexes for narrative_analyses
    op.create_index('idx_narrative_analyses_report', 'narrative_analyses', ['report_id'])
    op.create_index('idx_narrative_analyses_sentiment', 'narrative_analyses', ['overall_sentiment_score'])
    op.create_index('idx_narrative_analyses_created', 'narrative_analyses', ['created_at'])
    
    # Create narrative_deltas table
    op.create_table(
        'narrative_deltas',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('base_analysis_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('comparison_analysis_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('optimism_delta', sa.Float, nullable=False),
        sa.Column('risk_delta', sa.Float, nullable=False),
        sa.Column('uncertainty_delta', sa.Float, nullable=False),
        sa.Column('overall_sentiment_delta', sa.Float, nullable=False),
        sa.Column('significant_changes', sa.JSON, nullable=True),
        sa.Column('delta_summary', sa.Text, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['base_analysis_id'], ['narrative_analyses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['comparison_analysis_id'], ['narrative_analyses.id'], ondelete='CASCADE')
    )
    
    # Create indexes for narrative_deltas
    op.create_index('idx_narrative_deltas_base', 'narrative_deltas', ['base_analysis_id'])
    op.create_index('idx_narrative_deltas_comparison', 'narrative_deltas', ['comparison_analysis_id'])
    
    # Create alerts table
    op.create_table(
        'alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('alert_type', sa.String(30), nullable=False),
        sa.Column('threshold_percentage', sa.Float, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE')
    )
    
    # Create indexes for alerts
    op.create_index('idx_alerts_user', 'alerts', ['user_id'])
    op.create_index('idx_alerts_company', 'alerts', ['company_id'])
    op.create_index('idx_alerts_active', 'alerts', ['is_active'])
    
    # Create narrative_embeddings table (for vector search)
    # Using JSONB as fallback when pgvector not available
    op.create_table(
        'narrative_embeddings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('text_chunk', sa.Text, nullable=False),
        sa.Column('chunk_index', sa.Integer, nullable=False),
        sa.Column('embedding_vector', postgresql.JSONB, nullable=False),
        sa.Column('model_version', sa.String(50), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['report_id'], ['financial_reports.id'], ondelete='CASCADE')
    )
    
    # Create indexes for narrative_embeddings
    op.create_index('idx_narrative_embeddings_report', 'narrative_embeddings', ['report_id'])
    op.create_index('idx_narrative_embeddings_chunk', 'narrative_embeddings', ['chunk_index'])


def downgrade() -> None:
    # Drop tables in reverse order (due to foreign key constraints)
    op.drop_table('narrative_embeddings')
    op.drop_table('alerts')
    op.drop_table('narrative_deltas')
    op.drop_table('narrative_analyses')
    op.drop_table('financial_reports')
    op.drop_table('users')
    op.drop_table('companies')