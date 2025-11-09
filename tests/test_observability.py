"""
Unit tests for observability modules.

Tests logging, metrics collection, and monitoring functionality.
"""
import pytest
from orchestrator.observability.logger import StructuredLogger
from orchestrator.observability.metrics import MetricsCollector
from orchestrator.core.types import AgentMetrics


class TestStructuredLogger:
    """Test the StructuredLogger class."""

    def test_logger_initialization(self):
        """Test that logger can be initialized."""
        logger = StructuredLogger()
        assert logger is not None

    def test_logger_with_log_file(self, tmp_path):
        """Test logger initialization with log file."""
        log_file = tmp_path / "test.log"
        logger = StructuredLogger(log_file=log_file)
        assert logger is not None

    def test_logger_info_method_exists(self):
        """Test that logger has info method."""
        logger = StructuredLogger()
        assert hasattr(logger, "info")
        assert callable(logger.info)

    def test_logger_error_method_exists(self):
        """Test that logger has error method."""
        logger = StructuredLogger()
        assert hasattr(logger, "error")
        assert callable(logger.error)

    def test_logger_can_log_without_error(self):
        """Test that logging doesn't raise errors."""
        logger = StructuredLogger()
        # Should not raise an exception
        logger.info("test_event", key="value")
        logger.error("test_error", error="test")


class TestMetricsCollector:
    """Test the MetricsCollector class."""

    def test_metrics_collector_initialization(self):
        """Test that metrics collector can be initialized."""
        collector = MetricsCollector()
        assert collector is not None

    def test_record_agent_metrics_exists(self):
        """Test that record_agent_metrics method exists."""
        collector = MetricsCollector()
        assert hasattr(collector, "record_agent_metrics")
        assert callable(collector.record_agent_metrics)

    def test_get_summary_returns_dict(self):
        """Test that get_summary returns a dictionary."""
        collector = MetricsCollector()
        summary = collector.get_summary()
        assert isinstance(summary, dict)

    def test_record_and_retrieve_metrics(self):
        """Test recording and retrieving metrics."""
        collector = MetricsCollector()

        metrics = AgentMetrics(
            agent_id="test_agent",
            total_tokens=100,
            input_tokens=60,
            output_tokens=40,
            total_cost=0.001,
        )

        collector.record_agent_metrics(metrics)
        summary = collector.get_summary()

        # Summary should reflect recorded metrics
        assert isinstance(summary, dict)

    def test_multiple_metrics_recording(self):
        """Test recording metrics for multiple agents."""
        collector = MetricsCollector()

        metrics1 = AgentMetrics(
            agent_id="agent1",
            total_tokens=100,
            input_tokens=60,
            output_tokens=40,
            total_cost=0.001,
        )

        metrics2 = AgentMetrics(
            agent_id="agent2",
            total_tokens=200,
            input_tokens=120,
            output_tokens=80,
            total_cost=0.002,
        )

        collector.record_agent_metrics(metrics1)
        collector.record_agent_metrics(metrics2)

        summary = collector.get_summary()
        assert isinstance(summary, dict)


class TestAgentMetrics:
    """Test the AgentMetrics dataclass."""

    def test_agent_metrics_creation(self):
        """Test creating AgentMetrics instance."""
        metrics = AgentMetrics(
            agent_id="test_agent",
            total_tokens=100,
            input_tokens=60,
            output_tokens=40,
            total_cost=0.001,
        )

        assert metrics.agent_id == "test_agent"
        assert metrics.total_tokens == 100
        assert metrics.input_tokens == 60
        assert metrics.output_tokens == 40
        assert metrics.total_cost == 0.001

    def test_agent_metrics_with_all_fields(self):
        """Test creating AgentMetrics with all fields."""
        metrics = AgentMetrics(
            agent_id="test_agent",
            total_tokens=1000,
            input_tokens=600,
            output_tokens=400,
            cache_creation_input_tokens=100,
            cache_read_input_tokens=200,
            total_cost=0.01,
            tool_calls=5,
            files_read=["file1.py", "file2.py", "file3.py"],
            files_written=["output1.py", "output2.py"],
            execution_time_seconds=10.5,
        )

        assert metrics.tool_calls == 5
        assert len(metrics.files_read) == 3
        assert len(metrics.files_written) == 2
        assert metrics.execution_time_seconds == 10.5

    def test_agent_metrics_defaults(self):
        """Test AgentMetrics default values."""
        metrics = AgentMetrics(agent_id="test")

        assert metrics.total_tokens == 0
        assert metrics.input_tokens == 0
        assert metrics.output_tokens == 0
        assert metrics.total_cost == 0.0
        assert metrics.tool_calls == 0
        assert metrics.files_read == []
        assert metrics.files_written == []
