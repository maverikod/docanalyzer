"""
Tests for Base Processor

Unit tests for BaseProcessor abstract class and ProcessorResult class.
Tests cover validation, file handling, and result processing.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from docanalyzer.processors.base_processor import BaseProcessor, ProcessorResult
from docanalyzer.models.processing import ProcessingBlock, ProcessingStatus


class ConcreteProcessor(BaseProcessor):
    """Concrete implementation of BaseProcessor for testing."""
    
    def __init__(self, supported_extensions=None, processor_name="TestProcessor", max_file_size_bytes=1024):
        super().__init__(
            supported_extensions or ["txt"],
            processor_name,
            max_file_size_bytes
        )
    
    def process_file(self, file_path: str) -> ProcessorResult:
        """Concrete implementation of process_file."""
        return ProcessorResult(success=True, blocks=[])


class TestProcessorResult:
    """Test suite for ProcessorResult class."""
    
    def test_init_success_with_blocks(self):
        """Test successful initialization with blocks."""
        blocks = [ProcessingBlock("test", "paragraph", 1, 1, 0, 4)]
        result = ProcessorResult(success=True, blocks=blocks)
        
        assert result.success is True
        assert result.blocks == blocks
        assert result.error_message is None
        assert result.processing_time_seconds == 0.0
        assert result.file_size_bytes == 0
        assert result.supported_file_type is True
    
    def test_init_success_without_blocks(self):
        """Test successful initialization without blocks."""
        result = ProcessorResult(success=True, blocks=[])
        
        assert result.success is True
        assert result.blocks == []
    
    def test_init_failure(self):
        """Test initialization with failure."""
        result = ProcessorResult(
            success=False,
            error_message="Test error",
            processing_time_seconds=1.5,
            file_size_bytes=100
        )
        
        assert result.success is False
        assert result.error_message == "Test error"
        assert result.processing_time_seconds == 1.5
        assert result.file_size_bytes == 100
    
    def test_init_success_with_none_blocks_raises_error(self):
        """Test that success=True with None blocks raises error."""
        with pytest.raises(ValueError, match="blocks cannot be None when success is True"):
            ProcessorResult(success=True, blocks=None)
    
    def test_init_invalid_blocks_type(self):
        """Test that invalid blocks type raises error."""
        with pytest.raises(TypeError, match="blocks must be list"):
            ProcessorResult(success=True, blocks="not a list")
    
    def test_init_invalid_block_type(self):
        """Test that invalid block type raises error."""
        with pytest.raises(TypeError, match="blocks must contain ProcessingBlock instances"):
            ProcessorResult(success=True, blocks=["not a block"])
    
    def test_init_invalid_processing_time(self):
        """Test that invalid processing time raises error."""
        with pytest.raises(TypeError, match="processing_time_seconds must be float"):
            ProcessorResult(success=True, blocks=[], processing_time_seconds="invalid")
    
    def test_init_negative_processing_time(self):
        """Test that negative processing time raises error."""
        with pytest.raises(ValueError, match="processing_time_seconds must be non-negative float"):
            ProcessorResult(success=True, blocks=[], processing_time_seconds=-1.0)
    
    def test_init_invalid_file_size(self):
        """Test that invalid file size raises error."""
        with pytest.raises(TypeError, match="file_size_bytes must be integer"):
            ProcessorResult(success=True, blocks=[], file_size_bytes="invalid")
    
    def test_init_negative_file_size(self):
        """Test that negative file size raises error."""
        with pytest.raises(ValueError, match="file_size_bytes must be non-negative integer"):
            ProcessorResult(success=True, blocks=[], file_size_bytes=-1)
    
    def test_total_blocks(self):
        """Test total_blocks property."""
        blocks = [
            ProcessingBlock("block1", "paragraph", 1, 1, 0, 6),
            ProcessingBlock("block2", "paragraph", 2, 2, 7, 13)
        ]
        result = ProcessorResult(success=True, blocks=blocks)
        
        assert result.total_blocks == 2
    
    def test_total_characters(self):
        """Test total_characters property."""
        blocks = [
            ProcessingBlock("hello", "paragraph", 1, 1, 0, 5),
            ProcessingBlock("world", "paragraph", 2, 2, 6, 11)
        ]
        result = ProcessorResult(success=True, blocks=blocks)
        
        assert result.total_characters == 10
    
    def test_to_file_processing_result(self):
        """Test conversion to FileProcessingResult."""
        blocks = [ProcessingBlock("test", "paragraph", 1, 1, 0, 4)]
        result = ProcessorResult(
            success=True,
            blocks=blocks,
            processing_time_seconds=1.5,
            file_size_bytes=100
        )
        
        file_result = result.to_file_processing_result("/test/file.txt")
        
        assert file_result.file_path == "/test/file.txt"
        assert file_result.blocks == blocks
        assert file_result.processing_status == ProcessingStatus.COMPLETED
        assert file_result.processing_time_seconds == 1.5
        assert file_result.file_size_bytes == 100
    
    def test_to_file_processing_result_failure(self):
        """Test conversion to FileProcessingResult for failed processing."""
        result = ProcessorResult(
            success=False,
            error_message="Test error",
            processing_time_seconds=1.5
        )
        
        file_result = result.to_file_processing_result("/test/file.txt")
        
        assert file_result.processing_status == ProcessingStatus.FAILED
        assert file_result.error_message == "Test error"
    
    def test_to_file_processing_result_invalid_path(self):
        """Test conversion with invalid file path."""
        result = ProcessorResult(success=True, blocks=[])
        
        with pytest.raises(TypeError, match="file_path must be string"):
            result.to_file_processing_result(None)
        
        with pytest.raises(ValueError, match="file_path must be non-empty string"):
            result.to_file_processing_result("")
    
    def test_repr(self):
        """Test string representation."""
        result = ProcessorResult(
            success=True,
            blocks=[],
            processing_time_seconds=1.5,
            supported_file_type=True
        )
        
        repr_str = repr(result)
        assert "ProcessorResult(" in repr_str
        assert "success=True" in repr_str
        assert "blocks=0" in repr_str
        assert "time=1.50s" in repr_str
        assert "supported=True" in repr_str


class TestBaseProcessor:
    """Test suite for BaseProcessor class."""
    
    def test_init_valid_parameters(self):
        """Test valid initialization."""
        processor = ConcreteProcessor(
            supported_extensions=["txt", "md"],
            processor_name="TestProcessor",
            max_file_size_bytes=2048
        )
        
        assert processor.supported_extensions == ["txt", "md"]
        assert processor.processor_name == "TestProcessor"
        assert processor.max_file_size_bytes == 2048
    
    def test_init_empty_extensions_raises_error(self):
        """Test that empty extensions raises error."""
        # Create a processor that directly calls BaseProcessor.__init__ with empty list
        class TestProcessor(BaseProcessor):
            def __init__(self):
                super().__init__([], "TestProcessor", 1024)
            
            def process_file(self, file_path: str) -> ProcessorResult:
                return ProcessorResult(success=True, blocks=[])
        
        with pytest.raises(ValueError, match="supported_extensions cannot be empty"):
            TestProcessor()
    
    def test_init_invalid_extensions_type(self):
        """Test that invalid extensions type raises error."""
        with pytest.raises(TypeError, match="supported_extensions must be list"):
            ConcreteProcessor(supported_extensions="not a list")
    
    def test_init_empty_extension_string(self):
        """Test that empty extension string raises error."""
        with pytest.raises(ValueError, match="supported_extensions must contain non-empty strings"):
            ConcreteProcessor(supported_extensions=["txt", ""])
    
    def test_init_invalid_processor_name(self):
        """Test that invalid processor name raises error."""
        with pytest.raises(TypeError, match="processor_name must be string"):
            ConcreteProcessor(processor_name=123)
        
        with pytest.raises(ValueError, match="processor_name cannot be empty"):
            ConcreteProcessor(processor_name="")
    
    def test_init_invalid_max_file_size(self):
        """Test that invalid max file size raises error."""
        with pytest.raises(TypeError, match="max_file_size_bytes must be integer"):
            ConcreteProcessor(max_file_size_bytes="invalid")
        
        with pytest.raises(ValueError, match="max_file_size_bytes must be positive integer"):
            ConcreteProcessor(max_file_size_bytes=0)
    
    def test_can_process_file_supported_extension(self, tmp_path):
        """Test can_process_file with supported extension."""
        processor = ConcreteProcessor(supported_extensions=["txt"])
        
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        assert processor.can_process_file(str(test_file)) is True
    
    def test_can_process_file_unsupported_extension(self, tmp_path):
        """Test can_process_file with unsupported extension."""
        processor = ConcreteProcessor(supported_extensions=["txt"])
        
        # Create test file with unsupported extension
        test_file = tmp_path / "test.md"
        test_file.write_text("test content")
        
        assert processor.can_process_file(str(test_file)) is False
    
    def test_can_process_file_too_large(self, tmp_path):
        """Test can_process_file with file too large."""
        processor = ConcreteProcessor(max_file_size_bytes=10)
        
        # Create test file larger than limit
        test_file = tmp_path / "test.txt"
        test_file.write_text("this content is longer than 10 bytes")
        
        assert processor.can_process_file(str(test_file)) is False
    
    def test_can_process_file_nonexistent(self):
        """Test can_process_file with nonexistent file."""
        processor = ConcreteProcessor()
        
        assert processor.can_process_file("/nonexistent/file.txt") is False
    
    def test_can_process_file_invalid_path(self):
        """Test can_process_file with invalid path."""
        processor = ConcreteProcessor()
        
        with pytest.raises(TypeError, match="file_path must be string"):
            processor.can_process_file(None)
        
        with pytest.raises(ValueError, match="file_path cannot be empty"):
            processor.can_process_file("")
    
    def test_get_file_metadata(self, tmp_path):
        """Test get_file_metadata."""
        processor = ConcreteProcessor()
        
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        metadata = processor.get_file_metadata(str(test_file))
        
        assert metadata["size_bytes"] > 0
        assert metadata["file_extension"] == "txt"
        assert metadata["file_name"] == "test.txt"
        assert "file_path" in metadata
        assert "modified_time" in metadata
        assert "created_time" in metadata
    
    def test_get_file_metadata_nonexistent(self):
        """Test get_file_metadata with nonexistent file."""
        processor = ConcreteProcessor()
        
        metadata = processor.get_file_metadata("/nonexistent/file.txt")
        
        assert metadata == {}
    
    def test_get_file_metadata_invalid_path(self):
        """Test get_file_metadata with invalid path."""
        processor = ConcreteProcessor()
        
        with pytest.raises(TypeError, match="file_path must be string"):
            processor.get_file_metadata(None)
        
        with pytest.raises(ValueError, match="file_path cannot be empty"):
            processor.get_file_metadata("")
    
    def test_validate_file_path_valid(self, tmp_path):
        """Test validate_file_path with valid file."""
        processor = ConcreteProcessor()
        
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        # Should not raise any exception
        processor.validate_file_path(str(test_file))
    
    def test_validate_file_path_nonexistent(self):
        """Test validate_file_path with nonexistent file."""
        processor = ConcreteProcessor()
        
        with pytest.raises(FileNotFoundError, match="File not found"):
            processor.validate_file_path("/nonexistent/file.txt")
    
    def test_validate_file_path_directory(self, tmp_path):
        """Test validate_file_path with directory."""
        processor = ConcreteProcessor()
        
        with pytest.raises(ValueError, match="Path is not a file"):
            processor.validate_file_path(str(tmp_path))
    
    def test_validate_file_path_invalid_type(self):
        """Test validate_file_path with invalid type."""
        processor = ConcreteProcessor()
        
        with pytest.raises(TypeError, match="file_path must be string"):
            processor.validate_file_path(None)
        
        with pytest.raises(ValueError, match="file_path cannot be empty"):
            processor.validate_file_path("")
    
    def test_validate_file_path_too_large(self, tmp_path):
        """Test validate_file_path with file too large."""
        processor = ConcreteProcessor(max_file_size_bytes=10)
        
        # Create test file larger than limit
        test_file = tmp_path / "test.txt"
        test_file.write_text("this content is longer than 10 bytes")
        
        with pytest.raises(ValueError, match="File too large"):
            processor.validate_file_path(str(test_file))
    
    def test_validate_file_path_unsupported_type(self, tmp_path):
        """Test validate_file_path with unsupported file type."""
        processor = ConcreteProcessor(supported_extensions=["txt"])
        
        # Create test file with unsupported extension
        test_file = tmp_path / "test.md"
        test_file.write_text("test content")
        
        with pytest.raises(ValueError, match="File type not supported"):
            processor.validate_file_path(str(test_file))
    
    def test_process_file_abstract(self):
        """Test that process_file is abstract."""
        processor = ConcreteProcessor()
        
        # Should not raise exception for concrete implementation
        result = processor.process_file("/test/file.txt")
        assert isinstance(result, ProcessorResult)
    
    def test_repr(self):
        """Test string representation."""
        processor = ConcreteProcessor(
            supported_extensions=["txt", "md"],
            processor_name="TestProcessor",
            max_file_size_bytes=2048
        )
        
        repr_str = repr(processor)
        assert "TestProcessor(" in repr_str
        assert "extensions=['txt', 'md']" in repr_str
        assert "max_size=2048" in repr_str 