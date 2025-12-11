"""Add missing task status enum values

Revision ID: 7
Revises: 6
Create Date: 2024-09-01 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '7'
down_revision: Union[str, None] = '6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new enum values if they don't already exist. Postgres requires new enum
    # values to be committed before they can be used in the same migration, so we
    # run these statements in an autocommit block.
    with op.get_context().autocommit_block():
        for value in ('issued', 'canceled', 'failed'):
            op.execute(
                sa.text(
                    """ALTER TYPE taskstatus ADD VALUE IF NOT EXISTS :value"""
                ).bindparams(value=value)
            )

    # Ensure tasks without a status default to the issued state
    op.execute(sa.text("UPDATE tasks SET status = 'issued' WHERE status IS NULL"))
    op.execute(sa.text("ALTER TABLE tasks ALTER COLUMN status SET DEFAULT 'issued'"))


def downgrade() -> None:
    # Remove default before recreating the type
    op.execute(sa.text("ALTER TABLE tasks ALTER COLUMN status DROP DEFAULT"))

    # Rename existing type
    op.execute(sa.text("ALTER TYPE taskstatus RENAME TO taskstatus_old"))

    # Create new type with the original values
    op.execute(sa.text("CREATE TYPE taskstatus AS ENUM ('pending', 'in_progress', 'done', 'approved', 'rejected')"))

    # Cast the column to the new type, mapping newly introduced states back to pending
    op.execute(
        sa.text(
            """
            ALTER TABLE tasks
            ALTER COLUMN status TYPE taskstatus USING (
                CASE status::text
                    WHEN 'issued' THEN 'pending'
                    WHEN 'canceled' THEN 'rejected'
                    WHEN 'failed' THEN 'rejected'
                    ELSE status::text
                END
            )::taskstatus
            """
        )
    )

    # Drop the old type
    op.execute(sa.text("DROP TYPE taskstatus_old"))
