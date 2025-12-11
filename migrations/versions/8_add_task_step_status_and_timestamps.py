"""Add status and timestamps to task_steps

Revision ID: 8
Revises: 7
Create Date: 2024-09-05 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '8'
down_revision: Union[str, None] = '7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


step_status_enum = sa.Enum(
    'pending', 'in_progress', 'done', 'failed', 'canceled', name='stepstatus'
)


def upgrade() -> None:
    bind = op.get_bind()

    # Create the enum type once; checkfirst prevents errors if it already exists
    step_status_enum.create(bind, checkfirst=True)

    op.add_column(
        'task_steps',
        sa.Column(
            'status',
            step_status_enum,
            server_default='pending',
            nullable=False,
        ),
    )
    op.add_column(
        'task_steps',
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )
    op.add_column(
        'task_steps',
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )
    op.add_column('task_steps', sa.Column('done_at', sa.DateTime(timezone=True), nullable=True))



def downgrade() -> None:
    op.drop_column('task_steps', 'done_at')
    op.drop_column('task_steps', 'updated_at')
    op.drop_column('task_steps', 'created_at')
    op.drop_column('task_steps', 'status')

    bind = op.get_bind()
    step_status_enum.drop(bind, checkfirst=True)
