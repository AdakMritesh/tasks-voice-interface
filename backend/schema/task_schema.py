"""
Schema definitions for task-related operations
"""

import uuid

from pydantic import BaseModel, Field, AliasChoices, ConfigDict
from datetime import datetime

from backend.enums.task_statuses import TaskStatus

class TaskCreate(BaseModel):
    title: str
    status: TaskStatus = TaskStatus.TODO
    due_date: datetime | None = Field(
        default=None,
        validation_alias=AliasChoices(
            'dueDate',
            'due_date'
        )
    )
    model_config = ConfigDict(from_attributes=True)

class TaskUpdate(BaseModel):
    title: str | None = None
    status: TaskStatus | None = None
    due_date: datetime | None = Field(
        default=None,
        validation_alias=AliasChoices(
            'dueDate',
            'due_date'
        )
    )
    model_config = ConfigDict(from_attributes=True)

class TaskResponse(BaseModel):
    id: uuid.UUID
    title: str
    status: TaskStatus
    due_date: datetime | None
    # add audit fields if and when needed
    model_config = ConfigDict(from_attributes=True)