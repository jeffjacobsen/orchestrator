"""Add cost and duration tracking to tasks

Revision ID: c9f8e4a21234
Revises: b97f63d35867
Create Date: 2025-11-08 08:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c9f8e4a21234'
down_revision = 'b97f63d35867'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add cost and duration tracking columns
    op.add_column('tasks', sa.Column('total_cost', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('tasks', sa.Column('duration_seconds', sa.Integer(), nullable=True, server_default='0'))

    # Add indexes for efficient querying/sorting
    op.create_index(op.f('ix_tasks_total_cost'), 'tasks', ['total_cost'], unique=False)
    op.create_index(op.f('ix_tasks_duration_seconds'), 'tasks', ['duration_seconds'], unique=False)


def downgrade() -> None:
    # Remove indexes
    op.drop_index(op.f('ix_tasks_duration_seconds'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_total_cost'), table_name='tasks')

    # Remove columns
    op.drop_column('tasks', 'duration_seconds')
    op.drop_column('tasks', 'total_cost')
