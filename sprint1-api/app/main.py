"""Task Management REST API — Main Application.

A production-ready REST API built with FastAPI following the AI-first development
methodology: spec → generate → validate → own.
"""

import math
import os
import hmac
import logging
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
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


RATE_LIMIT_REQUESTS = int(os.environ.get("RATE_LIMIT_REQUESTS", "120"))
RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "60"))
_rate_limit_hits: dict[str, deque[float]] = defaultdict(deque)

audit_logger = logging.getLogger("gauntlet.audit")
if not audit_logger.handlers:
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))


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


def _validate_origin(origin: str) -> bool:
    """Validate a configured CORS origin."""
    try:
        parsed = urlparse(origin)
    except Exception:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    if not parsed.netloc:
        return False
    if os.environ.get("ENVIRONMENT") == "production":
        if parsed.hostname in {"localhost", "127.0.0.1", "::1"}:
            return False
    return True


def _get_allowed_origins() -> list[str]:
    """Build a validated CORS allowlist."""
    configured = [
        origin.strip()
        for origin in os.environ.get("ALLOWED_ORIGINS", "").split(",")
        if origin.strip()
    ]
    validated = [origin for origin in configured if origin != "*" and _validate_origin(origin)]
    if validated:
        return validated
    return ["http://localhost:3000", "http://localhost:8000"]


def _extract_bearer_token(authorization: str | None) -> str | None:
    """Extract a bearer token from an Authorization header."""
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token


async def require_write_auth(
    authorization: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
) -> None:
    """Require a write token when API_AUTH_TOKEN is configured.

    This keeps the Week 1 read-only demo publicly inspectable while allowing
    deployed instances to protect create/update/delete operations.
    """
    expected = os.environ.get("API_AUTH_TOKEN")
    if not expected:
        if os.environ.get("ENVIRONMENT") == "production":
            raise HTTPException(status_code=503, detail="API write authentication is not configured")
        return

    supplied = x_api_key or _extract_bearer_token(authorization)
    if not supplied or not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing API token")


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply lightweight per-client request rate limiting."""
    if request.url.path.startswith("/api/"):
        client_host = request.client.host if request.client else "unknown"
        key = f"{client_host}:{request.url.path}"
        now = time.monotonic()
        hits = _rate_limit_hits[key]
        while hits and now - hits[0] > RATE_LIMIT_WINDOW_SECONDS:
            hits.popleft()
        if len(hits) >= RATE_LIMIT_REQUESTS:
            audit_logger.warning("rate_limit_exceeded client=%s path=%s", client_host, request.url.path)
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please retry later."},
            )
        hits.append(now)
    return await call_next(request)


# CORS middleware
allowed_origins = _get_allowed_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
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
        timestamp=datetime.now(timezone.utc),
        version="1.0.0",
    )


@app.post("/api/v1/tasks", response_model=TaskResponse, status_code=201, tags=["Tasks"])
async def create_new_task(task: TaskCreate, _: None = Depends(require_write_auth)):
    """Create a new task.

    Requires at minimum a title. Status defaults to 'pending', priority to 'medium'.
    """
    result = await create_task(task)
    audit_logger.info("action=create_task title=%s", task.title)
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
    try:
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
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
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
async def update_existing_task(task_id: str, task: TaskUpdate, _: None = Depends(require_write_auth)):
    """Full update of a task (all fields required)."""
    result = await update_task(task_id, task)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Task with id '{task_id}' not found",
        )
    audit_logger.info("action=update_task task_id=%s", task_id)
    return result


@app.patch("/api/v1/tasks/{task_id}/status", response_model=TaskResponse, tags=["Tasks"])
async def patch_task_status(
    task_id: str,
    status_update: StatusUpdate,
    _: None = Depends(require_write_auth),
):
    """Update only the status of a task."""
    result = await update_task_status(task_id, status_update)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Task with id '{task_id}' not found",
        )
    audit_logger.info("action=patch_task_status task_id=%s status=%s", task_id, status_update.status.value)
    return result


@app.delete("/api/v1/tasks/{task_id}", status_code=204, tags=["Tasks"])
async def delete_existing_task(task_id: str, _: None = Depends(require_write_auth)):
    """Delete a task by ID. Returns 204 on success, 404 if not found."""
    deleted = await delete_task(task_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Task with id '{task_id}' not found",
        )
    audit_logger.info("action=delete_task task_id=%s", task_id)
    return None
