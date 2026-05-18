"""Database layer for the Task Management API.

Uses SQLite for the Week 1 demo. PostgreSQL support is future work.
Implements a repository pattern for clean separation of concerns.
"""

import uuid
import json
import os
from datetime import datetime, date, timezone
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


DEFAULT_DATABASE_PATH = "tasks.db"
SORT_FIELD_MAP = {
    "created_at": "created_at",
    "due_date": "due_date",
    "priority": "priority",
    "title": "title",
}
SORT_ORDER_MAP = {
    "asc": "ASC",
    "desc": "DESC",
}
MIN_PAGE_SIZE = 1
MAX_PAGE_SIZE = 100


async def get_db_path() -> str:
    """Get database path from environment or default."""
    return os.environ.get("DATABASE_PATH", DEFAULT_DATABASE_PATH)


def _parse_tags(tags_json: str | None) -> list[str]:
    """Safely parse task tags from stored JSON."""
    if not tags_json:
        return []
    try:
        parsed = json.loads(tags_json)
    except (json.JSONDecodeError, TypeError):
        return []
    if isinstance(parsed, list) and all(isinstance(tag, str) for tag in parsed):
        return parsed
    return []


def _parse_iso_date(value: str | None) -> date | None:
    """Safely parse an ISO date value from storage."""
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _parse_iso_datetime(value: str | None) -> datetime:
    """Safely parse an ISO datetime value from storage."""
    if not value:
        return datetime.now(timezone.utc)
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return datetime.now(timezone.utc)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


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
        due_date=_parse_iso_date(row[6]),
        tags=_parse_tags(row[7]),
        created_at=_parse_iso_datetime(row[8]),
        updated_at=_parse_iso_datetime(row[9]),
    )


async def create_task(task: TaskCreate) -> TaskResponse:
    """Create a new task and return it."""
    db_path = await get_db_path()
    task_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
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
        conditions.append("EXISTS (SELECT 1 FROM json_each(tasks.tags) WHERE json_each.value = ?)")
        params.append(tag)

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

    # Validate and map sort parameters before interpolation.
    if sort_by not in SORT_FIELD_MAP:
        valid_fields = ", ".join(sorted(SORT_FIELD_MAP))
        raise ValueError(f"Invalid sort field '{sort_by}'. Must be one of: {valid_fields}")
    if sort_order not in SORT_ORDER_MAP:
        raise ValueError(f"Invalid sort order '{sort_order}'. Must be 'asc' or 'desc'")
    sort_field = SORT_FIELD_MAP[sort_by]
    sort_direction = SORT_ORDER_MAP[sort_order]

    # Clamp pagination
    per_page = max(MIN_PAGE_SIZE, min(per_page, MAX_PAGE_SIZE))
    page = max(page, 1)
    assert per_page > 0, "per_page must be positive"
    offset = (page - 1) * per_page

    async with aiosqlite.connect(db_path) as db:
        # Get total count
        count_query = f"SELECT COUNT(*) FROM tasks{where_clause}"
        cursor = await db.execute(count_query, params)
        total = (await cursor.fetchone())[0]

        # Get paginated results
        query = f"""SELECT id, title, description, status, priority, assignee, due_date, tags, created_at, updated_at
                    FROM tasks{where_clause}
                    ORDER BY {sort_field} {sort_direction}
                    LIMIT ? OFFSET ?"""
        cursor = await db.execute(query, params + [per_page, offset])
        rows = await cursor.fetchall()

    tasks = [_row_to_task(row) for row in rows]
    return tasks, total


async def update_task(task_id: str, task: TaskUpdate) -> Optional[TaskResponse]:
    """Full update of a task."""
    db_path = await get_db_path()
    now = datetime.now(timezone.utc).isoformat()
    tags_json = json.dumps(task.tags if task.tags else [])
    due_date_str = task.due_date.isoformat() if task.due_date else None

    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
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
        if cursor.rowcount == 0:
            return None
        await db.commit()

    return await get_task(task_id)


async def update_task_status(task_id: str, status_update: StatusUpdate) -> Optional[TaskResponse]:
    """Update only the status of a task."""
    db_path = await get_db_path()
    now = datetime.now(timezone.utc).isoformat()

    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "UPDATE tasks SET status=?, updated_at=? WHERE id=?",
            (status_update.status.value, now, task_id),
        )
        if cursor.rowcount == 0:
            return None
        await db.commit()

    return await get_task(task_id)


async def delete_task(task_id: str) -> bool:
    """Delete a task. Returns True if deleted, False if not found."""
    db_path = await get_db_path()
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        if cursor.rowcount == 0:
            return False
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
