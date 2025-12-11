"""Enforce single wallet per user

Revision ID: 12
Revises: 11
Create Date: 2024-10-30 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '12'
down_revision: Union[str, None] = '11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    duplicate_wallets = bind.execute(
        sa.text(
            """
            SELECT user_id, array_agg(id ORDER BY id) AS wallet_ids
            FROM wallets
            WHERE user_id IS NOT NULL
            GROUP BY user_id
            HAVING COUNT(*) > 1
            """
        )
    ).mappings()

    for row in duplicate_wallets:
        keep_wallet_id = row["wallet_ids"][0]
        extra_wallet_ids = row["wallet_ids"][1:]

        for wallet_id in extra_wallet_ids:
            bind.execute(
                sa.text(
                    "UPDATE wallet_transactions SET wallet_id = :keep_id WHERE wallet_id = :old_id"
                ),
                {"keep_id": keep_wallet_id, "old_id": wallet_id},
            )
            bind.execute(sa.text("DELETE FROM wallets WHERE id = :wallet_id"), {"wallet_id": wallet_id})

    op.alter_column('wallets', 'user_id', existing_type=sa.Integer(), nullable=False)
    op.create_unique_constraint('uq_wallets_user_id', 'wallets', ['user_id'])


def downgrade() -> None:
    op.drop_constraint('uq_wallets_user_id', 'wallets', type_='unique')
    op.alter_column('wallets', 'user_id', existing_type=sa.Integer(), nullable=True)
