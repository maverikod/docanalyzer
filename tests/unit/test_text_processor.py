"""
Tests for Text Processor

Comprehensive test suite for text file processing functionality.
Tests text block extraction, file processing, and encoding handling.

Author: DocAnalyzer Team
Version: 1.0.0
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
from datetime import datetime

from docanalyzer.processors.text_processor import TextProcessor, TextBlockExtractor
from docanalyzer.processors.base_processor import ProcessorResult
from docanalyzer.models.processing import ProcessingBlock


class TestTextBlockExtractor:
    """Test suite for TextBlockExtractor class."""
    
    @pytest.fixture
    def extractor(self):
        """Create test text block extractor."""
        return TextBlockExtractor()
    
    def test_init_default_values(self, extractor):
        """Test initialization with default values."""
        assert extractor.strategy == "paragraph"
        assert extractor.min_block_size == 50
        assert extractor.max_block_size == 2000
        assert extractor.custom_delimiters == []
    
    def test_init_custom_values(self):
        """Test initialization with custom values."""
        extractor = TextBlockExtractor(
            strategy="line",
            min_block_size=100,
            max_block_size=1500,
            custom_delimiters=["###", "---"]
        )
        
        assert extractor.strategy == "line"
        assert extractor.min_block_size == 100
        assert extractor.max_block_size == 1500
        assert extractor.custom_delimiters == ["###", "---"]
    
    def test_init_invalid_strategy(self):
        """Test initialization with invalid strategy."""
        with pytest.raises(ValueError, match="strategy must be one of"):
            TextBlockExtractor(strategy="invalid")
    
    def test_init_invalid_min_block_size(self):
        """Test initialization with invalid min block size."""
        with pytest.raises(ValueError, match="min_block_size must be positive integer"):
            TextBlockExtractor(min_block_size=0)
        
        with pytest.raises(ValueError, match="min_block_size must be positive integer"):
            TextBlockExtractor(min_block_size=-1)
        
        with pytest.raises(ValueError, match="min_block_size must be positive integer"):
            TextBlockExtractor(min_block_size="invalid")
    
    def test_init_invalid_max_block_size(self):
        """Test initialization with invalid max block size."""
        with pytest.raises(ValueError, match="max_block_size must be >= min_block_size"):
            TextBlockExtractor(min_block_size=100, max_block_size=50)
    
    def test_init_custom_strategy_without_delimiters(self):
        """Test custom strategy without delimiters."""
        with pytest.raises(TypeError, match="custom_delimiters must be list for custom strategy"):
            TextBlockExtractor(strategy="custom", custom_delimiters="invalid")
        
        with pytest.raises(ValueError, match="custom_delimiters cannot be empty for custom strategy"):
            TextBlockExtractor(strategy="custom", custom_delimiters=[])
    
    def test_extract_blocks_paragraph_strategy(self, extractor):
        """Test paragraph-based block extraction."""
        # Create longer paragraphs to meet min_block_size requirement
        text = "This is a longer paragraph with enough content to meet the minimum block size requirement.\n\nThis is another paragraph with sufficient content to be considered a valid block.\n\nThis is the third paragraph that should also be extracted as a separate block."
        
        blocks = extractor.extract_blocks(text)
        
        assert len(blocks) == 3
        assert "longer paragraph" in blocks[0]
        assert "another paragraph" in blocks[1]
        assert "third paragraph" in blocks[2]
    
    def test_extract_blocks_line_strategy(self):
        """Test line-based block extraction."""
        extractor = TextBlockExtractor(strategy="line", min_block_size=10)  # Lower min size for testing
        text = "This is line 1 with enough content.\nThis is line 2 with sufficient text.\nThis is line 3 with adequate length.\nThis is line 4 with proper content."
        
        blocks = extractor.extract_blocks(text)
        
        assert len(blocks) == 1  # All lines combined into one block
        assert "line 1" in blocks[0]
        assert "line 4" in blocks[0]
    
    def test_extract_blocks_custom_strategy(self):
        """Test custom delimiter-based block extraction."""
        extractor = TextBlockExtractor(
            strategy="custom",
            custom_delimiters=["###", "---"],
            min_block_size=10  # Lower min size for testing
        )
        text = "This is block 1 with enough content ### This is block 2 with sufficient text --- This is block 3 with adequate length ### This is block 4 with proper content"
        
        blocks = extractor.extract_blocks(text)
        
        assert len(blocks) == 4
        assert "block 1" in blocks[0]
        assert "block 2" in blocks[1]
        assert "block 3" in blocks[2]
        assert "block 4" in blocks[3]
    
    def test_extract_blocks_empty_text(self, extractor):
        """Test extraction with empty text."""
        with pytest.raises(ValueError, match="text cannot be empty"):
            extractor.extract_blocks("")
    
    def test_extract_blocks_invalid_text(self, extractor):
        """Test extraction with invalid text."""
        with pytest.raises(TypeError, match="text must be string"):
            extractor.extract_blocks(123)
    
    def test_extract_blocks_large_paragraph(self, extractor):
        """Test extraction with large paragraph that exceeds max size."""
        # Create a large text that exceeds max_block_size
        large_text = "This is a very long paragraph. " * 100  # Should exceed 2000 chars
        
        blocks = extractor.extract_blocks(large_text)
        
        assert len(blocks) > 1  # Should be split into multiple blocks
        assert all(len(block) <= extractor.max_block_size for block in blocks)
    
    def test_extract_blocks_small_paragraphs(self, extractor):
        """Test extraction with small paragraphs that get merged."""
        text = "Short 1.\n\nShort 2.\n\nShort 3."
        
        blocks = extractor.extract_blocks(text)
        
        # Small paragraphs should be merged
        assert len(blocks) < 3
    
    def test_extract_paragraph_blocks_with_whitespace(self, extractor):
        """Test paragraph extraction with various whitespace."""
        text = "  This is paragraph 1 with enough content to meet minimum size requirements.  \n\n  \n\n  This is paragraph 2 with sufficient text to be considered a valid block.  "
        
        blocks = extractor.extract_blocks(text)
        
        assert len(blocks) == 2
        assert "paragraph 1" in blocks[0]
        assert "paragraph 2" in blocks[1]
    
    def test_extract_line_blocks_with_empty_lines(self):
        """Test line extraction with empty lines."""
        extractor = TextBlockExtractor(strategy="line", min_block_size=10)
        text = "This is line 1 with enough content.\n\nThis is line 2 with sufficient text.\n\n\nThis is line 3 with adequate length."
        
        blocks = extractor.extract_blocks(text)
        
        assert len(blocks) == 1  # Should be one block with all non-empty lines
        assert "line 1" in blocks[0]
        assert "line 2" in blocks[0]
        assert "line 3" in blocks[0]
    
    def test_extract_custom_blocks_multiple_delimiters(self):
        """Test custom extraction with multiple delimiters."""
        extractor = TextBlockExtractor(
            strategy="custom",
            custom_delimiters=["###", "---", "***"],
            min_block_size=10
        )
        text = "This is block 1 with content ### This is block 2 with text --- This is block 3 with length *** This is block 4 with content"
        
        blocks = extractor.extract_blocks(text)
        
        assert len(blocks) == 4
        assert all("block" in block for block in blocks)
    
    def test_split_large_block(self, extractor):
        """Test splitting of large blocks."""
        large_block = "This is a very long block. " * 100  # Should exceed max_block_size
        
        blocks = extractor._split_large_block(large_block)
        
        assert len(blocks) > 1
        assert all(len(block) <= extractor.max_block_size for block in blocks)
        assert all(len(block) >= extractor.min_block_size for block in blocks)
    
    def test_split_large_block_small_size(self, extractor):
        """Test splitting with small block size."""
        extractor.min_block_size = 100
        extractor.max_block_size = 200
        
        large_block = "This is a sentence. " * 30  # Should exceed max_block_size
        
        blocks = extractor._split_large_block(large_block)
        
        assert len(blocks) > 1
        assert all(len(block) <= extractor.max_block_size for block in blocks)
    
    def test_extract_blocks_unknown_strategy(self):
        """Test extraction with unknown strategy."""
        extractor = TextBlockExtractor(strategy="paragraph")
        extractor.strategy = "unknown"  # Manually set invalid strategy
        
        with pytest.raises(ValueError, match="Unknown strategy"):
            extractor.extract_blocks("Test text")


class TestTextProcessor:
    """Test suite for TextProcessor class."""
    
    @pytest.fixture
    def processor(self):
        """Create test text processor."""
        return TextProcessor()
    
    @pytest.fixture
    def temp_text_file(self):
        """Create temporary text file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is paragraph 1 with enough content to meet the minimum block size requirement.\n\nThis is paragraph 2 with sufficient content to be considered a valid block.\n\nThis is paragraph 3 that should also be extracted as a separate block.")
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        os.unlink(temp_file)
    
    def test_init_default_values(self, processor):
        """Test initialization with default values."""
        assert processor.supported_extensions == ["txt"]
        assert processor.processor_name == "TextProcessor"
        assert processor.encoding == "utf-8"
        assert processor.normalize_whitespace is True
        assert processor.remove_empty_blocks is True
        assert isinstance(processor.block_extractor, TextBlockExtractor)
    
    def test_init_custom_values(self):
        """Test initialization with custom values."""
        extractor = TextBlockExtractor(strategy="line")
        processor = TextProcessor(
            block_extractor=extractor,
            encoding="latin-1",
            normalize_whitespace=False,
            remove_empty_blocks=False,
            max_file_size_bytes=5 * 1024 * 1024
        )
        
        assert processor.block_extractor == extractor
        assert processor.encoding == "latin-1"
        assert processor.normalize_whitespace is False
        assert processor.remove_empty_blocks is False
        assert processor.max_file_size_bytes == 5 * 1024 * 1024
    
    def test_init_invalid_block_extractor(self):
        """Test initialization with invalid block extractor."""
        with pytest.raises(TypeError, match="block_extractor must be TextBlockExtractor instance"):
            TextProcessor(block_extractor="invalid")
    
    def test_init_invalid_encoding(self):
        """Test initialization with invalid encoding."""
        with pytest.raises(TypeError, match="encoding must be string"):
            TextProcessor(encoding=123)
        
        with pytest.raises(ValueError, match="encoding cannot be empty"):
            TextProcessor(encoding="")
    
    def test_process_file_success(self, processor, temp_text_file):
        """Test successful file processing."""
        result = processor.process_file(temp_text_file)
        
        assert result.success is True
        assert len(result.blocks) > 0
        assert all(isinstance(block, ProcessingBlock) for block in result.blocks)
        assert result.supported_file_type is True
        assert result.processing_time_seconds > 0
        assert result.file_size_bytes > 0
        
        # Check processing metadata
        assert result.processing_metadata["processor_type"] == "text"
        assert result.processing_metadata["encoding"] == "utf-8"
        assert result.processing_metadata["normalize_whitespace"] is True
        assert result.processing_metadata["remove_empty_blocks"] is True
        assert result.processing_metadata["extraction_strategy"] == "paragraph"
    
    def test_process_file_not_found(self, processor):
        """Test processing non-existent file."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            processor.process_file("/nonexistent/file.txt")
    
    def test_process_file_invalid_path(self, processor):
        """Test processing with invalid file path."""
        with pytest.raises(ValueError, match="file_path cannot be empty"):
            processor.process_file("")
        
        with pytest.raises(TypeError, match="file_path must be string"):
            processor.process_file(None)
    
    def test_process_file_unsupported_extension(self, processor):
        """Test processing file with unsupported extension."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_file = f.name
        
        try:
            with pytest.raises(ValueError, match="File type not supported"):
                processor.process_file(temp_file)
        finally:
            os.unlink(temp_file)
    
    def test_process_file_encoding_error(self, processor):
        """Test processing file with encoding error."""
        # Create file with invalid UTF-8
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b'\xff\xfe\x00\x00')  # Invalid UTF-8
            temp_file = f.name
        
        try:
            result = processor.process_file(temp_file)
            # Should handle encoding error gracefully
            assert result.success is True  # Alternative encodings should work
        finally:
            os.unlink(temp_file)
    
    def test_process_file_with_alternative_encoding(self):
        """Test processing file with alternative encoding."""
        processor = TextProcessor(encoding="utf-8")
        
        # Create file with latin-1 encoding
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write("This is a test file with enough content to meet the minimum block size requirement. It contains special characters: éñü and should be processed correctly.".encode('latin-1'))
            temp_file = f.name
        
        try:
            result = processor.process_file(temp_file)
            assert result.success is True
            assert len(result.blocks) > 0
        finally:
            os.unlink(temp_file)
    
    def test_process_file_large_file(self):
        """Test processing large file."""
        processor = TextProcessor(max_file_size_bytes=100)  # Small limit
        
        # Create large file
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(("A" * 200).encode('utf-8'))  # Exceeds limit
            temp_file = f.name
        
        try:
            with pytest.raises(ValueError, match="File too large"):
                processor.process_file(temp_file)
        finally:
            os.unlink(temp_file)
    
    def test_read_file_content_success(self, processor, temp_text_file):
        """Test successful file content reading."""
        content = processor._read_file_content(temp_text_file)
        
        assert isinstance(content, str)
        assert "paragraph 1" in content
        assert "paragraph 3" in content
    
    def test_read_file_content_encoding_error(self, processor):
        """Test file content reading with encoding error."""
        # Create file with invalid encoding
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b'\xff\xfe\x00\x00')  # Invalid UTF-8
            temp_file = f.name
        
        try:
            # Should try alternative encodings
            content = processor._read_file_content(temp_file)
            assert isinstance(content, str)
        finally:
            os.unlink(temp_file)
    
    def test_read_file_content_alternative_encoding(self, processor):
        """Test file content reading with alternative encoding."""
        # Create file with latin-1 encoding
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write("Test content: éñü".encode('latin-1'))
            temp_file = f.name
        
        try:
            content = processor._read_file_content(temp_file)
            assert "Test content: éñü" in content
        finally:
            os.unlink(temp_file)
    
    def test_process_text_content_normalize_whitespace(self, processor):
        """Test text content processing with whitespace normalization."""
        text = "  Multiple    spaces\n\n\n\nMultiple newlines  "
        
        processed = processor._process_text_content(text)
        
        assert "  " not in processed  # No multiple spaces
        assert "\n\n\n\n" not in processed  # No multiple newlines
        assert processed.strip() == processed  # No leading/trailing whitespace
    
    def test_process_text_content_no_normalization(self):
        """Test text content processing without normalization."""
        processor = TextProcessor(normalize_whitespace=False)
        text = "  Original   formatting\n\n\n\n  "
        
        processed = processor._process_text_content(text)
        
        assert processed == text  # Should be unchanged
    
    def test_create_processing_blocks(self, processor, temp_text_file):
        """Test creation of processing blocks."""
        text_blocks = ["Block 1", "Block 2", "Block 3"]
        
        blocks = processor._create_processing_blocks(text_blocks, temp_text_file)
        
        assert len(blocks) == 3
        assert all(isinstance(block, ProcessingBlock) for block in blocks)
        assert blocks[0].content == "Block 1"
        assert blocks[1].content == "Block 2"
        assert blocks[2].content == "Block 3"
        assert all(block.block_type == "text_paragraph" for block in blocks)
        assert all(block.metadata["file_path"] == temp_text_file for block in blocks)
    
    def test_create_processing_blocks_with_empty_blocks(self, processor, temp_text_file):
        """Test creation of processing blocks with empty blocks."""
        processor.remove_empty_blocks = True
        text_blocks = ["Block 1", "", "   ", "Block 2"]
        
        blocks = processor._create_processing_blocks(text_blocks, temp_text_file)
        
        assert len(blocks) == 2  # Empty blocks should be removed
        assert blocks[0].content == "Block 1"
        assert blocks[1].content == "Block 2"
    
    def test_create_processing_blocks_keep_empty_blocks(self, processor, temp_text_file):
        """Test creation of processing blocks keeping empty blocks."""
        processor.remove_empty_blocks = False
        text_blocks = ["Block 1 with content", "Non-empty block", "Block 2 with content"]
        
        blocks = processor._create_processing_blocks(text_blocks, temp_text_file)
        
        assert len(blocks) == 3  # All blocks should be kept
        assert blocks[0].content == "Block 1 with content"
        assert blocks[1].content == "Non-empty block"
        assert blocks[2].content == "Block 2 with content"
    
    def test_process_file_with_line_strategy(self, temp_text_file):
        """Test file processing with line extraction strategy."""
        extractor = TextBlockExtractor(strategy="line")
        processor = TextProcessor(block_extractor=extractor)
        
        result = processor.process_file(temp_text_file)
        
        assert result.success is True
        assert len(result.blocks) > 0
        assert result.processing_metadata["extraction_strategy"] == "line"
    
    def test_process_file_with_custom_strategy(self, temp_text_file):
        """Test file processing with custom extraction strategy."""
        extractor = TextBlockExtractor(
            strategy="custom",
            custom_delimiters=["###", "---"],
            min_block_size=10
        )
        processor = TextProcessor(block_extractor=extractor)
        
        # Create file with custom delimiters
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is block 1 with content ### This is block 2 with text --- This is block 3 with content")
            custom_file = f.name
        
        try:
            result = processor.process_file(custom_file)
            assert result.success is True
            assert len(result.blocks) == 3
            assert result.processing_metadata["extraction_strategy"] == "custom"
        finally:
            os.unlink(custom_file)
    
    def test_process_file_exception_handling(self, processor, temp_text_file):
        """Test exception handling during file processing."""
        with patch.object(processor, '_read_file_content', side_effect=Exception("Test error")):
            result = processor.process_file(temp_text_file)
            
            assert result.success is False
            assert "Test error" in result.error_message
            assert result.processing_time_seconds > 0 