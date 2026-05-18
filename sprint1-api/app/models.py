"""Data models for the Task Management API."""

import uuid
from datetime import datetime, date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class TaskStatus(str, Enum):
    """Valid task statuses."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Valid task priorities."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskCreate(BaseModel):
    """Schema for creating a new task."""
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=2000, description="Task description")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Task status")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Task priority")
    assignee: Optional[str] = Field(None, max_length=100, description="Person assigned")
    due_date: Optional[date] = Field(None, description="Due date in ISO 8601 format")
    tags: Optional[list[str]] = Field(default=None, description="List of tags")

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is not None:
            if len(v) > 10:
                raise ValueError("Maximum 10 tags allowed")
            for tag in v:
                if len(tag) > 50:
                    raise ValueError(f"Tag '{tag[:20]}...' exceeds 50 character limit")
                if len(tag) == 0:
                    raise ValueError("Empty tags are not allowed")
        return v


class TaskUpdate(BaseModel):
    """Schema for full task update (PUT)."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: TaskStatus
    priority: TaskPriority
    assignee: Optional[str] = Field(None, max_length=100)
    due_date: Optional[date] = None
    tags: Optional[list[str]] = None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is not None:
            if len(v) > 10:
                raise ValueError("Maximum 10 tags allowed")
            for tag in v:
                if len(tag) > 50:
                    raise ValueError(f"Tag '{tag[:20]}...' exceeds 50 character limit")
                if len(tag) == 0:
                    raise ValueError("Empty tags are not allowed")
        return v


class StatusUpdate(BaseModel):
    """Schema for updating only the task status (PATCH)."""
    status: TaskStatus


class TaskResponse(BaseModel):
    """Schema for task response."""
    id: str
    title: str
    description: Optional[str] = None
    status: TaskStatus
    priority: TaskPriority
    assignee: Optional[str] = None
    due_date: Optional[date] = None
    tags: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    """Schema for paginated task list response."""
    tasks: list[TaskResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class TaskStats(BaseModel):
    """Schema for task statistics."""
    total_tasks: int
    by_status: dict[str, int]
    by_priority: dict[str, int]


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str
    timestamp: datetime
    version: str


class ErrorDetail(BaseModel):
    """Individual error detail."""
    field: str
    message: str


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    errors: list[ErrorDetail] = Field(default_factory=list)
