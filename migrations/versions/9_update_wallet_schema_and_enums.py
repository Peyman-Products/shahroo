"""Add wallet timestamps and align wallet transaction enums

Revision ID: 9
Revises: 8
Create Date: 2024-09-12 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '9'
down_revision: Union[str, None] = '8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


new_transaction_type = sa.Enum('earning', 'payout', 'adjustment', name='transactiontype')
old_transaction_type = sa.Enum('earning', 'withdrawal', 'refund', name='transactiontype')

new_transaction_status = sa.Enum('pending', 'confirmed', 'canceled', name='transactionstatus')
old_transaction_status = sa.Enum('pending', 'confirmed', 'rejected', name='transactionstatus')


def upgrade() -> None:
    bind = op.get_bind()

    # Add wallet timestamps to match the ORM model
    op.add_column(
        'wallets',
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=True,
        ),
    )
    op.add_column(
        'wallets',
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=True,
        ),
    )

    # Align wallet transaction type values with the application model
    op.execute("ALTER TYPE transactiontype RENAME TO transactiontype_old")
    op.execute("ALTER TABLE wallet_transactions ALTER COLUMN type TYPE TEXT USING type::text")
    op.execute("UPDATE wallet_transactions SET type = 'payout' WHERE type = 'withdrawal'")
    op.execute("UPDATE wallet_transactions SET type = 'adjustment' WHERE type = 'refund'")

    new_transaction_type.create(bind)
    op.execute(
        "ALTER TABLE wallet_transactions ALTER COLUMN type "
        "TYPE transactiontype USING type::transactiontype"
    )
    op.execute("DROP TYPE transactiontype_old")

    # Align wallet transaction status values with the application model
    op.execute("ALTER TYPE transactionstatus RENAME TO transactionstatus_old")
    op.execute("ALTER TABLE wallet_transactions ALTER COLUMN status TYPE TEXT USING status::text")
    op.execute("UPDATE wallet_transactions SET status = 'canceled' WHERE status = 'rejected'")

    new_transaction_status.create(bind)
    op.execute(
        "ALTER TABLE wallet_transactions ALTER COLUMN status "
        "TYPE transactionstatus USING status::transactionstatus"
    )
    op.execute("DROP TYPE transactionstatus_old")


def downgrade() -> None:
    bind = op.get_bind()

    # Revert wallet transaction status enum values
    op.execute("ALTER TYPE transactionstatus RENAME TO transactionstatus_new")
    op.execute("ALTER TABLE wallet_transactions ALTER COLUMN status TYPE TEXT USING status::text")
    op.execute("UPDATE wallet_transactions SET status = 'rejected' WHERE status = 'canceled'")

    old_transaction_status.create(bind)
    op.execute(
        "ALTER TABLE wallet_transactions ALTER COLUMN status "
        "TYPE transactionstatus USING status::transactionstatus"
    )
    op.execute("DROP TYPE transactionstatus_new")

    # Revert wallet transaction type enum values
    op.execute("ALTER TYPE transactiontype RENAME TO transactiontype_new")
    op.execute("ALTER TABLE wallet_transactions ALTER COLUMN type TYPE TEXT USING type::text")
    op.execute("UPDATE wallet_transactions SET type = 'withdrawal' WHERE type = 'payout'")
    op.execute("UPDATE wallet_transactions SET type = 'refund' WHERE type = 'adjustment'")

    old_transaction_type.create(bind)
    op.execute(
        "ALTER TABLE wallet_transactions ALTER COLUMN type "
        "TYPE transactiontype USING type::transactiontype"
    )
    op.execute("DROP TYPE transactiontype_new")

    # Remove wallet timestamps
    op.drop_column('wallets', 'updated_at')
    op.drop_column('wallets', 'created_at')
