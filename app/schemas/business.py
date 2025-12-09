from pydantic import BaseModel
from typing import Optional

class BusinessBase(BaseModel):
    name: str
    contact_person: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None

class BusinessCreate(BusinessBase):
    pass

class BusinessUpdate(BusinessBase):
    status: Optional[str] = None

class Business(BusinessBase):
    id: int
    status: str
    created_by_admin_id: int

    class Config:
        from_attributes = True
