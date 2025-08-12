"""
Tests for Processing Models

Comprehensive test suite for processing models including ProcessingStatus,
ProcessingBlock, and FileProcessingResult classes.

Author: DocAnalyzer Team
Version: 1.0.0
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from docanalyzer.models.processing import (
    ProcessingStatus, ProcessingBlock, FileProcessingResult
)


class TestProcessingStatus:
    """Test suite for ProcessingStatus enum."""
    
    def test_processing_status_values(self):
        """Test that ProcessingStatus has expected values."""
        assert ProcessingStatus.PENDING.value == "pending"
        assert ProcessingStatus.PROCESSING.value == "processing"
        assert ProcessingStatus.COMPLETED.value == "completed"
        assert ProcessingStatus.FAILED.value == "failed"
        assert ProcessingStatus.SKIPPED.value == "skipped"
        assert ProcessingStatus.CANCELLED.value == "cancelled"


class TestProcessingBlock:
    """Test suite for ProcessingBlock class."""
    
    @pytest.fixture
    def processing_block(self):
        """Create ProcessingBlock instance for testing."""
        return ProcessingBlock(
            content="Hello world",
            block_type="paragraph",
            start_line=1,
            end_line=1,
            start_char=0,
            end_char=11
        )
    
    def test_processing_block_creation_success(self):
        """Test successful ProcessingBlock creation."""
        # Act
        block = ProcessingBlock(
            content="Hello world",
            block_type="paragraph",
            start_line=1,
            end_line=1,
            start_char=0,
            end_char=11
        )
        
        # Assert
        assert block.content == "Hello world"
        assert block.block_type == "paragraph"
        assert block.start_line == 1
        assert block.end_line == 1
        assert block.start_char == 0
        assert block.end_char == 11
        assert block.processing_status == ProcessingStatus.PENDING
        assert block.metadata == {}
        assert block.block_id is not None
        assert block.created_at is not None
        assert block.modified_at is not None
    
    def test_processing_block_creation_with_optional_params(self):
        """Test ProcessingBlock creation with optional parameters."""
        # Arrange
        created_at = datetime.now()
        modified_at = datetime.now()
        metadata = {"language": "en", "sentiment": "positive"}
        
        # Act
        block = ProcessingBlock(
            content="Hello world",
            block_type="paragraph",
            start_line=1,
            end_line=1,
            start_char=0,
            end_char=11,
            block_id="test_id",
            metadata=metadata,
            processing_status=ProcessingStatus.COMPLETED,
            created_at=created_at,
            modified_at=modified_at
        )
        
        # Assert
        assert block.block_id == "test_id"
        assert block.metadata == metadata
        assert block.processing_status == ProcessingStatus.COMPLETED
        assert block.created_at == created_at
        assert block.modified_at == modified_at
    
    def test_processing_block_creation_empty_content(self):
        """Test ProcessingBlock creation with empty content."""
        # Act & Assert
        with pytest.raises(ValueError, match="content must be non-empty string"):
            ProcessingBlock("", "paragraph", 1, 1, 0, 11)
    
    def test_processing_block_creation_empty_type(self):
        """Test ProcessingBlock creation with empty block type."""
        # Act & Assert
        with pytest.raises(ValueError, match="block_type must be non-empty string"):
            ProcessingBlock("Hello", "", 1, 1, 0, 11)
    
    def test_processing_block_creation_invalid_line_numbers(self):
        """Test ProcessingBlock creation with invalid line numbers."""
        # Act & Assert
        with pytest.raises(ValueError, match="start_line must be positive integer"):
            ProcessingBlock("Hello", "paragraph", 0, 1, 0, 11)
        
        with pytest.raises(ValueError, match="end_line must be >= start_line"):
            ProcessingBlock("Hello", "paragraph", 2, 1, 0, 11)
    
    def test_processing_block_creation_invalid_char_positions(self):
        """Test ProcessingBlock creation with invalid character positions."""
        # Act & Assert
        with pytest.raises(ValueError, match="start_char must be non-negative integer"):
            ProcessingBlock("Hello", "paragraph", 1, 1, -1, 11)
        
        with pytest.raises(ValueError, match="end_char must be >= start_char"):
            ProcessingBlock("Hello", "paragraph", 1, 1, 5, 3)
    
    def test_processing_block_creation_invalid_status(self):
        """Test ProcessingBlock creation with invalid processing status."""
        # Act & Assert
        with pytest.raises(ValueError, match="processing_status must be ProcessingStatus enum value"):
            ProcessingBlock(
                "Hello", "paragraph", 1, 1, 0, 11,
                processing_status="invalid_status"
            )
    
    def test_content_length_property(self, processing_block):
        """Test content_length property."""
        # Act
        length = processing_block.content_length
        
        # Assert
        assert length == 11  # "Hello world" has 11 characters
    
    def test_line_count_property(self, processing_block):
        """Test line_count property."""
        # Act
        count = processing_block.line_count
        
        # Assert
        assert count == 1  # Single line
    
    def test_line_count_multiple_lines(self):
        """Test line_count property with multiple lines."""
        # Arrange
        block = ProcessingBlock(
            content="Hello\nworld",
            block_type="paragraph",
            start_line=1,
            end_line=2,
            start_char=0,
            end_char=11
        )
        
        # Act
        count = block.line_count
        
        # Assert
        assert count == 2  # Two lines
    
    def test_update_content(self, processing_block):
        """Test update_content method."""
        # Act
        processing_block.update_content("Updated content")
        
        # Assert
        assert processing_block.content == "Updated content"
        assert processing_block.content_length == 15  # "Updated content" has 15 characters
        assert processing_block.modified_at > processing_block.created_at
    
    def test_update_content_empty(self, processing_block):
        """Test update_content with empty content."""
        # Act & Assert
        with pytest.raises(ValueError, match="new_content must be non-empty string"):
            processing_block.update_content("")
    
    def test_update_content_invalid_type(self, processing_block):
        """Test update_content with invalid type."""
        # Act & Assert
        with pytest.raises(TypeError, match="new_content must be string"):
            processing_block.update_content(123)
    
    def test_update_metadata(self, processing_block):
        """Test update_metadata method."""
        # Arrange
        new_metadata = {"language": "en", "sentiment": "positive"}
        
        # Act
        processing_block.update_metadata(new_metadata)
        
        # Assert
        assert processing_block.metadata == new_metadata
        assert processing_block.modified_at > processing_block.created_at
    
    def test_update_metadata_invalid_type(self, processing_block):
        """Test update_metadata with invalid type."""
        # Act & Assert
        with pytest.raises(TypeError, match="new_metadata must be dictionary"):
            processing_block.update_metadata("not a dict")
    
    def test_to_dict(self, processing_block):
        """Test to_dict method."""
        # Act
        data = processing_block.to_dict()
        
        # Assert
        assert data["content"] == "Hello world"
        assert data["block_type"] == "paragraph"
        assert data["start_line"] == 1
        assert data["end_line"] == 1
        assert data["start_char"] == 0
        assert data["end_char"] == 11
        assert data["processing_status"] == "pending"
        assert data["metadata"] == {}
        assert "block_id" in data
        assert "created_at" in data
        assert "modified_at" in data
    
    def test_from_dict(self, processing_block):
        """Test from_dict method."""
        # Arrange
        data = processing_block.to_dict()
        
        # Act
        new_block = ProcessingBlock.from_dict(data)
        
        # Assert
        assert new_block.content == processing_block.content
        assert new_block.block_type == processing_block.block_type
        assert new_block.start_line == processing_block.start_line
        assert new_block.end_line == processing_block.end_line
    
    def test_from_dict_missing_required_fields(self):
        """Test from_dict method with missing required fields."""
        # Arrange
        data = {"content": "Hello"}  # Missing other required fields
        
        # Act & Assert
        with pytest.raises(ValueError, match="Missing required field"):
            ProcessingBlock.from_dict(data)
    
    def test_equality(self, processing_block):
        """Test equality comparison."""
        # Arrange
        same_block = ProcessingBlock(
            content=processing_block.content,
            block_type=processing_block.block_type,
            start_line=processing_block.start_line,
            end_line=processing_block.end_line,
            start_char=processing_block.start_char,
            end_char=processing_block.end_char
        )
        
        # Act & Assert
        assert processing_block == same_block
    
    def test_inequality(self, processing_block):
        """Test inequality comparison."""
        # Arrange
        different_block = ProcessingBlock(
            content="Different content",
            block_type=processing_block.block_type,
            start_line=processing_block.start_line,
            end_line=processing_block.end_line,
            start_char=processing_block.start_char,
            end_char=processing_block.end_char
        )
        
        # Act & Assert
        assert processing_block != different_block
    
    def test_equality_different_type(self, processing_block):
        """Test equality with different type."""
        # Act & Assert
        assert processing_block != "not a ProcessingBlock"
    
    def test_repr(self, processing_block):
        """Test string representation."""
        # Act
        repr_str = repr(processing_block)
        
        # Assert
        assert "ProcessingBlock" in repr_str
        assert processing_block.block_type in repr_str
        assert "lines=1-1" in repr_str
        assert processing_block.processing_status.value in repr_str


class TestFileProcessingResult:
    """Test suite for FileProcessingResult class."""
    
    @pytest.fixture
    def processing_block(self):
        """Create ProcessingBlock instance for testing."""
        return ProcessingBlock(
            content="Hello world",
            block_type="paragraph",
            start_line=1,
            end_line=1,
            start_char=0,
            end_char=11
        )
    
    @pytest.fixture
    def file_processing_result(self, processing_block):
        """Create FileProcessingResult instance for testing."""
        return FileProcessingResult(
            file_path="/path/to/file.txt",
            blocks=[processing_block]
        )
    
    def test_file_processing_result_creation_success(self, processing_block):
        """Test successful FileProcessingResult creation."""
        # Act
        result = FileProcessingResult(
            file_path="/path/to/file.txt",
            blocks=[processing_block]
        )
        
        # Assert
        assert result.file_path == "/path/to/file.txt"
        assert result.blocks == [processing_block]
        assert result.processing_status == ProcessingStatus.PENDING
        assert result.processing_time_seconds == 0.0
        assert result.error_message is None
        assert result.processing_metadata == {}
        assert result.file_size_bytes == 0
        assert result.supported_file_type is True
        assert result.processing_id is not None
        assert result.started_at is not None
        assert result.completed_at is None
    
    def test_file_processing_result_creation_with_optional_params(self, processing_block):
        """Test FileProcessingResult creation with optional parameters."""
        # Arrange
        started_at = datetime.now()
        metadata = {"config": "test", "version": "1.0"}
        
        # Act
        result = FileProcessingResult(
            file_path="/path/to/file.txt",
            blocks=[processing_block],
            processing_id="test_id",
            processing_status=ProcessingStatus.COMPLETED,
            processing_time_seconds=1.5,
            processing_metadata=metadata,
            file_size_bytes=1024,
            supported_file_type=True,
            started_at=started_at
        )
        
        # Assert
        assert result.processing_id == "test_id"
        assert result.processing_status == ProcessingStatus.COMPLETED
        assert result.processing_time_seconds == 1.5
        assert result.processing_metadata == metadata
        assert result.file_size_bytes == 1024
        assert result.supported_file_type is True
        assert result.started_at == started_at
    
    def test_file_processing_result_creation_empty_path(self):
        """Test FileProcessingResult creation with empty file path."""
        # Act & Assert
        with pytest.raises(ValueError, match="file_path must be non-empty string"):
            FileProcessingResult("", [])
    
    def test_file_processing_result_creation_invalid_blocks(self):
        """Test FileProcessingResult creation with invalid blocks."""
        # Act & Assert
        with pytest.raises(TypeError, match="blocks must be list"):
            FileProcessingResult("/path/to/file.txt", "not a list")
    
    def test_file_processing_result_creation_invalid_block_type(self):
        """Test FileProcessingResult creation with invalid block type."""
        # Act & Assert
        with pytest.raises(TypeError, match="blocks must contain ProcessingBlock instances"):
            FileProcessingResult("/path/to/file.txt", ["not a ProcessingBlock"])
    
    def test_file_processing_result_creation_invalid_status(self):
        """Test FileProcessingResult creation with invalid processing status."""
        # Act & Assert
        with pytest.raises(ValueError, match="processing_status must be ProcessingStatus enum value"):
            FileProcessingResult(
                "/path/to/file.txt", [],
                processing_status="invalid_status"
            )
    
    def test_file_processing_result_creation_negative_time(self):
        """Test FileProcessingResult creation with negative processing time."""
        # Act & Assert
        with pytest.raises(ValueError, match="processing_time_seconds must be non-negative float"):
            FileProcessingResult(
                "/path/to/file.txt", [],
                processing_time_seconds=-1.0
            )
    
    def test_total_blocks_property(self, file_processing_result, processing_block):
        """Test total_blocks property."""
        # Arrange
        file_processing_result.blocks = [processing_block, processing_block]
        
        # Act
        total = file_processing_result.total_blocks
        
        # Assert
        assert total == 2
    
    def test_total_characters_property(self, file_processing_result, processing_block):
        """Test total_characters property."""
        # Arrange
        file_processing_result.blocks = [processing_block, processing_block]
        
        # Act
        total = file_processing_result.total_characters
        
        # Assert
        assert total == 22  # 11 characters per block * 2 blocks
    
    def test_add_block(self, file_processing_result, processing_block):
        """Test add_block method."""
        # Act
        file_processing_result.add_block(processing_block)
        
        # Assert
        assert len(file_processing_result.blocks) == 2
        assert file_processing_result.blocks[1] == processing_block
    
    def test_add_block_none(self, file_processing_result):
        """Test add_block with None block."""
        # Act & Assert
        with pytest.raises(ValueError, match="block cannot be None"):
            file_processing_result.add_block(None)
    
    def test_add_block_invalid_type(self, file_processing_result):
        """Test add_block with invalid block type."""
        # Act & Assert
        with pytest.raises(TypeError, match="block must be ProcessingBlock instance"):
            file_processing_result.add_block("not a ProcessingBlock")
    
    def test_mark_completed(self, file_processing_result):
        """Test mark_completed method."""
        # Act
        file_processing_result.mark_completed(1.5)
        
        # Assert
        assert file_processing_result.processing_status == ProcessingStatus.COMPLETED
        assert file_processing_result.processing_time_seconds == 1.5
        assert file_processing_result.completed_at is not None
    
    def test_mark_completed_negative_time(self, file_processing_result):
        """Test mark_completed with negative processing time."""
        # Act & Assert
        with pytest.raises(ValueError, match="processing_time_seconds must be non-negative float"):
            file_processing_result.mark_completed(-1.0)
    
    def test_mark_completed_invalid_type(self, file_processing_result):
        """Test mark_completed with invalid processing time type."""
        # Act & Assert
        with pytest.raises(TypeError, match="processing_time_seconds must be float"):
            file_processing_result.mark_completed("not a float")
    
    def test_mark_failed(self, file_processing_result):
        """Test mark_failed method."""
        # Act
        file_processing_result.mark_failed("File format not supported")
        
        # Assert
        assert file_processing_result.processing_status == ProcessingStatus.FAILED
        assert file_processing_result.error_message == "File format not supported"
        assert file_processing_result.completed_at is not None
    
    def test_mark_failed_empty_message(self, file_processing_result):
        """Test mark_failed with empty error message."""
        # Act & Assert
        with pytest.raises(ValueError, match="error_message must be non-empty string"):
            file_processing_result.mark_failed("")
    
    def test_mark_failed_invalid_type(self, file_processing_result):
        """Test mark_failed with invalid error message type."""
        # Act & Assert
        with pytest.raises(TypeError, match="error_message must be string"):
            file_processing_result.mark_failed(123)
    
    def test_to_dict(self, file_processing_result):
        """Test to_dict method."""
        # Act
        data = file_processing_result.to_dict()
        
        # Assert
        assert data["file_path"] == "/path/to/file.txt"
        assert data["processing_status"] == "pending"
        assert data["processing_time_seconds"] == 0.0
        assert data["error_message"] is None
        assert data["processing_metadata"] == {}
        assert data["file_size_bytes"] == 0
        assert data["supported_file_type"] is True
        assert data["total_blocks"] == 1
        assert data["total_characters"] == 11
        assert "processing_id" in data
        assert "started_at" in data
        assert data["completed_at"] is None
        assert len(data["blocks"]) == 1
    
    def test_from_dict(self, file_processing_result):
        """Test from_dict method."""
        # Arrange
        data = file_processing_result.to_dict()
        
        # Act
        new_result = FileProcessingResult.from_dict(data)
        
        # Assert
        assert new_result.file_path == file_processing_result.file_path
        assert new_result.processing_status == file_processing_result.processing_status
        assert new_result.total_blocks == file_processing_result.total_blocks
    
    def test_from_dict_missing_required_fields(self):
        """Test from_dict method with missing required fields."""
        # Arrange
        data = {"file_path": "/path/to/file.txt"}  # Missing blocks
        
        # Act & Assert
        with pytest.raises(ValueError, match="Missing required field"):
            FileProcessingResult.from_dict(data)
    
    def test_equality(self, file_processing_result):
        """Test equality comparison."""
        # Arrange
        same_result = FileProcessingResult(
            file_path=file_processing_result.file_path,
            blocks=file_processing_result.blocks
        )
        
        # Act & Assert
        assert file_processing_result == same_result
    
    def test_inequality(self, file_processing_result):
        """Test inequality comparison."""
        # Arrange
        different_result = FileProcessingResult(
            file_path="/different/path.txt",
            blocks=file_processing_result.blocks
        )
        
        # Act & Assert
        assert file_processing_result != different_result
    
    def test_equality_different_type(self, file_processing_result):
        """Test equality with different type."""
        # Act & Assert
        assert file_processing_result != "not a FileProcessingResult"
    
    def test_repr(self, file_processing_result):
        """Test string representation."""
        # Act
        repr_str = repr(file_processing_result)
        
        # Assert
        assert "FileProcessingResult" in repr_str
        assert file_processing_result.file_path in repr_str
        assert str(file_processing_result.total_blocks) in repr_str
        assert file_processing_result.processing_status.value in repr_str 