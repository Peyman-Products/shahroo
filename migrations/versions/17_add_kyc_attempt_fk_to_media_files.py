"""Ensure media_files has a kyc_attempt_id column

Revision ID: 17
Revises: 16
Create Date: 2024-11-20 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "17"
down_revision: Union[str, None] = "16"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_columns = {column["name"] for column in inspector.get_columns("media_files")}
    if "kyc_attempt_id" not in existing_columns:
        op.add_column("media_files", sa.Column("kyc_attempt_id", sa.Integer(), nullable=True))
        existing_columns.add("kyc_attempt_id")

    fk_name = "media_files_kyc_attempt_id_fkey"
    existing_foreign_keys = {fk["name"] for fk in inspector.get_foreign_keys("media_files")}
    if "kyc_attempt_id" in existing_columns and fk_name not in existing_foreign_keys:
        op.create_foreign_key(
            fk_name,
            "media_files",
            "kyc_attempts",
            ["kyc_attempt_id"],
            ["id"],
        )

    index_name = op.f("ix_media_files_kyc_attempt_id")
    existing_indexes = {index["name"] for index in inspector.get_indexes("media_files")}
    if "kyc_attempt_id" in existing_columns and index_name not in existing_indexes:
        op.create_index(index_name, "media_files", ["kyc_attempt_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    fk_name = "media_files_kyc_attempt_id_fkey"
    existing_foreign_keys = {fk["name"] for fk in inspector.get_foreign_keys("media_files")}
    if fk_name in existing_foreign_keys:
        op.drop_constraint(fk_name, "media_files", type_="foreignkey")

    index_name = op.f("ix_media_files_kyc_attempt_id")
    existing_indexes = {index["name"] for index in inspector.get_indexes("media_files")}
    if index_name in existing_indexes:
        op.drop_index(index_name, table_name="media_files")

    existing_columns = {column["name"] for column in inspector.get_columns("media_files")}
    if "kyc_attempt_id" in existing_columns:
        op.drop_column("media_files", "kyc_attempt_id")
