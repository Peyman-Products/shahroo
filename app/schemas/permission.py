from pydantic import BaseModel
from typing import List, Optional

class PermissionBase(BaseModel):
    name: str

class PermissionCreate(PermissionBase):
    pass

class Permission(PermissionBase):
    id: int

    class Config:
        from_attributes = True

class RoleBase(BaseModel):
    name: str

class RoleCreate(RoleBase):
    pass

class Role(RoleBase):
    id: int
    permissions: List[Permission] = []

    class Config:
        from_attributes = True

class UserRole(BaseModel):
    user_id: int
    role_id: int

class RolePermission(BaseModel):
    role_id: int
    permission_id: int
