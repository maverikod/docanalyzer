"""
Markdown Processor - Markdown File Processing

Implements file processing for Markdown files (.md extension).
Extracts text blocks from Markdown files with support for different
Markdown elements and formatting options.

This processor handles:
- Markdown files with .md extension
- Extraction of headers, paragraphs, code blocks, lists, and other elements
- Markdown syntax parsing and cleaning
- Preservation of semantic structure

Author: DocAnalyzer Team
Version: 1.0.0
"""

from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging
from datetime import datetime
import time
import re

from .base_processor import BaseProcessor, ProcessorResult
from docanalyzer.models.processing import ProcessingBlock, ProcessingStatus

logger = logging.getLogger(__name__)


class MarkdownElement:
    """
    Markdown Element - Markdown Structure Component
    
    Represents a single Markdown element (header, paragraph, code block, etc.)
    with its content, type, and metadata. Used for structured processing
    of Markdown documents.
    
    Attributes:
        element_type (str): Type of Markdown element.
            Must be one of: 'header', 'paragraph', 'code_block', 'list_item', 'blockquote'.
        content (str): Text content of the element.
            Cleaned text without Markdown syntax.
        level (int): Element level (for headers: 1-6, for lists: nesting level).
            Must be positive integer.
        line_number (int): Line number where element starts in original file.
            Must be positive integer.
        metadata (Dict[str, Any]): Additional element metadata.
            Can contain language info, list type, etc.
    
    Example:
        >>> element = MarkdownElement('header', '# Title', 1, 1)
        >>> print(element.content)  # "Title"
        >>> print(element.level)    # 1
    
    Raises:
        ValueError: If element_type is invalid or level is not positive
        TypeError: If content is not string or metadata is not dict
    """
    
    def __init__(
        self,
        element_type: str,
        content: str,
        level: int = 1,
        line_number: int = 1,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize MarkdownElement instance.
        
        Args:
            element_type (str): Type of Markdown element.
                Must be one of: 'header', 'paragraph', 'code_block', 'list_item', 'blockquote'.
            content (str): Text content of the element.
                Must be non-empty string.
            level (int, optional): Element level.
                Defaults to 1. Must be positive integer.
            line_number (int, optional): Line number in original file.
                Defaults to 1. Must be positive integer.
            metadata (Optional[Dict[str, Any]], optional): Additional metadata.
                Defaults to None.
        
        Raises:
            ValueError: If element_type is invalid or level is not positive
            TypeError: If content is not string or metadata is not dict
        """
        # Validate element_type
        valid_types = ["header", "paragraph", "code_block", "list_item", "blockquote"]
        if element_type not in valid_types:
            raise ValueError(f"element_type must be one of {valid_types}")
        
        # Validate content
        if not isinstance(content, str):
            raise TypeError("content must be string")
        if not content:
            raise ValueError("content cannot be empty")
        
        # Validate level
        if not isinstance(level, int) or level <= 0:
            raise ValueError("level must be positive integer")
        
        # Validate line_number
        if not isinstance(line_number, int) or line_number <= 0:
            raise ValueError("line_number must be positive integer")
        
        # Validate metadata
        if metadata is not None and not isinstance(metadata, dict):
            raise TypeError("metadata must be dictionary")
        
        # Set attributes
        self.element_type = element_type
        self.content = content
        self.level = level
        self.line_number = line_number
        self.metadata = metadata or {}
    
    def __repr__(self) -> str:
        """
        String representation of MarkdownElement.
        
        Returns:
            str: Human-readable representation.
        
        Example:
            >>> element = MarkdownElement('header', 'Title', 1, 1)
            >>> print(element)  # "MarkdownElement(type='header', level=1, line=1)"
        """
        return (
            f"MarkdownElement("
            f"type='{self.element_type}', "
            f"level={self.level}, "
            f"line={self.line_number}"
            f")"
        )


class MarkdownParser:
    """
    Markdown Parser - Markdown Document Parser
    
    Parses Markdown documents and extracts structured elements.
    Supports various Markdown syntax elements and provides
    clean text extraction with semantic structure preservation.
    
    This parser handles:
    - Headers (# ## ### etc.)
    - Paragraphs and text blocks
    - Code blocks (``` ```)
    - Lists (ordered and unordered)
    - Blockquotes (>)
    - Links and images (extracts text only)
    
    Attributes:
        preserve_structure (bool): Whether to preserve semantic structure.
            True to maintain element relationships, False for flat extraction.
        extract_links (bool): Whether to extract link text.
            True to include link text in content, False to skip links.
        extract_images (bool): Whether to extract image alt text.
            True to include image alt text, False to skip images.
        clean_markdown (bool): Whether to clean Markdown syntax.
            True to remove syntax, False to preserve some formatting.
    
    Example:
        >>> parser = MarkdownParser()
        >>> elements = parser.parse_markdown("# Title\n\nContent")
        >>> print(len(elements))  # 2 (header + paragraph)
    
    Raises:
        ValueError: If markdown_text is empty
        TypeError: If markdown_text is not string
    """
    
    def __init__(
        self,
        preserve_structure: bool = True,
        extract_links: bool = True,
        extract_images: bool = True,
        clean_markdown: bool = True
    ):
        """
        Initialize MarkdownParser instance.
        
        Args:
            preserve_structure (bool, optional): Whether to preserve structure.
                Defaults to True.
            extract_links (bool, optional): Whether to extract link text.
                Defaults to True.
            extract_images (bool, optional): Whether to extract image alt text.
                Defaults to True.
            clean_markdown (bool, optional): Whether to clean Markdown syntax.
                Defaults to True.
        """
        self.preserve_structure = preserve_structure
        self.extract_links = extract_links
        self.extract_images = extract_images
        self.clean_markdown = clean_markdown
        
        logger.debug("Initialized MarkdownParser")
    
    def parse_markdown(self, markdown_text: str) -> List[MarkdownElement]:
        """
        Parse Markdown text and extract elements.
        
        Args:
            markdown_text (str): Markdown text to parse.
                Must be non-empty string.
        
        Returns:
            List[MarkdownElement]: List of parsed Markdown elements.
                Elements are ordered by appearance in the document.
        
        Raises:
            ValueError: If markdown_text is empty
            TypeError: If markdown_text is not string
        
        Example:
            >>> parser = MarkdownParser()
            >>> elements = parser.parse_markdown("# Title\n\nContent")
            >>> print(elements[0].element_type)  # "header"
        """
        if not isinstance(markdown_text, str):
            raise TypeError("markdown_text must be string")
        if not markdown_text:
            raise ValueError("markdown_text cannot be empty")
        
        elements = []
        lines = markdown_text.split('\n')
        current_line = 1
        
        i = 0
        while i < len(lines):
            line = lines[i].rstrip()
            
            if not line.strip():
                # Empty line - skip
                i += 1
                current_line += 1
                continue
            
            # Check for headers
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if header_match:
                level = len(header_match.group(1))
                content = header_match.group(2).strip()
                content = self._clean_content(content)
                
                element = MarkdownElement(
                    element_type="header",
                    content=content,
                    level=level,
                    line_number=current_line
                )
                elements.append(element)
                i += 1
                current_line += 1
                continue
            
            # Check for code blocks
            if line.startswith('```'):
                code_block = self._extract_code_block(lines, i, current_line)
                if code_block:
                    elements.append(code_block)
                    i = code_block.metadata.get('end_line_index', i + 1)
                    current_line = code_block.metadata.get('end_line_number', current_line + 1)
                    continue
            
            # Check for blockquotes
            if line.startswith('>'):
                blockquote = self._extract_blockquote(lines, i, current_line)
                if blockquote:
                    elements.append(blockquote)
                    i = blockquote.metadata.get('end_line_index', i + 1)
                    current_line = blockquote.metadata.get('end_line_number', current_line + 1)
                    continue
            
            # Check for list items
            list_match = re.match(r'^(\s*)([-*+]|\d+\.)\s+(.+)$', line)
            if list_match:
                list_item = self._extract_list_item(lines, i, current_line)
                if list_item:
                    elements.append(list_item)
                    i = list_item.metadata.get('end_line_index', i + 1)
                    current_line = list_item.metadata.get('end_line_number', current_line + 1)
                    continue
            
            # Regular paragraph
            paragraph = self._extract_paragraph(lines, i, current_line)
            if paragraph:
                elements.append(paragraph)
                i = paragraph.metadata.get('end_line_index', i + 1)
                current_line = paragraph.metadata.get('end_line_number', current_line + 1)
                continue
            
            # Skip unrecognized line
            i += 1
            current_line += 1
        
        return elements
    
    def _clean_content(self, content: str) -> str:
        """
        Clean Markdown content by removing syntax.
        
        Args:
            content (str): Raw content to clean.
        
        Returns:
            str: Cleaned content without Markdown syntax.
        """
        if not self.clean_markdown:
            return content
        
        # Remove bold/italic
        content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)
        content = re.sub(r'\*(.*?)\*', r'\1', content)
        content = re.sub(r'__(.*?)__', r'\1', content)
        content = re.sub(r'_(.*?)_', r'\1', content)
        
        # Handle links
        if self.extract_links:
            content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)
        else:
            content = re.sub(r'\[([^\]]+)\]\([^)]+\)', '', content)
        
        # Handle images
        if self.extract_images:
            content = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', content)
        else:
            content = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', content)
        
        # Remove inline code
        content = re.sub(r'`([^`]+)`', r'\1', content)
        
        # Remove strikethrough
        content = re.sub(r'~~(.*?)~~', r'\1', content)
        
        return content.strip()
    
    def _extract_code_block(self, lines: List[str], start_index: int, start_line: int) -> Optional[MarkdownElement]:
        """
        Extract code block from lines.
        
        Args:
            lines (List[str]): All lines of the document.
            start_index (int): Index of the starting line.
            start_line (int): Line number of the starting line.
        
        Returns:
            Optional[MarkdownElement]: Code block element or None.
        """
        if start_index >= len(lines) or not lines[start_index].startswith('```'):
            return None
        
        # Find language specification
        first_line = lines[start_index]
        language = ""
        if len(first_line) > 3:
            language = first_line[3:].strip()
        
        # Find closing ```
        content_lines = []
        end_index = start_index + 1
        end_line = start_line + 1
        
        while end_index < len(lines):
            if lines[end_index].strip() == '```':
                break
            content_lines.append(lines[end_index])
            end_index += 1
            end_line += 1
        
        if end_index >= len(lines):
            # No closing ``` found
            return None
        
        content = '\n'.join(content_lines)
        
        return MarkdownElement(
            element_type="code_block",
            content=content,
            level=1,
            line_number=start_line,
            metadata={
                "language": language,
                "end_line_index": end_index + 1,
                "end_line_number": end_line + 1
            }
        )
    
    def _extract_blockquote(self, lines: List[str], start_index: int, start_line: int) -> Optional[MarkdownElement]:
        """
        Extract blockquote from lines.
        
        Args:
            lines (List[str]): All lines of the document.
            start_index (int): Index of the starting line.
            start_line (int): Line number of the starting line.
        
        Returns:
            Optional[MarkdownElement]: Blockquote element or None.
        """
        content_lines = []
        end_index = start_index
        end_line = start_line
        
        while end_index < len(lines):
            line = lines[end_index]
            if not line.strip():
                break
            if not line.startswith('>'):
                break
            
            # Remove > prefix and clean
            content_line = line[1:].strip()
            if content_line:
                content_lines.append(content_line)
            
            end_index += 1
            end_line += 1
        
        if not content_lines:
            return None
        
        content = ' '.join(content_lines)
        content = self._clean_content(content)
        
        return MarkdownElement(
            element_type="blockquote",
            content=content,
            level=1,
            line_number=start_line,
            metadata={
                "end_line_index": end_index,
                "end_line_number": end_line
            }
        )
    
    def _extract_list_item(self, lines: List[str], start_index: int, start_line: int) -> Optional[MarkdownElement]:
        """
        Extract list item from lines.
        
        Args:
            lines (List[str]): All lines of the document.
            start_index (int): Index of the starting line.
            start_line (int): Line number of the starting line.
        
        Returns:
            Optional[MarkdownElement]: List item element or None.
        """
        line = lines[start_index]
        list_match = re.match(r'^(\s*)([-*+]|\d+\.)\s+(.+)$', line)
        if not list_match:
            return None
        
        indent = len(list_match.group(1))
        marker = list_match.group(2)
        content = list_match.group(3)
        
        # Calculate level based on indentation
        level = (indent // 2) + 1
        
        # Check for continuation lines
        end_index = start_index + 1
        end_line = start_line + 1
        
        while end_index < len(lines):
            next_line = lines[end_index]
            if not next_line.strip():
                break
            
            # Check if it's a continuation (indented content)
            if re.match(r'^\s+\S', next_line):
                content += ' ' + next_line.strip()
                end_index += 1
                end_line += 1
            else:
                break
        
        content = self._clean_content(content)
        
        return MarkdownElement(
            element_type="list_item",
            content=content,
            level=level,
            line_number=start_line,
            metadata={
                "marker": marker,
                "indent": indent,
                "end_line_index": end_index,
                "end_line_number": end_line
            }
        )
    
    def _extract_paragraph(self, lines: List[str], start_index: int, start_line: int) -> Optional[MarkdownElement]:
        """
        Extract paragraph from lines.
        
        Args:
            lines (List[str]): All lines of the document.
            start_index (int): Index of the starting line.
            start_line (int): Line number of the starting line.
        
        Returns:
            Optional[MarkdownElement]: Paragraph element or None.
        """
        content_lines = []
        end_index = start_index
        end_line = start_line
        
        while end_index < len(lines):
            line = lines[end_index]
            if not line.strip():
                break
            
            # Check if it's a special Markdown element
            if (re.match(r'^(#{1,6})\s+', line) or
                line.startswith('```') or
                line.startswith('>') or
                re.match(r'^(\s*)([-*+]|\d+\.)\s+', line)):
                break
            
            content_lines.append(line.strip())
            end_index += 1
            end_line += 1
        
        if not content_lines:
            return None
        
        content = ' '.join(content_lines)
        content = self._clean_content(content)
        
        return MarkdownElement(
            element_type="paragraph",
            content=content,
            level=1,
            line_number=start_line,
            metadata={
                "end_line_index": end_index,
                "end_line_number": end_line
            }
        )


class MarkdownProcessor(BaseProcessor):
    """
    Markdown Processor - Markdown File Processing
    
    Processes Markdown files (.md extension) and extracts structured text blocks
    with semantic information. Supports various Markdown elements and provides
    clean text extraction while preserving document structure.
    
    This processor handles:
    - Markdown files with .md extension
    - Extraction of headers, paragraphs, code blocks, lists, and blockquotes
    - Markdown syntax cleaning and text normalization
    - Semantic structure preservation
    
    Attributes:
        parser (MarkdownParser): Markdown parsing engine.
            Configurable parser for different Markdown processing options.
        preserve_structure (bool): Whether to preserve semantic structure.
            True to maintain element relationships, False for flat extraction.
        extract_code_blocks (bool): Whether to extract code blocks.
            True to include code blocks as separate elements, False to skip.
        clean_markdown (bool): Whether to clean Markdown syntax.
            True to remove syntax, False to preserve some formatting.
    
    Example:
        >>> processor = MarkdownProcessor()
        >>> result = processor.process_file("/path/file.md")
        >>> print(result.success)  # True if processing succeeded
        >>> print(len(result.blocks))  # Number of extracted blocks
    
    Raises:
        ValueError: If parser configuration is invalid
        TypeError: If parser is not MarkdownParser instance
    """
    
    def __init__(
        self,
        parser: Optional[MarkdownParser] = None,
        preserve_structure: bool = True,
        extract_code_blocks: bool = True,
        clean_markdown: bool = True,
        max_file_size_bytes: int = 10 * 1024 * 1024  # 10MB
    ):
        """
        Initialize MarkdownProcessor instance.
        
        Args:
            parser (Optional[MarkdownParser], optional): Markdown parser.
                Defaults to None. If None, creates default parser.
            preserve_structure (bool, optional): Whether to preserve structure.
                Defaults to True.
            extract_code_blocks (bool, optional): Whether to extract code blocks.
                Defaults to True.
            clean_markdown (bool, optional): Whether to clean Markdown syntax.
                Defaults to True.
            max_file_size_bytes (int, optional): Maximum file size in bytes.
                Defaults to 10MB. Must be positive integer.
        
        Raises:
            ValueError: If parser configuration is invalid
            TypeError: If parser is not MarkdownParser instance
        """
        # Initialize base processor
        super().__init__(
            supported_extensions=["md", "markdown"],
            processor_name="MarkdownProcessor",
            max_file_size_bytes=max_file_size_bytes
        )
        
        # Validate and set parser
        if parser is not None:
            if not isinstance(parser, MarkdownParser):
                raise TypeError("parser must be MarkdownParser instance")
            self.parser = parser
        else:
            self.parser = MarkdownParser(
                preserve_structure=preserve_structure,
                clean_markdown=clean_markdown
            )
        
        # Set attributes
        self.preserve_structure = preserve_structure
        self.extract_code_blocks = extract_code_blocks
        self.clean_markdown = clean_markdown
        
        logger.debug("Initialized MarkdownProcessor")
    
    def process_file(self, file_path: str) -> ProcessorResult:
        """
        Process the given Markdown file and extract text blocks.
        
        Reads the Markdown file, parses it into structured elements,
        converts elements to ProcessingBlock instances, and returns
        a ProcessorResult with extracted blocks and metadata.
        
        Args:
            file_path (str): Path to the Markdown file to process.
                Must be existing .md file that this processor can handle.
        
        Returns:
            ProcessorResult: Result of the processing operation.
                Contains extracted ProcessingBlock instances and processing metadata.
        
        Raises:
            FileNotFoundError: If file does not exist
            PermissionError: If file cannot be read
            UnicodeDecodeError: If file encoding cannot be decoded
            ValueError: If file_path is empty or file cannot be processed
            TypeError: If file_path is not string
        
        Example:
            >>> processor = MarkdownProcessor()
            >>> result = processor.process_file("/path/file.md")
            >>> print(result.success)  # True if processing succeeded
            >>> print(len(result.blocks))  # Number of extracted blocks
        """
        # Validate file path
        self.validate_file_path(file_path)
        
        start_time = time.time()
        
        try:
            # Get file metadata
            metadata = self.get_file_metadata(file_path)
            file_size = metadata.get("size_bytes", 0)
            
            # Read file content
            markdown_content = self._read_file_content(file_path)
            
            # Parse Markdown content
            markdown_elements = self.parser.parse_markdown(markdown_content)
            
            # Convert to ProcessingBlock instances
            processing_blocks = self._create_processing_blocks(markdown_elements, file_path)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Create processing metadata
            processing_metadata = {
                "processor_type": "markdown",
                "preserve_structure": self.preserve_structure,
                "extract_code_blocks": self.extract_code_blocks,
                "clean_markdown": self.clean_markdown,
                "total_markdown_elements": len(markdown_elements),
                "total_processing_blocks": len(processing_blocks),
                "element_types": self._count_element_types(markdown_elements)
            }
            
            return ProcessorResult(
                success=True,
                blocks=processing_blocks,
                processing_metadata=processing_metadata,
                processing_time_seconds=processing_time,
                file_size_bytes=file_size,
                supported_file_type=True
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error processing Markdown file {file_path}: {e}")
            
            return ProcessorResult(
                success=False,
                error_message=str(e),
                processing_time_seconds=processing_time,
                file_size_bytes=0,
                supported_file_type=True
            )
    
    def _read_file_content(self, file_path: str) -> str:
        """
        Read file content with UTF-8 encoding.
        
        Args:
            file_path (str): Path to the file to read.
        
        Returns:
            str: File content as string.
        
        Raises:
            UnicodeDecodeError: If file encoding cannot be decoded
            OSError: If file cannot be read
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Try alternative encodings for Markdown files
            for alt_encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(file_path, 'r', encoding=alt_encoding) as file:
                        content = file.read()
                        logger.info(f"Successfully read {file_path} with {alt_encoding} encoding")
                        return content
                except UnicodeDecodeError:
                    continue
            
            raise UnicodeDecodeError(f"Cannot decode {file_path} with any supported encoding")
    
    def _create_processing_blocks(self, markdown_elements: List[MarkdownElement], file_path: str) -> List[ProcessingBlock]:
        """
        Convert Markdown elements to ProcessingBlock instances.
        
        Args:
            markdown_elements (List[MarkdownElement]): List of Markdown elements.
            file_path (str): Path to the source file.
        
        Returns:
            List[ProcessingBlock]: List of ProcessingBlock instances.
        """
        processing_blocks = []
        char_position = 0
        
        for i, element in enumerate(markdown_elements):
            # Skip code blocks if not configured to extract them
            if not self.extract_code_blocks and element.element_type == "code_block":
                continue
            
            # Calculate block boundaries
            content_length = len(element.content)
            end_char = char_position + content_length
            
            # Create ProcessingBlock
            block = ProcessingBlock(
                content=element.content,
                block_type=f"markdown_{element.element_type}",
                start_line=element.line_number,
                end_line=element.line_number,
                start_char=char_position,
                end_char=end_char,
                metadata={
                    "file_path": file_path,
                    "element_index": i,
                    "processor_type": "markdown",
                    "element_type": element.element_type,
                    "element_level": element.level,
                    "preserve_structure": self.preserve_structure,
                    **element.metadata
                }
            )
            
            processing_blocks.append(block)
            char_position = end_char + 1  # +1 for newline
        
        return processing_blocks
    
    def _count_element_types(self, elements: List[MarkdownElement]) -> Dict[str, int]:
        """
        Count occurrences of each element type.
        
        Args:
            elements (List[MarkdownElement]): List of Markdown elements.
        
        Returns:
            Dict[str, int]: Dictionary with element type counts.
        """
        counts = {}
        for element in elements:
            element_type = element.element_type
            counts[element_type] = counts.get(element_type, 0) + 1
        return counts 