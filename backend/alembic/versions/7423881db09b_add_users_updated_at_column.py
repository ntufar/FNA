"""add_users_updated_at_column

Revision ID: 7423881db09b
Revises: 0001
Create Date: 2025-10-29 04:46:48.827711

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7423881db09b"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add updated_at column to users table
    op.add_column(
        'users',
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now())
    )


def downgrade() -> None:
    # Remove updated_at column from users table
    op.drop_column('users', 'updated_at')
