from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, Float, Enum
from sqlalchemy.orm import relationship
from app.db import Base
from app.models.task_meta import task_tag_link
import enum

class TaskStatus(enum.Enum):
    issued = "issued"
    in_progress = "in_progress"
    done = "done"
    approved = "approved"
    canceled = "canceled"
    failed = "failed"
    rejected = "rejected"

class StepStatus(enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    done = "done"
    failed = "failed"
    canceled = "canceled"

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"))
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by_admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("task_categories.id"))
    price = Column(Float)
    estimated_time = Column(Integer) # in minutes
    start_datetime = Column(DateTime(timezone=True))
    status = Column(Enum(TaskStatus), default=TaskStatus.issued)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    done_at = Column(DateTime(timezone=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    start_location_country_id = Column(Integer, ForeignKey("countries.id"))
    start_location_province_id = Column(Integer, ForeignKey("provinces.id"))
    start_location_city_id = Column(Integer, ForeignKey("cities.id"))
    address = Column(String)
    lat = Column(Float)
    lng = Column(Float)

    business = relationship("Business")
    assigned_user = relationship("User", foreign_keys=[assigned_user_id])
    created_by_admin = relationship("User", foreign_keys=[created_by_admin_id])
    steps = relationship("TaskStep", back_populates="task")
    category = relationship("TaskCategory", back_populates="tasks")
    tags = relationship("TaskTag", secondary=task_tag_link, back_populates="tasks")

class TaskStep(Base):
    __tablename__ = "task_steps"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    title = Column(String)
    description = Column(String, nullable=True)
    address = Column(String)
    lat = Column(Float)
    lng = Column(Float)
    estimated_time = Column(Integer)
    start_time = Column(DateTime(timezone=True))
    status = Column(Enum(StepStatus), default=StepStatus.pending)
    order = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    done_at = Column(DateTime(timezone=True), nullable=True)

    task = relationship("Task", back_populates="steps")
