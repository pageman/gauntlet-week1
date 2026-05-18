# Sprint 1 Specification: AI-Assisted REST API with Full Test Coverage

## Overview

A Week 1 production-style Task Management REST API built with FastAPI following the AI-first development methodology: **spec → generate → validate → own**. This API demonstrates the core principles of the Gauntlet curriculum: rigorous specification before code, AI-assisted development with validation discipline, public deployment, and comprehensive endpoint testing.

## What It Does

A REST API that provides complete CRUD operations for task management:

1. **Create tasks** — POST with title, description, status, priority, assignee, due date, and tags
2. **List tasks** — GET with filtering, sorting, and pagination
3. **Retrieve tasks** — GET a single task by ID
4. **Update tasks** — PUT for full updates, PATCH for status-only updates
5. **Delete tasks** — DELETE a task by ID
6. **Task statistics** — GET aggregated counts by status and priority
7. **Health checks** — GET system health for deployment monitoring

## API Endpoints

| Method | Path | Description | Status Code |
|--------|------|-------------|-------------|
| GET | `/health` | Health check | 200 |
| POST | `/api/v1/tasks` | Create task | 201 |
| GET | `/api/v1/tasks` | List tasks (with filters, sort, pagination) | 200 |
| GET | `/api/v1/tasks/stats` | Task statistics | 200 |
| GET | `/api/v1/tasks/{task_id}` | Get single task | 200 |
| PUT | `/api/v1/tasks/{task_id}` | Full task update | 200 |
| PATCH | `/api/v1/tasks/{task_id}/status` | Update status only | 200 |
| DELETE | `/api/v1/tasks/{task_id}` | Delete task | 204 |

## Request/Response Schemas

### TaskCreate (POST /api/v1/tasks)

```json
{
  "title": "string (required, 1-200 chars)",
  "description": "string (optional, max 2000 chars)",
  "status": "pending|in_progress|completed|cancelled (default: pending)",
  "priority": "low|medium|high|critical (default: medium)",
  "assignee": "string (optional, max 100 chars)",
  "due_date": "YYYY-MM-DD (optional)",
  "tags": "list of strings (optional, max 10 tags, each max 50 chars)"
}
```

### TaskResponse

```json
{
  "id": "UUID string",
  "title": "string",
  "description": "string or null",
  "status": "pending|in_progress|completed|cancelled",
  "priority": "low|medium|high|critical",
  "assignee": "string or null",
  "due_date": "YYYY-MM-DD or null",
  "tags": "list of strings",
  "created_at": "ISO 8601 timestamp",
  "updated_at": "ISO 8601 timestamp"
}
```

### TaskListResponse

```json
{
  "tasks": "list of TaskResponse",
  "total": "integer (total count)",
  "page": "integer (current page)",
  "per_page": "integer (items per page)",
  "total_pages": "integer (calculated)"
}
```

### TaskStats

```json
{
  "total_tasks": "integer",
  "by_status": {
    "pending": "integer",
    "in_progress": "integer",
    "completed": "integer",
    "cancelled": "integer"
  },
  "by_priority": {
    "low": "integer",
    "medium": "integer",
    "high": "integer",
    "critical": "integer"
  }
}
```

## Validation Rules

- **Title**: Required, 1-200 characters
- **Description**: Optional, max 2000 characters
- **Status**: One of four enum values; defaults to "pending"
- **Priority**: One of four enum values; defaults to "medium"
- **Assignee**: Optional, max 100 characters
- **Due Date**: Optional, ISO 8601 format (YYYY-MM-DD)
- **Tags**: Optional list; max 10 tags, each 1-50 characters, no empty tags

## Error Handling

All errors return structured JSON responses:

### 422 Validation Error

```json
{
  "detail": "Validation error: request body contains invalid data",
  "errors": [
    {"field": "title", "message": "ensure this value has at least 1 characters"},
    {"field": "tags", "message": "Maximum 10 tags allowed"}
  ]
}
```

### 404 Not Found

```json
{
  "detail": "Task with id 'xyz' not found"
}
```

### Malformed JSON

Returns 422 with structured error response (no raw parsing errors exposed).

## Query Parameters (GET /api/v1/tasks)

- `status`: Filter by status (pending, in_progress, completed, cancelled)
- `priority`: Filter by priority (low, medium, high, critical)
- `assignee`: Filter by assignee name
- `tag`: Filter by tag (matches if tag is in task's tag list)
- `sort_by`: Sort field (created_at, due_date, priority, title; default: created_at)
- `sort_order`: Sort order (asc, desc; default: desc)
- `page`: Page number (default: 1, min: 1)
- `per_page`: Items per page (default: 20, min: 1, max: 100)

## Database

- **Storage**: SQLite for the Week 1 demo; PostgreSQL is future work
- **Schema**: Single `tasks` table with indexed columns (status, priority, assignee)
- **Initialization**: Automatic on application startup via lifespan context manager

## Deployment

- **Framework**: FastAPI with Uvicorn
- **Container**: Docker with health check
- **Health Check**: HTTP GET /health endpoint
- **CORS**: Configurable through `ALLOWED_ORIGINS`; default is `*` for Week 1 demo
- **Port**: 8000 (configurable via PORT env var)

## Testing

- **Framework**: pytest with pytest-asyncio
- **Coverage**: endpoint coverage through 36 tests
- **Scope**: Happy paths, validation errors, edge cases, filtering, pagination, sorting, concurrent operations
- **Fixtures**: Async client, temporary database, sample task data

## Success Criteria

1. All 8 endpoints (including health check) functional and tested
2. 100% test coverage of endpoint behavior
3. Comprehensive validation with structured error responses
4. Deployable via Docker with working health checks
5. Clean-clone runnable: `git clone → pip install -r requirements.txt → pytest → docker build`
6. AI interaction log documenting all generated code, accepted/rejected changes, and validation discipline
