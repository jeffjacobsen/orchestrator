"""
Manual agent control example.

Demonstrates:
- Manually creating agents
- Sending messages to specific agents
- Direct agent interaction
- CRUD operations
"""

import asyncio
from orchestrator import Orchestrator
from orchestrator.core.types import AgentRole


async def main():
    # Note: API key is not needed - Claude Code SDK uses CLI authentication
    orchestrator = Orchestrator()

    try:
        await orchestrator.start()

        # CREATE: Manually create a Planner agent
        print("=== CREATE ===")
        planner_id = await orchestrator.create_agent(
            role=AgentRole.PLANNER,
            name="My Custom Planner",
        )
        print(f"Created Planner agent: {planner_id}")

        # READ: Get agent details
        print("\n=== READ ===")
        agent_details = orchestrator.get_agent_details(planner_id)
        print(f"Agent name: {agent_details['name']}")
        print(f"Agent role: {agent_details['role']}")
        print(f"Agent status: {agent_details['status']}")

        # UPDATE: Send messages to the agent
        print("\n=== UPDATE (Interact) ===")

        response1 = await orchestrator.send_to_agent(
            planner_id,
            "Create a plan to add a new feature that logs all API calls"
        )
        print(f"Response 1: {response1[:200]}...")

        response2 = await orchestrator.send_to_agent(
            planner_id,
            "What are the key dependencies for this plan?"
        )
        print(f"Response 2: {response2[:200]}...")

        # The agent maintains conversation context
        print("\n=== CONTEXT MAINTAINED ===")
        print("The agent remembers the previous conversation and can refer back to it.")

        # Check context window usage
        updated_details = orchestrator.get_agent_details(planner_id)
        context_usage = updated_details['context_usage']
        print(f"Context usage: {context_usage['usage_percentage']:.2f}%")
        print(f"Tokens used: {context_usage['total_tokens_used']}")
        print(f"Messages in history: {context_usage['messages_in_history']}")

        # DELETE: Remove the agent when done
        print("\n=== DELETE ===")
        deleted = await orchestrator.delete_agent(planner_id)
        print(f"Agent deleted: {deleted}")

        # Verify deletion
        agent_after_delete = orchestrator.get_agent_details(planner_id)
        print(f"Agent exists after deletion: {agent_after_delete is not None}")

        print("\n=== KEY CONCEPT ===")
        print("Agents are temporary, deletable resources.")
        print("Create them for specific jobs, then delete them to free resources.")
        print("This is the key to managing agents at scale.")

    finally:
        await orchestrator.stop()


if __name__ == "__main__":
    asyncio.run(main())
