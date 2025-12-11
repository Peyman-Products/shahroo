from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.task import TaskStatus, StepStatus


class TaskKindBase(BaseModel):
    name: str = Field(..., example="Delivery")
    description: Optional[str] = Field(None, example="Tasks related to delivering items")


class TaskKindCreate(TaskKindBase):
    pass


class TaskKind(TaskKindBase):
    id: int

    class Config:
        from_attributes = True

class TaskStepBase(BaseModel):
    title: str = Field(..., example="Pick up package")
    description: Optional[str] = Field(None, example="Package is at the front desk")
    address: str = Field(..., example="456 Oak Ave")
    lat: Optional[float] = Field(None, example=51.5074)
    lng: Optional[float] = Field(None, example=-0.1278)
    order: int = Field(..., example=1)

class TaskStepCreate(TaskStepBase):
    pass

class TaskStepUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    status: Optional[StepStatus] = None
    order: Optional[int] = None

class TaskStep(TaskStepBase):
    id: int
    task_id: int
    status: StepStatus
    done_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TaskBase(BaseModel):
    title: str = Field(..., example="Deliver package to customer")
    description: Optional[str] = Field(None, example="Deliver two small boxes")
    business_id: int = Field(..., example=1)
    category_id: Optional[int] = Field(None, example=2)
    task_kind_id: Optional[int] = Field(None, example=3)
    price: float = Field(..., example=15.50)
    estimated_time: int = Field(..., example=90)
    start_datetime: datetime = Field(..., example="2025-01-01T12:00:00Z")
    address: Optional[str] = Field(None, example="123 Main St")
    lat: Optional[float] = Field(None, example=34.0522)
    lng: Optional[float] = Field(None, example=-118.2437)

class TaskCreate(TaskBase):
    steps: List[TaskStepCreate] = Field(..., example=[{"title": "Pick up package", "description": "Package is at the front desk", "address": "456 Oak Ave", "order": 1}])

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    business_id: Optional[int] = None
    category_id: Optional[int] = None
    task_kind_id: Optional[int] = None
    price: Optional[float] = None
    estimated_time: Optional[int] = None
    start_datetime: Optional[datetime] = None
    status: Optional[TaskStatus] = None
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None

class Task(TaskBase):
    id: int
    assigned_user_id: Optional[int] = None
    task_kind_id: Optional[int] = None
    status: TaskStatus
    steps: List[TaskStep] = Field(default_factory=list)
    kind: Optional[TaskKind] = None
    accepted_at: Optional[datetime] = None
    done_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None

    class Config:
        from_attributes = True
