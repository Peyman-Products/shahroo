from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db import get_db
from app.schemas.permission import Role, RoleCreate, Permission, PermissionCreate, UserRole
from app.models.permission import Role as RoleModel, Permission as PermissionModel
from app.models.user import User
from app.utils.deps import get_current_user

router = APIRouter()

def get_current_owner_or_admin_user(current_user: User = Depends(get_current_user)):
    if not current_user.role or current_user.role.name not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
    return current_user

@router.post("/roles", response_model=Role)
def create_role(role: RoleCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_owner_or_admin_user)):
    db_role = RoleModel(name=role.name)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

@router.get("/roles", response_model=List[Role])
def read_roles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_owner_or_admin_user)):
    roles = db.query(RoleModel).offset(skip).limit(limit).all()
    return roles

@router.post("/permissions", response_model=Permission)
def create_permission(permission: PermissionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_owner_or_admin_user)):
    db_permission = PermissionModel(name=permission.name)
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_permission

@router.get("/permissions", response_model=List[Permission])
def read_permissions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_owner_or_admin_user)):
    permissions = db.query(PermissionModel).offset(skip).limit(limit).all()
    return permissions

from app.schemas.permission import RolePermission

@router.post("/users/roles")
def assign_role_to_user(user_role: UserRole, db: Session = Depends(get_db), current_user: User = Depends(get_current_owner_or_admin_user)):
    user = db.query(User).filter(User.id == user_role.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    role = db.query(RoleModel).filter(RoleModel.id == user_role.role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    user.role_id = role.id
    db.commit()
    return {"message": "Role assigned successfully"}

@router.post("/roles/permissions")
def assign_permission_to_role(role_permission: RolePermission, db: Session = Depends(get_db), current_user: User = Depends(get_current_owner_or_admin_user)):
    role = db.query(RoleModel).filter(RoleModel.id == role_permission.role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    permission = db.query(PermissionModel).filter(PermissionModel.id == role_permission.permission_id).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    role.permissions.append(permission)
    db.commit()
    return {"message": "Permission assigned to role successfully"}
