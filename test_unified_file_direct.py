#!/usr/bin/env python3
"""
Direct Test for Unified File Model

Direct test for the unified file model without
importing the entire docanalyzer package.

Author: DocAnalyzer Team
Version: 1.0.0
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import tempfile

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import only the unified file module
sys.path.insert(0, str(project_root / "docanalyzer" / "models"))

# Mock external dependencies
import unittest.mock as mock

# Now import the unified file model
from unified_file import (
    FileStatus,
    FileMetadata,
    UnifiedFile,
    UnifiedFileManager,
    get_unified_file_manager,
    create_unified_file
)


def test_file_status_enum():
    """Test FileStatus enum values."""
    assert FileStatus.NEW.value == "new"
    assert FileStatus.PENDING.value == "pending"
    assert FileStatus.PROCESSING.value == "processing"
    assert FileStatus.COMPLETED.value == "completed"
    assert FileStatus.FAILED.value == "failed"
    assert FileStatus.SKIPPED.value == "skipped"
    assert FileStatus.DELETED.value == "deleted"
    assert FileStatus.ARCHIVED.value == "archived"
    assert FileStatus.ERROR.value == "error"
    print("✅ FileStatus enum test passed")


def test_file_metadata_defaults():
    """Test FileMetadata with default values."""
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
    print("✅ FileMetadata defaults test passed")


def test_file_metadata_custom_values():
    """Test FileMetadata with custom values."""
    metadata = FileMetadata(
        custom_attributes={"author": "John Doe", "version": "1.0"},
        processing_info={"last_processor": "text_processor"},
        system_info={"permissions": "644"},
        tags=["document", "important"],
        categories=["text", "documentation"],
        priority=5,
        checksum="abc123",
        mime_type="text/plain",
        encoding="utf-8"
    )
    
    assert metadata.custom_attributes["author"] == "John Doe"
    assert metadata.processing_info["last_processor"] == "text_processor"
    assert metadata.tags == ["document", "important"]
    assert metadata.categories == ["text", "documentation"]
    assert metadata.priority == 5
    assert metadata.checksum == "abc123"
    assert metadata.mime_type == "text/plain"
    assert metadata.encoding == "utf-8"
    print("✅ FileMetadata custom values test passed")


def test_file_metadata_to_dict():
    """Test FileMetadata to_dict method."""
    metadata = FileMetadata(
        custom_attributes={"author": "John Doe"},
        tags=["document"],
        priority=3
    )
    
    metadata_dict = metadata.to_dict()
    
    assert metadata_dict["custom_attributes"]["author"] == "John Doe"
    assert metadata_dict["tags"] == ["document"]
    assert metadata_dict["priority"] == 3
    assert metadata_dict["checksum"] is None
    print("✅ FileMetadata to_dict test passed")


def test_file_metadata_from_dict():
    """Test FileMetadata from_dict method."""
    data = {
        "custom_attributes": {"author": "Jane Doe"},
        "processing_info": {"processor": "markdown"},
        "tags": ["markdown", "documentation"],
        "priority": 7,
        "checksum": "def456"
    }
    
    metadata = FileMetadata.from_dict(data)
    
    assert metadata.custom_attributes["author"] == "Jane Doe"
    assert metadata.processing_info["processor"] == "markdown"
    assert metadata.tags == ["markdown", "documentation"]
    assert metadata.priority == 7
    assert metadata.checksum == "def456"
    print("✅ FileMetadata from_dict test passed")


def test_unified_file_creation():
    """Test UnifiedFile creation with basic parameters."""
    file_path = "/path/to/document.txt"
    file_size = 1024
    modification_time = datetime.now()
    
    file = UnifiedFile(
        file_path=file_path,
        file_size=file_size,
        modification_time=modification_time
    )
    
    assert file.file_path == file_path
    assert file.file_size == file_size
    assert file.modification_time == modification_time
    assert file.file_name == "document.txt"
    assert file.file_extension == ".txt"
    assert file.is_directory is False
    assert file.status == FileStatus.NEW
    assert file.processing_count == 0
    assert file.chunk_count == 0
    assert file.file_id is not None
    print("✅ UnifiedFile creation test passed")


def test_unified_file_directory():
    """Test UnifiedFile creation for directory."""
    file_path = "/path/to/documents"
    file_size = 0
    modification_time = datetime.now()
    
    file = UnifiedFile(
        file_path=file_path,
        file_size=file_size,
        modification_time=modification_time,
        is_directory=True
    )
    
    assert file.file_path == file_path
    assert file.file_name == "documents"
    assert file.file_extension == ""
    assert file.is_directory is True
    print("✅ UnifiedFile directory test passed")


def test_unified_file_with_metadata():
    """Test UnifiedFile creation with metadata."""
    file_path = "/path/to/document.txt"
    file_size = 1024
    modification_time = datetime.now()
    
    metadata = FileMetadata(
        tags=["important"],
        priority=5,
        mime_type="text/plain"
    )
    
    file = UnifiedFile(
        file_path=file_path,
        file_size=file_size,
        modification_time=modification_time,
        metadata=metadata
    )
    
    assert file.metadata.tags == ["important"]
    assert file.metadata.priority == 5
    assert file.metadata.mime_type == "text/plain"
    print("✅ UnifiedFile with metadata test passed")


def test_unified_file_status_updates():
    """Test UnifiedFile status updates."""
    file = create_unified_file(
        file_path="/path/file.txt",
        file_size=512,
        modification_time=datetime.now()
    )
    
    # Test status update
    file.update_status(FileStatus.PROCESSING)
    assert file.status == FileStatus.PROCESSING
    
    file.update_status(FileStatus.COMPLETED)
    assert file.status == FileStatus.COMPLETED
    print("✅ UnifiedFile status updates test passed")


def test_unified_file_processing_errors():
    """Test UnifiedFile processing error handling."""
    file = create_unified_file(
        file_path="/path/file.txt",
        file_size=512,
        modification_time=datetime.now()
    )
    
    # Add processing error
    file.add_processing_error("File format not supported")
    assert len(file.processing_errors) == 1
    assert "File format not supported" in file.processing_errors
    assert file.status == FileStatus.FAILED
    
    # Add another error
    file.add_processing_error("Processing timeout")
    assert len(file.processing_errors) == 2
    print("✅ UnifiedFile processing errors test passed")


def test_unified_file_mark_processed():
    """Test UnifiedFile mark as processed."""
    file = create_unified_file(
        file_path="/path/file.txt",
        file_size=512,
        modification_time=datetime.now()
    )
    
    # Mark as processed
    file.mark_processed(vector_store_id="vs_123", chunk_count=5)
    
    assert file.status == FileStatus.COMPLETED
    assert file.processing_count == 1
    assert file.last_processed_at is not None
    assert file.vector_store_id == "vs_123"
    assert file.chunk_count == 5
    
    # Check processing info in metadata
    assert file.metadata.processing_info["vector_store_id"] == "vs_123"
    assert file.metadata.processing_info["chunk_count"] == 5
    print("✅ UnifiedFile mark processed test passed")


def test_unified_file_tags_and_categories():
    """Test UnifiedFile tag and category management."""
    file = create_unified_file(
        file_path="/path/file.txt",
        file_size=512,
        modification_time=datetime.now()
    )
    
    # Add tags
    file.add_tag("document")
    file.add_tag("important")
    assert file.metadata.tags == ["document", "important"]
    
    # Remove tag
    file.remove_tag("document")
    assert file.metadata.tags == ["important"]
    
    # Add categories
    file.add_category("text")
    file.add_category("documentation")
    assert file.metadata.categories == ["text", "documentation"]
    
    # Remove category
    file.remove_category("text")
    assert file.metadata.categories == ["documentation"]
    print("✅ UnifiedFile tags and categories test passed")


def test_unified_file_priority():
    """Test UnifiedFile priority management."""
    file = create_unified_file(
        file_path="/path/file.txt",
        file_size=512,
        modification_time=datetime.now()
    )
    
    # Set priority
    file.set_priority(10)
    assert file.metadata.priority == 10
    
    file.set_priority(5)
    assert file.metadata.priority == 5
    print("✅ UnifiedFile priority test passed")


def test_unified_file_to_dict():
    """Test UnifiedFile to_dict method."""
    file = create_unified_file(
        file_path="/path/document.txt",
        file_size=1024,
        modification_time=datetime.now(),
        status=FileStatus.COMPLETED
    )
    
    file.add_tag("important")
    file.set_priority(5)
    
    file_dict = file.to_dict()
    
    assert file_dict["file_path"] == "/path/document.txt"
    assert file_dict["file_name"] == "document.txt"
    assert file_dict["file_size"] == 1024
    assert file_dict["status"] == "completed"
    assert file_dict["metadata"]["tags"] == ["important"]
    assert file_dict["metadata"]["priority"] == 5
    print("✅ UnifiedFile to_dict test passed")


def test_unified_file_from_dict():
    """Test UnifiedFile from_dict method."""
    # Create a file first
    original_file = create_unified_file(
        file_path="/path/test.txt",
        file_size=2048,
        modification_time=datetime.now(),
        status=FileStatus.PROCESSING
    )
    
    original_file.add_tag("test")
    original_file.set_priority(3)
    
    # Convert to dict and back
    file_dict = original_file.to_dict()
    restored_file = UnifiedFile.from_dict(file_dict)
    
    assert restored_file.file_path == original_file.file_path
    assert restored_file.file_name == original_file.file_name
    assert restored_file.file_size == original_file.file_size
    assert restored_file.status == original_file.status
    assert restored_file.metadata.tags == original_file.metadata.tags
    assert restored_file.metadata.priority == original_file.metadata.priority
    print("✅ UnifiedFile from_dict test passed")


def test_unified_file_summaries():
    """Test UnifiedFile summary methods."""
    file = create_unified_file(
        file_path="/path/summary.txt",
        file_size=1024,
        modification_time=datetime.now(),
        status=FileStatus.COMPLETED
    )
    
    file.add_tag("summary")
    file.add_category("test")
    file.set_priority(8)
    file.mark_processed(vector_store_id="vs_456", chunk_count=3)
    
    # Test file info summary
    file_info = file.get_file_info_summary()
    assert file_info["file_name"] == "summary.txt"
    assert file_info["tags"] == ["summary"]
    assert file_info["priority"] == 8
    
    # Test processing summary
    processing_summary = file.get_processing_summary()
    assert processing_summary["status"] == "completed"
    assert processing_summary["processing_count"] == 1
    assert processing_summary["chunk_count"] == 3
    assert processing_summary["vector_store_id"] == "vs_456"
    print("✅ UnifiedFile summaries test passed")


def test_unified_file_manager():
    """Test UnifiedFileManager functionality."""
    manager = UnifiedFileManager()
    
    # Test global manager
    global_manager = get_unified_file_manager()
    assert global_manager is not None
    assert isinstance(global_manager, UnifiedFileManager)
    print("✅ UnifiedFileManager test passed")


def test_create_unified_file_function():
    """Test create_unified_file convenience function."""
    file_path = "/path/convenience.txt"
    file_size = 512
    modification_time = datetime.now()
    
    file = create_unified_file(
        file_path=file_path,
        file_size=file_size,
        modification_time=modification_time,
        status=FileStatus.PENDING
    )
    
    assert file.file_path == file_path
    assert file.file_size == file_size
    assert file.modification_time == modification_time
    assert file.status == FileStatus.PENDING
    print("✅ create_unified_file function test passed")


def test_unified_file_validation():
    """Test UnifiedFile validation."""
    file = create_unified_file(
        file_path="/path/validation.txt",
        file_size=1024,
        modification_time=datetime.now()
    )
    
    # Test modification check
    assert file.is_modified_since_last_processing() is True
    
    # Mark as processed
    file.mark_processed()
    assert file.is_modified_since_last_processing() is False
    
    # Update modification time
    file.modification_time = datetime.now()
    assert file.is_modified_since_last_processing() is True
    print("✅ UnifiedFile validation test passed")


def main():
    """Run all tests."""
    print("🧪 Running Unified File Model Tests")
    print("=" * 50)
    
    try:
        test_file_status_enum()
        test_file_metadata_defaults()
        test_file_metadata_custom_values()
        test_file_metadata_to_dict()
        test_file_metadata_from_dict()
        test_unified_file_creation()
        test_unified_file_directory()
        test_unified_file_with_metadata()
        test_unified_file_status_updates()
        test_unified_file_processing_errors()
        test_unified_file_mark_processed()
        test_unified_file_tags_and_categories()
        test_unified_file_priority()
        test_unified_file_to_dict()
        test_unified_file_from_dict()
        test_unified_file_summaries()
        test_unified_file_manager()
        test_create_unified_file_function()
        test_unified_file_validation()
        
        print("=" * 50)
        print("🎉 All unified file model tests passed successfully!")
        return 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main()) 