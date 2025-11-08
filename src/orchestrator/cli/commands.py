"""Command-line interface for the orchestrator."""

import asyncio
import json
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.json import JSON

from orchestrator import Orchestrator
from orchestrator.core.types import AgentRole


console = Console()


@click.group()
def cli() -> None:
    """Claude Multi-Agent Orchestrator CLI.

    Note: Authentication is handled through Claude Code CLI.
    No API key configuration needed.
    """
    pass


@cli.command()
@click.argument("prompt")
@click.option("--task-type", default="auto", help="Task type (auto, feature_implementation, bug_fix, etc.)")
@click.option("--mode", default="sequential", type=click.Choice(["sequential", "parallel"]))
@click.option("--no-cleanup", is_flag=True, help="Don't cleanup agents after completion")
def execute(prompt: str, task_type: str, mode: str, no_cleanup: bool) -> None:
    """Execute a high-level task with the orchestrator."""
    async def run() -> None:
        orchestrator = Orchestrator(enable_monitoring=True)

        try:
            await orchestrator.start()

            console.print(Panel(f"[cyan]Executing task:[/cyan] {prompt}"))
            console.print(f"Task type: {task_type}")
            console.print(f"Execution mode: {mode}\n")

            result = await orchestrator.execute(
                prompt=prompt,
                task_type=task_type,
                execution_mode=mode,
            )

            # Display results
            console.print("\n[green]✓ Task completed![/green]\n")

            console.print(Panel(result.output or "No output", title="Result"))

            # Display metrics
            table = Table(title="Metrics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Total Cost", f"${result.metrics.total_cost:.4f}")
            table.add_row("Total Tokens", str(result.metrics.total_tokens))
            table.add_row("Messages Sent", str(result.metrics.messages_sent))
            table.add_row("Tool Calls", str(result.metrics.tool_calls))
            table.add_row("Execution Time", f"{result.metrics.execution_time_seconds:.2f}s")
            table.add_row("Files Read", str(len(result.metrics.files_read)))
            table.add_row("Files Written", str(len(result.metrics.files_written)))

            console.print(table)

            if result.artifacts:
                console.print("\n[cyan]Artifacts produced:[/cyan]")
                for artifact in result.artifacts:
                    console.print(f"  • {artifact}")

        finally:
            await orchestrator.stop()

    asyncio.run(run())


@cli.command()
def status() -> None:
    """Show orchestrator status."""
    async def run() -> None:
        orchestrator = Orchestrator(enable_monitoring=False)

        try:
            status_data = orchestrator.get_status()

            console.print(Panel("[cyan]Orchestrator Status[/cyan]"))
            console.print(JSON(json.dumps(status_data), indent=2))

        finally:
            await orchestrator.stop()

    asyncio.run(run())


@cli.command()
@click.option("--role", type=click.Choice([r.value for r in AgentRole]), help="Filter by role")
def list_agents(role: Optional[str]) -> None:
    """List all active agents."""
    async def run() -> None:
        orchestrator = Orchestrator(enable_monitoring=False)

        try:
            agents = orchestrator.list_agents()

            if role:
                agents = [a for a in agents if a["role"] == role]

            if not agents:
                console.print("[yellow]No active agents[/yellow]")
                return

            table = Table(title=f"Active Agents ({len(agents)})")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Role", style="blue")
            table.add_column("Status", style="yellow")
            table.add_column("Cost", style="red")
            table.add_column("Tokens", style="magenta")

            for agent in agents:
                table.add_row(
                    agent["agent_id"][:8],
                    agent["name"],
                    agent["role"],
                    agent["status"],
                    agent["metrics"]["total_cost"],
                    str(agent["metrics"]["total_tokens"]),
                )

            console.print(table)

        finally:
            await orchestrator.stop()

    asyncio.run(run())


@cli.command()
def list_tasks() -> None:
    """List all tasks."""
    async def run() -> None:
        orchestrator = Orchestrator(enable_monitoring=False)

        try:
            tasks = orchestrator.list_tasks()

            if not tasks:
                console.print("[yellow]No tasks found[/yellow]")
                return

            table = Table(title=f"Tasks ({len(tasks)})")
            table.add_column("ID", style="cyan")
            table.add_column("Description", style="green")
            table.add_column("Status", style="yellow")
            table.add_column("Agents", style="blue")
            table.add_column("Created", style="magenta")

            for task in tasks:
                table.add_row(
                    task["task_id"][:8],
                    task["description"][:50],
                    task["status"],
                    str(len(task["assigned_agents"])),
                    task["created_at"][:19],
                )

            console.print(table)

        finally:
            await orchestrator.stop()

    asyncio.run(run())


@cli.command()
@click.argument("task_id")
def task_details(task_id: str) -> None:
    """Show details for a specific task."""
    async def run() -> None:
        orchestrator = Orchestrator(enable_monitoring=False)

        try:
            task = orchestrator.get_task_status(task_id)

            if not task:
                console.print(f"[red]Task {task_id} not found[/red]")
                return

            console.print(Panel("[cyan]Task Details[/cyan]"))
            console.print(JSON(json.dumps(task), indent=2))

        finally:
            await orchestrator.stop()

    asyncio.run(run())


@cli.command()
@click.argument("agent_id")
def agent_details(agent_id: str) -> None:
    """Show details for a specific agent."""
    async def run() -> None:
        orchestrator = Orchestrator(enable_monitoring=False)

        try:
            agent = orchestrator.get_agent_details(agent_id)

            if not agent:
                console.print(f"[red]Agent {agent_id} not found[/red]")
                return

            console.print(Panel("[cyan]Agent Details[/cyan]"))
            console.print(JSON(json.dumps(agent), indent=2))

        finally:
            await orchestrator.stop()

    asyncio.run(run())


@cli.command()
def init() -> None:
    """Initialize a new orchestrator configuration."""
    if Path(".env").exists():
        overwrite = click.confirm(".env file exists. Overwrite?")
        if not overwrite:
            return

    console.print("[cyan]Initializing orchestrator configuration...[/cyan]\n")
    console.print("[yellow]Note: API key is no longer required.[/yellow]")
    console.print("[yellow]Authentication is handled through Claude Code CLI.[/yellow]\n")

    # Optional configuration prompts
    db_path = click.prompt("Database path", default="./orchestrator.db")
    log_level = click.prompt("Log level", default="INFO",
                             type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]))
    max_parallel = click.prompt("Max parallel agents", default=5, type=int)
    monitor_interval = click.prompt("Monitor interval (seconds)", default=15, type=int)

    env_content = f"""# Orchestrator Configuration
# Note: ANTHROPIC_API_KEY is no longer required
# Authentication is handled through Claude Code CLI

# Default Model Configuration
DEFAULT_MODEL=claude-sonnet-4-5-20250929

# Orchestrator Settings
ORCHESTRATOR_DB_PATH={db_path}
ORCHESTRATOR_LOG_LEVEL={log_level}
ORCHESTRATOR_MAX_PARALLEL_AGENTS={max_parallel}

# Monitoring Settings
MONITOR_INTERVAL_SECONDS={monitor_interval}
ENABLE_COST_TRACKING=true
ENABLE_OBSERVABILITY=true
"""

    Path(".env").write_text(env_content)
    console.print("\n[green]✓ Configuration saved to .env[/green]")
    console.print("\n[cyan]You can now use orchestrator commands:[/cyan]")
    console.print("  orchestrator execute \"your task here\"")
    console.print("  orchestrator status")
    console.print("  orchestrator list-agents")


@cli.command()
@click.option("--older-than", type=int, help="Clean agents/tasks older than N days")
@click.option("--dry-run", is_flag=True, help="Show what would be deleted without deleting")
def clean(older_than: Optional[int], dry_run: bool) -> None:
    """Clean up old agents and tasks from the database."""
    async def run() -> None:
        orchestrator = Orchestrator(enable_monitoring=False)

        try:
            # Get current agents and tasks
            agents = orchestrator.list_agents()
            tasks = orchestrator.list_tasks()

            # Filter based on status
            completed_agents = [a for a in agents if a["status"] in ["completed", "failed", "deleted"]]
            completed_tasks = [t for t in tasks if t["status"] in ["completed", "failed"]]

            if dry_run:
                console.print("[yellow]DRY RUN - No changes will be made[/yellow]\n")

            # Show what will be cleaned
            console.print(f"[cyan]Agents to clean:[/cyan] {len(completed_agents)}")
            console.print(f"[cyan]Tasks to clean:[/cyan] {len(completed_tasks)}\n")

            if not dry_run:
                if completed_agents or completed_tasks:
                    confirm = click.confirm("Proceed with cleanup?", default=True)
                    if confirm:
                        # Clean up agents
                        for agent in completed_agents:
                            await orchestrator.delete_agent(agent["agent_id"])

                        console.print(f"[green]✓ Cleaned {len(completed_agents)} agents[/green]")
                        console.print(f"[green]✓ Cleaned {len(completed_tasks)} tasks[/green]")
                    else:
                        console.print("[yellow]Cleanup cancelled[/yellow]")
                else:
                    console.print("[green]Nothing to clean[/green]")

        finally:
            await orchestrator.stop()

    asyncio.run(run())


@cli.command()
@click.option("--format", type=click.Choice(["table", "json", "csv"]), default="table", help="Output format")
@click.option("--by-agent", is_flag=True, help="Show breakdown by agent")
@click.option("--by-role", is_flag=True, help="Show breakdown by role")
def cost_report(format: str, by_agent: bool, by_role: bool) -> None:
    """Generate a cost analysis report."""
    async def run() -> None:
        orchestrator = Orchestrator(enable_monitoring=False)

        try:
            status = orchestrator.get_status()
            agents = orchestrator.list_agents()

            console.print(Panel("[cyan]Cost Analysis Report[/cyan]"))

            # Overall summary
            console.print(f"\n[bold]Total Cost:[/bold] {status['fleet']['total_cost']}")
            console.print(f"[bold]Total Tokens:[/bold] {status['fleet']['total_tokens']:,}")
            console.print(f"[bold]Total Agents:[/bold] {status['fleet']['total_agents']}")

            # By agent breakdown
            if by_agent and agents:
                console.print("\n[cyan]Cost by Agent:[/cyan]")

                agent_table = Table(title="Agent Cost Breakdown")
                agent_table.add_column("Agent ID", style="cyan")
                agent_table.add_column("Name", style="green")
                agent_table.add_column("Role", style="blue")
                agent_table.add_column("Cost", style="red", justify="right")
                agent_table.add_column("Tokens", style="magenta", justify="right")
                agent_table.add_column("Messages", style="yellow", justify="right")

                for agent in sorted(agents, key=lambda a: float(a["metrics"]["total_cost"].replace("$", "")), reverse=True):
                    agent_table.add_row(
                        agent["agent_id"][:8],
                        agent["name"],
                        agent["role"],
                        agent["metrics"]["total_cost"],
                        f"{agent['metrics']['total_tokens']:,}",
                        str(agent["metrics"]["messages_sent"])
                    )

                console.print(agent_table)

            # By role breakdown
            if by_role:
                console.print("\n[cyan]Cost by Role:[/cyan]")

                role_table = Table(title="Role Cost Breakdown")
                role_table.add_column("Role", style="blue")
                role_table.add_column("Count", style="cyan", justify="right")

                for role, count in status['fleet']['by_role'].items():
                    if count > 0:
                        role_table.add_row(role, str(count))

                console.print(role_table)

            # File operations summary
            console.print("\n[cyan]File Operations:[/cyan]")
            files = status['monitoring']['files']
            console.print(f"Files consumed: {len(files['consumed'])}")
            console.print(f"Files produced: {len(files['produced'])}")
            console.print(f"Net files created: {files['net_files_created']}")

            # Export options
            if format == "json":
                console.print("\n[cyan]JSON Export:[/cyan]")
                console.print(JSON(json.dumps({
                    "total_cost": status['fleet']['total_cost'],
                    "total_tokens": status['fleet']['total_tokens'],
                    "agents": agents,
                    "by_role": status['fleet']['by_role']
                }), indent=2))
            elif format == "csv":
                console.print("\n[yellow]CSV export not yet implemented[/yellow]")

        finally:
            await orchestrator.stop()

    asyncio.run(run())


if __name__ == "__main__":
    cli()
