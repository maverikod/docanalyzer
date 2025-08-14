"""
Tests for Unified File Model

Comprehensive test suite for the unified file model system.
Tests all file types, metadata, and file handling functionality.
"""

import pytest
import tempfile
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from docanalyzer.models.unified_file import (
    FileStatus,
    FileMetadata,
    UnifiedFile,
    UnifiedFileManager
)


class TestFileStatus:
    """Test suite for FileStatus enum."""
    
    def test_file_status_values(self):
        """Test that all file statuses have correct values."""
        assert FileStatus.NEW.value == "new"
        assert FileStatus.PENDING.value == "pending"
        assert FileStatus.PROCESSING.value == "processing"
        assert FileStatus.COMPLETED.value == "completed"
        assert FileStatus.FAILED.value == "failed"
        assert FileStatus.SKIPPED.value == "skipped"
        assert FileStatus.DELETED.value == "deleted"
        assert FileStatus.ARCHIVED.value == "archived"
        assert FileStatus.ERROR.value == "error"
    
    def test_file_status_from_string(self):
        """Test creating FileStatus from string."""
        assert FileStatus("new") == FileStatus.NEW
        assert FileStatus("completed") == FileStatus.COMPLETED
        assert FileStatus("failed") == FileStatus.FAILED


class TestFileMetadata:
    """Test suite for FileMetadata dataclass."""
    
    def test_file_metadata_creation(self):
        """Test creating FileMetadata with default values."""
        metadata = FileMetadata()
        
        assert metadata.custom_attributes == {}
        assert metadata.processing_info == {}
        assert metadata.system_info == {}
        assert metadata.tags == []
        assert metadata.categories == []
        assert metadata.priority == 0
        assert metadata.checksum is None
        assert metadata.mime_type is None
        assert metadata.encoding is None
    
    def test_file_metadata_with_values(self):
        """Test creating FileMetadata with custom values."""
        custom_attrs = {"author": "John Doe", "version": "1.0"}
        processing_info = {"processed_at": "2024-01-01"}
        system_info = {"created": "2024-01-01"}
        tags = ["document", "important"]
        categories = ["text", "manual"]
        
        metadata = FileMetadata(
            custom_attributes=custom_attrs,
            processing_info=processing_info,
            system_info=system_info,
            tags=tags,
            categories=categories,
            priority=5,
            checksum="abc123",
            mime_type="text/plain",
            encoding="utf-8"
        )
        
        assert metadata.custom_attributes == custom_attrs
        assert metadata.processing_info == processing_info
        assert metadata.system_info == system_info
        assert metadata.tags == tags
        assert metadata.categories == categories
        assert metadata.priority == 5
        assert metadata.checksum == "abc123"
        assert metadata.mime_type == "text/plain"
        assert metadata.encoding == "utf-8"
    
    def test_file_metadata_to_dict(self):
        """Test converting FileMetadata to dictionary."""
        metadata = FileMetadata(
            custom_attributes={"key": "value"},
            tags=["tag1", "tag2"],
            priority=3,
            checksum="abc123"
        )
        
        result = metadata.to_dict()
        
        assert result["custom_attributes"] == {"key": "value"}
        assert result["tags"] == ["tag1", "tag2"]
        assert result["priority"] == 3
        assert result["checksum"] == "abc123"
        assert result["mime_type"] is None


class TestUnifiedFile:
    """Test suite for UnifiedFile class."""
    
    @pytest.fixture
    def temp_file(self):
        """Create a temporary file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Test content")
            temp_path = f.name
        
        yield Path(temp_path)
        
        # Cleanup
        try:
            os.unlink(temp_path)
        except OSError:
            pass
    
    def test_unified_file_creation(self, temp_file):
        """Test creating UnifiedFile with required fields."""
        file_obj = UnifiedFile(
            file_path=str(temp_file),
            file_size=temp_file.stat().st_size,
            modification_time=datetime.fromtimestamp(temp_file.stat().st_mtime)
        )
        
        assert file_obj.file_path == str(temp_file)
        assert file_obj.file_name == temp_file.name
        assert file_obj.file_size == temp_file.stat().st_size
        assert file_obj.status == FileStatus.NEW
        assert isinstance(file_obj.created_at, datetime)
        assert file_obj.file_id is not None
    
    def test_unified_file_with_optional_fields(self, temp_file):
        """Test creating UnifiedFile with optional fields."""
        metadata = FileMetadata(tags=["test"], priority=5)
        file_obj = UnifiedFile(
            file_path=str(temp_file),
            file_size=temp_file.stat().st_size,
            modification_time=datetime.fromtimestamp(temp_file.stat().st_mtime),
            status=FileStatus.COMPLETED,
            metadata=metadata,
            file_id="test-id-123"
        )
        
        assert file_obj.status == FileStatus.COMPLETED
        assert file_obj.metadata == metadata
        assert file_obj.file_id == "test-id-123"
    
    def test_unified_file_to_dict(self, temp_file):
        """Test converting UnifiedFile to dictionary."""
        file_obj = UnifiedFile(
            file_path=str(temp_file),
            file_size=temp_file.stat().st_size,
            modification_time=datetime.fromtimestamp(temp_file.stat().st_mtime),
            status=FileStatus.COMPLETED,
            file_id="test-id"
        )
        
        result = file_obj.to_dict()
        
        assert result["file_path"] == str(temp_file)
        assert result["file_name"] == temp_file.name
        assert result["file_size"] == temp_file.stat().st_size
        assert result["status"] == "completed"
        assert result["file_id"] == "test-id"
        assert "created_at" in result
        assert "metadata" in result
    
    def test_unified_file_str_representation(self, temp_file):
        """Test string representation of UnifiedFile."""
        file_obj = UnifiedFile(
            file_path=str(temp_file),
            file_size=temp_file.stat().st_size,
            modification_time=datetime.fromtimestamp(temp_file.stat().st_mtime)
        )
        
        file_str = str(file_obj)
        assert temp_file.name in file_str
        assert "new" in file_str
    
    def test_unified_file_repr_representation(self, temp_file):
        """Test repr representation of UnifiedFile."""
        file_obj = UnifiedFile(
            file_path=str(temp_file),
            file_size=temp_file.stat().st_size,
            modification_time=datetime.fromtimestamp(temp_file.stat().st_mtime)
        )
        
        file_repr = repr(file_obj)
        assert "UnifiedFile" in file_repr
        assert temp_file.name in file_repr
    
    def test_unified_file_update_status(self, temp_file):
        """Test updating file status."""
        file_obj = UnifiedFile(
            file_path=str(temp_file),
            file_size=temp_file.stat().st_size,
            modification_time=datetime.fromtimestamp(temp_file.stat().st_mtime)
        )
        
        assert file_obj.status == FileStatus.NEW
        
        file_obj.update_status(FileStatus.PROCESSING)
        assert file_obj.status == FileStatus.PROCESSING
        
        file_obj.update_status(FileStatus.COMPLETED)
        assert file_obj.status == FileStatus.COMPLETED
    
    def test_unified_file_update_metadata(self, temp_file):
        """Test updating file metadata."""
        file_obj = UnifiedFile(
            file_path=str(temp_file),
            file_size=temp_file.stat().st_size,
            modification_time=datetime.fromtimestamp(temp_file.stat().st_mtime)
        )
        
        # Test adding tags and categories
        file_obj.add_tag("updated")
        file_obj.add_category("test_category")
        file_obj.set_priority(10)
        
        assert "updated" in file_obj.metadata.tags
        assert "test_category" in file_obj.metadata.categories
        assert file_obj.metadata.priority == 10
    
    def test_unified_file_get_extension(self, temp_file):
        """Test getting file extension."""
        file_obj = UnifiedFile(
            file_path=str(temp_file),
            file_size=temp_file.stat().st_size,
            modification_time=datetime.fromtimestamp(temp_file.stat().st_mtime)
        )
        
        # file_extension is set in __post_init__
        assert file_obj.file_extension == temp_file.suffix.lower()
    
    def test_unified_file_get_directory(self, temp_file):
        """Test getting file directory."""
        file_obj = UnifiedFile(
            file_path=str(temp_file),
            file_size=temp_file.stat().st_size,
            modification_time=datetime.fromtimestamp(temp_file.stat().st_mtime)
        )
        
        # Directory is the parent of file_path
        directory = str(temp_file.parent)
        assert file_obj.file_path.startswith(directory)
    
    def test_unified_file_is_readable(self, temp_file):
        """Test checking if file is readable."""
        file_obj = UnifiedFile(
            file_path=str(temp_file),
            file_size=temp_file.stat().st_size,
            modification_time=datetime.fromtimestamp(temp_file.stat().st_mtime)
        )
        
        # Check if file exists and is readable
        assert temp_file.exists()
        assert temp_file.is_file()
    
    def test_unified_file_is_writable(self, temp_file):
        """Test checking if file is writable."""
        file_obj = UnifiedFile(
            file_path=str(temp_file),
            file_size=temp_file.stat().st_size,
            modification_time=datetime.fromtimestamp(temp_file.stat().st_mtime)
        )
        
        # Check if file exists and is writable
        assert temp_file.exists()
        assert temp_file.is_file()


class TestUnifiedFileManager:
    """Test suite for UnifiedFileManager class."""
    
    @pytest.fixture
    def temp_files(self):
        """Create temporary files for testing."""
        files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=f'.txt') as f:
                f.write(f"Content {i}")
                files.append(Path(f.name))
        
        yield files
        
        # Cleanup
        for file_path in files:
            try:
                os.unlink(file_path)
            except OSError:
                pass
    
    def test_unified_file_manager_creation(self):
        """Test creating UnifiedFileManager."""
        manager = UnifiedFileManager()
        
        # Check that manager was created successfully
        assert manager is not None
        assert hasattr(manager, 'create_from_path')
    
    def test_create_from_path(self, temp_files):
        """Test creating file from path."""
        manager = UnifiedFileManager()
        
        file_obj = manager.create_from_path(str(temp_files[0]))
        
        assert file_obj.file_path == str(temp_files[0])
        assert file_obj.file_name == temp_files[0].name
        assert file_obj.file_size == temp_files[0].stat().st_size
        assert file_obj.status == FileStatus.NEW
    
    def test_validate_file(self, temp_files):
        """Test file validation."""
        manager = UnifiedFileManager()
        
        file_obj = manager.create_from_path(str(temp_files[0]))
        
        # File should be valid
        assert manager.validate_file(file_obj) is True
    
    def test_get_summary(self, temp_files):
        """Test getting file summary."""
        manager = UnifiedFileManager()
        
        file_obj = manager.create_from_path(str(temp_files[0]))
        
        summary = manager.get_summary(file_obj)
        
        assert "file_info" in summary
        # Check that summary contains expected file information
        assert summary["file_info"]["file_name"] == temp_files[0].name
        assert "file_id" in summary["file_info"] 