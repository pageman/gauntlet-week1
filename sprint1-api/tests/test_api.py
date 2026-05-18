"""Comprehensive test suite for the Task Management API.

Tests cover all 7 endpoints + health check with:
- Happy path (valid inputs)
- Validation errors (invalid inputs)
- Edge cases (not found, malformed JSON, boundary values)
- Filtering, pagination, and sorting
"""

import pytest
import aiosqlite
from datetime import datetime, timezone
from httpx import AsyncClient

from app import main as app_main


# ============================================================
# HEALTH CHECK TESTS
# ============================================================


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Health endpoint returns 200 with status info."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert datetime.fromisoformat(data["timestamp"]).tzinfo is not None
    assert data["version"] == "1.0.0"


# ============================================================
# POST /api/v1/tasks — CREATE TASK
# ============================================================


@pytest.mark.asyncio
async def test_create_task_success(client: AsyncClient, sample_task):
    """Creating a task with valid data returns 201."""
    response = await client.post("/api/v1/tasks", json=sample_task)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == sample_task["title"]
    assert data["description"] == sample_task["description"]
    assert data["status"] == "pending"
    assert data["priority"] == "high"
    assert data["assignee"] == "alice"
    assert data["due_date"] == "2026-06-01"
    assert data["tags"] == ["backend", "security"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert datetime.fromisoformat(data["created_at"]).tzinfo is not None
    assert datetime.fromisoformat(data["updated_at"]).tzinfo is not None


@pytest.mark.asyncio
async def test_create_task_minimal(client: AsyncClient):
    """Creating a task with only title uses defaults."""
    response = await client.post("/api/v1/tasks", json={"title": "Minimal task"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Minimal task"
    assert data["status"] == "pending"
    assert data["priority"] == "medium"
    assert data["assignee"] is None
    assert data["description"] is None


@pytest.mark.asyncio
async def test_create_task_missing_title(client: AsyncClient):
    """Creating a task without title returns 422."""
    response = await client.post("/api/v1/tasks", json={"description": "No title"})
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert "errors" in data


@pytest.mark.asyncio
async def test_create_task_empty_title(client: AsyncClient):
    """Creating a task with empty title returns 422."""
    response = await client.post("/api/v1/tasks", json={"title": ""})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_task_title_too_long(client: AsyncClient):
    """Creating a task with title > 200 chars returns 422."""
    response = await client.post("/api/v1/tasks", json={"title": "x" * 201})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_task_invalid_status(client: AsyncClient):
    """Creating a task with invalid status returns 422."""
    response = await client.post("/api/v1/tasks", json={"title": "Test", "status": "invalid"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_task_invalid_priority(client: AsyncClient):
    """Creating a task with invalid priority returns 422."""
    response = await client.post("/api/v1/tasks", json={"title": "Test", "priority": "urgent"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_task_too_many_tags(client: AsyncClient):
    """Creating a task with > 10 tags returns 422."""
    tags = [f"tag{i}" for i in range(11)]
    response = await client.post("/api/v1/tasks", json={"title": "Test", "tags": tags})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_task_tag_too_long(client: AsyncClient):
    """Creating a task with a tag > 50 chars returns 422."""
    response = await client.post("/api/v1/tasks", json={"title": "Test", "tags": ["x" * 51]})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_task_malformed_json(client: AsyncClient):
    """Sending malformed JSON returns 422."""
    response = await client.post(
        "/api/v1/tasks",
        content=b"not json at all",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_task_invalid_date(client: AsyncClient):
    """Creating a task with invalid date format returns 422."""
    response = await client.post(
        "/api/v1/tasks", json={"title": "Test", "due_date": "not-a-date"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_write_auth_is_required_when_token_configured(client: AsyncClient, sample_task, monkeypatch):
    """Mutating endpoints require a token only when API_AUTH_TOKEN is configured."""
    monkeypatch.setenv("API_AUTH_TOKEN", "test-secret")

    missing = await client.post("/api/v1/tasks", json=sample_task)
    assert missing.status_code == 401

    valid = await client.post("/api/v1/tasks", json=sample_task, headers={"X-API-Key": "test-secret"})
    assert valid.status_code == 201


@pytest.mark.asyncio
async def test_write_auth_blocks_unconfigured_production_writes(client: AsyncClient, sample_task, monkeypatch):
    """Production mode fails closed if write auth is not configured."""
    monkeypatch.delenv("API_AUTH_TOKEN", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "production")

    response = await client.post("/api/v1/tasks", json=sample_task)

    assert response.status_code == 503
    assert "write authentication is not configured" in response.json()["detail"]


# ============================================================
# GET /api/v1/tasks — LIST TASKS
# ============================================================


@pytest.mark.asyncio
async def test_list_tasks_empty(client: AsyncClient):
    """Listing tasks when none exist returns empty list."""
    response = await client.get("/api/v1/tasks")
    assert response.status_code == 200
    data = response.json()
    assert data["tasks"] == []
    assert data["total"] == 0
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_list_tasks_with_data(client: AsyncClient, sample_task):
    """Listing tasks returns created tasks."""
    await client.post("/api/v1/tasks", json=sample_task)
    await client.post("/api/v1/tasks", json={"title": "Second task"})

    response = await client.get("/api/v1/tasks")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["tasks"]) == 2


@pytest.mark.asyncio
async def test_list_tasks_filter_by_status(client: AsyncClient):
    """Filtering by status returns only matching tasks."""
    await client.post("/api/v1/tasks", json={"title": "Pending", "status": "pending"})
    await client.post("/api/v1/tasks", json={"title": "Done", "status": "completed"})

    response = await client.get("/api/v1/tasks", params={"status": "pending"})
    data = response.json()
    assert data["total"] == 1
    assert data["tasks"][0]["title"] == "Pending"


@pytest.mark.asyncio
async def test_list_tasks_filter_by_priority(client: AsyncClient):
    """Filtering by priority returns only matching tasks."""
    await client.post("/api/v1/tasks", json={"title": "Low", "priority": "low"})
    await client.post("/api/v1/tasks", json={"title": "High", "priority": "high"})

    response = await client.get("/api/v1/tasks", params={"priority": "high"})
    data = response.json()
    assert data["total"] == 1
    assert data["tasks"][0]["title"] == "High"


@pytest.mark.asyncio
async def test_list_tasks_filter_by_assignee(client: AsyncClient):
    """Filtering by assignee returns only matching tasks."""
    await client.post("/api/v1/tasks", json={"title": "Alice's", "assignee": "alice"})
    await client.post("/api/v1/tasks", json={"title": "Bob's", "assignee": "bob"})

    response = await client.get("/api/v1/tasks", params={"assignee": "alice"})
    data = response.json()
    assert data["total"] == 1
    assert data["tasks"][0]["assignee"] == "alice"


@pytest.mark.asyncio
async def test_list_tasks_pagination(client: AsyncClient):
    """Pagination works correctly."""
    for i in range(5):
        await client.post("/api/v1/tasks", json={"title": f"Task {i}"})

    response = await client.get("/api/v1/tasks", params={"page": 1, "per_page": 2})
    data = response.json()
    assert len(data["tasks"]) == 2
    assert data["total"] == 5
    assert data["total_pages"] == 3
    assert data["page"] == 1

    response = await client.get("/api/v1/tasks", params={"page": 3, "per_page": 2})
    data = response.json()
    assert len(data["tasks"]) == 1


@pytest.mark.asyncio
async def test_list_tasks_sort_order(client: AsyncClient):
    """Sorting works correctly."""
    await client.post("/api/v1/tasks", json={"title": "Alpha"})
    await client.post("/api/v1/tasks", json={"title": "Beta"})

    response = await client.get("/api/v1/tasks", params={"sort_by": "title", "sort_order": "asc"})
    data = response.json()
    assert data["tasks"][0]["title"] == "Alpha"
    assert data["tasks"][1]["title"] == "Beta"


@pytest.mark.asyncio
async def test_list_tasks_rejects_invalid_sort_field(client: AsyncClient):
    """Invalid sort fields return 422 instead of silently falling back."""
    response = await client.get("/api/v1/tasks", params={"sort_by": "title;DROP TABLE tasks"})

    assert response.status_code == 422
    assert "Invalid sort field" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_tasks_rejects_invalid_sort_order(client: AsyncClient):
    """Invalid sort order returns 422 before SQL construction."""
    response = await client.get("/api/v1/tasks", params={"sort_order": "desc;DROP TABLE tasks"})

    assert response.status_code == 422
    assert "Invalid sort order" in response.json()["detail"]


# ============================================================
# GET /api/v1/tasks/{task_id} — GET SINGLE TASK
# ============================================================


@pytest.mark.asyncio
async def test_get_task_success(client: AsyncClient, created_task):
    """Getting an existing task returns it."""
    task_id = created_task["id"]
    response = await client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == created_task["title"]


@pytest.mark.asyncio
async def test_get_task_not_found(client: AsyncClient):
    """Getting a non-existent task returns 404."""
    response = await client.get("/api/v1/tasks/nonexistent-id-12345")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


# ============================================================
# PUT /api/v1/tasks/{task_id} — UPDATE TASK
# ============================================================


@pytest.mark.asyncio
async def test_update_task_success(client: AsyncClient, created_task):
    """Updating a task with valid data returns updated task."""
    task_id = created_task["id"]
    update_data = {
        "title": "Updated title",
        "description": "Updated description",
        "status": "in_progress",
        "priority": "critical",
        "assignee": "bob",
        "due_date": "2026-07-01",
        "tags": ["updated"],
    }
    response = await client.put(f"/api/v1/tasks/{task_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated title"
    assert data["status"] == "in_progress"
    assert data["priority"] == "critical"
    assert data["assignee"] == "bob"


@pytest.mark.asyncio
async def test_update_task_not_found(client: AsyncClient):
    """Updating a non-existent task returns 404."""
    update_data = {
        "title": "Test",
        "status": "pending",
        "priority": "low",
    }
    response = await client.put("/api/v1/tasks/nonexistent-id", json=update_data)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_task_invalid_data(client: AsyncClient, created_task):
    """Updating with invalid data returns 422."""
    task_id = created_task["id"]
    response = await client.put(f"/api/v1/tasks/{task_id}", json={"title": ""})
    assert response.status_code == 422


# ============================================================
# PATCH /api/v1/tasks/{task_id}/status — UPDATE STATUS
# ============================================================


@pytest.mark.asyncio
async def test_patch_status_success(client: AsyncClient, created_task):
    """Patching status with valid value updates the task."""
    task_id = created_task["id"]
    response = await client.patch(
        f"/api/v1/tasks/{task_id}/status", json={"status": "completed"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["id"] == task_id


@pytest.mark.asyncio
async def test_patch_status_not_found(client: AsyncClient):
    """Patching status of non-existent task returns 404."""
    response = await client.patch(
        "/api/v1/tasks/nonexistent-id/status", json={"status": "completed"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_patch_status_invalid(client: AsyncClient, created_task):
    """Patching with invalid status returns 422."""
    task_id = created_task["id"]
    response = await client.patch(
        f"/api/v1/tasks/{task_id}/status", json={"status": "invalid_status"}
    )
    assert response.status_code == 422


# ============================================================
# DELETE /api/v1/tasks/{task_id} — DELETE TASK
# ============================================================


@pytest.mark.asyncio
async def test_delete_task_success(client: AsyncClient, created_task):
    """Deleting an existing task returns 204."""
    task_id = created_task["id"]
    response = await client.delete(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 204

    # Verify it's gone
    response = await client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_task_not_found(client: AsyncClient):
    """Deleting a non-existent task returns 404."""
    response = await client.delete("/api/v1/tasks/nonexistent-id")
    assert response.status_code == 404


# ============================================================
# GET /api/v1/tasks/stats — TASK STATISTICS
# ============================================================


@pytest.mark.asyncio
async def test_stats_empty(client: AsyncClient):
    """Stats with no tasks returns zeros."""
    response = await client.get("/api/v1/tasks/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_tasks"] == 0
    assert data["by_status"] == {}
    assert data["by_priority"] == {}


@pytest.mark.asyncio
async def test_stats_with_data(client: AsyncClient):
    """Stats correctly counts tasks by status and priority."""
    await client.post("/api/v1/tasks", json={"title": "T1", "status": "pending", "priority": "high"})
    await client.post("/api/v1/tasks", json={"title": "T2", "status": "pending", "priority": "low"})
    await client.post("/api/v1/tasks", json={"title": "T3", "status": "completed", "priority": "high"})

    response = await client.get("/api/v1/tasks/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_tasks"] == 3
    assert data["by_status"]["pending"] == 2
    assert data["by_status"]["completed"] == 1
    assert data["by_priority"]["high"] == 2
    assert data["by_priority"]["low"] == 1


# ============================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================


@pytest.mark.asyncio
async def test_malformed_json_all_endpoints(client: AsyncClient):
    """All write endpoints handle malformed JSON gracefully."""
    bad_json = b"{invalid json content"
    headers = {"Content-Type": "application/json"}

    # POST
    response = await client.post("/api/v1/tasks", content=bad_json, headers=headers)
    assert response.status_code == 422

    # PUT (need a valid task first)
    task = await client.post("/api/v1/tasks", json={"title": "Test"})
    task_id = task.json()["id"]
    response = await client.put(f"/api/v1/tasks/{task_id}", content=bad_json, headers=headers)
    assert response.status_code == 422

    # PATCH
    response = await client.patch(f"/api/v1/tasks/{task_id}/status", content=bad_json, headers=headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_concurrent_task_creation(client: AsyncClient):
    """Multiple concurrent task creations work correctly."""
    import asyncio
    
    tasks_data = [{"title": f"Concurrent task {i}"} for i in range(10)]
    responses = await asyncio.gather(*[
        client.post("/api/v1/tasks", json=task_data)
        for task_data in tasks_data
    ])
    
    assert all(r.status_code == 201 for r in responses)
    
    # Verify all were created
    list_response = await client.get("/api/v1/tasks")
    assert list_response.json()["total"] == 10


@pytest.mark.asyncio
async def test_rate_limit_returns_429(client: AsyncClient, monkeypatch):
    """The lightweight limiter returns 429 after the configured threshold."""
    app_main._rate_limit_hits.clear()
    monkeypatch.setattr(app_main, "RATE_LIMIT_REQUESTS", 2)
    monkeypatch.setattr(app_main, "RATE_LIMIT_WINDOW_SECONDS", 60)

    assert (await client.get("/api/v1/tasks")).status_code == 200
    assert (await client.get("/api/v1/tasks")).status_code == 200
    response = await client.get("/api/v1/tasks")

    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["detail"]
    app_main._rate_limit_hits.clear()


@pytest.mark.asyncio
async def test_filter_by_tag(client: AsyncClient):
    """Filtering by tag works correctly."""
    await client.post("/api/v1/tasks", json={"title": "T1", "tags": ["urgent", "backend"]})
    await client.post("/api/v1/tasks", json={"title": "T2", "tags": ["frontend"]})
    await client.post("/api/v1/tasks", json={"title": "T3", "tags": ["urgent", "frontend"]})

    response = await client.get("/api/v1/tasks", params={"tag": "urgent"})
    data = response.json()
    assert data["total"] == 2
    assert all("urgent" in task["tags"] for task in data["tasks"])


@pytest.mark.asyncio
async def test_filter_by_tag_requires_exact_match(client: AsyncClient):
    """Filtering by tag does not match substrings inside other tags."""
    await client.post("/api/v1/tasks", json={"title": "T1", "tags": ["urgent"]})
    await client.post("/api/v1/tasks", json={"title": "T2", "tags": ["ur"]})
    await client.post("/api/v1/tasks", json={"title": "T3", "tags": ["super"]})

    partial_response = await client.get("/api/v1/tasks", params={"tag": "urge"})
    partial_data = partial_response.json()
    assert partial_data["total"] == 0
    assert partial_data["tasks"] == []

    exact_response = await client.get("/api/v1/tasks", params={"tag": "ur"})
    exact_data = exact_response.json()
    assert exact_data["total"] == 1
    assert exact_data["tasks"][0]["title"] == "T2"
    assert exact_data["tasks"][0]["tags"] == ["ur"]


@pytest.mark.asyncio
async def test_malformed_stored_tags_and_timestamps_do_not_crash(client: AsyncClient, temp_db):
    """Corrupt persisted optional fields are sanitized during response mapping."""
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(temp_db) as db:
        await db.execute(
            """INSERT INTO tasks
               (id, title, description, status, priority, assignee, due_date, tags, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "corrupt-row",
                "Corrupt optional fields",
                None,
                "pending",
                "medium",
                None,
                "not-a-date",
                "{not-json",
                "not-a-datetime",
                now,
            ),
        )
        await db.commit()

    response = await client.get("/api/v1/tasks/corrupt-row")
    data = response.json()

    assert response.status_code == 200
    assert data["tags"] == []
    assert data["due_date"] is None
    assert datetime.fromisoformat(data["created_at"]).tzinfo is not None


@pytest.mark.asyncio
async def test_pagination_boundary_conditions(client: AsyncClient):
    """Pagination handles boundary conditions correctly."""
    # Create 25 tasks
    for i in range(25):
        await client.post("/api/v1/tasks", json={"title": f"Task {i}"})

    # Test page beyond total
    response = await client.get("/api/v1/tasks", params={"page": 100, "per_page": 10})
    data = response.json()
    assert data["tasks"] == []
    assert data["total"] == 25

    # Test per_page = 1
    response = await client.get("/api/v1/tasks", params={"page": 1, "per_page": 1})
    data = response.json()
    assert len(data["tasks"]) == 1
    assert data["total_pages"] == 25
