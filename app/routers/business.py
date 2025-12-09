from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db import get_db
from app.schemas.business import Business, BusinessCreate, BusinessUpdate
from app.models.business import Business as BusinessModel
from app.models.user import User
from app.utils.deps import get_current_user

router = APIRouter()

def get_current_admin_user(current_user: User = Depends(get_current_user)):
    if not current_user.role or current_user.role.name not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
    return current_user

@router.post("/", response_model=Business)
def create_business(business: BusinessCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    db_business = BusinessModel(**business.dict(), created_by_admin_id=current_user.id)
    db.add(db_business)
    db.commit()
    db.refresh(db_business)
    return db_business

@router.get("/", response_model=List[Business])
def read_businesses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    businesses = db.query(BusinessModel).offset(skip).limit(limit).all()
    return businesses

@router.patch("/{business_id}", response_model=Business)
def update_business(business_id: int, business: BusinessUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    db_business = db.query(BusinessModel).filter(BusinessModel.id == business_id).first()
    if not db_business:
        raise HTTPException(status_code=404, detail="Business not found")
    for field, value in business.dict(exclude_unset=True).items():
        setattr(db_business, field, value)
    db.commit()
    db.refresh(db_business)
    return db_business
