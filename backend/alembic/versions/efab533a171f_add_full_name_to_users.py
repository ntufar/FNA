"""add_full_name_to_users

Revision ID: efab533a171f
Revises: 7423881db09b
Create Date: 2025-10-29 05:07:07.872660

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "efab533a171f"
down_revision = "7423881db09b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add full_name column to users table
    op.add_column(
        'users',
        sa.Column('full_name', sa.String(length=255), nullable=False, server_default='Unknown')
    )
    
    # Remove the temporary server default after adding the column
    op.alter_column('users', 'full_name', server_default=None)


def downgrade() -> None:
    # Remove full_name column from users table
    op.drop_column('users', 'full_name')
