"""
Parallel execution example.

Demonstrates:
- Running multiple agents in parallel
- Scaling compute with a single prompt
- Performance benefits of parallelization
"""

import asyncio
import time
from orchestrator import Orchestrator
from orchestrator.core.types import AgentRole


async def main():
    # Note: API key is not needed - Claude Code SDK uses CLI authentication
    orchestrator = Orchestrator()

    try:
        await orchestrator.start()

        # Compare sequential vs parallel execution
        task_prompt = "Analyze the code quality and suggest improvements"

        # Sequential execution
        print("=== SEQUENTIAL EXECUTION ===")
        start = time.time()

        sequential_result = await orchestrator.execute_custom_workflow(
            prompt=task_prompt,
            roles=[AgentRole.REVIEWER, AgentRole.ANALYST, AgentRole.TESTER],
            parallel=False,
        )

        sequential_time = time.time() - start
        print(f"Time: {sequential_time:.2f}s")

        # Parallel execution
        print("\n=== PARALLEL EXECUTION ===")
        start = time.time()

        parallel_result = await orchestrator.execute_custom_workflow(
            prompt=task_prompt,
            roles=[AgentRole.REVIEWER, AgentRole.ANALYST, AgentRole.TESTER],
            parallel=True,
        )

        parallel_time = time.time() - start
        print(f"Time: {parallel_time:.2f}s")

        # Show speedup
        print("\n=== PERFORMANCE ===")
        print(f"Sequential: {sequential_time:.2f}s")
        print(f"Parallel: {parallel_time:.2f}s")
        print(f"Speedup: {sequential_time / parallel_time:.2f}x")

        # This demonstrates the key concept:
        # Deploy 3x the compute with a single prompt
        print("\n=== KEY INSIGHT ===")
        print("Parallel execution allows you to scale compute and impact.")
        print("Instead of waiting for agents sequentially, deploy them all at once.")

    finally:
        await orchestrator.stop()


if __name__ == "__main__":
    asyncio.run(main())
