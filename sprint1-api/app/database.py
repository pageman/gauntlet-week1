"""Database layer for the Task Management API.

Uses SQLite for development and supports PostgreSQL via DATABASE_URL env var.
Implements a repository pattern for clean separation of concerns.
"""

import uuid
import json
from datetime import datetime, date
from typing import Optional

import aiosqlite

from app.models import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskStatus,
    TaskPriority,
    StatusUpdate,
)


DATABASE_PATH = "tasks.db"


async def get_db_path() -> str:
    """Get database path from environment or default."""
    import os
    return os.environ.get("DATABASE_PATH", DATABASE_PATH)


async def init_db() -> None:
    """Initialize the database schema."""
    db_path = await get_db_path()
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                priority TEXT NOT NULL DEFAULT 'medium',
                assignee TEXT,
                due_date TEXT,
                tags TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_assignee ON tasks(assignee)
        """)
        await db.commit()


def _row_to_task(row: aiosqlite.Row) -> TaskResponse:
    """Convert a database row to a TaskResponse."""
    return TaskResponse(
        id=row[0],
        title=row[1],
        description=row[2],
        status=TaskStatus(row[3]),
        priority=TaskPriority(row[4]),
        assignee=row[5],
        due_date=date.fromisoformat(row[6]) if row[6] else None,
        tags=json.loads(row[7]) if row[7] else [],
        created_at=datetime.fromisoformat(row[8]),
        updated_at=datetime.fromisoformat(row[9]),
    )


async def create_task(task: TaskCreate) -> TaskResponse:
    """Create a new task and return it."""
    db_path = await get_db_path()
    task_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    tags_json = json.dumps(task.tags if task.tags else [])
    due_date_str = task.due_date.isoformat() if task.due_date else None

    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """INSERT INTO tasks (id, title, description, status, priority, assignee, due_date, tags, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                task_id,
                task.title,
                task.description,
                task.status.value,
                task.priority.value,
                task.assignee,
                due_date_str,
                tags_json,
                now,
                now,
            ),
        )
        await db.commit()

    return TaskResponse(
        id=task_id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        assignee=task.assignee,
        due_date=task.due_date,
        tags=task.tags if task.tags else [],
        created_at=datetime.fromisoformat(now),
        updated_at=datetime.fromisoformat(now),
    )


async def get_task(task_id: str) -> Optional[TaskResponse]:
    """Get a single task by ID."""
    db_path = await get_db_path()
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "SELECT id, title, description, status, priority, assignee, due_date, tags, created_at, updated_at FROM tasks WHERE id = ?",
            (task_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return _row_to_task(row)


async def list_tasks(
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    assignee: Optional[str] = None,
    tag: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[TaskResponse], int]:
    """List tasks with filtering, sorting, and pagination."""
    db_path = await get_db_path()

    # Build query with filters
    conditions = []
    params = []

    if status:
        conditions.append("status = ?")
        params.append(status.value)
    if priority:
        conditions.append("priority = ?")
        params.append(priority.value)
    if assignee:
        conditions.append("assignee = ?")
        params.append(assignee)
    if tag:
        conditions.append("tags LIKE ?")
        params.append(f'%"{tag}"%')

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

    # Validate sort parameters
    valid_sort_fields = {"created_at", "due_date", "priority", "title"}
    if sort_by not in valid_sort_fields:
        sort_by = "created_at"
    if sort_order not in ("asc", "desc"):
        sort_order = "desc"

    # Clamp pagination
    per_page = min(max(per_page, 1), 100)
    page = max(page, 1)
    offset = (page - 1) * per_page

    async with aiosqlite.connect(db_path) as db:
        # Get total count
        count_query = f"SELECT COUNT(*) FROM tasks{where_clause}"
        cursor = await db.execute(count_query, params)
        total = (await cursor.fetchone())[0]

        # Get paginated results
        query = f"""SELECT id, title, description, status, priority, assignee, due_date, tags, created_at, updated_at
                    FROM tasks{where_clause}
                    ORDER BY {sort_by} {sort_order}
                    LIMIT ? OFFSET ?"""
        cursor = await db.execute(query, params + [per_page, offset])
        rows = await cursor.fetchall()

    tasks = [_row_to_task(row) for row in rows]
    return tasks, total


async def update_task(task_id: str, task: TaskUpdate) -> Optional[TaskResponse]:
    """Full update of a task."""
    db_path = await get_db_path()
    now = datetime.utcnow().isoformat()
    tags_json = json.dumps(task.tags if task.tags else [])
    due_date_str = task.due_date.isoformat() if task.due_date else None

    async with aiosqlite.connect(db_path) as db:
        # Check existence
        cursor = await db.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
        if await cursor.fetchone() is None:
            return None

        await db.execute(
            """UPDATE tasks SET title=?, description=?, status=?, priority=?, assignee=?, due_date=?, tags=?, updated_at=?
               WHERE id=?""",
            (
                task.title,
                task.description,
                task.status.value,
                task.priority.value,
                task.assignee,
                due_date_str,
                tags_json,
                now,
                task_id,
            ),
        )
        await db.commit()

    return await get_task(task_id)


async def update_task_status(task_id: str, status_update: StatusUpdate) -> Optional[TaskResponse]:
    """Update only the status of a task."""
    db_path = await get_db_path()
    now = datetime.utcnow().isoformat()

    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
        if await cursor.fetchone() is None:
            return None

        await db.execute(
            "UPDATE tasks SET status=?, updated_at=? WHERE id=?",
            (status_update.status.value, now, task_id),
        )
        await db.commit()

    return await get_task(task_id)


async def delete_task(task_id: str) -> bool:
    """Delete a task. Returns True if deleted, False if not found."""
    db_path = await get_db_path()
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
        if await cursor.fetchone() is None:
            return False

        await db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        await db.commit()
    return True


async def get_stats() -> dict:
    """Get task statistics."""
    db_path = await get_db_path()
    async with aiosqlite.connect(db_path) as db:
        # Total count
        cursor = await db.execute("SELECT COUNT(*) FROM tasks")
        total = (await cursor.fetchone())[0]

        # By status
        cursor = await db.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status")
        by_status = {row[0]: row[1] for row in await cursor.fetchall()}

        # By priority
        cursor = await db.execute("SELECT priority, COUNT(*) FROM tasks GROUP BY priority")
        by_priority = {row[0]: row[1] for row in await cursor.fetchall()}

    return {
        "total_tasks": total,
        "by_status": by_status,
        "by_priority": by_priority,
    }
