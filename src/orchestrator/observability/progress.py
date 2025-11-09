"""Real-time progress tracking for agent operations."""

import time
from typing import Dict, Optional

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel

from orchestrator.core.types import AgentStatus


class ProgressTracker:
    """
    Tracks and displays real-time progress of agent operations.

    Provides visual feedback for:
    - Current agent activity
    - Tool calls being made
    - Time elapsed
    - Cost accumulating
    - Workflow step progress
    """

    def __init__(self, console: Optional[Console] = None, enabled: bool = True):
        """
        Initialize progress tracker.

        Args:
            console: Rich console for output (creates new if None)
            enabled: Whether to show progress (False for non-TTY)
        """
        self.console = console or Console()
        self.enabled = enabled
        self.live: Optional[Live] = None

        # Agent tracking
        self.agents: Dict[str, Dict] = {}
        self.current_agent_id: Optional[str] = None
        self.workflow_steps: list = []
        self.current_step: int = 0

        # Metrics
        self.total_cost: float = 0.0
        self.start_time: Optional[float] = None

    def start(self, workflow_steps: Optional[list] = None) -> None:
        """
        Start progress tracking display.

        Args:
            workflow_steps: List of workflow step names for progress bar
        """
        if not self.enabled:
            return

        self.start_time = time.time()
        self.workflow_steps = workflow_steps or []
        self.current_step = 0

        # Create live display
        self.live = Live(
            self._generate_display(), console=self.console, refresh_per_second=4, transient=False
        )
        self.live.start()

    def stop(self) -> None:
        """Stop progress tracking display."""
        if self.live:
            self.live.stop()
            self.live = None

    def _generate_display(self) -> Panel:
        """Generate the progress display layout."""
        # Create main layout
        layout_table = Table.grid(padding=(0, 2))
        layout_table.add_column()

        # Add workflow progress if we have steps
        if self.workflow_steps:
            workflow_progress = self._create_workflow_progress()
            layout_table.add_row(workflow_progress)

        # Add current agent status
        agent_status = self._create_agent_status()
        layout_table.add_row(agent_status)

        # Add metrics summary
        metrics = self._create_metrics()
        layout_table.add_row(metrics)

        # Wrap in panel
        elapsed = f"{int(time.time() - self.start_time)}s" if self.start_time else "0s"
        return Panel(
            layout_table,
            title="[bold cyan]Orchestrator Progress[/bold cyan]",
            subtitle=f"Elapsed: {elapsed}",
            border_style="cyan",
        )

    def _create_workflow_progress(self) -> Table:
        """Create workflow step progress display."""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Step", style="bold")
        table.add_column("Status")

        for idx, step in enumerate(self.workflow_steps):
            if idx < self.current_step:
                status = "[green]✓[/green]"
            elif idx == self.current_step:
                status = "[yellow]→[/yellow]"
            else:
                status = "[dim]○[/dim]"

            table.add_row(status, step if idx == self.current_step else f"[dim]{step}[/dim]")

        return table

    def _create_agent_status(self) -> Table:
        """Create current agent status display."""
        table = Table(show_header=True, box=None, padding=(0, 1))
        table.add_column("Agent", style="cyan")
        table.add_column("Status")
        table.add_column("Activity", style="dim")

        if self.current_agent_id and self.current_agent_id in self.agents:
            agent = self.agents[self.current_agent_id]
            status_icon = self._get_status_icon(agent.get("status", AgentStatus.CREATED))
            activity = agent.get("current_activity", "Initializing...")

            table.add_row(agent.get("name", "Unknown"), status_icon, activity)
        else:
            table.add_row("[dim]No active agent[/dim]", "", "")

        return table

    def _create_metrics(self) -> str:
        """Create metrics summary."""
        active_count = sum(
            1 for a in self.agents.values() if a.get("status") == AgentStatus.RUNNING
        )
        completed_count = sum(
            1 for a in self.agents.values() if a.get("status") == AgentStatus.COMPLETED
        )

        return (
            f"[dim]Active: {active_count} | "
            f"Completed: {completed_count} | "
            f"Cost: ${self.total_cost:.4f}[/dim]"
        )

    def _get_status_icon(self, status: AgentStatus) -> str:
        """Get icon for agent status."""
        icons = {
            AgentStatus.CREATED: "[dim]○[/dim] Created",
            AgentStatus.RUNNING: "[yellow]●[/yellow] Running",
            AgentStatus.COMPLETED: "[green]✓[/green] Completed",
            AgentStatus.FAILED: "[red]✗[/red] Failed",
            AgentStatus.DELETED: "[dim]✓[/dim] Deleted",
        }
        return icons.get(status, "[dim]?[/dim] Unknown")

    def update(self) -> None:
        """Refresh the display with current state."""
        if self.live:
            self.live.update(self._generate_display())

    def agent_created(self, agent_id: str, name: str, role: str) -> None:
        """Record agent creation."""
        self.agents[agent_id] = {
            "name": name,
            "role": role,
            "status": AgentStatus.CREATED,
            "current_activity": "Starting...",
            "created_at": time.time(),
        }
        self.current_agent_id = agent_id
        self.update()

    def agent_started(self, agent_id: str) -> None:
        """Record agent started execution."""
        if agent_id in self.agents:
            self.agents[agent_id]["status"] = AgentStatus.RUNNING
            self.agents[agent_id]["current_activity"] = "Executing task..."
            self.current_agent_id = agent_id
            self.update()

    def agent_activity(self, agent_id: str, activity: str) -> None:
        """Update agent's current activity."""
        if agent_id in self.agents:
            self.agents[agent_id]["current_activity"] = activity
            self.update()

    def agent_completed(self, agent_id: str, cost: float) -> None:
        """Record agent completion."""
        if agent_id in self.agents:
            self.agents[agent_id]["status"] = AgentStatus.COMPLETED
            self.agents[agent_id]["current_activity"] = "Done"
            self.total_cost += cost

            # Move to next workflow step
            if self.current_step < len(self.workflow_steps):
                self.current_step += 1

            self.update()

    def agent_failed(self, agent_id: str, error: str) -> None:
        """Record agent failure."""
        if agent_id in self.agents:
            self.agents[agent_id]["status"] = AgentStatus.FAILED
            self.agents[agent_id]["current_activity"] = f"Error: {error[:50]}"
            self.update()

    def tool_call(self, agent_id: str, tool_name: str) -> None:
        """Record tool call."""
        if agent_id in self.agents:
            self.agents[agent_id]["current_activity"] = f"Using {tool_name}..."
            self.update()

    def thinking(self, agent_id: str) -> None:
        """Record agent thinking."""
        if agent_id in self.agents:
            self.agents[agent_id]["current_activity"] = "Thinking..."
            self.update()
