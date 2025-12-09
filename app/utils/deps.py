from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db import get_db
from app.models.user import User
from app.models.permission import Role

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

def get_current_user(token: str = Depends(api_key_header), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    if token.startswith("Bearer "):
        token = token.split("Bearer ")[1]

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

def user_has_permission(required_permission: str):
    def _user_has_permission(current_user: User = Depends(get_current_user)):
        if not current_user.role:
            raise HTTPException(status_code=403, detail="The user does not have a role assigned")

        if current_user.role.name == "owner":
            return current_user

        for permission in current_user.role.permissions:
            if permission.name == required_permission:
                return current_user

        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")

    return _user_has_permission
