"""create_batch_jobs_table

Revision ID: 2d307d8695a5
Revises: c81546f00f10
Create Date: 2025-01-27

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2d307d8695a5'
down_revision = 'c81546f00f10'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create batch_jobs table
    op.create_table(
        'batch_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('batch_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('total_reports', sa.Integer(), nullable=False),
        sa.Column('successful', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('results', sa.JSON(), nullable=True),
        sa.Column('report_ids', sa.JSON(), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Create indexes
    op.create_index(op.f('ix_batch_jobs_batch_id'), 'batch_jobs', ['batch_id'], unique=True)
    op.create_index(op.f('ix_batch_jobs_user_id'), 'batch_jobs', ['user_id'], unique=False)
    op.create_index(op.f('ix_batch_jobs_status'), 'batch_jobs', ['status'], unique=False)
    # Index for pending jobs (most common query)
    op.execute("""
        CREATE INDEX idx_batch_jobs_pending 
        ON batch_jobs(status) 
        WHERE status IN ('PENDING', 'PROCESSING')
    """)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_batch_jobs_pending', table_name='batch_jobs')
    op.drop_index(op.f('ix_batch_jobs_status'), table_name='batch_jobs')
    op.drop_index(op.f('ix_batch_jobs_user_id'), table_name='batch_jobs')
    op.drop_index(op.f('ix_batch_jobs_batch_id'), table_name='batch_jobs')
    
    # Drop table
    op.drop_table('batch_jobs')


