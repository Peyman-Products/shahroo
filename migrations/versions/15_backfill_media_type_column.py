"""Ensure media_files has a type column

Revision ID: 15
Revises: 14
Create Date: 2024-11-10 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "15"
down_revision: Union[str, None] = "14"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    mediatype_enum = postgresql.ENUM("id_card", "selfie", "avatar", name="mediatype")
    mediatype_enum.create(bind, checkfirst=True)

    existing_columns = {column["name"] for column in inspector.get_columns("media_files")}
    if "type" not in existing_columns:
        op.add_column("media_files", sa.Column("type", mediatype_enum, nullable=True))
        op.execute(
            """
            UPDATE media_files
            SET type = CASE
                WHEN file_path ILIKE '%kyc/id-card%' OR file_path ILIKE '%id-card%' THEN 'id_card'::mediatype
                WHEN file_path ILIKE '%kyc/selfie%' OR file_path ILIKE '%selfie%' THEN 'selfie'::mediatype
                ELSE 'avatar'::mediatype
            END
            WHERE type IS NULL
            """
        )
        op.alter_column("media_files", "type", nullable=False, existing_type=mediatype_enum)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_columns = {column["name"] for column in inspector.get_columns("media_files")}
    if "type" in existing_columns:
        op.drop_column("media_files", "type")

    mediatype_enum = postgresql.ENUM("id_card", "selfie", "avatar", name="mediatype")
    mediatype_enum.drop(bind, checkfirst=True)
