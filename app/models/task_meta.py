from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.db import Base

task_tag_link = Table('task_tag_link', Base.metadata,
    Column('task_id', Integer, ForeignKey('tasks.id')),
    Column('tag_id', Integer, ForeignKey('task_tags.id'))
)

class TaskCategory(Base):
    __tablename__ = "task_categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

class TaskTag(Base):
    __tablename__ = "task_tags"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
