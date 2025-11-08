"""Add current_step to tasks table

Revision ID: b97f63d35867
Revises: 
Create Date: 2025-11-06 11:58:54.861573

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b97f63d35867'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add current_step column to track workflow progress
    op.add_column('tasks', sa.Column('current_step', sa.Integer(), nullable=True))


def downgrade() -> None:
    # Remove current_step column
    op.drop_column('tasks', 'current_step')
