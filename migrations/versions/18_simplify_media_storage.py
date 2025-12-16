"""Simplify media storage to file names on users

Revision ID: 18
Revises: 17
Create Date: 2024-11-25 00:00:00.000000
"""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "18"
down_revision: Union[str, None] = "17"
branch_labels = None
depends_on = None


def _existing_columns(inspector, table_name: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    user_columns = _existing_columns(inspector, "users")
    if "avatar_image" not in user_columns:
        op.add_column("users", sa.Column("avatar_image", sa.String(), nullable=True))

    tables = inspector.get_table_names()
    if "media_files" in tables:
        metadata = sa.MetaData()
        media_files = sa.Table("media_files", metadata, autoload_with=bind)
        users = sa.Table("users", metadata, autoload_with=bind)

        results = bind.execute(
            sa.select(
                media_files.c.owner_user_id, media_files.c.type, media_files.c.file_path, media_files.c.is_active
            )
        ).fetchall()

        media_map: dict[int, dict[str, str]] = {}
        for owner_user_id, media_type, file_path, is_active in results:
            if not is_active or not file_path:
                continue
            user_entry = media_map.setdefault(owner_user_id, {})
            media_key = media_type.value if hasattr(media_type, "value") else str(media_type)
            user_entry[media_key] = file_path

        for user_id, paths in media_map.items():
            updates = {}
            if paths.get("avatar"):
                updates["avatar_image"] = paths["avatar"]
            if paths.get("id_card"):
                updates["id_card_image"] = paths["id_card"]
            if paths.get("selfie"):
                updates["selfie_image"] = paths["selfie"]
            if updates:
                bind.execute(
                    sa.update(users)
                    .where(users.c.id == user_id)
                    .values(**updates)
                )

        fk_by_column = {fk["constrained_columns"][0]: fk["name"] for fk in inspector.get_foreign_keys("users")}
        indexes = {idx["name"] for idx in inspector.get_indexes("users")}

        for column in ["avatar_media_id", "active_id_card_media_id", "active_selfie_media_id"]:
            if column in user_columns:
                if column in fk_by_column:
                    op.drop_constraint(fk_by_column[column], "users", type_="foreignkey")
                index_name = op.f(f"ix_users_{column}")
                if index_name in indexes:
                    op.drop_index(index_name, table_name="users")
                op.drop_column("users", column)

        op.drop_table("media_files")

    user_columns = _existing_columns(inspector, "users")
    indexes = {idx["name"] for idx in inspector.get_indexes("users")}
    fk_by_column = {fk["constrained_columns"][0]: fk["name"] for fk in inspector.get_foreign_keys("users")}

    if "current_kyc_attempt_id" in user_columns and "fk_users_current_kyc_attempt" not in fk_by_column.values():
        op.create_foreign_key(
            "fk_users_current_kyc_attempt",
            "users",
            "kyc_attempts",
            ["current_kyc_attempt_id"],
            ["id"],
        )

    index_name = op.f("ix_users_current_kyc_attempt_id")
    if "current_kyc_attempt_id" in user_columns and index_name not in indexes:
        op.create_index(index_name, "users", ["current_kyc_attempt_id"], unique=False)



def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_columns = _existing_columns(inspector, "users")

    mediatype_enum = sa.Enum("id_card", "selfie", "avatar", name="mediatype")
    mediatype_enum.create(bind, checkfirst=True)

    if "media_files" not in inspector.get_table_names():
        op.create_table(
            "media_files",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("owner_user_id", sa.Integer(), nullable=True),
            sa.Column("kyc_attempt_id", sa.Integer(), nullable=True),
            sa.Column("type", mediatype_enum, nullable=False),
            sa.Column("file_path", sa.String(), nullable=True, unique=True),
            sa.Column("mime_type", sa.String(), nullable=True),
            sa.Column("size_bytes", sa.Integer(), nullable=True),
            sa.Column("checksum", sa.String(), nullable=True),
            sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
            sa.ForeignKeyConstraint(["kyc_attempt_id"], ["kyc_attempts.id"]),
            sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_media_files_id"), "media_files", ["id"], unique=False)
        op.create_index(op.f("ix_media_files_owner_user_id"), "media_files", ["owner_user_id"], unique=False)
        op.create_index(op.f("ix_media_files_kyc_attempt_id"), "media_files", ["kyc_attempt_id"], unique=False)

    fk_by_column = {fk["constrained_columns"][0]: fk["name"] for fk in inspector.get_foreign_keys("users")}
    indexes = {idx["name"] for idx in inspector.get_indexes("users")}

    columns_to_restore = {
        "avatar_media_id": sa.Column("avatar_media_id", sa.Integer(), nullable=True),
        "active_id_card_media_id": sa.Column("active_id_card_media_id", sa.Integer(), nullable=True),
        "active_selfie_media_id": sa.Column("active_selfie_media_id", sa.Integer(), nullable=True),
    }

    for name, column in columns_to_restore.items():
        if name not in existing_columns:
            op.add_column("users", column)
        fk_name = fk_by_column.get(name) or f"fk_users_{name}"
        if name in _existing_columns(sa.inspect(bind), "users") and fk_name not in fk_by_column.values():
            op.create_foreign_key(fk_name, "users", "media_files", [name], ["id"])
        index_name = op.f(f"ix_users_{name}")
        if index_name not in indexes:
            op.create_index(index_name, "users", [name], unique=False)

    if "current_kyc_attempt_id" in existing_columns:
        fk_by_column = {fk["constrained_columns"][0]: fk["name"] for fk in sa.inspect(bind).get_foreign_keys("users")}
        if "current_kyc_attempt_id" not in fk_by_column:
            op.create_foreign_key(
                "fk_users_current_kyc_attempt",
                "users",
                "kyc_attempts",
                ["current_kyc_attempt_id"],
                ["id"],
            )

    if "avatar_image" in existing_columns:
        op.drop_column("users", "avatar_image")
