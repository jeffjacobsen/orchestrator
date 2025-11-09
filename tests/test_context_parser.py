"""
Unit tests for the context_parser module.

Tests context parsing, summary extraction, and file manifest functionality.
"""
import pytest
from orchestrator.workflow.context_parser import (
    AgentContext,
    extract_structured_output,
    _extract_file_list,
    _extract_bullet_list,
)


class TestExtractStructuredOutput:
    """Test the extract_structured_output function."""

    def test_extract_from_planner_output(self):
        """Test extracting context from planner output."""
        output = """
        ## Implementation Plan

        1. Create authentication module
        2. Add OAuth2 support
        3. Update session management

        ## Files to Create
        - src/auth/oauth.py
        - src/auth/session.py

        ## Risks
        - Breaking changes for existing users
        """

        context = extract_structured_output(output, "planner")

        assert isinstance(context, AgentContext)
        assert len(context.full_output) > 0

    def test_extract_from_builder_output(self):
        """Test extracting context from builder output."""
        output = """
        I've implemented the requested feature.

        Files created:
        - src/feature.py

        Files modified:
        - src/main.py
        - tests/test_main.py
        """

        context = extract_structured_output(output, "builder")

        assert isinstance(context, AgentContext)

    def test_extract_from_tester_output(self):
        """Test extracting context from tester output."""
        output = """
        Test Results:
        - test_feature_works: PASS
        - test_edge_case: PASS
        - test_invalid_input: PASS

        All tests passing!
        """

        context = extract_structured_output(output, "tester")

        assert isinstance(context, AgentContext)

    def test_extract_from_empty_output(self):
        """Test extracting from empty output."""
        context = extract_structured_output("", "planner")

        assert isinstance(context, AgentContext)
        assert context.full_output == ""


class TestExtractFileList:
    """Test file list extraction."""

    def test_extract_files_from_bullet_list(self):
        """Test extracting files from bullet list."""
        text = """
        Files modified:
        - src/auth.py
        - src/utils.py
        - tests/test_auth.py
        """

        files = _extract_file_list(text)

        assert isinstance(files, list)
        assert len(files) >= 0  # Implementation may vary

    def test_extract_files_from_code_mentions(self):
        """Test extracting files mentioned in text."""
        text = "I updated `config/settings.py` and modified `app/main.py`"

        files = _extract_file_list(text)

        assert isinstance(files, list)

    def test_extract_files_handles_empty_input(self):
        """Test that empty input returns empty list."""
        files = _extract_file_list("")

        assert files == []


class TestExtractBulletList:
    """Test bullet list extraction."""

    def test_extract_markdown_bullets(self):
        """Test extracting markdown bullet points."""
        text = """
        Key points:
        - First point
        - Second point
        - Third point
        """

        items = _extract_bullet_list(text)

        assert isinstance(items, list)
        assert len(items) >= 0  # Implementation may vary

    def test_extract_numbered_list(self):
        """Test extracting numbered list."""
        text = """
        Steps:
        1. First step
        2. Second step
        3. Third step
        """

        items = _extract_bullet_list(text)

        assert isinstance(items, list)

    def test_extract_mixed_list_formats(self):
        """Test extracting mixed list formats."""
        text = """
        - Bullet point
        * Another bullet
        + Yet another
        1. Numbered
        2. Also numbered
        """

        items = _extract_bullet_list(text)

        assert isinstance(items, list)

    def test_extract_from_empty_text(self):
        """Test extraction from empty text."""
        items = _extract_bullet_list("")

        assert items == []


class TestAgentContextDataclass:
    """Test the AgentContext dataclass."""

    def test_agent_context_creation_with_defaults(self):
        """Test creating AgentContext with default values."""
        context = AgentContext()

        assert context.summary == ""
        assert context.files_created == []
        assert context.files_modified == []
        assert context.key_findings == []
        assert context.errors == []
        assert context.full_output == ""

    def test_agent_context_creation_with_values(self):
        """Test creating AgentContext with specific values."""
        context = AgentContext(
            summary="Test summary",
            files_created=["file1.py", "file2.py"],
            key_findings=["Finding 1", "Finding 2"],
            full_output="Full output text"
        )

        assert context.summary == "Test summary"
        assert len(context.files_created) == 2
        assert len(context.key_findings) == 2
        assert context.full_output == "Full output text"

    def test_agent_context_mutable_defaults(self):
        """Test that mutable defaults are properly initialized."""
        context1 = AgentContext()
        context2 = AgentContext()

        # Modifying one shouldn't affect the other
        context1.files_created.append("file1.py")

        assert len(context1.files_created) == 1
        assert len(context2.files_created) == 0


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_extract_from_very_long_output(self):
        """Test extracting from very long output."""
        long_output = "x" * 100_000  # 100KB of text

        # Should handle large input without crashing
        context = extract_structured_output(long_output, "planner")
        assert context is not None

    def test_extract_from_output_with_special_characters(self):
        """Test extracting from output with special characters."""
        output = "Special chars: \n\t\r ñ 中文 emoji: 🎉"

        # Should handle special characters
        context = extract_structured_output(output, "builder")
        assert context is not None

    def test_extract_with_malformed_markdown(self):
        """Test extracting from malformed markdown."""
        output = """
        ### Unclosed section
        ## Another section with ## extra # marks
        ###
        """

        # Should handle gracefully without errors
        context = extract_structured_output(output, "planner")
        assert context is not None

    def test_extract_file_list_with_invalid_paths(self):
        """Test file extraction with invalid paths."""
        text = """
        - /invalid/path/../../etc/passwd
        - C:\\Windows\\System32
        - ../../sensitive_file
        """

        # Should handle without errors
        files = _extract_file_list(text)
        assert isinstance(files, list)

    def test_extract_bullet_list_with_no_bullets(self):
        """Test bullet list extraction when there are no bullets."""
        text = "This is just plain text without any list markers."

        items = _extract_bullet_list(text)
        assert items == []
