"""Structured logging for the orchestrator system."""

import logging
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pathlib import Path


class StructuredLogger:
    """
    Structured logger for agent operations.

    Logs are structured JSON for easy parsing and analysis.
    """

    def __init__(
        self,
        log_file: Optional[Path] = None,
        level: int = logging.INFO,
    ) -> None:
        self.logger = logging.getLogger("orchestrator")
        self.logger.setLevel(level)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        self.logger.addHandler(console_handler)

        # File handler if specified
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            self.logger.addHandler(file_handler)

    def log(
        self,
        level: str,
        event: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """
        Log a structured event.

        Args:
            level: Log level (info, warning, error, etc.)
            event: Event name/type
            data: Additional structured data
            **kwargs: Additional fields
        """
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            **(data or {}),
            **kwargs,
        }

        log_message = json.dumps(log_entry)

        if level == "debug":
            self.logger.debug(log_message)
        elif level == "info":
            self.logger.info(log_message)
        elif level == "warning":
            self.logger.warning(log_message)
        elif level == "error":
            self.logger.error(log_message)
        elif level == "critical":
            self.logger.critical(log_message)

    def info(self, event: str, **kwargs: Any) -> None:
        """Log info level event."""
        self.log("info", event, **kwargs)

    def warning(self, event: str, **kwargs: Any) -> None:
        """Log warning level event."""
        self.log("warning", event, **kwargs)

    def error(self, event: str, **kwargs: Any) -> None:
        """Log error level event."""
        self.log("error", event, **kwargs)

    def debug(self, event: str, **kwargs: Any) -> None:
        """Log debug level event."""
        self.log("debug", event, **kwargs)
