"""Task Management REST API — Main Application.

A production-ready REST API built with FastAPI following the AI-first development
methodology: spec → generate → validate → own.
"""

import math
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.models import (
    ErrorResponse,
    HealthResponse,
    StatusUpdate,
    TaskCreate,
    TaskListResponse,
    TaskPriority,
    TaskResponse,
    TaskStats,
    TaskStatus,
    TaskUpdate,
)
from app.database import (
    create_task,
    delete_task,
    get_stats,
    get_task,
    init_db,
    list_tasks,
    update_task,
    update_task_status,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize DB on startup."""
    await init_db()
    yield


app = FastAPI(
    title="Task Management API",
    description="A Week 1 production-style task management REST API built with AI-first methodology.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
allowed_origins = [
    origin.strip()
    for origin in os.environ.get("ALLOWED_ORIGINS", "*").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Custom handler for validation errors — returns structured error response."""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        errors.append({"field": field, "message": error["msg"]})

    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error: request body contains invalid data",
            "errors": errors,
        },
    )


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check endpoint for deployment monitoring."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0",
    )


@app.post("/api/v1/tasks", response_model=TaskResponse, status_code=201, tags=["Tasks"])
async def create_new_task(task: TaskCreate):
    """Create a new task.

    Requires at minimum a title. Status defaults to 'pending', priority to 'medium'.
    """
    result = await create_task(task)
    return result


@app.get("/api/v1/tasks", response_model=TaskListResponse, tags=["Tasks"])
async def list_all_tasks(
    status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    priority: Optional[TaskPriority] = Query(None, description="Filter by priority"),
    assignee: Optional[str] = Query(None, description="Filter by assignee"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """List all tasks with optional filtering, sorting, and pagination."""
    tasks, total = await list_tasks(
        status=status,
        priority=priority,
        assignee=assignee,
        tag=tag,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        per_page=per_page,
    )
    total_pages = math.ceil(total / per_page) if total > 0 else 0
    return TaskListResponse(
        tasks=tasks,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )


@app.get("/api/v1/tasks/stats", response_model=TaskStats, tags=["Tasks"])
async def get_task_stats():
    """Get task statistics: counts by status and priority."""
    stats = await get_stats()
    return TaskStats(**stats)


@app.get("/api/v1/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
async def get_single_task(task_id: str):
    """Get a single task by its ID."""
    task = await get_task(task_id)
    if task is None:
        raise HTTPException(
            status_code=404,
            detail=f"Task with id '{task_id}' not found",
        )
    return task


@app.put("/api/v1/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
async def update_existing_task(task_id: str, task: TaskUpdate):
    """Full update of a task (all fields required)."""
    result = await update_task(task_id, task)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Task with id '{task_id}' not found",
        )
    return result


@app.patch("/api/v1/tasks/{task_id}/status", response_model=TaskResponse, tags=["Tasks"])
async def patch_task_status(task_id: str, status_update: StatusUpdate):
    """Update only the status of a task."""
    result = await update_task_status(task_id, status_update)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Task with id '{task_id}' not found",
        )
    return result


@app.delete("/api/v1/tasks/{task_id}", status_code=204, tags=["Tasks"])
async def delete_existing_task(task_id: str):
    """Delete a task by ID. Returns 204 on success, 404 if not found."""
    deleted = await delete_task(task_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Task with id '{task_id}' not found",
        )
    return None
