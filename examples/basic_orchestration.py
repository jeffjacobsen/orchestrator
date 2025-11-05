"""
Basic orchestration example.

Demonstrates:
- Creating an orchestrator
- Executing a simple task
- Viewing results and metrics
"""

import asyncio
from orchestrator import Orchestrator


async def main():
    # Note: API key is not needed - Claude Code SDK uses CLI authentication
    # Create orchestrator
    orchestrator = Orchestrator(
        enable_monitoring=True,
    )

    try:
        # Start the orchestrator
        await orchestrator.start()

        # Execute a simple task
        print("Executing task...")
        result = await orchestrator.execute(
            prompt="Find all Python files in the current directory and analyze their structure",
            task_type="auto",
            execution_mode="sequential",
        )

        # Print results
        print("\n=== RESULT ===")
        print(f"Success: {result.success}")
        print(f"Output: {result.output}")

        print("\n=== METRICS ===")
        print(f"Total Cost: ${result.metrics.total_cost:.4f}")
        print(f"Total Tokens: {result.metrics.total_tokens}")
        print(f"Execution Time: {result.metrics.execution_time_seconds:.2f}s")
        print(f"Files Read: {len(result.metrics.files_read)}")
        print(f"Files Written: {len(result.metrics.files_written)}")

        # Get orchestrator status
        print("\n=== ORCHESTRATOR STATUS ===")
        status = orchestrator.get_status()
        print(f"Total agents created: {status['fleet']['total_agents']}")
        print(f"Total cost: {status['fleet']['total_cost']}")
        print(f"Total tokens: {status['fleet']['total_tokens']}")

    finally:
        # Cleanup
        await orchestrator.stop()


if __name__ == "__main__":
    asyncio.run(main())
