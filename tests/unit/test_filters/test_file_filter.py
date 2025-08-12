"""
Tests for File Filter System

Comprehensive test suite for file filtering functionality.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from docanalyzer.filters.file_filter import FileFilter, FileFilterResult, SupportedFileTypes
from docanalyzer.models.file_system import FileInfo


def create_test_file_info(path: str, size: int = 1024, extension: str = ".txt") -> FileInfo:
    """Helper function to create test FileInfo instances."""
    # Create a mock FileInfo for testing
    file_info = Mock(spec=FileInfo)
    file_info.file_path = path
    file_info.file_size = size
    file_info.file_extension = extension.lstrip('.')
    file_info.file_name = Path(path).name
    file_info.is_directory = False
    file_info.processing_status = "pending"
    file_info.metadata = {"extension": extension}
    # Add extension attribute for backward compatibility
    file_info.extension = extension
    return file_info


class TestFileFilterResult:
    """Test suite for FileFilterResult class."""
    
    def test_init_valid_parameters(self):
        """Test initialization with valid parameters."""
        result = FileFilterResult(
            should_process=True,
            reason="Test reason",
            filter_name="test_filter",
            metadata={"key": "value"}
        )
        
        assert result.should_process is True
        assert result.reason == "Test reason"
        assert result.filter_name == "test_filter"
        assert result.metadata == {"key": "value"}
    
    def test_init_without_metadata(self):
        """Test initialization without metadata."""
        result = FileFilterResult(
            should_process=False,
            reason="Test reason",
            filter_name="test_filter"
        )
        
        assert result.should_process is False
        assert result.metadata == {}
    
    def test_init_invalid_should_process(self):
        """Test initialization with invalid should_process."""
        with pytest.raises(ValueError, match="should_process must be boolean"):
            FileFilterResult(
                should_process="not_bool",
                reason="Test reason",
                filter_name="test_filter"
            )
    
    def test_init_empty_reason(self):
        """Test initialization with empty reason."""
        with pytest.raises(ValueError, match="reason must be non-empty string"):
            FileFilterResult(
                should_process=True,
                reason="",
                filter_name="test_filter"
            )
    
    def test_init_empty_filter_name(self):
        """Test initialization with empty filter name."""
        with pytest.raises(ValueError, match="filter_name must be non-empty string"):
            FileFilterResult(
                should_process=True,
                reason="Test reason",
                filter_name=""
            )
    
    def test_init_invalid_metadata_type(self):
        """Test initialization with invalid metadata type."""
        with pytest.raises(TypeError, match="metadata must be dictionary or None"):
            FileFilterResult(
                should_process=True,
                reason="Test reason",
                filter_name="test_filter",
                metadata="not_dict"
            )
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = FileFilterResult(
            should_process=True,
            reason="Test reason",
            filter_name="test_filter",
            metadata={"key": "value"}
        )
        
        data = result.to_dict()
        assert data["should_process"] is True
        assert data["reason"] == "Test reason"
        assert data["filter_name"] == "test_filter"
        assert data["metadata"] == {"key": "value"}
    
    def test_str_representation(self):
        """Test string representation."""
        result = FileFilterResult(
            should_process=True,
            reason="Test reason",
            filter_name="test_filter"
        )
        
        str_repr = str(result)
        assert "FilterResult" in str_repr
        assert "should_process=True" in str_repr
        assert "reason='Test reason'" in str_repr
        assert "filter='test_filter'" in str_repr


class TestFileFilter:
    """Test suite for FileFilter class."""
    
    @pytest.fixture
    def file_filter(self):
        """Create FileFilter instance for testing."""
        return FileFilter(
            supported_extensions={".txt", ".md", ".py"},
            max_file_size=1024 * 1024,  # 1MB
            min_file_size=100,  # 100 bytes
            exclude_patterns=["*.tmp", "*.log"],
            include_patterns=["*.txt", "*.md"]
        )
    
    def test_init_valid_parameters(self, file_filter):
        """Test initialization with valid parameters."""
        assert file_filter.supported_extensions == {".txt", ".md", ".py"}
        assert file_filter.max_file_size == 1024 * 1024
        assert file_filter.min_file_size == 100
        assert file_filter.exclude_patterns == ["*.tmp", "*.log"]
        assert file_filter.include_patterns == ["*.txt", "*.md"]
    
    def test_init_default_parameters(self):
        """Test initialization with default parameters."""
        filter_instance = FileFilter()
        
        assert filter_instance.supported_extensions == set()
        assert filter_instance.max_file_size == 10 * 1024 * 1024  # 10MB
        assert filter_instance.min_file_size == 0
        assert filter_instance.exclude_patterns == []
        assert filter_instance.include_patterns == []
    
    def test_init_invalid_max_file_size(self):
        """Test initialization with invalid max file size."""
        with pytest.raises(ValueError, match="max_file_size must be positive"):
            FileFilter(max_file_size=0)
    
    def test_init_invalid_min_file_size(self):
        """Test initialization with negative min file size."""
        with pytest.raises(ValueError, match="min_file_size must be non-negative"):
            FileFilter(min_file_size=-1)
    
    def test_init_min_greater_than_max(self):
        """Test initialization with min greater than max file size."""
        with pytest.raises(ValueError, match="min_file_size cannot be greater than max_file_size"):
            FileFilter(min_file_size=1000, max_file_size=500)
    
    def test_init_invalid_supported_extensions_type(self):
        """Test initialization with invalid supported extensions type."""
        with pytest.raises(TypeError, match="supported_extensions must be set or None"):
            FileFilter(supported_extensions=["not", "a", "set"])
    
    def test_init_invalid_exclude_patterns_type(self):
        """Test initialization with invalid exclude patterns type."""
        with pytest.raises(TypeError, match="exclude_patterns must be list or None"):
            FileFilter(exclude_patterns="not_a_list")
    
    def test_init_invalid_include_patterns_type(self):
        """Test initialization with invalid include patterns type."""
        with pytest.raises(TypeError, match="include_patterns must be list or None"):
            FileFilter(include_patterns="not_a_list")
    
    def test_filter_file_success(self, file_filter):
        """Test successful file filtering."""
        file_info = create_test_file_info("/test/file.txt", 1024, ".txt")
        
        result = file_filter.filter_file(file_info)
        
        assert result.should_process is True
        assert "passes all filters" in result.reason
        assert result.filter_name == "file_filter"
    
    def test_filter_file_none_file_info(self, file_filter):
        """Test filtering with None file info."""
        with pytest.raises(ValueError, match="file_info cannot be None"):
            file_filter.filter_file(None)
    
    def test_filter_file_invalid_file_info_type(self, file_filter):
        """Test filtering with invalid file info type."""
        with pytest.raises(ValueError, match="file_info must be FileInfo instance"):
            file_filter.filter_file("not_file_info")
    
    def test_filter_file_unsupported_extension(self, file_filter):
        """Test filtering file with unsupported extension."""
        file_info = create_test_file_info("/test/file.doc", 1024, ".doc")
        
        result = file_filter.filter_file(file_info)
        
        assert result.should_process is False
        assert "not supported" in result.reason
        assert result.filter_name == "extension_filter"
    
    def test_filter_file_size_too_small(self, file_filter):
        """Test filtering file that is too small."""
        file_info = create_test_file_info("/test/file.txt", 50, ".txt")  # Below min_file_size of 100
        
        result = file_filter.filter_file(file_info)
        
        assert result.should_process is False
        assert "below minimum" in result.reason
        assert result.filter_name == "size_filter"
    
    def test_filter_file_size_too_large(self, file_filter):
        """Test filtering file that is too large."""
        file_info = create_test_file_info("/test/file.txt", 2 * 1024 * 1024, ".txt")  # Above max_file_size of 1MB
        
        result = file_filter.filter_file(file_info)
        
        assert result.should_process is False
        assert "exceeds maximum" in result.reason
        assert result.filter_name == "size_filter"
    
    def test_filter_file_excluded_pattern(self, file_filter):
        """Test filtering file that matches exclude pattern."""
        # Create a file with supported extension but excluded pattern
        file_info = create_test_file_info("/test/file.txt.tmp", 1024, ".txt")
        
        result = file_filter.filter_file(file_info)
        
        assert result.should_process is False
        assert "exclude pattern" in result.reason
        assert result.filter_name == "pattern_filter"
    
    def test_filter_files_success(self, file_filter):
        """Test filtering multiple files successfully."""
        file_infos = [
            create_test_file_info("/test/file1.txt", 1024, ".txt"),
            create_test_file_info("/test/file2.md", 2048, ".md")
        ]
        
        results = file_filter.filter_files(file_infos)
        
        assert len(results) == 2
        assert all(result.should_process for result in results)
    
    def test_filter_files_none_list(self, file_filter):
        """Test filtering with None file list."""
        with pytest.raises(ValueError, match="file_infos cannot be None"):
            file_filter.filter_files(None)
    
    def test_filter_files_invalid_list_type(self, file_filter):
        """Test filtering with invalid list type."""
        with pytest.raises(ValueError, match="file_infos must be list"):
            file_filter.filter_files("not_a_list")
    
    def test_filter_files_with_errors(self, file_filter):
        """Test filtering files with some errors."""
        file_infos = [
            create_test_file_info("/test/file1.txt", 1024, ".txt"),
            "invalid_file_info"  # This will cause an error
        ]
        
        results = file_filter.filter_files(file_infos)
        
        assert len(results) == 2
        assert results[0].should_process is True
        assert results[1].should_process is False
        assert "Filtering error" in results[1].reason
    
    def test_check_extension_supported(self, file_filter):
        """Test extension check with supported extension."""
        file_info = create_test_file_info("/test/file.txt", 1024, ".txt")
        
        result = file_filter._check_extension(file_info)
        
        assert result.should_process is True
        assert "is supported" in result.reason
        assert result.filter_name == "extension_filter"
    
    def test_check_extension_unsupported(self, file_filter):
        """Test extension check with unsupported extension."""
        file_info = create_test_file_info("/test/file.doc", 1024, ".doc")
        
        result = file_filter._check_extension(file_info)
        
        assert result.should_process is False
        assert "not supported" in result.reason
        assert result.filter_name == "extension_filter"
    
    def test_check_extension_no_restrictions(self):
        """Test extension check with no restrictions."""
        filter_instance = FileFilter()  # No extension restrictions
        file_info = create_test_file_info("/test/file.txt", 1024, ".txt")
        
        result = filter_instance._check_extension(file_info)
        
        assert result.should_process is True
        assert "No extension restrictions" in result.reason
    
    def test_check_size_within_range(self, file_filter):
        """Test size check with file within range."""
        file_info = create_test_file_info("/test/file.txt", 1024, ".txt")
        
        result = file_filter._check_size(file_info)
        
        assert result.should_process is True
        assert "within acceptable range" in result.reason
        assert result.filter_name == "size_filter"
    
    def test_check_size_too_small(self, file_filter):
        """Test size check with file too small."""
        file_info = create_test_file_info("/test/file.txt", 50, ".txt")  # Below min_file_size of 100
        
        result = file_filter._check_size(file_info)
        
        assert result.should_process is False
        assert "below minimum" in result.reason
        assert result.filter_name == "size_filter"
    
    def test_check_size_too_large(self, file_filter):
        """Test size check with file too large."""
        file_info = create_test_file_info("/test/file.txt", 2 * 1024 * 1024, ".txt")  # Above max_file_size of 1MB
        
        result = file_filter._check_size(file_info)
        
        assert result.should_process is False
        assert "exceeds maximum" in result.reason
        assert result.filter_name == "size_filter"
    
    def test_check_patterns_excluded(self, file_filter):
        """Test pattern check with excluded file."""
        file_info = create_test_file_info("/test/file.tmp", 1024, ".tmp")
        
        result = file_filter._check_patterns(file_info)
        
        assert result.should_process is False
        assert "exclude pattern" in result.reason
        assert result.filter_name == "pattern_filter"
    
    def test_check_patterns_included(self, file_filter):
        """Test pattern check with included file."""
        file_info = create_test_file_info("/test/file.txt", 1024, ".txt")
        
        result = file_filter._check_patterns(file_info)
        
        assert result.should_process is True
        assert "include pattern" in result.reason
        assert result.filter_name == "pattern_filter"
    
    def test_check_patterns_no_restrictions(self):
        """Test pattern check with no restrictions."""
        filter_instance = FileFilter()  # No pattern restrictions
        file_info = create_test_file_info("/test/file.txt", 1024, ".txt")
        
        result = filter_instance._check_patterns(file_info)
        
        assert result.should_process is True
        assert "No pattern restrictions" in result.reason
    
    def test_get_supported_extensions(self, file_filter):
        """Test getting supported extensions."""
        extensions = file_filter.get_supported_extensions()
        
        assert extensions == {".txt", ".md", ".py"}
        # Ensure it's a copy, not the original
        assert extensions is not file_filter.supported_extensions
    
    def test_add_supported_extension(self):
        """Test adding supported extension."""
        filter_instance = FileFilter()
        
        filter_instance.add_supported_extension(".py")
        
        assert ".py" in filter_instance.supported_extensions
    
    def test_add_supported_extension_invalid_type(self):
        """Test adding extension with invalid type."""
        filter_instance = FileFilter()
        
        with pytest.raises(TypeError, match="extension must be string"):
            filter_instance.add_supported_extension(123)
    
    def test_add_supported_extension_empty(self):
        """Test adding empty extension."""
        filter_instance = FileFilter()
        
        with pytest.raises(ValueError, match="extension cannot be empty"):
            filter_instance.add_supported_extension("")
    
    def test_remove_supported_extension(self, file_filter):
        """Test removing supported extension."""
        file_filter.remove_supported_extension(".txt")
        
        assert ".txt" not in file_filter.supported_extensions
        assert ".md" in file_filter.supported_extensions  # Others remain
    
    def test_remove_supported_extension_invalid_type(self):
        """Test removing extension with invalid type."""
        filter_instance = FileFilter()
        
        with pytest.raises(TypeError, match="extension must be string"):
            filter_instance.remove_supported_extension(123)
    
    def test_remove_supported_extension_empty(self):
        """Test removing empty extension."""
        filter_instance = FileFilter()
        
        with pytest.raises(ValueError, match="extension cannot be empty"):
            filter_instance.remove_supported_extension("")


class TestSupportedFileTypes:
    """Test suite for SupportedFileTypes enum."""
    
    def test_enum_values(self):
        """Test that all expected file types are present."""
        expected_types = [
            "text", "markdown", "python", "javascript", "typescript",
            "json", "yaml", "xml", "html", "css", "sql", "shell", "config"
        ]
        
        for expected_type in expected_types:
            assert hasattr(SupportedFileTypes, expected_type.upper())
    
    def test_enum_value_access(self):
        """Test accessing enum values."""
        assert SupportedFileTypes.TEXT.value == "text"
        assert SupportedFileTypes.MARKDOWN.value == "markdown"
        assert SupportedFileTypes.PYTHON.value == "python" 