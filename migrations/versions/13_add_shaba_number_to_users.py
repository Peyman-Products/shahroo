"""Add shaba number to users

Revision ID: 13
Revises: 12
Create Date: 2024-11-01 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '13'
down_revision: Union[str, None] = '12'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('shaba_number', sa.String(), nullable=True))
    op.create_unique_constraint('uq_users_shaba_number', 'users', ['shaba_number'])


def downgrade() -> None:
    op.drop_constraint('uq_users_shaba_number', 'users', type_='unique')
    op.drop_column('users', 'shaba_number')
