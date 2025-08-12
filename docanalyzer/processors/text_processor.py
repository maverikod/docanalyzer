"""
Text Processor - Plain Text File Processing

Implements file processing for plain text files (.txt extension).
Extracts text blocks from text files with support for different
text block extraction strategies and formatting options.

This processor handles:
- Plain text files with .txt extension
- Text block extraction by paragraphs, lines, or custom delimiters
- Encoding detection and handling
- Text normalization and cleaning

Author: DocAnalyzer Team
Version: 1.0.0
"""

from typing import List, Dict, Any, Optional, Iterator
from pathlib import Path
import logging
from datetime import datetime
import time

from .base_processor import BaseProcessor, ProcessorResult
from docanalyzer.models.processing import ProcessingBlock, ProcessingStatus

logger = logging.getLogger(__name__)


class TextBlockExtractor:
    """
    Text Block Extractor - Text Segmentation Strategy
    
    Implements different strategies for extracting text blocks from
    plain text files. Supports paragraph-based, line-based, and
    custom delimiter-based extraction.
    
    This class provides flexible text segmentation for different
    use cases and text formats.
    
    Attributes:
        strategy (str): Extraction strategy to use.
            Must be one of: 'paragraph', 'line', 'custom'.
        min_block_size (int): Minimum block size in characters.
            Blocks smaller than this will be merged with adjacent blocks.
        max_block_size (int): Maximum block size in characters.
            Blocks larger than this will be split.
        custom_delimiters (List[str]): Custom delimiters for 'custom' strategy.
            List of strings that mark block boundaries.
    
    Example:
        >>> extractor = TextBlockExtractor('paragraph', min_size=100, max_size=1000)
        >>> blocks = extractor.extract_blocks("Text content...")
        >>> print(len(blocks))  # Number of extracted blocks
    
    Raises:
        ValueError: If strategy is invalid or size limits are inconsistent
        TypeError: If custom_delimiters is not list when using custom strategy
    """
    
    def __init__(
        self,
        strategy: str = "paragraph",
        min_block_size: int = 50,
        max_block_size: int = 2000,
        custom_delimiters: Optional[List[str]] = None
    ):
        """
        Initialize TextBlockExtractor instance.
        
        Args:
            strategy (str): Extraction strategy to use.
                Must be one of: 'paragraph', 'line', 'custom'.
                Defaults to 'paragraph'.
            min_block_size (int): Minimum block size in characters.
                Defaults to 50. Must be positive integer.
            max_block_size (int): Maximum block size in characters.
                Defaults to 2000. Must be >= min_block_size.
            custom_delimiters (Optional[List[str]], optional): Custom delimiters.
                Required for 'custom' strategy. Defaults to None.
        
        Raises:
            ValueError: If strategy is invalid or size limits are inconsistent
            TypeError: If custom_delimiters is not list when using custom strategy
        """
        # Validate strategy
        valid_strategies = ["paragraph", "line", "custom"]
        if strategy not in valid_strategies:
            raise ValueError(f"strategy must be one of {valid_strategies}")
        
        # Validate size limits
        if not isinstance(min_block_size, int) or min_block_size <= 0:
            raise ValueError("min_block_size must be positive integer")
        if not isinstance(max_block_size, int) or max_block_size < min_block_size:
            raise ValueError("max_block_size must be >= min_block_size")
        
        # Validate custom_delimiters for custom strategy
        if strategy == "custom":
            if not isinstance(custom_delimiters, list):
                raise TypeError("custom_delimiters must be list for custom strategy")
            if not custom_delimiters:
                raise ValueError("custom_delimiters cannot be empty for custom strategy")
        
        # Set attributes
        self.strategy = strategy
        self.min_block_size = min_block_size
        self.max_block_size = max_block_size
        self.custom_delimiters = custom_delimiters or []
        
        logger.debug(f"Initialized TextBlockExtractor with strategy: {strategy}")
    
    def extract_blocks(self, text: str) -> List[str]:
        """
        Extract text blocks from the given text.
        
        Args:
            text (str): Text content to extract blocks from.
                Must be non-empty string.
        
        Returns:
            List[str]: List of extracted text blocks.
                Each block is a non-empty string within size limits.
        
        Raises:
            ValueError: If text is empty
            TypeError: If text is not string
        
        Example:
            >>> extractor = TextBlockExtractor('paragraph')
            >>> blocks = extractor.extract_blocks("Paragraph 1.\n\nParagraph 2.")
            >>> print(len(blocks))  # 2
        """
        if not isinstance(text, str):
            raise TypeError("text must be string")
        if not text:
            raise ValueError("text cannot be empty")
        
        if self.strategy == "paragraph":
            return self._extract_paragraph_blocks(text)
        elif self.strategy == "line":
            return self._extract_line_blocks(text)
        elif self.strategy == "custom":
            return self._extract_custom_blocks(text)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")
    
    def _extract_paragraph_blocks(self, text: str) -> List[str]:
        """
        Extract blocks by paragraphs (double newlines).
        
        Args:
            text (str): Text content to extract from.
        
        Returns:
            List[str]: List of paragraph blocks.
        """
        # Split by double newlines and filter empty blocks
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        # Apply size constraints
        blocks = []
        current_block = ""
        
        for paragraph in paragraphs:
            # If current paragraph is already large enough, add it as separate block
            if len(paragraph) >= self.min_block_size and len(paragraph) <= self.max_block_size:
                if current_block:
                    if len(current_block) >= self.min_block_size:
                        blocks.append(current_block)
                    current_block = ""
                blocks.append(paragraph)
            elif len(current_block) + len(paragraph) + 2 <= self.max_block_size:  # +2 for \n\n
                if current_block:
                    current_block += "\n\n" + paragraph
                else:
                    current_block = paragraph
            else:
                if current_block:
                    if len(current_block) >= self.min_block_size:
                        blocks.append(current_block)
                    current_block = paragraph
                else:
                    # Single paragraph is too large, split it
                    blocks.extend(self._split_large_block(paragraph))
        
        # Add remaining block
        if current_block and len(current_block) >= self.min_block_size:
            blocks.append(current_block)
        
        return blocks
    
    def _extract_line_blocks(self, text: str) -> List[str]:
        """
        Extract blocks by lines.
        
        Args:
            text (str): Text content to extract from.
        
        Returns:
            List[str]: List of line-based blocks.
        """
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        blocks = []
        current_block = ""
        
        for line in lines:
            if len(current_block) + len(line) + 1 <= self.max_block_size:
                if current_block:
                    current_block += "\n" + line
                else:
                    current_block = line
            else:
                if current_block:
                    if len(current_block) >= self.min_block_size:
                        blocks.append(current_block)
                    current_block = line
                else:
                    # Single line is too large, split it
                    blocks.extend(self._split_large_block(line))
        
        # Add remaining block
        if current_block and len(current_block) >= self.min_block_size:
            blocks.append(current_block)
        
        return blocks
    
    def _extract_custom_blocks(self, text: str) -> List[str]:
        """
        Extract blocks using custom delimiters.
        
        Args:
            text (str): Text content to extract from.
        
        Returns:
            List[str]: List of custom-delimited blocks.
        """
        # Split by first delimiter, then by others
        blocks = [text]
        
        for delimiter in self.custom_delimiters:
            new_blocks = []
            for block in blocks:
                new_blocks.extend(block.split(delimiter))
            blocks = [b.strip() for b in new_blocks if b.strip()]
        
        # Apply size constraints
        result_blocks = []
        current_block = ""
        
        for block in blocks:
            # If current block is already large enough, add it as separate block
            if len(block) >= self.min_block_size and len(block) <= self.max_block_size:
                if current_block:
                    if len(current_block) >= self.min_block_size:
                        result_blocks.append(current_block)
                    current_block = ""
                result_blocks.append(block)
            elif len(current_block) + len(block) + 1 <= self.max_block_size:  # +1 for space
                if current_block:
                    current_block += " " + block
                else:
                    current_block = block
            else:
                if current_block:
                    if len(current_block) >= self.min_block_size:
                        result_blocks.append(current_block)
                    current_block = block
                else:
                    result_blocks.extend(self._split_large_block(block))
        
        # Add remaining block
        if current_block and len(current_block) >= self.min_block_size:
            result_blocks.append(current_block)
        
        return result_blocks
    
    def _split_large_block(self, block: str) -> List[str]:
        """
        Split a block that exceeds max_block_size.
        
        Args:
            block (str): Block to split.
        
        Returns:
            List[str]: List of smaller blocks.
        """
        if len(block) <= self.max_block_size:
            return [block] if len(block) >= self.min_block_size else []
        
        # Split by sentences or words
        parts = block.split('. ')
        if len(parts) == 1:
            parts = block.split(' ')
        
        result = []
        current_part = ""
        
        for part in parts:
            if len(current_part) + len(part) + 1 <= self.max_block_size:
                if current_part:
                    current_part += " " + part
                else:
                    current_part = part
            else:
                if current_part and len(current_part) >= self.min_block_size:
                    result.append(current_part)
                current_part = part
        
        if current_part and len(current_part) >= self.min_block_size:
            result.append(current_part)
        
        return result


class TextProcessor(BaseProcessor):
    """
    Text Processor - Plain Text File Processing
    
    Processes plain text files (.txt extension) and extracts text blocks
    using configurable extraction strategies. Supports different text
    segmentation methods and provides comprehensive text processing.
    
    This processor handles:
    - Plain text files with .txt extension
    - Multiple text block extraction strategies
    - Text encoding detection and handling
    - Text normalization and cleaning
    
    Attributes:
        block_extractor (TextBlockExtractor): Text block extraction strategy.
            Configurable extractor for different text segmentation methods.
        encoding (str): Text encoding to use for file reading.
            Defaults to 'utf-8'. Can be 'utf-8', 'latin-1', 'cp1252', etc.
        normalize_whitespace (bool): Whether to normalize whitespace.
            True to clean up extra spaces, newlines, etc.
        remove_empty_blocks (bool): Whether to remove empty blocks.
            True to filter out blocks with no content.
    
    Example:
        >>> processor = TextProcessor()
        >>> result = processor.process_file("/path/file.txt")
        >>> print(result.success)  # True if processing succeeded
        >>> print(len(result.blocks))  # Number of extracted blocks
    
    Raises:
        ValueError: If encoding is not supported or extraction strategy is invalid
        TypeError: If block_extractor is not TextBlockExtractor instance
    """
    
    def __init__(
        self,
        block_extractor: Optional[TextBlockExtractor] = None,
        encoding: str = "utf-8",
        normalize_whitespace: bool = True,
        remove_empty_blocks: bool = True,
        max_file_size_bytes: int = 10 * 1024 * 1024  # 10MB
    ):
        """
        Initialize TextProcessor instance.
        
        Args:
            block_extractor (Optional[TextBlockExtractor], optional): Text extraction strategy.
                Defaults to None. If None, creates default paragraph-based extractor.
            encoding (str, optional): Text encoding for file reading.
                Defaults to "utf-8". Must be valid encoding name.
            normalize_whitespace (bool, optional): Whether to normalize whitespace.
                Defaults to True.
            remove_empty_blocks (bool, optional): Whether to remove empty blocks.
                Defaults to True.
            max_file_size_bytes (int, optional): Maximum file size in bytes.
                Defaults to 10MB. Must be positive integer.
        
        Raises:
            ValueError: If encoding is not supported or extraction strategy is invalid
            TypeError: If block_extractor is not TextBlockExtractor instance
        """
        # Initialize base processor
        super().__init__(
            supported_extensions=["txt"],
            processor_name="TextProcessor",
            max_file_size_bytes=max_file_size_bytes
        )
        
        # Validate and set block_extractor
        if block_extractor is not None:
            if not isinstance(block_extractor, TextBlockExtractor):
                raise TypeError("block_extractor must be TextBlockExtractor instance")
            self.block_extractor = block_extractor
        else:
            self.block_extractor = TextBlockExtractor()
        
        # Validate encoding
        if not isinstance(encoding, str):
            raise TypeError("encoding must be string")
        if not encoding:
            raise ValueError("encoding cannot be empty")
        
        # Set attributes
        self.encoding = encoding
        self.normalize_whitespace = normalize_whitespace
        self.remove_empty_blocks = remove_empty_blocks
        
        logger.debug(f"Initialized TextProcessor with encoding: {encoding}")
    
    def process_file(self, file_path: str) -> ProcessorResult:
        """
        Process the given text file and extract text blocks.
        
        Reads the text file, applies text processing (normalization, cleaning),
        extracts text blocks using the configured strategy, and returns
        a ProcessorResult with extracted ProcessingBlock instances.
        
        Args:
            file_path (str): Path to the text file to process.
                Must be existing .txt file that this processor can handle.
        
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
            >>> processor = TextProcessor()
            >>> result = processor.process_file("/path/file.txt")
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
            text_content = self._read_file_content(file_path)
            
            # Process text content
            processed_text = self._process_text_content(text_content)
            
            # Extract text blocks
            text_blocks = self.block_extractor.extract_blocks(processed_text)
            
            # Convert to ProcessingBlock instances
            processing_blocks = self._create_processing_blocks(text_blocks, file_path)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Create processing metadata
            processing_metadata = {
                "processor_type": "text",
                "encoding": self.encoding,
                "normalize_whitespace": self.normalize_whitespace,
                "remove_empty_blocks": self.remove_empty_blocks,
                "extraction_strategy": self.block_extractor.strategy,
                "min_block_size": self.block_extractor.min_block_size,
                "max_block_size": self.block_extractor.max_block_size,
                "total_text_blocks": len(text_blocks),
                "total_processing_blocks": len(processing_blocks)
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
            logger.error(f"Error processing text file {file_path}: {e}")
            
            return ProcessorResult(
                success=False,
                error_message=str(e),
                processing_time_seconds=processing_time,
                file_size_bytes=0,
                supported_file_type=True
            )
    
    def _read_file_content(self, file_path: str) -> str:
        """
        Read file content with encoding handling.
        
        Args:
            file_path (str): Path to the file to read.
        
        Returns:
            str: File content as string.
        
        Raises:
            UnicodeDecodeError: If file encoding cannot be decoded
            OSError: If file cannot be read
        """
        try:
            with open(file_path, 'r', encoding=self.encoding) as file:
                return file.read()
        except UnicodeDecodeError:
            # Try alternative encodings
            for alt_encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(file_path, 'r', encoding=alt_encoding) as file:
                        content = file.read()
                        logger.info(f"Successfully read {file_path} with {alt_encoding} encoding")
                        return content
                except UnicodeDecodeError:
                    continue
            
            raise UnicodeDecodeError(f"Cannot decode {file_path} with any supported encoding")
    
    def _process_text_content(self, text: str) -> str:
        """
        Process and normalize text content.
        
        Args:
            text (str): Raw text content to process.
        
        Returns:
            str: Processed and normalized text content.
        """
        if not self.normalize_whitespace:
            return text
        
        # Normalize whitespace
        import re
        
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        
        # Replace multiple newlines with double newline
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def _create_processing_blocks(self, text_blocks: List[str], file_path: str) -> List[ProcessingBlock]:
        """
        Convert text blocks to ProcessingBlock instances.
        
        Args:
            text_blocks (List[str]): List of text blocks to convert.
            file_path (str): Path to the source file.
        
        Returns:
            List[ProcessingBlock]: List of ProcessingBlock instances.
        """
        processing_blocks = []
        char_position = 0
        
        for i, text_block in enumerate(text_blocks):
            # Skip empty blocks if configured
            if self.remove_empty_blocks and not text_block.strip():
                continue
            
            # Calculate line numbers (approximate)
            lines_before = text_block.count('\n') + 1
            start_line = char_position // 80 + 1  # Approximate line calculation
            end_line = start_line + lines_before - 1
            
            # Create ProcessingBlock
            block = ProcessingBlock(
                content=text_block,
                block_type="text_paragraph",
                start_line=start_line,
                end_line=end_line,
                start_char=char_position,
                end_char=char_position + len(text_block),
                metadata={
                    "file_path": file_path,
                    "block_index": i,
                    "processor_type": "text",
                    "extraction_strategy": self.block_extractor.strategy
                }
            )
            
            processing_blocks.append(block)
            char_position += len(text_block) + 1  # +1 for newline
        
        return processing_blocks 