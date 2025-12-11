"""Add requested wallet transaction status

Revision ID: 10
Revises: 9
Create Date: 2024-09-13 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '10'
down_revision: Union[str, None] = '9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


new_transaction_status = sa.Enum('requested', 'pending', 'confirmed', 'canceled', name='transactionstatus')
old_transaction_status = sa.Enum('pending', 'confirmed', 'canceled', name='transactionstatus')


def upgrade() -> None:
    bind = op.get_bind()

    op.execute("ALTER TYPE transactionstatus RENAME TO transactionstatus_old")
    op.execute("ALTER TABLE wallet_transactions ALTER COLUMN status TYPE TEXT USING status::text")

    new_transaction_status.create(bind)
    op.execute(
        "ALTER TABLE wallet_transactions ALTER COLUMN status "
        "TYPE transactionstatus USING status::transactionstatus"
    )
    op.execute("DROP TYPE transactionstatus_old")


def downgrade() -> None:
    bind = op.get_bind()

    op.execute("ALTER TYPE transactionstatus RENAME TO transactionstatus_new")
    op.execute("ALTER TABLE wallet_transactions ALTER COLUMN status TYPE TEXT USING status::text")
    op.execute("UPDATE wallet_transactions SET status = 'pending' WHERE status = 'requested'")

    old_transaction_status.create(bind)
    op.execute(
        "ALTER TABLE wallet_transactions ALTER COLUMN status "
        "TYPE transactionstatus USING status::transactionstatus"
    )
    op.execute("DROP TYPE transactionstatus_new")
