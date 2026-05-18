"""Pytest configuration and fixtures for the Task Management API tests."""

import os
import tempfile
import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.main import app
from app.database import init_db


@pytest_asyncio.fixture
async def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    os.environ["DATABASE_PATH"] = db_path
    await init_db()
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)
    if "DATABASE_PATH" in os.environ:
        del os.environ["DATABASE_PATH"]


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
