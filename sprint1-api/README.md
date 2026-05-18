# Task Management REST API

A Week 1 production-style REST API for task management built with FastAPI,
demonstrating AI-first development methodology with rigorous validation
discipline.

## Live Deployment

Public Render URL:

```text
https://gauntlet-week1.onrender.com
```

Useful live endpoints:

```text
https://gauntlet-week1.onrender.com/health
https://gauntlet-week1.onrender.com/api/v1/tasks
https://gauntlet-week1.onrender.com/api/v1/tasks/stats
https://gauntlet-week1.onrender.com/docs
```

Render Free caveat: the first request after inactivity can take 20-30 seconds
because the instance spins down. This free deployment uses temporary SQLite
storage, so task data is demo data and may reset across restarts.

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd sprint1-api

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running Locally

```bash
# Run the API
uvicorn app.main:app --reload

# The API will be available at http://localhost:8000
# OpenAPI docs at http://localhost:8000/docs
```

### Running Tests

```bash
# Run all tests
python -m pytest tests -q

# Run with verbose output
python -m pytest tests -v

# Run with coverage
python -m pytest --cov=app tests/
```

### Docker Deployment

```bash
# Build the image
docker build -t task-api:latest .

# Run the container
docker run -p 8000:8000 -e DATABASE_PATH=/data/tasks.db task-api:latest

# The API will be available at http://localhost:8000
```

## API Endpoints

### Health Check
- **GET** `/health` — System health status

### Task Operations
- **POST** `/api/v1/tasks` — Create a new task
- **GET** `/api/v1/tasks` — List tasks (with filtering, sorting, pagination)
- **GET** `/api/v1/tasks/stats` — Get task statistics
- **GET** `/api/v1/tasks/{task_id}` — Get a single task
- **PUT** `/api/v1/tasks/{task_id}` — Update a task (full update)
- **PATCH** `/api/v1/tasks/{task_id}/status` — Update task status only
- **DELETE** `/api/v1/tasks/{task_id}` — Delete a task

## Example Usage

### Create a Task

```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Implement authentication",
    "description": "Add JWT-based authentication to the API",
    "priority": "high",
    "assignee": "alice",
    "tags": ["backend", "security"]
  }'
```

### List Tasks with Filtering

```bash
# List all pending tasks
curl "http://localhost:8000/api/v1/tasks?status=pending"

# List high-priority tasks assigned to alice
curl "http://localhost:8000/api/v1/tasks?priority=high&assignee=alice"

# List tasks with pagination
curl "http://localhost:8000/api/v1/tasks?page=1&per_page=10"

# Sort by title ascending
curl "http://localhost:8000/api/v1/tasks?sort_by=title&sort_order=asc"
```

### Get Task Statistics

```bash
curl http://localhost:8000/api/v1/tasks/stats
```

### Update a Task Status

```bash
curl -X PATCH http://localhost:8000/api/v1/tasks/{task_id}/status \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'
```

## Architecture

```
app/
├── __init__.py
├── main.py           # FastAPI application and endpoints
├── models.py         # Pydantic models for validation
└── database.py       # SQLite repository layer

tests/
├── __init__.py
├── conftest.py       # Pytest fixtures and configuration
└── test_api.py       # Comprehensive test suite

Dockerfile           # Container definition
requirements.txt     # Python dependencies
SPEC.md             # Detailed specification
README.md           # This file
```

## Key Features

- **AI-First Development**: Built using Claude Code with rigorous validation discipline
- **Comprehensive Validation**: Pydantic models with custom validators for all inputs
- **Full Endpoint Coverage**: 42 tests covering all endpoints and edge cases
- **Clean Error Handling**: Structured JSON error responses with actionable messages
- **Async/Await**: Built on FastAPI's async foundation for high concurrency
- **Deployment-Ready**: Includes Docker support, health checks, and Render config
- **Database Flexibility**: SQLite for Week 1 demo/development; PostgreSQL is future work
- **Security Guardrails**: Optional write-token auth, lightweight rate limiting,
  CORS origin validation, audit logging, exact tag filtering, and safe parsing
  for malformed stored data

## Environment Variables

- `DATABASE_PATH` — Path to SQLite database (default: `tasks.db`)
- `PORT` — Server port supplied by the host platform; do not hardcode it on Render
- `ALLOWED_ORIGINS` — Comma-separated CORS origins (default: local development origins)
- `API_AUTH_TOKEN` — Optional token for write endpoints; accepted as
  `Authorization: Bearer ...` or `X-API-Key`
- `RATE_LIMIT_REQUESTS` — Per-client request count for `/api/` routes (default: `120`)
- `RATE_LIMIT_WINDOW_SECONDS` — Rate-limit window in seconds (default: `60`)

## Testing

The test suite includes:

- **Health check tests** — Verify system health endpoint
- **CRUD operation tests** — Create, read, update, delete functionality
- **Validation tests** — Invalid inputs, boundary conditions, malformed JSON
- **Filtering tests** — Status, priority, assignee, tag filters
- **Pagination tests** — Page navigation, per_page limits
- **Sorting tests** — Multiple sort fields and orders
- **Edge cases** — Concurrent operations, not-found scenarios
- **Error handling** — Proper HTTP status codes and error messages
- **Security regression tests** — Write auth, rate limiting, invalid sort
  rejection, exact tag matching, and corrupt stored JSON/timestamp handling

## AI Interaction Log

This project was built using AI-first methodology with strict validation discipline. All AI-generated code was:

1. **Reviewed** — Every function read and understood before committing
2. **Tested** — Comprehensive test suite validates all behavior
3. **Validated** — Security vulnerabilities (e.g., SQL injection) caught and fixed
4. **Owned** — All changes documented and explained

See `AI-INTERACTION-LOG.md` for detailed session logs.

## Deployment

### Render

```bash
Root Directory: sprint1-api
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Environment: DATABASE_PATH=/tmp/tasks.db
ALLOWED_ORIGINS=https://gauntlet-week1.onrender.com
ENVIRONMENT=production
API_AUTH_TOKEN=<Render secret>
Health Check Path: /health
```

### Other Platforms

Railway and Fly.io are reasonable alternatives, but this repo currently ships a
verified Render deployment as the public Week 1 evidence.

## Known Limitations

- Single-instance deployment (no horizontal scaling in this sprint)
- SQLite not recommended for high-concurrency production (use PostgreSQL)
- Write authentication is optional unless `API_AUTH_TOKEN` is configured; this
  is sufficient for Week 1 demo hardening but not a full identity system
- Rate limiting is in-process and per-instance; use a gateway or managed
  limiter for production traffic

## Development

### Adding a New Endpoint

1. Define the request/response models in `app/models.py`
2. Add database operations in `app/database.py`
3. Add the endpoint in `app/main.py`
4. Write tests in `tests/test_api.py`
5. Run tests: `pytest`

### Running with Hot Reload

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Support

For issues or questions, refer to the SPEC.md for detailed requirements or review the test suite for usage examples.
