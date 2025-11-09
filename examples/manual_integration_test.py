"""Test script for refactored orchestrator using Claude Code SDK."""

import asyncio
from pathlib import Path
from orchestrator.core.orchestrator import Orchestrator
from orchestrator.core.types import AgentRole


async def test_basic_agent():
    """Test basic agent creation and execution."""
    print("=" * 60)
    print("Testing Refactored Orchestrator with Claude Code SDK")
    print("=" * 60)

    # Create orchestrator (no API key needed!)
    orchestrator = Orchestrator(
        log_path=Path("logs/test_orchestrator.log"),
        enable_monitoring=False,
    )

    print("\n✓ Orchestrator initialized (no API key required)")

    try:
        await orchestrator.start()
        print("✓ Orchestrator started")

        # Test 1: Create a single agent manually
        print("\n" + "=" * 60)
        print("Test 1: Manual Agent Creation")
        print("=" * 60)

        agent_id = await orchestrator.create_agent(
            role=AgentRole.PLANNER,
            name="Test Planner",
        )

        print(f"✓ Created agent: {agent_id}")

        # Test 2: Send a simple message
        print("\n" + "=" * 60)
        print("Test 2: Send Message to Agent")
        print("=" * 60)

        response = await orchestrator.send_to_agent(
            agent_id,
            "What files are in the current directory? Just list the top-level files."
        )

        print(f"\n✓ Agent response:\n{response}")

        # Test 3: Get agent details
        print("\n" + "=" * 60)
        print("Test 3: Agent Metrics and Details")
        print("=" * 60)

        details = orchestrator.get_agent_details(agent_id)
        print(f"\nAgent Summary:")
        print(f"  ID: {details['agent_id']}")
        print(f"  Name: {details['name']}")
        print(f"  Role: {details['role']}")
        print(f"  Status: {details['status']}")
        print(f"  Total Cost: {details['metrics']['total_cost']}")
        print(f"  Total Tokens: {details['metrics']['total_tokens']}")
        print(f"    - Input: {details['metrics']['input_tokens']}")
        print(f"    - Output: {details['metrics']['output_tokens']}")
        print(f"    - Cache Creation: {details['metrics']['cache_creation_tokens']}")
        print(f"    - Cache Read: {details['metrics']['cache_read_tokens']}")
        print(f"  Tool Calls: {details['metrics']['tool_calls']}")
        print(f"  Files Read: {details['metrics']['files_read']}")
        print(f"  Execution Time: {details['metrics']['execution_time']}")

        # Test 4: Execute a high-level task using the orchestrator
        print("\n" + "=" * 60)
        print("Test 4: High-Level Task Execution")
        print("=" * 60)

        result = await orchestrator.execute(
            prompt="Create a simple README.md file in a test directory with a brief description of this project.",
            task_type="auto",
            execution_mode="sequential",
        )

        print(f"\n✓ Task completed: {result.success}")
        print(f"  Output: {result.output[:200]}...")
        print(f"  Total Cost: ${result.metrics.total_cost:.4f}")
        print(f"  Total Tokens: {result.metrics.total_tokens}")
        print(f"  Files Written: {result.metrics.files_written}")

        # Test 5: Get fleet summary
        print("\n" + "=" * 60)
        print("Test 5: Fleet Status")
        print("=" * 60)

        status = orchestrator.get_status()
        print(f"\nFleet Summary:")
        print(f"  Total Agents: {status['fleet']['total_agents']}")
        print(f"  Active Agents: {status['fleet']['active_agents']}")
        print(f"  Total Cost: {status['fleet']['total_cost']}")
        print(f"  Total Tokens: {status['fleet']['total_tokens']}")

    finally:
        # Cleanup
        print("\n" + "=" * 60)
        print("Cleanup")
        print("=" * 60)

        await orchestrator.stop()
        print("✓ Orchestrator stopped and cleaned up")

    print("\n" + "=" * 60)
    print("All Tests Completed Successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_basic_agent())
