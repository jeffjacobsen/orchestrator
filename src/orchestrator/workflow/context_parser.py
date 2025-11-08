"""
Context parsing utilities for extracting structured information from agent outputs.

This module provides functions to parse agent outputs and extract:
- Structured summaries
- File manifests (created/modified files)
- Key findings and recommendations
- Error messages and test results
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class AgentContext:
    """Structured context extracted from an agent's output."""

    # Core summary (concise, for passing to next agent)
    summary: str = ""

    # File manifests
    files_created: List[str] = None
    files_modified: List[str] = None

    # Key information
    key_findings: List[str] = None
    recommendations: str = ""

    # Test-specific
    test_results: Optional[Dict[str, any]] = None  # pass/fail, errors

    # Error handling
    errors: List[str] = None
    requires_fix: bool = False

    # Full output (for rollback/debugging)
    full_output: str = ""

    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.files_created is None:
            self.files_created = []
        if self.files_modified is None:
            self.files_modified = []
        if self.key_findings is None:
            self.key_findings = []
        if self.errors is None:
            self.errors = []

    def get_forward_context(self) -> str:
        """
        Get minimal context to pass to the next agent in sequence.

        This is the concise summary that subsequent agents need,
        not the full output which wastes tokens.
        """
        context_parts = []

        if self.summary:
            context_parts.append(f"## Previous Agent Summary\n{self.summary}")

        if self.files_created:
            context_parts.append(f"\n## Files Created\n" + "\n".join(f"- {f}" for f in self.files_created))

        if self.files_modified:
            context_parts.append(f"\n## Files Modified\n" + "\n".join(f"- {f}" for f in self.files_modified))

        if self.key_findings:
            context_parts.append(f"\n## Key Findings\n" + "\n".join(f"- {f}" for f in self.key_findings))

        if self.recommendations:
            context_parts.append(f"\n## Recommendations\n{self.recommendations}")

        return "\n".join(context_parts)

    def get_error_context(self) -> str:
        """
        Get detailed error context for rollback/fixing.

        When tests fail or review finds issues, this provides
        the full details needed to fix the problem.
        """
        context_parts = [f"## Previous Agent Summary\n{self.summary}"]

        if self.errors:
            context_parts.append(f"\n## Errors Found\n" + "\n".join(f"- {e}" for e in self.errors))

        if self.test_results:
            context_parts.append(f"\n## Test Results\n{self._format_test_results()}")

        # Include relevant portions of full output for debugging
        if self.full_output and self.requires_fix:
            context_parts.append(f"\n## Additional Details\n{self.full_output[:1000]}")

        return "\n".join(context_parts)

    def _format_test_results(self) -> str:
        """Format test results for readability."""
        if not self.test_results:
            return "No test results available"

        parts = []
        if "passed" in self.test_results:
            parts.append(f"Passed: {self.test_results['passed']}")
        if "failed" in self.test_results:
            parts.append(f"Failed: {self.test_results['failed']}")
        if "failures" in self.test_results:
            parts.append(f"\nFailure Details:\n{self.test_results['failures']}")

        return "\n".join(parts)


def extract_structured_output(agent_output: str, agent_role: str) -> AgentContext:
    """
    Extract structured information from an agent's output.

    Parses the markdown-formatted summary section that agents are
    instructed to include at the end of their output.

    Args:
        agent_output: Full text output from the agent
        agent_role: Role of the agent (for role-specific parsing)

    Returns:
        AgentContext with extracted information
    """
    context = AgentContext(full_output=agent_output)

    # Extract summary section
    summary_match = re.search(r'## Summary\s*\n(.*?)(?=\n##|\Z)', agent_output, re.DOTALL)
    if summary_match:
        context.summary = summary_match.group(1).strip()

    # Extract files created
    files_created_match = re.search(
        r'## (?:Files Created|Documentation Files Created|Test Files Created)\s*\n(.*?)(?=\n##|\Z)',
        agent_output,
        re.DOTALL
    )
    if files_created_match:
        files_text = files_created_match.group(1)
        context.files_created = _extract_file_list(files_text)

    # Extract files modified
    files_modified_match = re.search(r'## Files Modified\s*\n(.*?)(?=\n##|\Z)', agent_output, re.DOTALL)
    if files_modified_match:
        files_text = files_modified_match.group(1)
        context.files_modified = _extract_file_list(files_text)

    # Extract key findings
    findings_match = re.search(r'## Key Findings\s*\n(.*?)(?=\n##|\Z)', agent_output, re.DOTALL)
    if findings_match:
        findings_text = findings_match.group(1)
        context.key_findings = _extract_bullet_list(findings_text)

    # Extract recommendations
    rec_match = re.search(
        r'## (?:Recommendations for Next Agent|For Next Agent)\s*\n(.*?)(?=\n##|\Z)',
        agent_output,
        re.DOTALL
    )
    if rec_match:
        context.recommendations = rec_match.group(1).strip()

    # Role-specific extraction
    if agent_role == "TESTER":
        context.test_results = _extract_test_results(agent_output)
        context.requires_fix = _has_test_failures(context.test_results)
        if context.requires_fix:
            context.errors = _extract_test_errors(agent_output)

    elif agent_role == "REVIEWER":
        context.requires_fix = _has_review_issues(agent_output)
        if context.requires_fix:
            context.errors = _extract_review_issues(agent_output)

    return context


def _extract_file_list(text: str) -> List[str]:
    """Extract file paths from markdown list."""
    files = []
    for line in text.split('\n'):
        line = line.strip()
        if line.startswith('- '):
            file_path = line[2:].strip()
            if file_path:
                files.append(file_path)
    return files


def _extract_bullet_list(text: str) -> List[str]:
    """Extract bullet points from markdown list."""
    items = []
    for line in text.split('\n'):
        line = line.strip()
        if line.startswith('- '):
            item = line[2:].strip()
            if item:
                items.append(item)
    return items


def _extract_test_results(output: str) -> Optional[Dict[str, any]]:
    """Extract test results from TESTER output."""
    results = {}

    # Look for pytest-style output
    passed_match = re.search(r'(\d+) passed', output)
    if passed_match:
        results['passed'] = int(passed_match.group(1))

    failed_match = re.search(r'(\d+) failed', output)
    if failed_match:
        results['failed'] = int(failed_match.group(1))

    # Extract failure details
    failures_match = re.search(r'FAILED.*?(?=\n(?:PASSED|=====|$))', output, re.DOTALL)
    if failures_match:
        results['failures'] = failures_match.group(0)

    return results if results else None


def _has_test_failures(test_results: Optional[Dict]) -> bool:
    """Check if test results indicate failures."""
    if not test_results:
        return False
    return test_results.get('failed', 0) > 0


def _extract_test_errors(output: str) -> List[str]:
    """Extract specific error messages from test failures."""
    errors = []

    # Look for assertion errors or exceptions
    error_patterns = [
        r'AssertionError: (.*?)(?=\n|$)',
        r'Error: (.*?)(?=\n|$)',
        r'Exception: (.*?)(?=\n|$)',
    ]

    for pattern in error_patterns:
        matches = re.findall(pattern, output)
        errors.extend(matches)

    return errors[:5]  # Limit to top 5 errors


def _has_review_issues(output: str) -> bool:
    """Check if reviewer found issues."""
    # Look for negative indicators
    indicators = [
        'does not meet',
        'missing',
        'issues found',
        'problems',
        'incorrect',
        'needs revision',
    ]
    output_lower = output.lower()
    return any(ind in output_lower for ind in indicators)


def _extract_review_issues(output: str) -> List[str]:
    """Extract specific issues from REVIEWER output."""
    issues = []

    # Look for "Issues" section
    issues_match = re.search(r'## Issues\s*\n(.*?)(?=\n##|\Z)', output, re.DOTALL)
    if issues_match:
        issues = _extract_bullet_list(issues_match.group(1))

    return issues
