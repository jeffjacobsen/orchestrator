"""
WebSocket endpoint for real-time updates.

This module provides WebSocket connections for real-time updates of:
- Agent status changes
- Task progress updates
- New agents/tasks created
"""

from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.models.agent import Agent
from app.models.task import Task
from app.schemas.agent import AgentResponse
from app.schemas.task import TaskResponse
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections and broadcasts updates to all clients."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Unregister a WebSocket connection."""
        self.active_connections.discard(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast_agent_update(self, agent: Agent):
        """Broadcast agent update to all connected clients."""
        agent_data = AgentResponse.model_validate(agent)
        message = {
            "type": "agent_update",
            "data": agent_data.model_dump(mode="json", by_alias=True),
        }
        await self._broadcast(message)

    async def broadcast_agent_deleted(self, agent_id: str):
        """Broadcast agent deletion to all connected clients."""
        message = {"type": "agent_deleted", "data": {"id": agent_id}}
        await self._broadcast(message)

    async def broadcast_task_update(self, task: Task):
        """Broadcast task update to all connected clients."""
        task_data = TaskResponse.model_validate(task)
        message = {"type": "task_update", "data": task_data.model_dump(mode="json", by_alias=True)}
        await self._broadcast(message)

    async def broadcast_task_deleted(self, task_id: str):
        """Broadcast task deletion to all connected clients."""
        message = {"type": "task_deleted", "data": {"id": task_id}}
        await self._broadcast(message)

    async def _broadcast(self, message: dict):
        """Send message to all connected clients."""
        if not self.active_connections:
            return

        disconnected = set()
        message_json = json.dumps(message)

        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates.

    Clients connect to this endpoint to receive real-time updates about:
    - Agent status changes (agent_update)
    - Agent deletions (agent_deleted)
    - Task status changes (task_update)
    - Task deletions (task_deleted)

    Message format:
    ```json
    {
        "type": "agent_update",
        "data": { ... agent data ... }
    }
    ```
    """
    await manager.connect(websocket)

    try:
        # Keep connection alive and handle client messages
        while True:
            # Wait for any client messages (like ping/pong)
            data = await websocket.receive_text()

            # Echo back pings for keepalive
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


def get_websocket_manager() -> ConnectionManager:
    """Get the global WebSocket connection manager."""
    return manager
