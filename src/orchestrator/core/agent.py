"""Individual agent wrapper for Claude Code SDK interactions."""

import inspect
import os
import time
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union
from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock,
    ThinkingBlock,
)
from orchestrator.core.types import (
    AgentConfig,
    AgentStatus,
    AgentMetrics,
    ToolCall,
    TaskResult,
)


class Agent:
    """
    Represents a single Claude agent with its own conversation thread.

    Key Design Principles:
    - Each agent maintains its own context window
    - Agents are temporary, deletable resources
    - Focused on a single specialized task
    - Tracks all metrics and tool usage
    """

    def __init__(
        self,
        agent_id: str,
        config: AgentConfig,
        enable_logging: bool = True,
        progress_callback: Optional[
            Union[Callable[[str, str], None], Callable[[str, str], Awaitable[None]]]
        ] = None,
    ) -> None:
        self.agent_id = agent_id
        self.config = config

        # State management
        self.status = AgentStatus.CREATED
        self.tool_calls: List[ToolCall] = []

        # Metrics tracking
        self.metrics = AgentMetrics(agent_id=agent_id)
        self.created_at = datetime.now(timezone.utc)
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

        # Progress callback for real-time updates
        self.progress_callback = progress_callback

        # File logging - lazy import to avoid circular dependency
        from orchestrator.observability.agent_logger import AgentLogger

        self.logger = AgentLogger(
            agent_id=agent_id,
            agent_name=config.name,
            enabled=enable_logging,
            task_id=config.task_id,
        )

    async def _call_progress_callback(self, event: str, data: str = "") -> None:
        """Helper to call progress callback, handling both sync and async callbacks."""
        if self.progress_callback:
            result = self.progress_callback(event, data)
            if inspect.iscoroutine(result):
                await result

    async def execute_task(self, task_prompt: str) -> TaskResult:
        """
        Execute a task with the agent using Claude Code SDK.

        Args:
            task_prompt: The task description/prompt for the agent

        Returns:
            TaskResult containing output and metrics
        """
        self.status = AgentStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)
        start_time = time.time()

        # Notify progress callback that agent started
        await self._call_progress_callback("started")

        try:
            # Log the prompt
            self.logger.log_prompt(task_prompt)

            # Configure SDK client options
            options = self._build_options()

            # Process streaming response
            output_text = ""
            async for message in query(prompt=task_prompt, options=options):
                # Log every message
                self.logger.log_message(message)

                if isinstance(message, AssistantMessage):
                    # Process text blocks
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            output_text += block.text
                        elif isinstance(block, ThinkingBlock):
                            # Report thinking activity
                            await self._call_progress_callback("thinking")
                        elif isinstance(block, ToolUseBlock):
                            # Track tool usage
                            self._track_tool_use(block)
                            # Report tool activity
                            await self._call_progress_callback("tool_call", block.name)
                        elif isinstance(block, ToolResultBlock):
                            # Update tool call with result
                            self._track_tool_result(block)

                elif isinstance(message, ResultMessage):
                    # Extract final metrics from SDK
                    self._update_metrics_from_result(message)
                    # Save session ID for future conversations
                    if hasattr(message, "session_id"):
                        self.config.session_id = message.session_id

            self.metrics.messages_sent += 1
            self.metrics.execution_time_seconds = time.time() - start_time
            self.status = AgentStatus.COMPLETED
            self.completed_at = datetime.now(timezone.utc)

            # Notify progress callback of completion
            await self._call_progress_callback("completed")

            return TaskResult(
                agent_id=self.agent_id,
                task_description=task_prompt,
                success=True,
                output=output_text,
                metrics=self.metrics,
                artifacts=self.metrics.files_written,
            )

        except Exception as e:
            self.status = AgentStatus.FAILED
            self.completed_at = datetime.now(timezone.utc)
            self.metrics.execution_time_seconds = time.time() - start_time

            # Notify progress callback of failure
            await self._call_progress_callback("failed", str(e))

            return TaskResult(
                agent_id=self.agent_id,
                task_description=task_prompt,
                success=False,
                output=None,
                error=str(e),
                metrics=self.metrics,
            )

    async def send_message(self, message: str) -> str:
        """
        Send a message to the agent and get a response.
        Maintains conversation context via session_id.

        Args:
            message: Message to send to the agent

        Returns:
            Agent's response as text
        """
        self.status = AgentStatus.RUNNING

        # Log the message
        self.logger.log_prompt(f"[CONTINUE] {message}")

        # Configure SDK client options
        options = self._build_options()

        # Process response
        output_text = ""
        async for msg in query(prompt=message, options=options):
            # Log every message
            self.logger.log_message(msg)

            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        output_text += block.text
                    elif isinstance(block, ToolUseBlock):
                        self._track_tool_use(block)
                    elif isinstance(block, ToolResultBlock):
                        self._track_tool_result(block)

            elif isinstance(msg, ResultMessage):
                self._update_metrics_from_result(msg)
                if hasattr(msg, "session_id"):
                    self.config.session_id = msg.session_id

        self.metrics.messages_sent += 1
        self.status = AgentStatus.WAITING
        return output_text

    def _update_metrics_from_result(self, result: ResultMessage) -> None:
        """Update metrics from SDK ResultMessage."""
        # SDK provides accurate token counts via result.usage (dict)
        if hasattr(result, "usage") and result.usage:
            usage = result.usage

            # Track input/output tokens (usage is a dict)
            if "input_tokens" in usage:
                self.metrics.input_tokens += usage["input_tokens"]
            if "output_tokens" in usage:
                self.metrics.output_tokens += usage["output_tokens"]

            # Track cache tokens
            if "cache_creation_input_tokens" in usage:
                self.metrics.cache_creation_input_tokens += usage["cache_creation_input_tokens"]
            if "cache_read_input_tokens" in usage:
                self.metrics.cache_read_input_tokens += usage["cache_read_input_tokens"]

        # Calculate total tokens (including cache tokens)
        self.metrics.total_tokens = (
            self.metrics.input_tokens
            + self.metrics.output_tokens
            + self.metrics.cache_creation_input_tokens
            + self.metrics.cache_read_input_tokens
        )

        # SDK provides accurate cost tracking
        if hasattr(result, "total_cost_usd") and result.total_cost_usd:
            self.metrics.total_cost += result.total_cost_usd

        self.metrics.updated_at = datetime.now(timezone.utc)

    def _track_tool_use(self, tool_block: ToolUseBlock) -> None:
        """Track tool usage from SDK ToolUseBlock."""
        tool_call = ToolCall(
            tool_name=tool_block.name,
            arguments=tool_block.input,
        )
        self.tool_calls.append(tool_call)
        self.metrics.tool_calls += 1

        # Track file operations
        if tool_block.name == "Read":
            file_path = tool_block.input.get("file_path")
            if file_path and file_path not in self.metrics.files_read:
                self.metrics.files_read.append(file_path)

        elif tool_block.name in ["Write", "Edit"]:
            file_path = tool_block.input.get("file_path")
            if file_path and file_path not in self.metrics.files_written:
                self.metrics.files_written.append(file_path)

    def _track_tool_result(self, result_block: ToolResultBlock) -> None:
        """
        Track tool result and link it back to the corresponding tool call.
        Provides complete audit trail of tool execution.

        Args:
            result_block: ToolResultBlock from SDK
        """
        # Find the most recent tool call without a result and update it
        for tc in reversed(self.tool_calls):
            if tc.tool_name and not tc.result:
                tc.result = result_block.content
                tc.success = not result_block.is_error
                if result_block.is_error:
                    tc.error = str(result_block.content)
                break

    def get_context_window_usage(self) -> Dict[str, Any]:
        """
        Get information about context window usage.
        Critical for preventing context overflow.

        Returns:
            Dict with token counts and usage percentage
        """
        # Claude models have different context windows
        # Sonnet 4.5 has 200k token context
        max_context = 200_000

        return {
            "total_tokens_used": self.metrics.total_tokens,
            "max_context_tokens": max_context,
            "usage_percentage": (
                (self.metrics.total_tokens / max_context) * 100
                if self.metrics.total_tokens > 0
                else 0
            ),
            "session_id": self.config.session_id,
            "estimated_remaining": max_context - self.metrics.total_tokens,
        }

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the agent's state and metrics."""
        return {
            "agent_id": self.agent_id,
            "name": self.config.name,
            "role": self.config.role.value,
            "status": self.status.value,
            "model": self.config.model,
            "created_at": self.created_at.isoformat(),
            "metrics": {
                "total_cost": f"${self.metrics.total_cost:.4f}",
                "total_tokens": self.metrics.total_tokens,
                "input_tokens": self.metrics.input_tokens,
                "output_tokens": self.metrics.output_tokens,
                "cache_creation_tokens": self.metrics.cache_creation_input_tokens,
                "cache_read_tokens": self.metrics.cache_read_input_tokens,
                "messages_sent": self.metrics.messages_sent,
                "tool_calls": self.metrics.tool_calls,
                "files_read": len(self.metrics.files_read),
                "files_written": len(self.metrics.files_written),
                "execution_time": f"{self.metrics.execution_time_seconds:.2f}s",
            },
            "context_usage": self.get_context_window_usage(),
        }

    async def cleanup(self) -> None:
        """Cleanup agent resources. Mark as deleted."""
        self.status = AgentStatus.DELETED
        self.config.session_id = None  # Clear session
        self.tool_calls.clear()

    def _build_options(self) -> ClaudeAgentOptions:
        """
        Build ClaudeAgentOptions from agent config.
        Centralizes all options construction logic.

        Returns:
            ClaudeAgentOptions configured from agent config
        """
        options_dict: Dict[str, Any] = {}

        # Working directory
        if self.config.working_directory:
            options_dict["cwd"] = self.config.working_directory
        else:
            options_dict["cwd"] = os.getcwd()

        # System prompt
        if self.config.system_prompt:
            options_dict["system_prompt"] = self.config.system_prompt

        # Allowed tools (tool-level control)
        if self.config.allowed_tools:
            options_dict["allowed_tools"] = self.config.allowed_tools

        # Permission mode
        options_dict["permission_mode"] = self.config.permission_mode

        # Model
        if self.config.model:
            options_dict["model"] = self.config.model

        # Session resumption
        if self.config.session_id:
            options_dict["resume"] = self.config.session_id

        return ClaudeAgentOptions(**options_dict)
