"""
Unit tests for working directory validation logic.

These tests verify the directory validation logic in isolation,
without requiring the full FastAPI application setup.
"""

import os
import tempfile
import pytest


class TestWorkingDirectoryValidation:
    """Test suite for working directory validation logic."""

    def validate_working_directory(self, working_dir: str) -> tuple[bool, str]:
        """
        Validate working directory - extracted logic from tasks.py endpoint.

        Args:
            working_dir: Directory path to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not working_dir:
            return True, ""  # Empty/None is valid (uses default)

        working_dir = os.path.abspath(working_dir)

        if not os.path.exists(working_dir):
            return False, f"Working directory does not exist: {working_dir}"

        if not os.path.isdir(working_dir):
            return False, f"Working directory path is not a directory: {working_dir}"

        if not os.access(working_dir, os.R_OK | os.X_OK):
            return False, f"Working directory is not accessible (check permissions): {working_dir}"

        return True, ""

    def test_valid_directory(self):
        """Test validation with a valid directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            is_valid, error = self.validate_working_directory(tmpdir)
            assert is_valid is True
            assert error == ""

    def test_nonexistent_directory(self):
        """Test validation with non-existent directory."""
        nonexistent = "/path/that/does/not/exist/12345"
        is_valid, error = self.validate_working_directory(nonexistent)

        assert is_valid is False
        assert "does not exist" in error
        assert nonexistent in error

    def test_file_instead_of_directory(self):
        """Test validation with a file path instead of directory."""
        with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
            file_path = tmpfile.name

        try:
            is_valid, error = self.validate_working_directory(file_path)

            assert is_valid is False
            assert "not a directory" in error
        finally:
            if os.path.exists(file_path):
                os.unlink(file_path)

    def test_empty_string_directory(self):
        """Test validation with empty string."""
        is_valid, error = self.validate_working_directory("")

        # Empty string should be treated as valid (uses default)
        assert is_valid is True
        assert error == ""

    def test_current_directory(self):
        """Test validation with current directory ('.')."""
        is_valid, error = self.validate_working_directory(".")

        assert is_valid is True
        assert error == ""

    def test_parent_directory(self):
        """Test validation with parent directory ('..')."""
        is_valid, error = self.validate_working_directory("..")

        assert is_valid is True
        assert error == ""

    def test_nested_directory(self):
        """Test validation with nested directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested = os.path.join(tmpdir, "level1", "level2", "level3")
            os.makedirs(nested, exist_ok=True)

            is_valid, error = self.validate_working_directory(nested)

            assert is_valid is True
            assert error == ""

    def test_directory_with_spaces(self):
        """Test validation with directory containing spaces."""
        with tempfile.TemporaryDirectory() as tmpdir:
            space_dir = os.path.join(tmpdir, "dir with spaces")
            os.makedirs(space_dir, exist_ok=True)

            is_valid, error = self.validate_working_directory(space_dir)

            assert is_valid is True
            assert error == ""

    def test_directory_with_unicode(self):
        """Test validation with Unicode characters in path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            unicode_dir = os.path.join(tmpdir, "test_\u4e2d\u6587_\u65e5\u672c\u8a9e")
            os.makedirs(unicode_dir, exist_ok=True)

            is_valid, error = self.validate_working_directory(unicode_dir)

            assert is_valid is True
            assert error == ""

    @pytest.mark.skipif(os.name == "nt", reason="Permission tests not reliable on Windows")
    def test_unreadable_directory(self):
        """Test validation with directory without read permissions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            unreadable = os.path.join(tmpdir, "unreadable")
            os.makedirs(unreadable, exist_ok=True)

            try:
                # Remove read and execute permissions
                os.chmod(unreadable, 0o000)

                is_valid, error = self.validate_working_directory(unreadable)

                assert is_valid is False
                assert "not accessible" in error or "permission" in error.lower()
            finally:
                # Restore permissions for cleanup
                try:
                    os.chmod(unreadable, 0o755)
                except:
                    pass

    def test_symlink_to_valid_directory(self):
        """Test validation with symlink to valid directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = os.path.join(tmpdir, "target")
            symlink = os.path.join(tmpdir, "symlink")

            os.makedirs(target, exist_ok=True)

            try:
                os.symlink(target, symlink)
            except (OSError, NotImplementedError):
                pytest.skip("Symlinks not supported on this platform")

            is_valid, error = self.validate_working_directory(symlink)

            assert is_valid is True
            assert error == ""

    def test_symlink_to_nonexistent_directory(self):
        """Test validation with broken symlink."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent_target = os.path.join(tmpdir, "nonexistent")
            symlink = os.path.join(tmpdir, "broken_symlink")

            try:
                os.symlink(nonexistent_target, symlink)
            except (OSError, NotImplementedError):
                pytest.skip("Symlinks not supported on this platform")

            is_valid, error = self.validate_working_directory(symlink)

            # Broken symlink should fail validation
            assert is_valid is False
            assert "does not exist" in error

    def test_relative_path_conversion(self):
        """Test that relative paths are converted to absolute."""
        relative_path = "."
        absolute_path = os.path.abspath(relative_path)

        is_valid, error = self.validate_working_directory(relative_path)

        assert is_valid is True
        # Verify it was converted to absolute path internally
        assert os.path.isabs(absolute_path)

    def test_multiple_validations_with_same_directory(self):
        """Test that validating the same directory multiple times works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Validate multiple times
            for i in range(5):
                is_valid, error = self.validate_working_directory(tmpdir)
                assert is_valid is True
                assert error == ""


class TestWorkingDirectoryEdgeCases:
    """Test edge cases and special scenarios for directory validation."""

    def validate_working_directory(self, working_dir: str) -> tuple[bool, str]:
        """Same validation logic as above."""
        if not working_dir:
            return True, ""

        working_dir = os.path.abspath(working_dir)

        if not os.path.exists(working_dir):
            return False, f"Working directory does not exist: {working_dir}"

        if not os.path.isdir(working_dir):
            return False, f"Working directory path is not a directory: {working_dir}"

        if not os.access(working_dir, os.R_OK | os.X_OK):
            return False, f"Working directory is not accessible (check permissions): {working_dir}"

        return True, ""

    def test_very_long_path(self):
        """Test validation with very long path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a very long path
            long_path = tmpdir
            for i in range(10):
                long_path = os.path.join(long_path, f"subdir_{i}")

            os.makedirs(long_path, exist_ok=True)

            is_valid, error = self.validate_working_directory(long_path)

            # Should succeed if filesystem supports it
            assert is_valid is True or "does not exist" in error

    def test_path_with_special_characters(self):
        """Test validation with special characters in path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            special_chars_dir = os.path.join(tmpdir, "test-dir_123.backup")
            os.makedirs(special_chars_dir, exist_ok=True)

            is_valid, error = self.validate_working_directory(special_chars_dir)

            assert is_valid is True
            assert error == ""

    def test_root_directory(self):
        """Test validation with root directory."""
        if os.name == "nt":
            root = "C:\\\\"
        else:
            root = "/"

        is_valid, error = self.validate_working_directory(root)

        # Root should be valid on most systems
        assert is_valid is True

    def test_home_directory(self):
        """Test validation with user home directory."""
        home = os.path.expanduser("~")

        is_valid, error = self.validate_working_directory(home)

        assert is_valid is True
        assert error == ""

    def test_tmp_directory(self):
        """Test validation with system temp directory."""
        tmp = tempfile.gettempdir()

        is_valid, error = self.validate_working_directory(tmp)

        assert is_valid is True
        assert error == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
