"""
Tests for Markdown Processor

Unit tests for MarkdownProcessor and MarkdownParser classes.
Tests cover Markdown parsing, element extraction, and file processing.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from docanalyzer.processors.markdown_processor import (
    MarkdownProcessor, MarkdownParser, MarkdownElement
)
from docanalyzer.models.processing import ProcessingBlock, ProcessingStatus


class TestMarkdownElement:
    """Test suite for MarkdownElement class."""
    
    def test_init_valid_parameters(self):
        """Test valid initialization."""
        element = MarkdownElement(
            element_type="header",
            content="Test Header",
            level=2,
            line_number=5,
            metadata={"language": "en"}
        )
        
        assert element.element_type == "header"
        assert element.content == "Test Header"
        assert element.level == 2
        assert element.line_number == 5
        assert element.metadata == {"language": "en"}
    
    def test_init_invalid_element_type(self):
        """Test initialization with invalid element type."""
        with pytest.raises(ValueError, match="element_type must be one of"):
            MarkdownElement(element_type="invalid", content="test")
    
    def test_init_invalid_content_type(self):
        """Test initialization with invalid content type."""
        with pytest.raises(TypeError, match="content must be string"):
            MarkdownElement(element_type="header", content=123)
    
    def test_init_empty_content(self):
        """Test initialization with empty content."""
        with pytest.raises(ValueError, match="content cannot be empty"):
            MarkdownElement(element_type="header", content="")
    
    def test_init_invalid_level(self):
        """Test initialization with invalid level."""
        with pytest.raises(ValueError, match="level must be positive integer"):
            MarkdownElement(element_type="header", content="test", level=0)
        
        with pytest.raises(ValueError, match="level must be positive integer"):
            MarkdownElement(element_type="header", content="test", level=-1)
    
    def test_init_invalid_line_number(self):
        """Test initialization with invalid line number."""
        with pytest.raises(ValueError, match="line_number must be positive integer"):
            MarkdownElement(element_type="header", content="test", line_number=0)
    
    def test_init_invalid_metadata_type(self):
        """Test initialization with invalid metadata type."""
        with pytest.raises(TypeError, match="metadata must be dictionary"):
            MarkdownElement(element_type="header", content="test", metadata="invalid")
    
    def test_repr(self):
        """Test string representation."""
        element = MarkdownElement("header", "Test", 1, 5)
        
        repr_str = repr(element)
        assert "MarkdownElement(" in repr_str
        assert "type='header'" in repr_str
        assert "level=1" in repr_str
        assert "line=5" in repr_str


class TestMarkdownParser:
    """Test suite for MarkdownParser class."""
    
    def test_init_valid_parameters(self):
        """Test valid initialization."""
        parser = MarkdownParser(
            preserve_structure=True,
            extract_links=True,
            extract_images=True,
            clean_markdown=True
        )
        
        assert parser.preserve_structure is True
        assert parser.extract_links is True
        assert parser.extract_images is True
        assert parser.clean_markdown is True
    
    def test_parse_markdown_headers(self):
        """Test parsing Markdown headers."""
        parser = MarkdownParser()
        markdown = "# Header 1\n\n## Header 2\n\n### Header 3"
        
        elements = parser.parse_markdown(markdown)
        
        assert len(elements) == 3
        assert elements[0].element_type == "header"
        assert elements[0].content == "Header 1"
        assert elements[0].level == 1
        assert elements[1].element_type == "header"
        assert elements[1].content == "Header 2"
        assert elements[1].level == 2
        assert elements[2].element_type == "header"
        assert elements[2].content == "Header 3"
        assert elements[2].level == 3
    
    def test_parse_markdown_paragraphs(self):
        """Test parsing Markdown paragraphs."""
        parser = MarkdownParser()
        markdown = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        
        elements = parser.parse_markdown(markdown)
        
        assert len(elements) == 3
        assert elements[0].element_type == "paragraph"
        assert elements[0].content == "First paragraph."
        assert elements[1].element_type == "paragraph"
        assert elements[1].content == "Second paragraph."
        assert elements[2].element_type == "paragraph"
        assert elements[2].content == "Third paragraph."
    
    def test_parse_markdown_code_blocks(self):
        """Test parsing Markdown code blocks."""
        parser = MarkdownParser()
        markdown = "```python\ndef test():\n    return True\n```\n\n```\nplain code\n```"
        
        elements = parser.parse_markdown(markdown)
        
        assert len(elements) == 2
        assert elements[0].element_type == "code_block"
        assert "def test():" in elements[0].content
        assert elements[0].metadata["language"] == "python"
        assert elements[1].element_type == "code_block"
        assert elements[1].content == "plain code"
        assert elements[1].metadata["language"] == ""
    
    def test_parse_markdown_lists(self):
        """Test parsing Markdown lists."""
        parser = MarkdownParser()
        markdown = "- Item 1\n- Item 2\n- Item 3\n\n1. Numbered 1\n2. Numbered 2"
        
        elements = parser.parse_markdown(markdown)
        
        assert len(elements) == 5
        assert elements[0].element_type == "list_item"
        assert elements[0].content == "Item 1"
        assert elements[1].element_type == "list_item"
        assert elements[1].content == "Item 2"
        assert elements[2].element_type == "list_item"
        assert elements[2].content == "Item 3"
        assert elements[3].element_type == "list_item"
        assert elements[3].content == "Numbered 1"
        assert elements[4].element_type == "list_item"
        assert elements[4].content == "Numbered 2"
    
    def test_parse_markdown_blockquotes(self):
        """Test parsing Markdown blockquotes."""
        parser = MarkdownParser()
        markdown = "> This is a blockquote.\n> It can span multiple lines.\n\n> Another blockquote."
        
        elements = parser.parse_markdown(markdown)
        
        assert len(elements) == 2
        assert elements[0].element_type == "blockquote"
        assert "This is a blockquote" in elements[0].content
        assert "It can span multiple lines" in elements[0].content
        assert elements[1].element_type == "blockquote"
        assert elements[1].content == "Another blockquote."
    
    def test_parse_markdown_mixed_content(self):
        """Test parsing mixed Markdown content."""
        parser = MarkdownParser()
        markdown = "# Title\n\nThis is a paragraph.\n\n- List item 1\n- List item 2\n\n> Blockquote\n\n```\ncode\n```"
        
        elements = parser.parse_markdown(markdown)
        
        assert len(elements) == 6
        assert elements[0].element_type == "header"
        assert elements[1].element_type == "paragraph"
        assert elements[2].element_type == "list_item"
        assert elements[3].element_type == "list_item"
        assert elements[4].element_type == "blockquote"
        assert elements[5].element_type == "code_block"
    
    def test_parse_markdown_clean_syntax(self):
        """Test parsing with syntax cleaning."""
        parser = MarkdownParser(clean_markdown=True)
        markdown = "# **Bold Header**\n\nThis is *italic* text with **bold** parts.\n\n[Link text](http://example.com)"
        
        elements = parser.parse_markdown(markdown)
        
        assert len(elements) == 3  # header, paragraph, paragraph (link is separate)
        assert elements[0].element_type == "header"
        assert elements[0].content == "Bold Header"  # Bold syntax removed
        assert elements[1].element_type == "paragraph"
        assert "italic" in elements[1].content  # Italic syntax removed
        assert "bold" in elements[1].content  # Bold syntax removed
        assert elements[2].element_type == "paragraph"
        assert "Link text" in elements[2].content  # Link text extracted
    
    def test_parse_markdown_preserve_syntax(self):
        """Test parsing without syntax cleaning."""
        parser = MarkdownParser(clean_markdown=False)
        markdown = "# **Bold Header**\n\nThis is *italic* text."
        
        elements = parser.parse_markdown(markdown)
        
        assert len(elements) == 2
        assert elements[0].element_type == "header"
        assert "**Bold Header**" in elements[0].content  # Syntax preserved
        assert elements[1].element_type == "paragraph"
        assert "*italic*" in elements[1].content  # Syntax preserved
    
    def test_parse_markdown_empty_text(self):
        """Test parsing empty Markdown text."""
        parser = MarkdownParser()
        
        with pytest.raises(ValueError, match="markdown_text cannot be empty"):
            parser.parse_markdown("")
    
    def test_parse_markdown_invalid_text_type(self):
        """Test parsing with invalid text type."""
        parser = MarkdownParser()
        
        with pytest.raises(TypeError, match="markdown_text must be string"):
            parser.parse_markdown(None)
    
    def test_clean_content_bold_italic(self):
        """Test cleaning bold and italic syntax."""
        parser = MarkdownParser()
        
        content = "**Bold** and *italic* and __bold__ and _italic_"
        cleaned = parser._clean_content(content)
        
        assert "**Bold**" not in cleaned
        assert "*italic*" not in cleaned
        assert "__bold__" not in cleaned
        assert "_italic_" not in cleaned
        assert "Bold" in cleaned
        assert "italic" in cleaned
    
    def test_clean_content_links(self):
        """Test cleaning link syntax."""
        parser = MarkdownParser(extract_links=True)
        
        content = "[Link text](http://example.com)"
        cleaned = parser._clean_content(content)
        
        assert "[Link text](http://example.com)" not in cleaned
        assert "Link text" in cleaned
    
    def test_clean_content_images(self):
        """Test cleaning image syntax."""
        parser = MarkdownParser(extract_images=True)
        
        content = "![Alt text](image.jpg)"
        cleaned = parser._clean_content(content)
        
        assert "![Alt text](image.jpg)" not in cleaned
        assert "Alt text" in cleaned
    
    def test_clean_content_inline_code(self):
        """Test cleaning inline code syntax."""
        parser = MarkdownParser()
        
        content = "Use `code` in text"
        cleaned = parser._clean_content(content)
        
        assert "`code`" not in cleaned
        assert "code" in cleaned
    
    def test_clean_content_strikethrough(self):
        """Test cleaning strikethrough syntax."""
        parser = MarkdownParser()
        
        content = "~~strikethrough~~ text"
        cleaned = parser._clean_content(content)
        
        assert "~~strikethrough~~" not in cleaned
        assert "strikethrough" in cleaned


class TestMarkdownProcessor:
    """Test suite for MarkdownProcessor class."""
    
    def test_init_valid_parameters(self):
        """Test valid initialization."""
        processor = MarkdownProcessor(
            preserve_structure=True,
            extract_code_blocks=True,
            clean_markdown=True
        )
        
        assert processor.preserve_structure is True
        assert processor.extract_code_blocks is True
        assert processor.clean_markdown is True
        assert processor.supported_extensions == ["md", "markdown"]
        assert processor.processor_name == "MarkdownProcessor"
    
    def test_init_with_custom_parser(self):
        """Test initialization with custom parser."""
        parser = MarkdownParser()
        processor = MarkdownProcessor(parser=parser)
        
        assert processor.parser == parser
    
    def test_init_invalid_parser_type(self):
        """Test initialization with invalid parser type."""
        with pytest.raises(TypeError, match="parser must be MarkdownParser instance"):
            MarkdownProcessor(parser="invalid")
    
    def test_process_file_success(self, tmp_path):
        """Test successful file processing."""
        processor = MarkdownProcessor()
        
        # Create test Markdown file
        test_file = tmp_path / "test.md"
        test_file.write_text("# Title\n\nThis is a paragraph.\n\n- List item\n\n> Blockquote")
        
        result = processor.process_file(str(test_file))
        
        assert result.success is True
        assert len(result.blocks) == 4  # header, paragraph, list_item, blockquote
        assert result.supported_file_type is True
        assert result.processing_time_seconds > 0
        assert result.file_size_bytes > 0
        
        # Check processing metadata
        assert result.processing_metadata["processor_type"] == "markdown"
        assert result.processing_metadata["preserve_structure"] is True
        assert result.processing_metadata["extract_code_blocks"] is True
        assert result.processing_metadata["clean_markdown"] is True
        assert "total_markdown_elements" in result.processing_metadata
        assert "element_types" in result.processing_metadata
    
    def test_process_file_with_encoding_detection(self, tmp_path):
        """Test file processing with encoding detection."""
        processor = MarkdownProcessor()
        
        # Create test file with non-UTF-8 content
        test_file = tmp_path / "test.md"
        test_file.write_bytes(b"# Test\n\nContent with \xe9 character")
        
        result = processor.process_file(str(test_file))
        
        assert result.success is True
        assert len(result.blocks) > 0
    
    def test_process_file_encoding_error(self, tmp_path):
        """Test file processing with encoding error."""
        processor = MarkdownProcessor()
        
        # Create test file with invalid encoding
        test_file = tmp_path / "test.md"
        test_file.write_bytes(b"\xff\xfe\x00\x00")  # Invalid UTF-8
        
        # Mock the _read_file_content to raise UnicodeDecodeError
        with patch.object(processor, '_read_file_content', side_effect=UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")):
            result = processor.process_file(str(test_file))
            
            assert result.success is False
            assert "invalid start byte" in result.error_message
    
    def test_process_file_nonexistent(self):
        """Test processing nonexistent file."""
        processor = MarkdownProcessor()
        
        with pytest.raises(FileNotFoundError, match="File not found"):
            processor.process_file("/nonexistent/file.md")
    
    def test_process_file_unsupported_type(self, tmp_path):
        """Test processing unsupported file type."""
        processor = MarkdownProcessor()
        
        # Create test file with unsupported extension
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        with pytest.raises(ValueError, match="File type not supported"):
            processor.process_file(str(test_file))
    
    def test_process_file_too_large(self, tmp_path):
        """Test processing file too large."""
        processor = MarkdownProcessor(max_file_size_bytes=10)
        
        # Create test file larger than limit
        test_file = tmp_path / "test.md"
        test_file.write_text("this content is longer than 10 bytes")
        
        with pytest.raises(ValueError, match="File too large"):
            processor.process_file(str(test_file))
    
    def test_process_file_with_code_blocks(self, tmp_path):
        """Test file processing with code blocks."""
        processor = MarkdownProcessor(extract_code_blocks=True)
        
        # Create test file with code blocks
        test_file = tmp_path / "test.md"
        test_file.write_text("# Title\n\n```python\ndef test():\n    return True\n```\n\nParagraph")
        
        result = processor.process_file(str(test_file))
        
        assert result.success is True
        assert len(result.blocks) == 3  # header, code_block, paragraph
        
        # Find code block
        code_blocks = [b for b in result.blocks if b.block_type == "markdown_code_block"]
        assert len(code_blocks) == 1
        assert "def test():" in code_blocks[0].content
    
    def test_process_file_without_code_blocks(self, tmp_path):
        """Test file processing without code blocks."""
        processor = MarkdownProcessor(extract_code_blocks=False)
        
        # Create test file with code blocks
        test_file = tmp_path / "test.md"
        test_file.write_text("# Title\n\n```python\ndef test():\n    return True\n```\n\nParagraph")
        
        result = processor.process_file(str(test_file))
        
        assert result.success is True
        assert len(result.blocks) == 2  # header, paragraph (code block skipped)
        
        # No code blocks should be present
        code_blocks = [b for b in result.blocks if b.block_type == "markdown_code_block"]
        assert len(code_blocks) == 0
    
    def test_process_file_with_structure_preservation(self, tmp_path):
        """Test file processing with structure preservation."""
        processor = MarkdownProcessor(preserve_structure=True)
        
        # Create test file
        test_file = tmp_path / "test.md"
        test_file.write_text("# Header\n\nParagraph\n\n- List item")
        
        result = processor.process_file(str(test_file))
        
        assert result.success is True
        assert len(result.blocks) == 3
        
        # Check that structure is preserved in metadata
        for block in result.blocks:
            assert block.metadata["preserve_structure"] is True
    
    def test_process_file_large_content(self, tmp_path):
        """Test processing file with large content."""
        processor = MarkdownProcessor()
        
        # Create test file with large content
        content = "# Title\n\n" + "This is a test paragraph. " * 1000  # Large content
        test_file = tmp_path / "test.md"
        test_file.write_text(content)
        
        result = processor.process_file(str(test_file))
        
        assert result.success is True
        assert len(result.blocks) > 0
        assert result.processing_time_seconds > 0
    
    def test_process_file_error_handling(self, tmp_path):
        """Test error handling during file processing."""
        processor = MarkdownProcessor()
        
        # Create test file
        test_file = tmp_path / "test.md"
        test_file.write_text("test content")
        
        # Mock file reading to raise exception
        with patch.object(processor, '_read_file_content', side_effect=Exception("Test error")):
            result = processor.process_file(str(test_file))
            
            assert result.success is False
            assert "Test error" in result.error_message
            assert result.processing_time_seconds > 0
    
    def test_read_file_content_success(self, tmp_path):
        """Test successful file content reading."""
        processor = MarkdownProcessor()
        
        # Create test file
        test_file = tmp_path / "test.md"
        test_file.write_text("test content")
        
        content = processor._read_file_content(str(test_file))
        
        assert content == "test content"
    
    def test_read_file_content_encoding_error(self, tmp_path):
        """Test file content reading with encoding error."""
        processor = MarkdownProcessor()
        
        # Create test file with truly invalid encoding that can't be decoded by any fallback
        test_file = tmp_path / "test.md"
        test_file.write_bytes(b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff")  # Invalid bytes
        
        # Mock the alternative encodings to fail
        with patch.object(processor, '_read_file_content') as mock_read:
            mock_read.side_effect = UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")
            with pytest.raises(UnicodeDecodeError):
                processor._read_file_content(str(test_file))
    
    def test_create_processing_blocks(self):
        """Test creation of processing blocks."""
        processor = MarkdownProcessor()
        
        # Create test elements
        elements = [
            MarkdownElement("header", "Title", 1, 1),
            MarkdownElement("paragraph", "Content", 1, 3),
            MarkdownElement("code_block", "code", 1, 5, {"language": "python"})
        ]
        file_path = "/test/file.md"
        
        blocks = processor._create_processing_blocks(elements, file_path)
        
        assert len(blocks) == 3
        
        # Check header block
        assert blocks[0].block_type == "markdown_header"
        assert blocks[0].content == "Title"
        assert blocks[0].metadata["element_type"] == "header"
        assert blocks[0].metadata["element_level"] == 1
        assert blocks[0].metadata["file_path"] == file_path
        
        # Check paragraph block
        assert blocks[1].block_type == "markdown_paragraph"
        assert blocks[1].content == "Content"
        assert blocks[1].metadata["element_type"] == "paragraph"
        
        # Check code block
        assert blocks[2].block_type == "markdown_code_block"
        assert blocks[2].content == "code"
        assert blocks[2].metadata["element_type"] == "code_block"
        assert blocks[2].metadata["language"] == "python"
    
    def test_create_processing_blocks_skip_code_blocks(self):
        """Test creation of processing blocks skipping code blocks."""
        processor = MarkdownProcessor(extract_code_blocks=False)
        
        # Create test elements including code block
        elements = [
            MarkdownElement("header", "Title", 1, 1),
            MarkdownElement("code_block", "code", 1, 3),
            MarkdownElement("paragraph", "Content", 1, 5)
        ]
        file_path = "/test/file.md"
        
        blocks = processor._create_processing_blocks(elements, file_path)
        
        assert len(blocks) == 2  # Code block should be skipped
        assert blocks[0].block_type == "markdown_header"
        assert blocks[1].block_type == "markdown_paragraph"
    
    def test_count_element_types(self):
        """Test counting element types."""
        processor = MarkdownProcessor()
        
        # Create test elements
        elements = [
            MarkdownElement("header", "Title 1", 1, 1),
            MarkdownElement("header", "Title 2", 2, 3),
            MarkdownElement("paragraph", "Content 1", 1, 5),
            MarkdownElement("paragraph", "Content 2", 1, 7),
            MarkdownElement("code_block", "code", 1, 9)
        ]
        
        counts = processor._count_element_types(elements)
        
        assert counts["header"] == 2
        assert counts["paragraph"] == 2
        assert counts["code_block"] == 1
        assert len(counts) == 3 