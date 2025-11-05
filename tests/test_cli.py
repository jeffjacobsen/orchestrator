"""Tests for the CLI interface."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from click.testing import CliRunner
from pathlib import Path
import json

from orchestrator.cli.commands import cli
from orchestrator.core.types import AgentRole


@pytest.fixture
def cli_runner():
    """Fixture providing a CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_orchestrator():
    """Fixture providing a mocked Orchestrator."""
    with patch('orchestrator.cli.commands.Orchestrator') as mock:
        # Create a mock instance
        instance = MagicMock()
        mock.return_value = instance

        # Mock async methods
        instance.start = AsyncMock()
        instance.stop = AsyncMock()
        instance.execute = AsyncMock()
        instance.create_agent = AsyncMock()
        instance.delete_agent = AsyncMock()

        # Mock sync methods with default return values
        instance.get_status.return_value = {
            'fleet': {
                'total_agents': 0,
                'active_agents': 0,
                'by_status': {},
                'by_role': {},
                'total_cost': '$0.0000',
                'total_tokens': 0
            },
            'metrics': {
                'total_agents': 0,
                'total_cost': '$0.0000',
                'total_tokens': 0,
                'total_tool_calls': 0,
                'total_messages': 0,
                'files_consumed': 0,
                'files_produced': 0,
                'net_files_created': 0,
                'total_events': 0
            },
            'tasks': {'total': 0, 'active': 0},
            'monitoring': {
                'timestamp': '2025-01-01T00:00:00',
                'metrics': {},
                'files': {
                    'consumed': [],
                    'produced': [],
                    'net_files_created': 0
                }
            }
        }
        instance.list_agents.return_value = []
        instance.list_tasks.return_value = []
        instance.get_agent_details.return_value = None
        instance.get_task_status.return_value = None

        yield instance


class TestCLIHelp:
    """Tests for CLI help commands."""

    def test_cli_help(self, cli_runner):
        """Test main CLI help."""
        result = cli_runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'Claude Multi-Agent Orchestrator CLI' in result.output
        assert 'execute' in result.output
        assert 'status' in result.output
        assert 'clean' in result.output
        assert 'cost-report' in result.output

    def test_execute_help(self, cli_runner):
        """Test execute command help."""
        result = cli_runner.invoke(cli, ['execute', '--help'])
        assert result.exit_code == 0
        assert 'Execute a high-level task' in result.output
        assert '--task-type' in result.output
        assert '--mode' in result.output

    def test_status_help(self, cli_runner):
        """Test status command help."""
        result = cli_runner.invoke(cli, ['status', '--help'])
        assert result.exit_code == 0
        assert 'Show orchestrator status' in result.output

    def test_clean_help(self, cli_runner):
        """Test clean command help."""
        result = cli_runner.invoke(cli, ['clean', '--help'])
        assert result.exit_code == 0
        assert 'Clean up old agents' in result.output
        assert '--dry-run' in result.output
        assert '--older-than' in result.output

    def test_cost_report_help(self, cli_runner):
        """Test cost-report command help."""
        result = cli_runner.invoke(cli, ['cost-report', '--help'])
        assert result.exit_code == 0
        assert 'Generate a cost analysis' in result.output
        assert '--format' in result.output
        assert '--by-agent' in result.output
        assert '--by-role' in result.output


class TestStatusCommand:
    """Tests for the status command."""

    def test_status_command(self, cli_runner, mock_orchestrator):
        """Test status command displays orchestrator status."""
        result = cli_runner.invoke(cli, ['status'])

        assert result.exit_code == 0
        assert 'Orchestrator Status' in result.output
        mock_orchestrator.get_status.assert_called_once()
        mock_orchestrator.stop.assert_called_once()


class TestListCommands:
    """Tests for list-agents and list-tasks commands."""

    def test_list_agents_empty(self, cli_runner, mock_orchestrator):
        """Test list-agents with no agents."""
        mock_orchestrator.list_agents.return_value = []

        result = cli_runner.invoke(cli, ['list-agents'])

        assert result.exit_code == 0
        assert 'No active agents' in result.output
        mock_orchestrator.list_agents.assert_called_once()

    def test_list_agents_with_agents(self, cli_runner, mock_orchestrator):
        """Test list-agents with existing agents."""
        mock_orchestrator.list_agents.return_value = [
            {
                'agent_id': 'agent-123',
                'name': 'Test Agent',
                'role': 'planner',
                'status': 'running',
                'metrics': {
                    'total_cost': '$1.2345',
                    'total_tokens': 1000,
                    'messages_sent': 5
                }
            }
        ]

        result = cli_runner.invoke(cli, ['list-agents'])

        assert result.exit_code == 0
        assert 'Active Agents' in result.output
        assert 'Test Agent' in result.output

    def test_list_agents_filter_by_role(self, cli_runner, mock_orchestrator):
        """Test list-agents filtered by role."""
        all_agents = [
            {
                'agent_id': 'agent-1',
                'name': 'Planner',
                'role': 'planner',
                'status': 'running',
                'metrics': {'total_cost': '$1.00', 'total_tokens': 100, 'messages_sent': 1}
            },
            {
                'agent_id': 'agent-2',
                'name': 'Builder',
                'role': 'builder',
                'status': 'running',
                'metrics': {'total_cost': '$2.00', 'total_tokens': 200, 'messages_sent': 2}
            }
        ]
        mock_orchestrator.list_agents.return_value = all_agents

        result = cli_runner.invoke(cli, ['list-agents', '--role', 'planner'])

        assert result.exit_code == 0
        # The command filters client-side, so list_agents is called without filter
        mock_orchestrator.list_agents.assert_called_once()

    def test_list_tasks_empty(self, cli_runner, mock_orchestrator):
        """Test list-tasks with no tasks."""
        mock_orchestrator.list_tasks.return_value = []

        result = cli_runner.invoke(cli, ['list-tasks'])

        assert result.exit_code == 0
        assert 'No tasks found' in result.output

    def test_list_tasks_with_tasks(self, cli_runner, mock_orchestrator):
        """Test list-tasks with existing tasks."""
        mock_orchestrator.list_tasks.return_value = [
            {
                'task_id': 'task-123',
                'description': 'Test task',
                'status': 'completed',
                'assigned_agents': ['agent-1'],
                'created_at': '2025-01-01T00:00:00'
            }
        ]

        result = cli_runner.invoke(cli, ['list-tasks'])

        assert result.exit_code == 0
        assert 'Tasks' in result.output


class TestDetailsCommands:
    """Tests for agent-details and task-details commands."""

    def test_agent_details_not_found(self, cli_runner, mock_orchestrator):
        """Test agent-details when agent doesn't exist."""
        mock_orchestrator.get_agent_details.return_value = None

        result = cli_runner.invoke(cli, ['agent-details', 'nonexistent-id'])

        assert result.exit_code == 0
        assert 'not found' in result.output

    def test_agent_details_found(self, cli_runner, mock_orchestrator):
        """Test agent-details when agent exists."""
        mock_orchestrator.get_agent_details.return_value = {
            'agent_id': 'agent-123',
            'name': 'Test Agent',
            'role': 'planner',
            'status': 'running'
        }

        result = cli_runner.invoke(cli, ['agent-details', 'agent-123'])

        assert result.exit_code == 0
        assert 'Agent Details' in result.output
        mock_orchestrator.get_agent_details.assert_called_once_with('agent-123')

    def test_task_details_not_found(self, cli_runner, mock_orchestrator):
        """Test task-details when task doesn't exist."""
        mock_orchestrator.get_task_status.return_value = None

        result = cli_runner.invoke(cli, ['task-details', 'nonexistent-id'])

        assert result.exit_code == 0
        assert 'not found' in result.output

    def test_task_details_found(self, cli_runner, mock_orchestrator):
        """Test task-details when task exists."""
        mock_orchestrator.get_task_status.return_value = {
            'task_id': 'task-123',
            'description': 'Test task',
            'status': 'completed'
        }

        result = cli_runner.invoke(cli, ['task-details', 'task-123'])

        assert result.exit_code == 0
        assert 'Task Details' in result.output
        mock_orchestrator.get_task_status.assert_called_once_with('task-123')


class TestCleanCommand:
    """Tests for the clean command."""

    def test_clean_dry_run_empty(self, cli_runner, mock_orchestrator):
        """Test clean command with dry-run and no agents."""
        mock_orchestrator.list_agents.return_value = []
        mock_orchestrator.list_tasks.return_value = []

        result = cli_runner.invoke(cli, ['clean', '--dry-run'])

        assert result.exit_code == 0
        assert 'DRY RUN' in result.output
        assert 'Agents to clean: 0' in result.output
        assert 'Tasks to clean: 0' in result.output
        # Should not call delete_agent in dry-run
        mock_orchestrator.delete_agent.assert_not_called()

    def test_clean_dry_run_with_agents(self, cli_runner, mock_orchestrator):
        """Test clean command dry-run with completed agents."""
        mock_orchestrator.list_agents.return_value = [
            {
                'agent_id': 'agent-1',
                'status': 'completed',
                'name': 'Test Agent'
            },
            {
                'agent_id': 'agent-2',
                'status': 'running',
                'name': 'Active Agent'
            }
        ]
        mock_orchestrator.list_tasks.return_value = []

        result = cli_runner.invoke(cli, ['clean', '--dry-run'])

        assert result.exit_code == 0
        assert 'DRY RUN' in result.output
        assert 'Agents to clean: 1' in result.output
        mock_orchestrator.delete_agent.assert_not_called()

    def test_clean_with_confirmation_no(self, cli_runner, mock_orchestrator):
        """Test clean command with user declining confirmation."""
        mock_orchestrator.list_agents.return_value = [
            {'agent_id': 'agent-1', 'status': 'completed', 'name': 'Test'}
        ]
        mock_orchestrator.list_tasks.return_value = []

        result = cli_runner.invoke(cli, ['clean'], input='n\n')

        assert result.exit_code == 0
        assert 'Cleanup cancelled' in result.output
        mock_orchestrator.delete_agent.assert_not_called()

    def test_clean_nothing_to_clean(self, cli_runner, mock_orchestrator):
        """Test clean command when nothing needs cleaning."""
        mock_orchestrator.list_agents.return_value = [
            {'agent_id': 'agent-1', 'status': 'running', 'name': 'Active'}
        ]
        mock_orchestrator.list_tasks.return_value = []

        result = cli_runner.invoke(cli, ['clean'])

        assert result.exit_code == 0
        assert 'Nothing to clean' in result.output


class TestCostReportCommand:
    """Tests for the cost-report command."""

    def test_cost_report_basic(self, cli_runner, mock_orchestrator):
        """Test basic cost report."""
        result = cli_runner.invoke(cli, ['cost-report'])

        assert result.exit_code == 0
        assert 'Cost Analysis Report' in result.output
        assert 'Total Cost' in result.output
        assert 'Total Tokens' in result.output
        assert 'File Operations' in result.output
        mock_orchestrator.get_status.assert_called_once()

    def test_cost_report_by_agent(self, cli_runner, mock_orchestrator):
        """Test cost report with agent breakdown."""
        mock_orchestrator.list_agents.return_value = [
            {
                'agent_id': 'agent-1',
                'name': 'Test Agent',
                'role': 'planner',
                'metrics': {
                    'total_cost': '$1.5000',
                    'total_tokens': 1500,
                    'messages_sent': 10
                }
            }
        ]

        result = cli_runner.invoke(cli, ['cost-report', '--by-agent'])

        assert result.exit_code == 0
        assert 'Cost by Agent' in result.output
        assert 'Agent Cost Breakdown' in result.output

    def test_cost_report_by_role(self, cli_runner, mock_orchestrator):
        """Test cost report with role breakdown."""
        result = cli_runner.invoke(cli, ['cost-report', '--by-role'])

        assert result.exit_code == 0
        assert 'Cost by Role' in result.output

    def test_cost_report_json_format(self, cli_runner, mock_orchestrator):
        """Test cost report with JSON output."""
        result = cli_runner.invoke(cli, ['cost-report', '--format', 'json'])

        assert result.exit_code == 0
        assert 'JSON Export' in result.output

    def test_cost_report_csv_format(self, cli_runner, mock_orchestrator):
        """Test cost report with CSV output (not yet implemented)."""
        result = cli_runner.invoke(cli, ['cost-report', '--format', 'csv'])

        assert result.exit_code == 0
        assert 'CSV export not yet implemented' in result.output


class TestInitCommand:
    """Tests for the init command."""

    def test_init_creates_config(self, cli_runner, tmp_path):
        """Test init command creates config file."""
        # Change to temp directory
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(
                cli,
                ['init'],
                input='orchestrator.db\nINFO\n5\n15\n'
            )

            assert result.exit_code == 0
            assert Path('.env').exists()

            # Verify content
            content = Path('.env').read_text()
            assert 'ORCHESTRATOR_DB_PATH=orchestrator.db' in content
            assert 'ORCHESTRATOR_LOG_LEVEL=INFO' in content
            assert 'ORCHESTRATOR_MAX_PARALLEL_AGENTS=5' in content
            assert 'MONITOR_INTERVAL_SECONDS=15' in content
            assert 'Claude Code CLI' in content

    def test_init_overwrites_existing(self, cli_runner, tmp_path):
        """Test init command can overwrite existing config."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            # Create existing .env
            Path('.env').write_text('OLD_CONFIG=true')

            result = cli_runner.invoke(
                cli,
                ['init'],
                input='y\ntest.db\nDEBUG\n10\n30\n'
            )

            assert result.exit_code == 0
            content = Path('.env').read_text()
            assert 'OLD_CONFIG' not in content
            assert 'ORCHESTRATOR_DB_PATH=test.db' in content
            assert 'ORCHESTRATOR_LOG_LEVEL=DEBUG' in content

    def test_init_cancels_overwrite(self, cli_runner, tmp_path):
        """Test init command respects no overwrite."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            # Create existing .env
            original_content = 'OLD_CONFIG=true'
            Path('.env').write_text(original_content)

            result = cli_runner.invoke(cli, ['init'], input='n\n')

            assert result.exit_code == 0
            # Content should be unchanged
            assert Path('.env').read_text() == original_content


class TestCLIIntegration:
    """Integration tests for CLI commands."""

    def test_cli_commands_dont_require_api_key(self, cli_runner, mock_orchestrator):
        """Test that CLI commands work without API key."""
        # This should not raise an error about missing API key
        result = cli_runner.invoke(cli, ['status'])
        assert result.exit_code == 0

        result = cli_runner.invoke(cli, ['list-agents'])
        assert result.exit_code == 0

    def test_all_commands_call_stop(self, cli_runner, mock_orchestrator):
        """Test that all commands properly stop the orchestrator."""
        commands = [
            ['status'],
            ['list-agents'],
            ['list-tasks'],
            ['clean', '--dry-run']
        ]

        for command in commands:
            mock_orchestrator.stop.reset_mock()
            result = cli_runner.invoke(cli, command)
            assert result.exit_code == 0
            mock_orchestrator.stop.assert_called()
