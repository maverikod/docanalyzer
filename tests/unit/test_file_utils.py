"""
Tests for File Utilities

Comprehensive test suite for file system utility functions.

Author: DocAnalyzer Team
Version: 1.0.0
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime

from docanalyzer.utils.file_utils import (
    is_directory,
    is_file,
    is_readable,
    is_writable,
    get_file_metadata,
    safe_create_directory,
    safe_remove_file,
    get_file_size,
    get_file_modified_time,
    normalize_path,
    ensure_directory_exists,
)


class TestFileUtils:
    """Test suite for file utility functions."""
    
    @pytest.fixture
    def test_directory(self, tmp_path):
        """Create test directory."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        return str(test_dir)
    
    @pytest.fixture
    def test_file(self, tmp_path):
        """Create test file."""
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("test content")
        return str(test_file)
    
    def test_is_directory_true(self, test_directory):
        """Test is_directory with valid directory."""
        # Act
        result = is_directory(test_directory)
        
        # Assert
        assert result is True
    
    def test_is_directory_false(self, test_file):
        """Test is_directory with file."""
        # Act
        result = is_directory(test_file)
        
        # Assert
        assert result is False
    
    def test_is_directory_not_exists(self):
        """Test is_directory with non-existent path."""
        # Act
        result = is_directory("/nonexistent/path")
        
        # Assert
        assert result is False
    
    @patch('os.path.isdir')
    def test_is_directory_os_error(self, mock_isdir):
        """Test is_directory with OSError."""
        # Arrange
        mock_isdir.side_effect = OSError("Permission denied")
        
        # Act & Assert
        with pytest.raises(OSError):
            is_directory("/test/path")
    
    def test_is_file_true(self, test_file):
        """Test is_file with valid file."""
        # Act
        result = is_file(test_file)
        
        # Assert
        assert result is True
    
    def test_is_file_false(self, test_directory):
        """Test is_file with directory."""
        # Act
        result = is_file(test_directory)
        
        # Assert
        assert result is False
    
    def test_is_file_not_exists(self):
        """Test is_file with non-existent path."""
        # Act
        result = is_file("/nonexistent/file.txt")
        
        # Assert
        assert result is False
    
    @patch('os.path.isfile')
    def test_is_file_os_error(self, mock_isfile):
        """Test is_file with OSError."""
        # Arrange
        mock_isfile.side_effect = OSError("Permission denied")
        
        # Act & Assert
        with pytest.raises(OSError):
            is_file("/test/path")
    
    def test_is_readable_true(self, test_file):
        """Test is_readable with readable file."""
        # Act
        result = is_readable(test_file)
        
        # Assert
        assert result is True
    
    def test_is_readable_false(self, tmp_path):
        """Test is_readable with non-readable file."""
        # Arrange
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("test content")
        test_file.chmod(0o000)  # No permissions
        
        try:
            # Act
            result = is_readable(str(test_file))
            
            # Assert
            assert result is False
        finally:
            # Restore permissions for cleanup
            test_file.chmod(0o644)
    
    @patch('os.access')
    def test_is_readable_os_error(self, mock_access):
        """Test is_readable with OSError."""
        # Arrange
        mock_access.side_effect = OSError("Permission denied")
        
        # Act & Assert
        with pytest.raises(OSError):
            is_readable("/test/path")
    
    def test_is_writable_true(self, test_file):
        """Test is_writable with writable file."""
        # Act
        result = is_writable(test_file)
        
        # Assert
        assert result is True
    
    def test_is_writable_false(self, tmp_path):
        """Test is_writable with non-writable file."""
        # Arrange
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("test content")
        test_file.chmod(0o444)  # Read-only
        
        try:
            # Act
            result = is_writable(str(test_file))
            
            # Assert
            assert result is False
        finally:
            # Restore permissions for cleanup
            test_file.chmod(0o644)
    
    @patch('os.access')
    def test_is_writable_os_error(self, mock_access):
        """Test is_writable with OSError."""
        # Arrange
        mock_access.side_effect = OSError("Permission denied")
        
        # Act & Assert
        with pytest.raises(OSError):
            is_writable("/test/path")
    
    def test_get_file_metadata_success(self, test_file):
        """Test successful file metadata retrieval."""
        # Act
        metadata = get_file_metadata(test_file)
        
        # Assert
        assert "size" in metadata
        assert "modified_time" in metadata
        assert "created_time" in metadata
        assert "permissions" in metadata
        assert "owner" in metadata
        assert "group" in metadata
        assert metadata["size"] > 0
        assert isinstance(metadata["modified_time"], datetime)
        assert isinstance(metadata["created_time"], datetime)
    
    def test_get_file_metadata_file_not_found(self):
        """Test file metadata with non-existent file."""
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            get_file_metadata("/nonexistent/file.txt")
    
    def test_get_file_metadata_permission_denied(self, tmp_path):
        """Test file metadata with permission denied."""
        # Arrange
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("test content")
        test_file.chmod(0o000)  # No permissions
        
        try:
            # Act - should work but return numeric owner/group
            metadata = get_file_metadata(str(test_file))
            
            # Assert
            assert "size" in metadata
            assert "owner" in metadata
            assert "group" in metadata
            # Owner and group should be present (either string names or numeric)
            assert isinstance(metadata["owner"], str)
            assert isinstance(metadata["group"], str)
        finally:
            # Restore permissions for cleanup
            try:
                test_file.chmod(0o644)
            except FileNotFoundError:
                pass  # File might have been removed
    
    @patch('os.stat')
    def test_get_file_metadata_os_error(self, mock_stat):
        """Test file metadata with OSError."""
        # Arrange
        mock_stat.side_effect = OSError("File system error")
        
        # Act & Assert
        with pytest.raises(OSError):
            get_file_metadata("/test/path")
    
    @patch('os.stat')
    def test_get_file_metadata_os_error_logging(self, mock_stat):
        """Test file metadata with OSError to cover logging."""
        # Arrange
        mock_stat.side_effect = OSError(13, "Permission denied")
        
        # Act & Assert
        with pytest.raises(OSError):
            get_file_metadata("/test/path")
    
    @patch('pwd.getpwuid')
    def test_get_file_metadata_import_error(self, mock_getpwuid, test_file):
        """Test file metadata with ImportError (pwd module not available)."""
        # Arrange
        mock_getpwuid.side_effect = ImportError("No module named 'pwd'")
        
        # Act
        metadata = get_file_metadata(test_file)
        
        # Assert
        assert "owner" in metadata
        assert "group" in metadata
        # Should fall back to numeric owner/group
        assert metadata["owner"].isdigit()
        assert metadata["group"].isdigit()
    
    @patch('pwd.getpwuid')
    def test_get_file_metadata_key_error(self, mock_getpwuid, test_file):
        """Test file metadata with KeyError (user/group not found)."""
        # Arrange
        mock_getpwuid.side_effect = KeyError("User not found")
        
        # Act
        metadata = get_file_metadata(test_file)
        
        # Assert
        assert "owner" in metadata
        assert "group" in metadata
        # Should fall back to numeric owner/group
        assert metadata["owner"].isdigit()
        assert metadata["group"].isdigit()
    
    def test_safe_create_directory_success(self, tmp_path):
        """Test successful directory creation."""
        # Arrange
        new_dir = tmp_path / "new_directory"
        
        # Act
        result = safe_create_directory(str(new_dir))
        
        # Assert
        assert result is True
        assert new_dir.exists()
        assert new_dir.is_dir()
    
    def test_safe_create_directory_already_exists(self, test_directory):
        """Test directory creation when directory already exists."""
        # Act
        result = safe_create_directory(test_directory)
        
        # Assert
        assert result is True
    
    def test_safe_create_directory_permission_denied(self):
        """Test directory creation with permission denied."""
        # Act & Assert
        with pytest.raises(PermissionError):
            safe_create_directory("/root/test_directory")
    
    @patch('pathlib.Path.mkdir')
    def test_safe_create_directory_os_error(self, mock_mkdir):
        """Test directory creation with OSError."""
        # Arrange
        mock_mkdir.side_effect = OSError("File system error")
        
        # Act & Assert
        with pytest.raises(OSError):
            safe_create_directory("/test/path")
    
    def test_safe_remove_file_success(self, test_file):
        """Test successful file removal."""
        # Act
        result = safe_remove_file(test_file)
        
        # Assert
        assert result is True
        assert not Path(test_file).exists()
    
    def test_safe_remove_file_not_exists(self):
        """Test file removal when file doesn't exist."""
        # Act
        result = safe_remove_file("/nonexistent/file.txt")
        
        # Assert
        assert result is True
    
    def test_safe_remove_file_permission_denied(self, tmp_path):
        """Test file removal with permission denied."""
        # Arrange
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("test content")
        test_file.chmod(0o444)  # Read-only
        
        try:
            # Act - should work even with read-only permissions
            result = safe_remove_file(str(test_file))
            
            # Assert
            assert result is True
            assert not test_file.exists()
        finally:
            # Restore permissions for cleanup
            try:
                test_file.chmod(0o644)
            except FileNotFoundError:
                pass  # File might have been removed
    
    @patch('pathlib.Path.unlink')
    @patch('pathlib.Path.exists')
    def test_safe_remove_file_os_error(self, mock_exists, mock_unlink):
        """Test file removal with OSError."""
        # Arrange
        mock_exists.return_value = True  # File exists
        mock_unlink.side_effect = OSError("File system error")
        
        # Act & Assert
        with pytest.raises(OSError):
            safe_remove_file("/test/path")
    
    @patch('pathlib.Path.unlink')
    @patch('pathlib.Path.exists')
    def test_safe_remove_file_os_error_logging(self, mock_exists, mock_unlink):
        """Test file removal with OSError to cover logging."""
        # Arrange
        mock_exists.return_value = True  # File exists
        mock_unlink.side_effect = OSError(13, "Permission denied")
        
        # Act & Assert
        with pytest.raises(OSError):
            safe_remove_file("/test/path")
    
    def test_get_file_size_success(self, test_file):
        """Test successful file size retrieval."""
        # Act
        size = get_file_size(test_file)
        
        # Assert
        assert size > 0
        assert size == len("test content")
    
    def test_get_file_size_file_not_found(self):
        """Test file size with non-existent file."""
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            get_file_size("/nonexistent/file.txt")
    
    def test_get_file_size_permission_denied(self, tmp_path):
        """Test file size with permission denied."""
        # Arrange
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("test content")
        test_file.chmod(0o000)  # No permissions
        
        try:
            # Act - should work even with no permissions
            size = get_file_size(str(test_file))
            
            # Assert
            assert size > 0
            assert size == len("test content")
        finally:
            # Restore permissions for cleanup
            try:
                test_file.chmod(0o644)
            except FileNotFoundError:
                pass  # File might have been removed
    
    @patch('os.path.getsize')
    def test_get_file_size_os_error(self, mock_getsize):
        """Test file size with OSError."""
        # Arrange
        mock_getsize.side_effect = OSError("File system error")
        
        # Act & Assert
        with pytest.raises(OSError):
            get_file_size("/test/path")
    
    @patch('os.path.getsize')
    def test_get_file_size_os_error_logging(self, mock_getsize):
        """Test file size with OSError to cover logging."""
        # Arrange
        mock_getsize.side_effect = OSError(13, "Permission denied")
        
        # Act & Assert
        with pytest.raises(OSError):
            get_file_size("/test/path")
    
    def test_get_file_modified_time_success(self, test_file):
        """Test successful file modified time retrieval."""
        # Act
        modified_time = get_file_modified_time(test_file)
        
        # Assert
        assert isinstance(modified_time, datetime)
        assert modified_time <= datetime.now()
    
    def test_get_file_modified_time_file_not_found(self):
        """Test file modified time with non-existent file."""
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            get_file_modified_time("/nonexistent/file.txt")
    
    def test_get_file_modified_time_permission_denied(self, tmp_path):
        """Test file modified time with permission denied."""
        # Arrange
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("test content")
        test_file.chmod(0o000)  # No permissions
        
        try:
            # Act - should work even with no permissions
            modified_time = get_file_modified_time(str(test_file))
            
            # Assert
            assert isinstance(modified_time, datetime)
            assert modified_time <= datetime.now()
        finally:
            # Restore permissions for cleanup
            try:
                test_file.chmod(0o644)
            except FileNotFoundError:
                pass  # File might have been removed
    
    @patch('os.stat')
    def test_get_file_modified_time_os_error(self, mock_stat):
        """Test file modified time with OSError."""
        # Arrange
        mock_stat.side_effect = OSError("File system error")
        
        # Act & Assert
        with pytest.raises(OSError):
            get_file_modified_time("/test/path")
    
    @patch('os.stat')
    def test_get_file_modified_time_os_error_logging(self, mock_stat):
        """Test file modified time with OSError to cover logging."""
        # Arrange
        mock_stat.side_effect = OSError(13, "Permission denied")
        
        # Act & Assert
        with pytest.raises(OSError):
            get_file_modified_time("/test/path")
    
    def test_normalize_path_success(self, test_file):
        """Test successful path normalization."""
        # Act
        normalized = normalize_path(test_file)
        
        # Assert
        assert isinstance(normalized, str)
        assert normalized == str(Path(test_file).resolve())
    
    def test_normalize_path_relative(self, tmp_path):
        """Test path normalization with relative path."""
        # Arrange
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("test content")
        relative_path = "test_file.txt"
        
        # Act
        normalized = normalize_path(str(tmp_path / relative_path))
        
        # Assert
        assert isinstance(normalized, str)
        assert normalized == str(test_file.resolve())
    
    def test_normalize_path_not_exists(self):
        """Test path normalization with non-existent path."""
        # Act - should work even for non-existent paths
        result = normalize_path("/nonexistent/path/that/does/not/exist")
        
        # Assert
        assert isinstance(result, str)
        assert result == "/nonexistent/path/that/does/not/exist"
    
    @patch('pathlib.Path.resolve')
    def test_normalize_path_os_error(self, mock_resolve):
        """Test path normalization with OSError."""
        # Arrange
        mock_resolve.side_effect = OSError("Path resolution error")
        
        # Act & Assert
        with pytest.raises(OSError):
            normalize_path("/test/path")
    
    def test_ensure_directory_exists_success(self, tmp_path):
        """Test successful directory existence check."""
        # Arrange
        new_dir = tmp_path / "new_directory"
        
        # Act
        ensure_directory_exists(str(new_dir))
        
        # Assert
        assert new_dir.exists()
        assert new_dir.is_dir()
    
    def test_ensure_directory_exists_already_exists(self, test_directory):
        """Test directory existence check when directory already exists."""
        # Act & Assert (should not raise exception)
        ensure_directory_exists(test_directory)
    
    def test_ensure_directory_exists_permission_denied(self):
        """Test directory existence check with permission denied."""
        # Act & Assert
        with pytest.raises(PermissionError):
            ensure_directory_exists("/root/test_directory")
    
    @patch('pathlib.Path.mkdir')
    def test_ensure_directory_exists_os_error(self, mock_mkdir):
        """Test directory existence check with OSError."""
        # Arrange
        mock_mkdir.side_effect = OSError("File system error")
        
        # Act & Assert
        with pytest.raises(OSError):
            ensure_directory_exists("/test/path") 