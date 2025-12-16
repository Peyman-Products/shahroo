"""Ensure media_files has an is_active column

Revision ID: 16
Revises: 15
Create Date: 2024-11-16 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "16"
down_revision: Union[str, None] = "15"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_columns = {column["name"] for column in inspector.get_columns("media_files")}
    if "is_active" not in existing_columns:
        op.add_column(
            "media_files",
            sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.text("true")),
        )
        op.execute("UPDATE media_files SET is_active = true WHERE is_active IS NULL")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_columns = {column["name"] for column in inspector.get_columns("media_files")}
    if "is_active" in existing_columns:
        op.drop_column("media_files", "is_active")
