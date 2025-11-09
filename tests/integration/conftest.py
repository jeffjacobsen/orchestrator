"""
Integration test fixtures and configuration.
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from typing import AsyncGenerator

from orchestrator import Orchestrator
from orchestrator.core.types import AgentRole


@pytest.fixture
def temp_working_dir() -> Path:
    """Create a temporary working directory for tests."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_claude_response():
    """Mock response from Claude API."""
    response = MagicMock()
    response.id = "msg_test123"
    response.type = "message"
    response.role = "assistant"

    # Mock text content
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "Task completed successfully."
    response.content = [text_block]

    response.model = "claude-sonnet-4-5-20250929"
    response.stop_reason = "end_turn"

    # Mock usage
    usage = MagicMock()
    usage.input_tokens = 100
    usage.output_tokens = 50
    response.usage = usage

    return response


@pytest.fixture
def mock_claude_client(mock_claude_response):
    """Mock Claude SDK client for controlled testing."""
    client = MagicMock()
    client.messages.create = AsyncMock(return_value=mock_claude_response)
    return client


@pytest.fixture
async def test_orchestrator(temp_working_dir) -> AsyncGenerator[Orchestrator, None]:
    """
    Provides a test orchestrator instance without mocking.

    Note: This will make real API calls. Use mock_orchestrator for isolated tests.
    """
    orchestrator = Orchestrator(
        enable_monitoring=False,  # Disable for simpler testing
        working_directory=str(temp_working_dir)
    )

    await orchestrator.start()
    yield orchestrator
    await orchestrator.stop()
