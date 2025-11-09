"""
File-based logging for Agent SDK message streams.

This module provides JSONL-based logging to capture all agent interactions:
- Text blocks (agent responses and thinking)
- Tool usage (tool calls with inputs)
- Tool results (outputs from tools)
- System messages
- Result messages (final metrics)

Each agent gets a dedicated log directory with timestamped files for:
- prompt.txt: The original task prompt
- text.txt: All text and thinking blocks
- tools.jsonl: Tool calls and results in JSONL format
- summary.jsonl: System and result messages

Environment variables:
- ENABLE_AGENT_LOGGING: Enable file logging (default: true)
- AGENT_LOG_DIR: Directory for logs (default: ./agent_logs)
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Any, Optional

from claude_agent_sdk import (
    AssistantMessage,
    UserMessage,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock,
    ThinkingBlock,
)


class AgentLogger:
    """File-based logger for agent interactions"""

    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        log_dir: str = "./agent_logs",
        enabled: bool = True,
        task_id: Optional[str] = None,
    ):
        """
        Initialize agent logger.

        Args:
            agent_id: Unique agent identifier
            agent_name: Human-readable agent name
            log_dir: Base directory for all logs
            enabled: Whether logging is enabled
            task_id: Optional task ID to include in log directory name
        """
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.enabled = enabled
        self.task_id = task_id

        if not self.enabled:
            return

        # Create log directory structure: agent_logs/{task_id}/{agent_id}_{name}_{timestamp}/
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = agent_name.replace(" ", "_").replace("/", "_")

        # Include task_id in directory path if provided
        if task_id:
            task_dir = Path(log_dir) / task_id
            task_dir.mkdir(parents=True, exist_ok=True)
            self.log_subdir = task_dir / f"{agent_id[:8]}_{safe_name}_{timestamp}"
        else:
            self.log_subdir = Path(log_dir) / f"{agent_id[:8]}_{safe_name}_{timestamp}"

        self.log_subdir.mkdir(parents=True, exist_ok=True)

        # File paths
        self.prompt_file = self.log_subdir / "prompt.txt"
        self.text_file = self.log_subdir / "text.txt"
        self.tool_file = self.log_subdir / "tools.jsonl"
        self.summary_file = self.log_subdir / "summary.jsonl"

        self.message_count = 0

    def log_prompt(self, prompt: str) -> None:
        """Log the initial task prompt"""
        if not self.enabled:
            return

        self.prompt_file.write_text(prompt)

    def log_message(self, message: Any) -> None:
        """
        Log a message from the SDK stream.

        Args:
            message: Any message type from claude_agent_sdk
        """
        if not self.enabled:
            return

        self.message_count += 1

        # Handle Assistant or User messages
        if isinstance(message, AssistantMessage) or isinstance(message, UserMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    self._log_text_block(message, block)

                elif isinstance(block, ThinkingBlock):
                    self._log_thinking_block(block)

                elif isinstance(block, ToolUseBlock):
                    self._log_tool_use(block)

                elif isinstance(block, ToolResultBlock):
                    self._log_tool_result(block)

        # Handle system messages
        elif isinstance(message, SystemMessage):
            self._log_system_message(message)

        # Handle result message (final)
        elif isinstance(message, ResultMessage):
            self._log_result_message(message)

    def _log_text_block(self, message: Any, block: TextBlock) -> None:
        """Log text block from assistant/user"""
        with open(self.text_file, "a") as f:
            f.write(f"[{datetime.now().isoformat()}] {type(message).__name__}:\n")
            f.write(f"{block.text}\n\n")

    def _log_thinking_block(self, block: ThinkingBlock) -> None:
        """Log thinking block"""
        with open(self.text_file, "a") as f:
            f.write(f"[{datetime.now().isoformat()}] THINKING:\n")
            f.write(f"{block.thinking}\n\n")

    def _log_tool_use(self, block: ToolUseBlock) -> None:
        """Log tool use call"""
        with open(self.tool_file, "a") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "type": "tool_use",
                    "tool_name": block.name,
                    "tool_use_id": block.id,
                    "input": block.input,
                },
                f,
            )
            f.write("\n")

    def _log_tool_result(self, block: ToolResultBlock) -> None:
        """Log tool result"""
        with open(self.tool_file, "a") as f:
            # Truncate large results
            content = block.content
            if isinstance(content, str) and len(content) > 2000:
                content = content[:2000] + f"... (truncated {len(content) - 2000} chars)"
            elif not isinstance(content, str):
                content = str(content)[:2000]

            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "type": "tool_result",
                    "tool_use_id": block.tool_use_id,
                    "content": content,
                    "is_error": block.is_error,
                },
                f,
            )
            f.write("\n")

    def _log_system_message(self, message: SystemMessage) -> None:
        """Log system message"""
        with open(self.summary_file, "a") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "type": "SystemMessage",
                    "subtype": message.subtype,
                    "message": str(message),
                },
                f,
            )
            f.write("\n")

    def _log_result_message(self, message: ResultMessage) -> None:
        """Log final result message with metrics"""
        with open(self.summary_file, "a") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "type": "ResultMessage",
                    "is_error": message.is_error,
                    "result": message.result,
                    "duration_ms": message.duration_ms,
                    "num_turns": message.num_turns,
                    "session_id": message.session_id,
                    "total_cost_usd": message.total_cost_usd,
                    "usage": message.usage,
                    "total_messages_processed": self.message_count,
                },
                f,
            )
            f.write("\n")

    def get_log_path(self) -> Optional[Path]:
        """Get the log directory path"""
        if not self.enabled:
            return None
        return self.log_subdir
