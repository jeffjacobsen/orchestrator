"""
Comprehensive tests for task API endpoints, specifically testing working directory validation.

This test suite verifies that:
1. Tasks can be created with valid working directories
2. Invalid directory paths are rejected with appropriate error messages
3. Directory permission checks work correctly
4. Edge cases like file paths, non-existent directories, and relative paths are handled
"""

import os
import tempfile
import pytest
from httpx import AsyncClient
from fastapi import status

# These imports assume the backend app is properly structured
# Adjust imports based on actual project structure
try:
    from app.main import app
    from app.core.database import get_db
    from app.models.task import Task, TaskStatus
except ImportError:
    pytest.skip("Backend dependencies not available", allow_module_level=True)


@pytest.fixture
async def client():
    """Create an async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def valid_temp_directory():
    """Create a valid temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def temp_file_path():
    """Create a temporary file (not a directory) for testing."""
    with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
        file_path = tmpfile.name
    yield file_path
    # Cleanup
    if os.path.exists(file_path):
        os.unlink(file_path)


@pytest.fixture
def api_key_headers():
    """Return headers with API key for authenticated requests."""
    # Adjust based on your actual API key configuration
    return {
        "X-API-Key": os.getenv("API_KEY", "test-api-key")
    }


class TestTaskCreationWithValidDirectory:
    """Test suite for task creation with valid working directories."""

    @pytest.mark.asyncio
    async def test_create_task_with_valid_absolute_directory(
        self, client, valid_temp_directory, api_key_headers
    ):
        """Test creating a task with a valid absolute directory path."""
        task_data = {
            "description": "Test task with valid directory",
            "task_type": "feature_implementation",
            "working_directory": valid_temp_directory,
            "include_analyst": True,
        }

        response = await client.post(
            "/api/v1/tasks",
            json=task_data,
            headers=api_key_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["description"] == task_data["description"]
        assert data["task_type"] == task_data["task_type"]
        assert data["working_directory"] == valid_temp_directory
        assert data["status"] == "pending"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_task_with_relative_directory_that_exists(
        self, client, api_key_headers
    ):
        """Test creating a task with a relative directory path (current directory)."""
        task_data = {
            "description": "Test task with relative directory",
            "task_type": "bug_fix",
            "working_directory": ".",  # Current directory
            "include_analyst": False,
        }

        response = await client.post(
            "/api/v1/tasks",
            json=task_data,
            headers=api_key_headers
        )

        # Should succeed as '.' exists and is converted to absolute path
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_task_without_working_directory(
        self, client, api_key_headers
    ):
        """Test creating a task without specifying a working directory (should use default)."""
        task_data = {
            "description": "Test task without working directory",
            "task_type": "code_review",
            "include_analyst": True,
        }

        response = await client.post(
            "/api/v1/tasks",
            json=task_data,
            headers=api_key_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["working_directory"] is None  # Should be None if not provided

    @pytest.mark.asyncio
    async def test_create_task_with_nested_valid_directory(
        self, client, valid_temp_directory, api_key_headers
    ):
        """Test creating a task with a nested directory structure."""
        # Create nested directory
        nested_dir = os.path.join(valid_temp_directory, "level1", "level2", "level3")
        os.makedirs(nested_dir, exist_ok=True)

        task_data = {
            "description": "Test task with nested directory",
            "task_type": "documentation",
            "working_directory": nested_dir,
            "include_analyst": False,
        }

        response = await client.post(
            "/api/v1/tasks",
            json=task_data,
            headers=api_key_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["working_directory"] == nested_dir


class TestTaskCreationWithInvalidDirectory:
    """Test suite for task creation with invalid working directories."""

    @pytest.mark.asyncio
    async def test_create_task_with_nonexistent_directory(
        self, client, api_key_headers
    ):
        """Test that creating a task with non-existent directory fails."""
        nonexistent_path = "/path/that/definitely/does/not/exist/12345"

        task_data = {
            "description": "Test task with non-existent directory",
            "task_type": "feature_implementation",
            "working_directory": nonexistent_path,
            "include_analyst": True,
        }

        response = await client.post(
            "/api/v1/tasks",
            json=task_data,
            headers=api_key_headers
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "detail" in data
        assert "does not exist" in data["detail"].lower()
        assert nonexistent_path in data["detail"]

    @pytest.mark.asyncio
    async def test_create_task_with_file_path_instead_of_directory(
        self, client, temp_file_path, api_key_headers
    ):
        """Test that creating a task with a file path (not directory) fails."""
        task_data = {
            "description": "Test task with file path",
            "task_type": "bug_fix",
            "working_directory": temp_file_path,
            "include_analyst": False,
        }

        response = await client.post(
            "/api/v1/tasks",
            json=task_data,
            headers=api_key_headers
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "detail" in data
        assert "not a directory" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_task_with_empty_directory_string(
        self, client, api_key_headers
    ):
        """Test that creating a task with empty directory string is handled."""
        task_data = {
            "description": "Test task with empty directory",
            "task_type": "code_review",
            "working_directory": "",  # Empty string
            "include_analyst": True,
        }

        response = await client.post(
            "/api/v1/tasks",
            json=task_data,
            headers=api_key_headers
        )

        # Empty string should be treated as None/not provided or fail validation
        # Adjust assertion based on actual implementation behavior
        assert response.status_code in [
            status.HTTP_201_CREATED,  # If treated as None
            status.HTTP_400_BAD_REQUEST,  # If validation fails
            status.HTTP_422_UNPROCESSABLE_ENTITY,  # If schema validation fails
        ]


class TestTaskCreationDirectoryPermissions:
    """Test suite for directory permission validation."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(os.name == "nt", reason="Permission tests not reliable on Windows")
    async def test_create_task_with_unreadable_directory(
        self, client, valid_temp_directory, api_key_headers
    ):
        """Test that creating a task with unreadable directory fails."""
        # Create a directory with no read permissions
        unreadable_dir = os.path.join(valid_temp_directory, "unreadable")
        os.makedirs(unreadable_dir, exist_ok=True)

        try:
            # Remove read and execute permissions
            os.chmod(unreadable_dir, 0o000)

            task_data = {
                "description": "Test task with unreadable directory",
                "task_type": "feature_implementation",
                "working_directory": unreadable_dir,
                "include_analyst": True,
            }

            response = await client.post(
                "/api/v1/tasks",
                json=task_data,
                headers=api_key_headers
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            data = response.json()
            assert "detail" in data
            assert "not accessible" in data["detail"].lower() or "permission" in data["detail"].lower()

        finally:
            # Restore permissions for cleanup
            try:
                os.chmod(unreadable_dir, 0o755)
            except:
                pass

    @pytest.mark.asyncio
    async def test_create_task_with_readable_directory(
        self, client, valid_temp_directory, api_key_headers
    ):
        """Test that creating a task with proper read/execute permissions succeeds."""
        readable_dir = os.path.join(valid_temp_directory, "readable")
        os.makedirs(readable_dir, exist_ok=True)
        os.chmod(readable_dir, 0o755)  # rwxr-xr-x

        task_data = {
            "description": "Test task with readable directory",
            "task_type": "documentation",
            "working_directory": readable_dir,
            "include_analyst": False,
        }

        response = await client.post(
            "/api/v1/tasks",
            json=task_data,
            headers=api_key_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["working_directory"] == readable_dir


class TestTaskCreationEdgeCases:
    """Test suite for edge cases in working directory validation."""

    @pytest.mark.asyncio
    async def test_create_task_with_special_characters_in_path(
        self, client, valid_temp_directory, api_key_headers
    ):
        """Test creating a task with special characters in directory path."""
        special_dir = os.path.join(valid_temp_directory, "test dir with spaces")
        os.makedirs(special_dir, exist_ok=True)

        task_data = {
            "description": "Test task with special characters in path",
            "task_type": "bug_fix",
            "working_directory": special_dir,
            "include_analyst": True,
        }

        response = await client.post(
            "/api/v1/tasks",
            json=task_data,
            headers=api_key_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["working_directory"] == special_dir

    @pytest.mark.asyncio
    async def test_create_task_with_symlink_to_valid_directory(
        self, client, valid_temp_directory, api_key_headers
    ):
        """Test creating a task with a symlink to a valid directory."""
        target_dir = os.path.join(valid_temp_directory, "target")
        symlink_dir = os.path.join(valid_temp_directory, "symlink")

        os.makedirs(target_dir, exist_ok=True)

        # Skip on Windows if symlinks aren't supported
        try:
            os.symlink(target_dir, symlink_dir)
        except (OSError, NotImplementedError):
            pytest.skip("Symlinks not supported on this platform")

        task_data = {
            "description": "Test task with symlink directory",
            "task_type": "code_review",
            "working_directory": symlink_dir,
            "include_analyst": False,
        }

        response = await client.post(
            "/api/v1/tasks",
            json=task_data,
            headers=api_key_headers
        )

        # Should succeed as symlink resolves to valid directory
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.asyncio
    async def test_create_task_with_unicode_path(
        self, client, valid_temp_directory, api_key_headers
    ):
        """Test creating a task with Unicode characters in path."""
        unicode_dir = os.path.join(valid_temp_directory, "test_\u4e2d\u6587_\u65e5\u672c\u8a9e")
        os.makedirs(unicode_dir, exist_ok=True)

        task_data = {
            "description": "Test task with Unicode path",
            "task_type": "feature_implementation",
            "working_directory": unicode_dir,
            "include_analyst": True,
        }

        response = await client.post(
            "/api/v1/tasks",
            json=task_data,
            headers=api_key_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["working_directory"] == unicode_dir

    @pytest.mark.asyncio
    async def test_create_multiple_tasks_with_same_directory(
        self, client, valid_temp_directory, api_key_headers
    ):
        """Test creating multiple tasks with the same working directory."""
        task_data_1 = {
            "description": "First task in shared directory",
            "task_type": "feature_implementation",
            "working_directory": valid_temp_directory,
            "include_analyst": True,
        }

        task_data_2 = {
            "description": "Second task in shared directory",
            "task_type": "bug_fix",
            "working_directory": valid_temp_directory,
            "include_analyst": False,
        }

        response_1 = await client.post(
            "/api/v1/tasks",
            json=task_data_1,
            headers=api_key_headers
        )
        response_2 = await client.post(
            "/api/v1/tasks",
            json=task_data_2,
            headers=api_key_headers
        )

        assert response_1.status_code == status.HTTP_201_CREATED
        assert response_2.status_code == status.HTTP_201_CREATED

        data_1 = response_1.json()
        data_2 = response_2.json()

        # Both should succeed with same directory
        assert data_1["working_directory"] == valid_temp_directory
        assert data_2["working_directory"] == valid_temp_directory
        # But different task IDs
        assert data_1["id"] != data_2["id"]


class TestTaskComplexityDetection:
    """Test suite for task complexity detection based on description."""

    @pytest.mark.asyncio
    async def test_simple_task_complexity(
        self, client, valid_temp_directory, api_key_headers
    ):
        """Test that short descriptions result in simple complexity."""
        task_data = {
            "description": "Fix bug",  # Short description
            "task_type": "bug_fix",
            "working_directory": valid_temp_directory,
            "include_analyst": False,
        }

        response = await client.post(
            "/api/v1/tasks",
            json=task_data,
            headers=api_key_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["complexity"] == "simple"

    @pytest.mark.asyncio
    async def test_complex_task_complexity(
        self, client, valid_temp_directory, api_key_headers
    ):
        """Test that long descriptions result in complex complexity."""
        long_description = " ".join(["word"] * 60)  # More than 50 words

        task_data = {
            "description": long_description,
            "task_type": "feature_implementation",
            "working_directory": valid_temp_directory,
            "include_analyst": True,
        }

        response = await client.post(
            "/api/v1/tasks",
            json=task_data,
            headers=api_key_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["complexity"] == "complex"


# Integration test combining multiple scenarios
class TestTaskCreationIntegration:
    """Integration tests for complete task creation workflow."""

    @pytest.mark.asyncio
    async def test_complete_valid_task_creation_workflow(
        self, client, valid_temp_directory, api_key_headers
    ):
        """Test complete workflow: create task, verify fields, check status."""
        # Create a project structure
        src_dir = os.path.join(valid_temp_directory, "src")
        tests_dir = os.path.join(valid_temp_directory, "tests")
        os.makedirs(src_dir, exist_ok=True)
        os.makedirs(tests_dir, exist_ok=True)

        task_data = {
            "description": "Implement user authentication with OAuth2 support",
            "task_type": "feature_implementation",
            "working_directory": valid_temp_directory,
            "include_analyst": True,
            "task_metadata": {
                "priority": "high",
                "assigned_team": "backend"
            }
        }

        # Create task
        response = await client.post(
            "/api/v1/tasks",
            json=task_data,
            headers=api_key_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        # Verify all fields
        assert data["description"] == task_data["description"]
        assert data["task_type"] == task_data["task_type"]
        assert data["working_directory"] == valid_temp_directory
        assert data["include_analyst"] is True
        assert data["status"] == "pending"
        assert data["complexity"] in ["simple", "complex"]
        assert "id" in data
        assert "created_at" in data

        task_id = data["id"]

        # Verify we can retrieve the task
        get_response = await client.get(
            f"/api/v1/tasks/{task_id}",
            headers=api_key_headers
        )

        assert get_response.status_code == status.HTTP_200_OK
        retrieved_data = get_response.json()
        assert retrieved_data["id"] == task_id
        assert retrieved_data["working_directory"] == valid_temp_directory


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
