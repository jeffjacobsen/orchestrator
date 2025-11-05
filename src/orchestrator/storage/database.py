"""Database layer for persisting agent and task state."""

import json
import aiosqlite
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from orchestrator.storage.models import AgentRecord, TaskRecord


class Database:
    """
    SQLite database for persisting orchestrator state.

    Stores:
    - Agent lifecycle and metrics
    - Task history and results
    - Cost tracking over time
    """

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.connection: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        """Connect to database and create tables."""
        self.connection = await aiosqlite.connect(str(self.db_path))
        await self._create_tables()

    async def close(self) -> None:
        """Close database connection."""
        if self.connection:
            await self.connection.close()

    async def _create_tables(self) -> None:
        """Create database tables."""
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                model TEXT NOT NULL,
                status TEXT NOT NULL,
                total_cost REAL DEFAULT 0.0,
                total_tokens INTEGER DEFAULT 0,
                messages_sent INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                deleted_at TEXT
            )
        """)

        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                task_type TEXT NOT NULL,
                status TEXT NOT NULL,
                assigned_agents TEXT,
                total_cost REAL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                result TEXT
            )
        """)

        await self.connection.commit()

    # Agent operations

    async def save_agent(self, record: AgentRecord) -> None:
        """Save or update an agent record."""
        await self.connection.execute(
            """
            INSERT OR REPLACE INTO agents
            (agent_id, name, role, model, status, total_cost, total_tokens,
             messages_sent, created_at, completed_at, deleted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.agent_id,
                record.name,
                record.role,
                record.model,
                record.status,
                record.total_cost,
                record.total_tokens,
                record.messages_sent,
                record.created_at.isoformat(),
                record.completed_at.isoformat() if record.completed_at else None,
                record.deleted_at.isoformat() if record.deleted_at else None,
            ),
        )
        await self.connection.commit()

    async def get_agent(self, agent_id: str) -> Optional[AgentRecord]:
        """Get an agent record by ID."""
        cursor = await self.connection.execute(
            "SELECT * FROM agents WHERE agent_id = ?",
            (agent_id,),
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return self._agent_from_row(row)

    async def list_agents(
        self,
        status: Optional[str] = None,
        role: Optional[str] = None,
    ) -> List[AgentRecord]:
        """List agents with optional filtering."""
        query = "SELECT * FROM agents WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)

        if role:
            query += " AND role = ?"
            params.append(role)

        query += " ORDER BY created_at DESC"

        cursor = await self.connection.execute(query, params)
        rows = await cursor.fetchall()

        return [self._agent_from_row(row) for row in rows]

    def _agent_from_row(self, row) -> AgentRecord:
        """Convert database row to AgentRecord."""
        return AgentRecord(
            agent_id=row[0],
            name=row[1],
            role=row[2],
            model=row[3],
            status=row[4],
            total_cost=row[5],
            total_tokens=row[6],
            messages_sent=row[7],
            created_at=datetime.fromisoformat(row[8]),
            completed_at=datetime.fromisoformat(row[9]) if row[9] else None,
            deleted_at=datetime.fromisoformat(row[10]) if row[10] else None,
        )

    # Task operations

    async def save_task(self, record: TaskRecord) -> None:
        """Save or update a task record."""
        await self.connection.execute(
            """
            INSERT OR REPLACE INTO tasks
            (task_id, description, task_type, status, assigned_agents,
             total_cost, created_at, completed_at, result)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.task_id,
                record.description,
                record.task_type,
                record.status,
                record.assigned_agents,
                record.total_cost,
                record.created_at.isoformat(),
                record.completed_at.isoformat() if record.completed_at else None,
                record.result,
            ),
        )
        await self.connection.commit()

    async def get_task(self, task_id: str) -> Optional[TaskRecord]:
        """Get a task record by ID."""
        cursor = await self.connection.execute(
            "SELECT * FROM tasks WHERE task_id = ?",
            (task_id,),
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return self._task_from_row(row)

    async def list_tasks(self, status: Optional[str] = None) -> List[TaskRecord]:
        """List tasks with optional filtering."""
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY created_at DESC"

        cursor = await self.connection.execute(query, params)
        rows = await cursor.fetchall()

        return [self._task_from_row(row) for row in rows]

    def _task_from_row(self, row) -> TaskRecord:
        """Convert database row to TaskRecord."""
        return TaskRecord(
            task_id=row[0],
            description=row[1],
            task_type=row[2],
            status=row[3],
            assigned_agents=row[4],
            total_cost=row[5],
            created_at=datetime.fromisoformat(row[6]),
            completed_at=datetime.fromisoformat(row[7]) if row[7] else None,
            result=row[8],
        )

    # Analytics

    async def get_total_cost(self) -> float:
        """Get total cost across all tasks."""
        cursor = await self.connection.execute(
            "SELECT SUM(total_cost) FROM tasks"
        )
        row = await cursor.fetchone()
        return row[0] if row[0] else 0.0

    async def get_cost_by_role(self) -> dict:
        """Get cost breakdown by agent role."""
        cursor = await self.connection.execute(
            """
            SELECT role, SUM(total_cost) as total
            FROM agents
            GROUP BY role
            ORDER BY total DESC
            """
        )
        rows = await cursor.fetchall()
        return {row[0]: row[1] for row in rows}
