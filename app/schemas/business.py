from pydantic import BaseModel
from typing import Optional

class BusinessBase(BaseModel):
    name: str
    contact_person: str
    phone_number: str
    address: str
    status: Optional[bool] = True

class BusinessCreate(BusinessBase):
    pass

class BusinessUpdate(BusinessBase):
    pass

class Business(BusinessBase):
    id: int
    created_by_admin_id: int

    class Config:
        orm_mode = True
