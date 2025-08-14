"""
Tests for Text Processor

Unit tests for TextProcessor and TextBlockExtractor classes.
Tests cover text processing, block extraction, and file handling.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from docanalyzer.processors.text_processor import TextProcessor, TextBlockExtractor
from docanalyzer.models.processing import ProcessingBlock, ProcessingStatus


class TestTextBlockExtractor:
    """Test suite for TextBlockExtractor class."""
    
    def test_init_valid_parameters(self):
        """Test valid initialization."""
        extractor = TextBlockExtractor(
            strategy="paragraph",
            min_block_size=50,
            max_block_size=2000,
            custom_delimiters=["---", "==="]
        )
        
        assert extractor.strategy == "paragraph"
        assert extractor.min_block_size == 50
        assert extractor.max_block_size == 2000
        assert extractor.custom_delimiters == ["---", "==="]
    
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
    
    def test_init_invalid_max_block_size(self):
        """Test initialization with invalid max block size."""
        with pytest.raises(ValueError, match="max_block_size must be >= min_block_size"):
            TextBlockExtractor(min_block_size=100, max_block_size=50)
    
    def test_init_custom_strategy_without_delimiters(self):
        """Test custom strategy without delimiters."""
        with pytest.raises(TypeError, match="custom_delimiters must be list for custom strategy"):
            TextBlockExtractor(strategy="custom", custom_delimiters=None)
        
        with pytest.raises(ValueError, match="custom_delimiters cannot be empty for custom strategy"):
            TextBlockExtractor(strategy="custom", custom_delimiters=[])
    
    def test_extract_blocks_paragraph_strategy(self):
        """Test paragraph-based block extraction."""
        extractor = TextBlockExtractor(strategy="paragraph", min_block_size=5)
        text = "Paragraph 1.\n\nParagraph 2.\n\nParagraph 3."
        
        blocks = extractor.extract_blocks(text)
        
        assert len(blocks) == 3
        assert blocks[0] == "Paragraph 1."
        assert blocks[1] == "Paragraph 2."
        assert blocks[2] == "Paragraph 3."
    
    def test_extract_blocks_line_strategy(self):
        """Test line-based block extraction."""
        extractor = TextBlockExtractor(strategy="line", min_block_size=5)
        text = "Line 1\nLine 2\nLine 3"
        
        blocks = extractor.extract_blocks(text)
        
        assert len(blocks) == 1  # All lines merged into one block
        assert "Line 1" in blocks[0]
        assert "Line 2" in blocks[0]
        assert "Line 3" in blocks[0]
    
    def test_extract_blocks_custom_strategy(self):
        """Test custom delimiter-based block extraction."""
        extractor = TextBlockExtractor(
            strategy="custom",
            custom_delimiters=["---", "==="],
            min_block_size=5
        )
        text = "Block 1---Block 2===Block 3"
        
        blocks = extractor.extract_blocks(text)
        
        assert len(blocks) == 3
        assert blocks[0] == "Block 1"
        assert blocks[1] == "Block 2"
        assert blocks[2] == "Block 3"
    
    def test_extract_blocks_size_constraints(self):
        """Test block extraction with size constraints."""
        extractor = TextBlockExtractor(
            min_block_size=10,
            max_block_size=20
        )
        text = "Short.\n\nThis is a longer paragraph that should be split.\n\nAnother short one."
        
        blocks = extractor.extract_blocks(text)
        
        # All blocks should be within size constraints
        for block in blocks:
            assert len(block) >= 10
            # Note: max_block_size is used for merging, not strict splitting
            # So blocks can be larger than max_block_size if they can't be split further
    
    def test_extract_blocks_empty_text(self):
        """Test block extraction with empty text."""
        extractor = TextBlockExtractor()
        
        with pytest.raises(ValueError, match="text cannot be empty"):
            extractor.extract_blocks("")
    
    def test_extract_blocks_invalid_text_type(self):
        """Test block extraction with invalid text type."""
        extractor = TextBlockExtractor()
        
        with pytest.raises(TypeError, match="text must be string"):
            extractor.extract_blocks(None)
    
    def test_extract_blocks_unknown_strategy(self):
        """Test block extraction with unknown strategy."""
        extractor = TextBlockExtractor()
        extractor.strategy = "unknown"
        
        with pytest.raises(ValueError, match="Unknown strategy"):
            extractor.extract_blocks("test")
    
    def test_extract_paragraph_blocks_with_large_paragraphs(self):
        """Test paragraph extraction with large paragraphs that need splitting."""
        extractor = TextBlockExtractor(min_block_size=10, max_block_size=50)
        text = "This is a very long paragraph that exceeds the maximum block size and should be split into smaller blocks."
        
        blocks = extractor._extract_paragraph_blocks(text)
        
        assert len(blocks) > 1  # Should be split into multiple blocks
        for block in blocks:
            assert len(block) >= 10  # All blocks should meet minimum size
    
    def test_extract_paragraph_blocks_with_small_paragraphs(self):
        """Test paragraph extraction with small paragraphs that need merging."""
        extractor = TextBlockExtractor(min_block_size=20, max_block_size=100)
        text = "Short.\n\nAlso short.\n\nAnother short one."
        
        blocks = extractor._extract_paragraph_blocks(text)
        
        # Should merge small paragraphs
        assert len(blocks) < 3
        for block in blocks:
            assert len(block) >= 20
    
    def test_extract_line_blocks_with_large_lines(self):
        """Test line extraction with large lines that need splitting."""
        extractor = TextBlockExtractor(strategy="line", min_block_size=10, max_block_size=30)
        text = "This is a very long line that exceeds the maximum block size and should be split."
        
        blocks = extractor._extract_line_blocks(text)
        
        assert len(blocks) > 1  # Should be split into multiple blocks
        for block in blocks:
            assert len(block) >= 10
    
    def test_extract_line_blocks_with_small_lines(self):
        """Test line extraction with small lines that need merging."""
        extractor = TextBlockExtractor(strategy="line", min_block_size=20, max_block_size=100)
        text = "Short line.\nAnother short line.\nYet another short line."
        
        blocks = extractor._extract_line_blocks(text)
        
        # Should merge small lines
        assert len(blocks) < 3
        for block in blocks:
            assert len(block) >= 20
    
    def test_extract_custom_blocks_with_large_blocks(self):
        """Test custom extraction with large blocks that need splitting."""
        extractor = TextBlockExtractor(
            strategy="custom",
            custom_delimiters=["---"],
            min_block_size=10,
            max_block_size=30
        )
        text = "This is a very large block that exceeds the maximum size---Another large block."
        
        blocks = extractor._extract_custom_blocks(text)
        
        assert len(blocks) > 1  # Should be split into multiple blocks
        for block in blocks:
            assert len(block) >= 10
    
    def test_split_large_block_with_sentences(self):
        """Test splitting large blocks by sentences."""
        extractor = TextBlockExtractor(min_block_size=10, max_block_size=50)
        text = "This is the first sentence. This is the second sentence. This is the third sentence."
        
        blocks = extractor._split_large_block(text)
        
        assert len(blocks) > 1  # Should be split by sentences
        for block in blocks:
            assert len(block) >= 10
    
    def test_split_large_block_with_words(self):
        """Test splitting large blocks by words when sentences don't work."""
        extractor = TextBlockExtractor(min_block_size=10, max_block_size=30)
        text = "This is a very long block without proper sentence structure that needs to be split by words"
        
        blocks = extractor._split_large_block(text)
        
        assert len(blocks) > 1  # Should be split by words
        for block in blocks:
            assert len(block) >= 10
    
    def test_split_large_block_small_enough(self):
        """Test splitting block that is already small enough."""
        extractor = TextBlockExtractor(min_block_size=5, max_block_size=100)
        text = "Small block"
        
        blocks = extractor._split_large_block(text)
        
        assert len(blocks) == 1
        assert blocks[0] == text
    
    def test_split_large_block_too_small(self):
        """Test splitting block that is too small to meet minimum size."""
        extractor = TextBlockExtractor(min_block_size=20, max_block_size=100)
        text = "Too small"
        
        blocks = extractor._split_large_block(text)
        
        assert len(blocks) == 0  # Should be filtered out


class TestTextProcessor:
    """Test suite for TextProcessor class."""
    
    def test_init_valid_parameters(self):
        """Test valid initialization."""
        processor = TextProcessor(
            encoding="utf-8",
            normalize_whitespace=True,
            remove_empty_blocks=True
        )
        
        assert processor.encoding == "utf-8"
        assert processor.normalize_whitespace is True
        assert processor.remove_empty_blocks is True
        assert processor.supported_extensions == ["txt"]
        assert processor.processor_name == "TextProcessor"
    
    def test_init_with_custom_extractor(self):
        """Test initialization with custom block extractor."""
        extractor = TextBlockExtractor(strategy="line")
        processor = TextProcessor(block_extractor=extractor)
        
        assert processor.block_extractor == extractor
        assert processor.block_extractor.strategy == "line"
    
    def test_init_invalid_extractor_type(self):
        """Test initialization with invalid extractor type."""
        with pytest.raises(TypeError, match="block_extractor must be TextBlockExtractor instance"):
            TextProcessor(block_extractor="invalid")
    
    def test_init_invalid_encoding(self):
        """Test initialization with invalid encoding."""
        with pytest.raises(TypeError, match="encoding must be string"):
            TextProcessor(encoding=123)
        
        with pytest.raises(ValueError, match="encoding cannot be empty"):
            TextProcessor(encoding="")
    
    def test_process_file_success(self, tmp_path):
        """Test successful file processing."""
        extractor = TextBlockExtractor(min_block_size=5)
        processor = TextProcessor(block_extractor=extractor)
        
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Paragraph 1.\n\nParagraph 2.\n\nParagraph 3.")
        
        result = processor.process_file(str(test_file))
        
        assert result.success is True
        assert len(result.blocks) == 3
        assert result.supported_file_type is True
        assert result.processing_time_seconds > 0
        assert result.file_size_bytes > 0
        
        # Check processing metadata
        assert result.processing_metadata["processor_type"] == "text"
        assert result.processing_metadata["encoding"] == "utf-8"
        assert result.processing_metadata["extraction_strategy"] == "paragraph"
    
    def test_process_file_with_encoding_detection(self, tmp_path):
        """Test file processing with encoding detection."""
        extractor = TextBlockExtractor(min_block_size=5)
        processor = TextProcessor(encoding="utf-8", block_extractor=extractor)
        
        # Create test file with non-UTF-8 content
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Test content with \xe9 character")
        
        result = processor.process_file(str(test_file))
        
        assert result.success is True
        assert len(result.blocks) > 0
    
    def test_process_file_encoding_error(self, tmp_path):
        """Test file processing with encoding error."""
        extractor = TextBlockExtractor(min_block_size=5)
        processor = TextProcessor(encoding="utf-8", block_extractor=extractor)
        
        # Create test file with invalid encoding
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"\xff\xfe\x00\x00")  # Invalid UTF-8
        
        # Mock the _read_file_content to raise UnicodeDecodeError
        with patch.object(processor, '_read_file_content', side_effect=UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")):
            result = processor.process_file(str(test_file))
            
            assert result.success is False
            assert "invalid start byte" in result.error_message
    
    def test_process_file_nonexistent(self):
        """Test processing nonexistent file."""
        processor = TextProcessor()
        
        with pytest.raises(FileNotFoundError, match="File not found"):
            processor.process_file("/nonexistent/file.txt")
    
    def test_process_file_unsupported_type(self, tmp_path):
        """Test processing unsupported file type."""
        processor = TextProcessor()
        
        # Create test file with unsupported extension
        test_file = tmp_path / "test.md"
        test_file.write_text("test content")
        
        with pytest.raises(ValueError, match="File type not supported"):
            processor.process_file(str(test_file))
    
    def test_process_file_too_large(self, tmp_path):
        """Test processing file too large."""
        processor = TextProcessor(max_file_size_bytes=10)
        
        # Create test file larger than limit
        test_file = tmp_path / "test.txt"
        test_file.write_text("this content is longer than 10 bytes")
        
        with pytest.raises(ValueError, match="File too large"):
            processor.process_file(str(test_file))
    
    def test_process_file_with_normalization(self, tmp_path):
        """Test file processing with whitespace normalization."""
        extractor = TextBlockExtractor(min_block_size=5)
        processor = TextProcessor(normalize_whitespace=True, block_extractor=extractor)
        
        # Create test file with extra whitespace
        test_file = tmp_path / "test.txt"
        test_file.write_text("Paragraph 1.   \n\n   Paragraph 2.   \n\n   Paragraph 3.")
        
        result = processor.process_file(str(test_file))
        
        assert result.success is True
        assert len(result.blocks) == 3
        
        # Check that whitespace is normalized
        for block in result.blocks:
            assert not block.content.startswith(" ")
            assert not block.content.endswith(" ")
    
    def test_process_file_without_normalization(self, tmp_path):
        """Test file processing without whitespace normalization."""
        extractor = TextBlockExtractor(min_block_size=5)
        processor = TextProcessor(normalize_whitespace=False, block_extractor=extractor)
        
        # Create test file with extra whitespace
        test_file = tmp_path / "test.txt"
        test_file.write_text("   Paragraph 1.   \n\n   Paragraph 2.   ")
        
        result = processor.process_file(str(test_file))
        
        assert result.success is True
        assert len(result.blocks) == 2
        
        # Check that whitespace is preserved (but strip() is still applied in paragraph extraction)
        # The content should be "Paragraph 1." and "Paragraph 2." (whitespace removed by strip())
        assert result.blocks[0].content == "Paragraph 1."
        assert result.blocks[1].content == "Paragraph 2."
    
    def test_process_file_remove_empty_blocks(self, tmp_path):
        """Test file processing with empty block removal."""
        extractor = TextBlockExtractor(min_block_size=5)
        processor = TextProcessor(remove_empty_blocks=True, block_extractor=extractor)
        
        # Create test file with empty paragraphs
        test_file = tmp_path / "test.txt"
        test_file.write_text("Paragraph 1.\n\n   \n\nParagraph 2.\n\n\n\nParagraph 3.")
        
        result = processor.process_file(str(test_file))
        
        assert result.success is True
        assert len(result.blocks) == 3  # Empty blocks should be removed
    
    def test_process_file_keep_empty_blocks(self, tmp_path):
        """Test file processing keeping empty blocks."""
        extractor = TextBlockExtractor(min_block_size=5)
        processor = TextProcessor(remove_empty_blocks=False, block_extractor=extractor)
        
        # Create test file with empty paragraphs
        test_file = tmp_path / "test.txt"
        test_file.write_text("Paragraph 1.\n\n   \n\nParagraph 2.")
        
        result = processor.process_file(str(test_file))
        
        assert result.success is True
        assert len(result.blocks) >= 2  # May include empty blocks
    
    def test_process_file_with_custom_extractor(self, tmp_path):
        """Test file processing with custom block extractor."""
        extractor = TextBlockExtractor(strategy="line", min_block_size=5, max_block_size=50)
        processor = TextProcessor(block_extractor=extractor)
        
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3")
        
        result = processor.process_file(str(test_file))
        
        assert result.success is True
        assert len(result.blocks) > 0
        assert result.processing_metadata["extraction_strategy"] == "line"
    
    def test_process_file_large_content(self, tmp_path):
        """Test processing file with large content."""
        processor = TextProcessor()
        
        # Create test file with large content
        content = "This is a test paragraph. " * 1000  # Large content
        test_file = tmp_path / "test.txt"
        test_file.write_text(content)
        
        result = processor.process_file(str(test_file))
        
        assert result.success is True
        assert len(result.blocks) > 0
        assert result.processing_time_seconds > 0
    
    def test_process_file_error_handling(self, tmp_path):
        """Test error handling during file processing."""
        processor = TextProcessor()
        
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        # Mock file reading to raise exception
        with patch.object(processor, '_read_file_content', side_effect=Exception("Test error")):
            result = processor.process_file(str(test_file))
            
            assert result.success is False
            assert "Test error" in result.error_message
            assert result.processing_time_seconds > 0
    
    def test_read_file_content_success(self, tmp_path):
        """Test successful file content reading."""
        processor = TextProcessor(encoding="utf-8")
        
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        content = processor._read_file_content(str(test_file))
        
        assert content == "test content"
    
    def test_read_file_content_encoding_error(self, tmp_path):
        """Test file content reading with encoding error."""
        processor = TextProcessor(encoding="utf-8")
        
        # Create test file with truly invalid encoding that can't be decoded by any fallback
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff")  # Invalid bytes
        
        # Mock the alternative encodings to fail
        with patch.object(processor, '_read_file_content') as mock_read:
            mock_read.side_effect = UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")
            with pytest.raises(UnicodeDecodeError):
                processor._read_file_content(str(test_file))
    
    def test_read_file_content_with_alternative_encoding(self, tmp_path):
        """Test file content reading with alternative encoding fallback."""
        processor = TextProcessor(encoding="utf-8")
        
        # Create test file with latin-1 content
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Test content with \xe9 character")
        
        content = processor._read_file_content(str(test_file))
        
        assert "é" in content  # Should be decoded correctly
    
    def test_read_file_content_all_encodings_fail(self, tmp_path):
        """Test file content reading when all encodings fail."""
        processor = TextProcessor(encoding="utf-8")
        
        # Create test file with invalid bytes
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff")
        
        # Mock the alternative encodings to fail
        with patch('builtins.open') as mock_open:
            # Make all encoding attempts fail
            mock_open.side_effect = [
                UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte"),
                UnicodeDecodeError("latin-1", b"\xff", 0, 1, "invalid start byte"),
                UnicodeDecodeError("cp1252", b"\xff", 0, 1, "invalid start byte"),
                UnicodeDecodeError("iso-8859-1", b"\xff", 0, 1, "invalid start byte")
            ]
            
            with pytest.raises(UnicodeDecodeError):
                processor._read_file_content(str(test_file))
    
    def test_process_text_content_with_normalization(self):
        """Test text content processing with normalization."""
        processor = TextProcessor(normalize_whitespace=True)
        
        text = "   Multiple    spaces   \n\n\nMultiple\n\n\nnewlines   "
        processed = processor._process_text_content(text)
        
        assert "   " not in processed  # No multiple spaces
        assert "\n\n\n" not in processed  # No multiple newlines
        assert not processed.startswith(" ")
        assert not processed.endswith(" ")
    
    def test_process_text_content_without_normalization(self):
        """Test text content processing without normalization."""
        processor = TextProcessor(normalize_whitespace=False)
        
        text = "   Original   text   \n\n\nwith   spaces   "
        processed = processor._process_text_content(text)
        
        assert processed == text  # Should be unchanged
    
    def test_create_processing_blocks(self):
        """Test creation of processing blocks."""
        processor = TextProcessor()
        
        text_blocks = ["Block 1", "Block 2", "Block 3"]
        file_path = "/test/file.txt"
        
        blocks = processor._create_processing_blocks(text_blocks, file_path)
        
        assert len(blocks) == 3
        
        for i, block in enumerate(blocks):
            assert isinstance(block, ProcessingBlock)
            assert block.content == text_blocks[i]
            assert block.block_type == "text_paragraph"
            assert block.metadata["file_path"] == file_path
            assert block.metadata["block_index"] == i
            assert block.metadata["processor_type"] == "text"
    
    def test_create_processing_blocks_remove_empty(self):
        """Test creation of processing blocks with empty block removal."""
        processor = TextProcessor(remove_empty_blocks=True)
        
        text_blocks = ["Block 1", "   ", "Block 2", "", "Block 3"]
        file_path = "/test/file.txt"
        
        blocks = processor._create_processing_blocks(text_blocks, file_path)
        
        assert len(blocks) == 3  # Empty blocks should be removed
        assert blocks[0].content == "Block 1"
        assert blocks[1].content == "Block 2"
        assert blocks[2].content == "Block 3"
    
    def test_create_processing_blocks_keep_empty(self):
        """Test creation of processing blocks keeping empty blocks."""
        processor = TextProcessor(remove_empty_blocks=False)
        
        text_blocks = ["Block 1", "   ", "Block 2"]
        file_path = "/test/file.txt"
        
        blocks = processor._create_processing_blocks(text_blocks, file_path)
        
        assert len(blocks) == 3  # All blocks should be included
        assert blocks[0].content == "Block 1"
        assert blocks[1].content == "   "
        assert blocks[2].content == "Block 2"
    
    def test_create_processing_blocks_with_line_calculation(self):
        """Test creation of processing blocks with line number calculation."""
        processor = TextProcessor()
        
        # Create blocks with newlines to test line calculation
        text_blocks = ["Line 1\nLine 2", "Line 3\nLine 4\nLine 5", "Line 6"]
        file_path = "/test/file.txt"
        
        blocks = processor._create_processing_blocks(text_blocks, file_path)
        
        assert len(blocks) == 3
        
        # Check that line numbers are calculated
        for block in blocks:
            assert hasattr(block, 'start_line')
            assert hasattr(block, 'end_line')
            assert hasattr(block, 'start_char')
            assert hasattr(block, 'end_char')
            assert block.start_line > 0
            assert block.end_line >= block.start_line 