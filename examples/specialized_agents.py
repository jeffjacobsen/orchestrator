"""
Specialized agents example.

Demonstrates:
- Using specific agent roles
- Sequential workflow with specialized agents
- Agent specialization benefits
"""

import asyncio
from orchestrator import Orchestrator
from orchestrator.core.types import AgentRole


async def main():
    # Note: API key is not needed - Claude Code SDK uses CLI authentication
    orchestrator = Orchestrator()

    try:
        await orchestrator.start()

        # Define a workflow with specialized agents
        print("Creating a feature implementation workflow...")

        result = await orchestrator.execute_custom_workflow(
            prompt="Add a new feature to calculate factorial of a number",
            roles=[
                AgentRole.ANALYST,    # Research requirements and analyze codebase
                AgentRole.PLANNER,    # Create implementation plan
                AgentRole.BUILDER,    # Implement the feature
                AgentRole.TESTER,     # Write and run tests
                AgentRole.REVIEWER,   # Review that code follows the plan
            ],
            parallel=False,  # Sequential execution
        )

        # Print results from each agent
        print("\n=== WORKFLOW RESULTS ===")
        for i, agent_result in enumerate(result):
            print(f"\n--- Agent {i+1}: {agent_result.task_description} ---")
            print(f"Success: {agent_result.success}")
            print(f"Output: {agent_result.output[:200]}...")  # First 200 chars
            print(f"Cost: ${agent_result.metrics.total_cost:.4f}")

        # Show total metrics
        total_cost = sum(r.metrics.total_cost for r in result)
        total_tokens = sum(r.metrics.total_tokens for r in result)

        print("\n=== TOTAL METRICS ===")
        print(f"Total Cost: ${total_cost:.4f}")
        print(f"Total Tokens: {total_tokens}")

    finally:
        await orchestrator.stop()


if __name__ == "__main__":
    asyncio.run(main())
