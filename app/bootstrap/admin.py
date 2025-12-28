from sqlalchemy.orm import Session

from app.models.permission import Role, Permission
from app.models.user import User, VerificationStatus
from app.models.wallet import Wallet

ADMIN_ROLE = "admin"
ADMIN_PERMISSIONS = [
    "admin_access",
    "admin_users_read",
    "admin_users_verify",
    "admin_tasks_manage",
    "admin_wallets_manage",
    "admin_otp_lookup",
    "create_task",
]


def bootstrap_admin(db: Session, phone_number: str, force: bool = False) -> None:
    role = db.query(Role).filter(Role.name == ADMIN_ROLE).first()
    if not role:
        role = Role(name=ADMIN_ROLE)
        db.add(role)
        db.commit()
        db.refresh(role)

    existing_permissions = {
        permission.name: permission
        for permission in db.query(Permission)
        .filter(Permission.name.in_(ADMIN_PERMISSIONS))
        .all()
    }
    for name in ADMIN_PERMISSIONS:
        if name not in existing_permissions:
            permission = Permission(name=name)
            db.add(permission)
            existing_permissions[name] = permission
    db.commit()

    for name in ADMIN_PERMISSIONS:
        permission = existing_permissions.get(name)
        if permission and permission not in role.permissions:
            role.permissions.append(permission)
    db.commit()

    user = db.query(User).filter(User.phone_number == phone_number).first()
    if not user:
        user = User(
            phone_number=phone_number,
            role_id=role.id,
            verification_status=VerificationStatus.verified,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    elif user.role_id != role.id or force:
        user.role_id = role.id
        if force and user.verification_status != VerificationStatus.verified:
            user.verification_status = VerificationStatus.verified
        db.commit()

    wallet = db.query(Wallet).filter(Wallet.user_id == user.id).first()
    if not wallet:
        db.add(Wallet(user_id=user.id))
        db.commit()
