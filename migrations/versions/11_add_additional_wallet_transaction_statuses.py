"""Add additional wallet transaction statuses

Revision ID: 11
Revises: 10
Create Date: 2024-09-13 00:00:00.000001
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '11'
down_revision: Union[str, None] = '10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


new_transaction_status = sa.Enum(
    'requested',
    'pending',
    'confirmed',
    'canceled',
    'in_progress',
    'sent_to_bank',
    'paid',
    'denied',
    name='transactionstatus'
)

old_transaction_status = sa.Enum('requested', 'pending', 'confirmed', 'canceled', name='transactionstatus')


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
    op.execute(
        "UPDATE wallet_transactions SET status = 'pending' "
        "WHERE status IN ('in_progress', 'sent_to_bank', 'paid', 'denied')"
    )

    old_transaction_status.create(bind)
    op.execute(
        "ALTER TABLE wallet_transactions ALTER COLUMN status "
        "TYPE transactionstatus USING status::transactionstatus"
    )
    op.execute("DROP TYPE transactionstatus_new")
