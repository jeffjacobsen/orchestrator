"""
Observability demonstration.

Demonstrates:
- Real-time monitoring
- Cost tracking
- Files consumed vs produced
- Metrics collection
"""

import asyncio
from orchestrator import Orchestrator


async def main():
    # Note: API key is not needed - Claude Code SDK uses CLI authentication
    orchestrator = Orchestrator(
        enable_monitoring=True,  # Enable real-time monitoring
    )

    try:
        await orchestrator.start()

        # Execute a task that produces files
        print("Executing task with observability...")

        result = await orchestrator.execute(
            prompt="Create a simple Python script that prints 'Hello, World!'",
            task_type="feature_implementation",
            execution_mode="sequential",
        )

        # Get comprehensive status
        print("\n=== ORCHESTRATOR STATUS ===")
        status = orchestrator.get_status()

        # Fleet metrics
        print("\nFleet Summary:")
        for key, value in status['fleet'].items():
            print(f"  {key}: {value}")

        # Overall metrics
        print("\nMetrics Summary:")
        for key, value in status['metrics'].items():
            print(f"  {key}: {value}")

        # Files consumed vs produced (critical observability metric)
        print("\nFiles Consumed vs Produced:")
        files_data = status['monitoring']['files']
        print(f"  Files consumed: {len(files_data['consumed'])}")
        print(f"  Files produced: {len(files_data['produced'])}")
        print(f"  Net files created: {files_data['net_files_created']}")

        if files_data['consumed']:
            print("\n  Consumed:")
            for file in files_data['consumed']:
                print(f"    - {file}")

        if files_data['produced']:
            print("\n  Produced:")
            for file in files_data['produced']:
                print(f"    - {file}")

        # Per-agent breakdown
        print("\n=== AGENT BREAKDOWN ===")
        agents = orchestrator.list_agents()
        for agent in agents:
            print(f"\nAgent: {agent['name']} ({agent['role']})")
            print(f"  Status: {agent['status']}")
            print(f"  Cost: {agent['metrics']['total_cost']}")
            print(f"  Tokens: {agent['metrics']['total_tokens']}")
            print(f"  Messages: {agent['metrics']['messages_sent']}")
            print(f"  Files read: {agent['metrics']['files_read']}")
            print(f"  Files written: {agent['metrics']['files_written']}")

        print("\n=== KEY PRINCIPLE ===")
        print("If you can't measure it, you can't improve it.")
        print("If you can't measure it, you can't scale it.")
        print("\nThis observability system tracks:")
        print("  • Cost and performance metrics")
        print("  • Files consumed vs produced")
        print("  • Agent-level breakdowns")
        print("  • Real-time status updates")

    finally:
        await orchestrator.stop()


if __name__ == "__main__":
    asyncio.run(main())
