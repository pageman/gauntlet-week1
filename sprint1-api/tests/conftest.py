"""Pytest configuration and fixtures for the Task Management API tests."""

import os
import tempfile
import pytest
import pytest_asyncio
from httpx import AsyncClient

from app import main as app_main
from app.main import app
from app.database import init_db


@pytest_asyncio.fixture
async def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    old_api_token = os.environ.pop("API_AUTH_TOKEN", None)
    old_environment = os.environ.pop("ENVIRONMENT", None)
    os.environ["DATABASE_PATH"] = db_path
    app_main._rate_limit_hits.clear()
    await init_db()

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)
    if "DATABASE_PATH" in os.environ:
        del os.environ["DATABASE_PATH"]
    if old_api_token is not None:
        os.environ["API_AUTH_TOKEN"] = old_api_token
    else:
        os.environ.pop("API_AUTH_TOKEN", None)
    if old_environment is not None:
        os.environ["ENVIRONMENT"] = old_environment
    else:
        os.environ.pop("ENVIRONMENT", None)
    app_main._rate_limit_hits.clear()


@pytest_asyncio.fixture
async def client(temp_db):
    """Create an async HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_task():
    """Sample task data for testing."""
    return {
        "title": "Implement authentication",
        "description": "Add JWT-based authentication to the API",
        "status": "pending",
        "priority": "high",
        "assignee": "alice",
        "due_date": "2026-06-01",
        "tags": ["backend", "security"],
    }


@pytest_asyncio.fixture
async def created_task(client, sample_task):
    """Create and return a task for testing."""
    response = await client.post("/api/v1/tasks", json=sample_task)
    return response.json()
