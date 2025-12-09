from pydantic import BaseModel
from typing import Optional

from pydantic import Field

class BusinessBase(BaseModel):
    name: str = Field(..., example="ACME Corporation")
    contact_person: str = Field(..., example="John Doe")
    phone_number: str = Field(..., example="+15555555555")
    address: str = Field(..., example="123 Main St")
    status: Optional[bool] = Field(True, example=True)

class BusinessCreate(BusinessBase):
    pass

class BusinessUpdate(BusinessBase):
    pass

class Business(BusinessBase):
    id: int
    created_by_admin_id: int

    class Config:
        orm_mode = True
