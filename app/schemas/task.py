from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.task import TaskStatus, StepStatus

class TaskStepBase(BaseModel):
    title: str = Field(..., example="Pick up package")
    description: Optional[str] = Field(None, example="Package is at the front desk")
    address: str = Field(..., example="456 Oak Ave")
    order: int = Field(..., example=1)

class TaskStepCreate(TaskStepBase):
    pass

class TaskStepUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
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
    business_id: int = Field(..., example=1)
    price: float = Field(..., example=15.50)
    estimated_time: int = Field(..., example=90)
    start_datetime: datetime = Field(..., example="2025-01-01T12:00:00Z")

class TaskCreate(TaskBase):
    steps: List[TaskStepCreate] = Field(..., example=[{"title": "Pick up package", "description": "Package is at the front desk", "address": "456 Oak Ave", "order": 1}])

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    business_id: Optional[int] = None
    price: Optional[float] = None
    estimated_time: Optional[int] = None
    start_datetime: Optional[datetime] = None
    status: Optional[TaskStatus] = None

class Task(TaskBase):
    id: int
    assigned_user_id: Optional[int] = None
    status: TaskStatus
    steps: List[TaskStep] = []
    accepted_at: Optional[datetime] = None
    done_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None

    class Config:
        from_attributes = True
