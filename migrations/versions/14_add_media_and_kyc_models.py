"""Add media metadata and KYC attempts

Revision ID: 14
Revises: 13
Create Date: 2024-11-02 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '14'
down_revision: Union[str, None] = '13'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    mediatype = sa.Enum('id_card', 'selfie', 'avatar', name='mediatype')
    mediatype.create(op.get_bind(), checkfirst=True)
    verification_status = postgresql.ENUM(
        'unverified',
        'pending',
        'verified',
        'rejected',
        name='verificationstatus',
        create_type=False,
    )

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

    op.add_column('users', sa.Column('avatar_media_id', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('active_id_card_media_id', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('active_selfie_media_id', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('current_kyc_attempt_id', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('kyc_locked_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('kyc_last_reason_codes', sa.String(), nullable=True))
    op.add_column('users', sa.Column('kyc_last_reason_text', sa.String(), nullable=True))
    op.add_column('users', sa.Column('kyc_last_decided_at', sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key('fk_users_avatar_media_id', 'users', 'media_files', ['avatar_media_id'], ['id'])
    op.create_foreign_key('fk_users_id_card_media_id', 'users', 'media_files', ['active_id_card_media_id'], ['id'])
    op.create_foreign_key('fk_users_selfie_media_id', 'users', 'media_files', ['active_selfie_media_id'], ['id'])
    op.create_foreign_key('fk_users_current_kyc_attempt', 'users', 'kyc_attempts', ['current_kyc_attempt_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_users_current_kyc_attempt', 'users', type_='foreignkey')
    op.drop_constraint('fk_users_selfie_media_id', 'users', type_='foreignkey')
    op.drop_constraint('fk_users_id_card_media_id', 'users', type_='foreignkey')
    op.drop_constraint('fk_users_avatar_media_id', 'users', type_='foreignkey')
    op.drop_column('users', 'kyc_last_decided_at')
    op.drop_column('users', 'kyc_last_reason_text')
    op.drop_column('users', 'kyc_last_reason_codes')
    op.drop_column('users', 'kyc_locked_at')
    op.drop_column('users', 'current_kyc_attempt_id')
    op.drop_column('users', 'active_selfie_media_id')
    op.drop_column('users', 'active_id_card_media_id')
    op.drop_column('users', 'avatar_media_id')

    op.drop_index(op.f('ix_media_files_kyc_attempt_id'), table_name='media_files')
    op.drop_index(op.f('ix_media_files_owner_user_id'), table_name='media_files')
    op.drop_index(op.f('ix_media_files_id'), table_name='media_files')
    op.drop_table('media_files')

    op.drop_index(op.f('ix_kyc_attempts_user_id'), table_name='kyc_attempts')
    op.drop_index(op.f('ix_kyc_attempts_id'), table_name='kyc_attempts')
    op.drop_table('kyc_attempts')

    mediatype = sa.Enum('id_card', 'selfie', 'avatar', name='mediatype')
    mediatype.drop(op.get_bind(), checkfirst=True)
