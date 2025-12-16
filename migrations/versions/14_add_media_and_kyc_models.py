"""Add media metadata and KYC attempts

Revision ID: 14
Revises: 13
Create Date: 2024-11-02 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op


# revision identifiers, used by Alembic.
revision: str = '14'
down_revision: Union[str, None] = '13'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    mediatype_enum = postgresql.ENUM('id_card', 'selfie', 'avatar', name='mediatype')
    mediatype_enum.create(bind, checkfirst=True)
    mediatype = postgresql.ENUM('id_card', 'selfie', 'avatar', name='mediatype', create_type=False)
    verification_status = postgresql.ENUM(
        'unverified',
        'pending',
        'verified',
        'rejected',
        name='verificationstatus',
        create_type=False,
    )
    if not inspector.has_table('kyc_attempts'):
        op.create_table(
            'kyc_attempts',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('status', verification_status, nullable=True),
            sa.Column('reason_codes', sa.String(), nullable=True),
            sa.Column('reason_text', sa.String(), nullable=True),
            sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('allow_resubmission', sa.Boolean(), nullable=True, server_default=sa.text('true')),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_kyc_attempts_id'), 'kyc_attempts', ['id'], unique=False)
        op.create_index(op.f('ix_kyc_attempts_user_id'), 'kyc_attempts', ['user_id'], unique=False)

    if not inspector.has_table('media_files'):
        op.create_table(
            'media_files',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('owner_user_id', sa.Integer(), nullable=True),
            sa.Column('kyc_attempt_id', sa.Integer(), nullable=True),
            sa.Column('type', mediatype, nullable=False),
            sa.Column('file_path', sa.String(), nullable=True, unique=True),
            sa.Column('mime_type', sa.String(), nullable=True),
            sa.Column('size_bytes', sa.Integer(), nullable=True),
            sa.Column('checksum', sa.String(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('true')),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.ForeignKeyConstraint(['kyc_attempt_id'], ['kyc_attempts.id'], ),
            sa.ForeignKeyConstraint(['owner_user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_media_files_id'), 'media_files', ['id'], unique=False)
        op.create_index(op.f('ix_media_files_owner_user_id'), 'media_files', ['owner_user_id'], unique=False)
        op.create_index(op.f('ix_media_files_kyc_attempt_id'), 'media_files', ['kyc_attempt_id'], unique=False)

    existing_user_columns = {column['name'] for column in inspector.get_columns('users')}
    columns_to_add = [
        ('avatar_media_id', sa.Column('avatar_media_id', sa.Integer(), nullable=True)),
        ('active_id_card_media_id', sa.Column('active_id_card_media_id', sa.Integer(), nullable=True)),
        ('active_selfie_media_id', sa.Column('active_selfie_media_id', sa.Integer(), nullable=True)),
        ('current_kyc_attempt_id', sa.Column('current_kyc_attempt_id', sa.Integer(), nullable=True)),
        ('kyc_locked_at', sa.Column('kyc_locked_at', sa.DateTime(timezone=True), nullable=True)),
        ('kyc_last_reason_codes', sa.Column('kyc_last_reason_codes', sa.String(), nullable=True)),
        ('kyc_last_reason_text', sa.Column('kyc_last_reason_text', sa.String(), nullable=True)),
        ('kyc_last_decided_at', sa.Column('kyc_last_decided_at', sa.DateTime(timezone=True), nullable=True)),
    ]
    for name, column in columns_to_add:
        if name not in existing_user_columns:
            op.add_column('users', column)

    existing_foreign_keys = {fk['name'] for fk in inspector.get_foreign_keys('users')}
    if 'fk_users_avatar_media_id' not in existing_foreign_keys:
        op.create_foreign_key('fk_users_avatar_media_id', 'users', 'media_files', ['avatar_media_id'], ['id'])
    if 'fk_users_id_card_media_id' not in existing_foreign_keys:
        op.create_foreign_key('fk_users_id_card_media_id', 'users', 'media_files', ['active_id_card_media_id'], ['id'])
    if 'fk_users_selfie_media_id' not in existing_foreign_keys:
        op.create_foreign_key('fk_users_selfie_media_id', 'users', 'media_files', ['active_selfie_media_id'], ['id'])
    if 'fk_users_current_kyc_attempt' not in existing_foreign_keys:
        op.create_foreign_key('fk_users_current_kyc_attempt', 'users', 'kyc_attempts', ['current_kyc_attempt_id'], ['id'])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_foreign_keys = {fk['name'] for fk in inspector.get_foreign_keys('users')}
    if 'fk_users_current_kyc_attempt' in existing_foreign_keys:
        op.drop_constraint('fk_users_current_kyc_attempt', 'users', type_='foreignkey')
    if 'fk_users_selfie_media_id' in existing_foreign_keys:
        op.drop_constraint('fk_users_selfie_media_id', 'users', type_='foreignkey')
    if 'fk_users_id_card_media_id' in existing_foreign_keys:
        op.drop_constraint('fk_users_id_card_media_id', 'users', type_='foreignkey')
    if 'fk_users_avatar_media_id' in existing_foreign_keys:
        op.drop_constraint('fk_users_avatar_media_id', 'users', type_='foreignkey')

    existing_user_columns = {column['name'] for column in inspector.get_columns('users')}
    columns_to_drop = [
        'kyc_last_decided_at',
        'kyc_last_reason_text',
        'kyc_last_reason_codes',
        'kyc_locked_at',
        'current_kyc_attempt_id',
        'active_selfie_media_id',
        'active_id_card_media_id',
        'avatar_media_id',
    ]
    for column_name in columns_to_drop:
        if column_name in existing_user_columns:
            op.drop_column('users', column_name)

    if inspector.has_table('media_files'):
        existing_indexes = {index['name'] for index in inspector.get_indexes('media_files')}
        if op.f('ix_media_files_kyc_attempt_id') in existing_indexes:
            op.drop_index(op.f('ix_media_files_kyc_attempt_id'), table_name='media_files')
        if op.f('ix_media_files_owner_user_id') in existing_indexes:
            op.drop_index(op.f('ix_media_files_owner_user_id'), table_name='media_files')
        if op.f('ix_media_files_id') in existing_indexes:
            op.drop_index(op.f('ix_media_files_id'), table_name='media_files')
        op.drop_table('media_files')

    if inspector.has_table('kyc_attempts'):
        existing_indexes = {index['name'] for index in inspector.get_indexes('kyc_attempts')}
        if op.f('ix_kyc_attempts_user_id') in existing_indexes:
            op.drop_index(op.f('ix_kyc_attempts_user_id'), table_name='kyc_attempts')
        if op.f('ix_kyc_attempts_id') in existing_indexes:
            op.drop_index(op.f('ix_kyc_attempts_id'), table_name='kyc_attempts')
        op.drop_table('kyc_attempts')

    mediatype_enum = postgresql.ENUM('id_card', 'selfie', 'avatar', name='mediatype')
    mediatype_enum.drop(bind, checkfirst=True)
