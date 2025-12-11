"""Add business contact and audit fields

Revision ID: 5
Revises: 4
Create Date: 2024-08-31 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5'
down_revision: Union[str, None] = '4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('businesses', sa.Column('contact_person', sa.String(), nullable=True))
    op.add_column('businesses', sa.Column('phone_number', sa.String(), nullable=True))
    op.add_column('businesses', sa.Column('address', sa.String(), nullable=True))
    op.add_column('businesses', sa.Column('status', sa.Boolean(), server_default=sa.true(), nullable=False))
    op.add_column('businesses', sa.Column('created_by_admin_id', sa.Integer(), nullable=True))
    op.add_column('businesses', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))
    op.add_column('businesses', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))
    op.create_foreign_key(None, 'businesses', 'users', ['created_by_admin_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint(None, 'businesses', type_='foreignkey')
    op.drop_column('businesses', 'updated_at')
    op.drop_column('businesses', 'created_at')
    op.drop_column('businesses', 'created_by_admin_id')
    op.drop_column('businesses', 'status')
    op.drop_column('businesses', 'address')
    op.drop_column('businesses', 'phone_number')
    op.drop_column('businesses', 'contact_person')
