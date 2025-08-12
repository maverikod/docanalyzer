"""
Base Processor - Abstract File Processing Interface

Defines the base interface and abstract classes for file processors.
All file processors must implement this interface to ensure consistent
behavior and integration with the processing pipeline.

This module provides:
- BaseProcessor: Abstract base class for all file processors
- ProcessorResult: Result container for processing operations
- Common processing utilities and validation methods

Author: DocAnalyzer Team
Version: 1.0.0
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import logging
import os
from datetime import datetime

from docanalyzer.models.processing import ProcessingBlock, FileProcessingResult, ProcessingStatus

logger = logging.getLogger(__name__)


class ProcessorResult:
    """
    Processor Result - Processing Operation Outcome
    
    Container for the result of a file processing operation including
    extracted blocks, processing metadata, and operation status.
    
    This class provides a standardized way to return processing results
    from different processor implementations.
    
    Attributes:
        success (bool): Whether processing was successful.
            True if file was processed without errors, False otherwise.
        blocks (List[ProcessingBlock]): List of extracted text blocks.
            Empty list if processing failed or no blocks were extracted.
        error_message (Optional[str]): Error message if processing failed.
            None if processing was successful.
        processing_metadata (Dict[str, Any]): Additional processing metadata.
            Contains file type, processing options, performance metrics, etc.
        processing_time_seconds (float): Time taken for processing in seconds.
            Must be non-negative float.
        file_size_bytes (int): Size of the processed file in bytes.
            Must be non-negative integer.
        supported_file_type (bool): Whether file type is supported by processor.
            True if processor can handle this file type, False otherwise.
    
    Example:
        >>> result = ProcessorResult(success=True, blocks=[block1, block2])
        >>> print(result.success)  # True
        >>> print(len(result.blocks))  # 2
    
    Raises:
        ValueError: If success is True but blocks list is None
        TypeError: If blocks list contains non-ProcessingBlock objects
    """
    
    def __init__(
        self,
        success: bool,
        blocks: Optional[List[ProcessingBlock]] = None,
        error_message: Optional[str] = None,
        processing_metadata: Optional[Dict[str, Any]] = None,
        processing_time_seconds: float = 0.0,
        file_size_bytes: int = 0,
        supported_file_type: bool = True
    ):
        """
        Initialize ProcessorResult instance.
        
        Args:
            success (bool): Whether processing was successful.
                True if file was processed without errors.
            blocks (Optional[List[ProcessingBlock]], optional): Extracted text blocks.
                Defaults to None. Must be list of ProcessingBlock instances if provided.
            error_message (Optional[str], optional): Error message if failed.
                Defaults to None. Must be non-empty string if provided.
            processing_metadata (Optional[Dict[str, Any]], optional): Processing metadata.
                Defaults to None.
            processing_time_seconds (float, optional): Processing time in seconds.
                Defaults to 0.0. Must be non-negative float.
            file_size_bytes (int, optional): Size of processed file in bytes.
                Defaults to 0. Must be non-negative integer.
            supported_file_type (bool, optional): Whether file type is supported.
                Defaults to True.
        
        Raises:
            ValueError: If success is True but blocks list is None
            TypeError: If blocks list contains non-ProcessingBlock objects
        """
        # Validate success and blocks consistency
        if success and blocks is None:
            raise ValueError("blocks cannot be None when success is True")
        
        # Validate blocks if provided
        if blocks is not None:
            if not isinstance(blocks, list):
                raise TypeError("blocks must be list")
            for block in blocks:
                if not isinstance(block, ProcessingBlock):
                    raise TypeError("blocks must contain ProcessingBlock instances")
        
        # Validate processing_time_seconds
        if not isinstance(processing_time_seconds, (int, float)):
            raise TypeError("processing_time_seconds must be float")
        if processing_time_seconds < 0:
            raise ValueError("processing_time_seconds must be non-negative float")
        
        # Validate file_size_bytes
        if not isinstance(file_size_bytes, int):
            raise TypeError("file_size_bytes must be integer")
        if file_size_bytes < 0:
            raise ValueError("file_size_bytes must be non-negative integer")
        
        # Set attributes
        self.success = success
        self.blocks = blocks or []
        self.error_message = error_message
        self.processing_metadata = processing_metadata.copy() if processing_metadata else {}
        self.processing_time_seconds = float(processing_time_seconds)
        self.file_size_bytes = file_size_bytes
        self.supported_file_type = supported_file_type
    
    @property
    def total_blocks(self) -> int:
        """
        Get total number of extracted blocks.
        
        Returns:
            int: Number of blocks in the blocks list.
        
        Example:
            >>> result = ProcessorResult(success=True, blocks=[block1, block2])
            >>> print(result.total_blocks)  # 2
        """
        return len(self.blocks)
    
    @property
    def total_characters(self) -> int:
        """
        Get total number of characters in all blocks.
        
        Returns:
            int: Sum of content lengths of all blocks.
        
        Example:
            >>> result = ProcessorResult(success=True, blocks=[block1, block2])
            >>> print(result.total_characters)  # Sum of all block content lengths
        """
        return sum(block.content_length for block in self.blocks)
    
    def to_file_processing_result(self, file_path: str) -> FileProcessingResult:
        """
        Convert ProcessorResult to FileProcessingResult.
        
        Args:
            file_path (str): Path to the processed file.
                Must be non-empty string matching the processed file.
        
        Returns:
            FileProcessingResult: FileProcessingResult instance with same data.
        
        Raises:
            ValueError: If file_path is empty
            TypeError: If file_path is not string
        
        Example:
            >>> result = ProcessorResult(success=True, blocks=[block1])
            >>> file_result = result.to_file_processing_result("/path/file.txt")
        """
        if not isinstance(file_path, str):
            raise TypeError("file_path must be string")
        if not file_path:
            raise ValueError("file_path must be non-empty string")
        
        status = ProcessingStatus.COMPLETED if self.success else ProcessingStatus.FAILED
        
        return FileProcessingResult(
            file_path=file_path,
            blocks=self.blocks.copy(),
            processing_status=status,
            processing_time_seconds=self.processing_time_seconds,
            error_message=self.error_message,
            processing_metadata=self.processing_metadata.copy(),
            file_size_bytes=self.file_size_bytes,
            supported_file_type=self.supported_file_type
        )
    
    def __repr__(self) -> str:
        """
        String representation of ProcessorResult.
        
        Returns:
            str: Human-readable representation.
        
        Example:
            >>> result = ProcessorResult(success=True, blocks=[block1, block2])
            >>> print(result)  # "ProcessorResult(success=True, blocks=2, time=1.5s)"
        """
        return (
            f"ProcessorResult("
            f"success={self.success}, "
            f"blocks={len(self.blocks)}, "
            f"time={self.processing_time_seconds:.2f}s, "
            f"supported={self.supported_file_type}"
            f")"
        )


class BaseProcessor(ABC):
    """
    Base Processor - Abstract File Processing Interface
    
    Abstract base class that defines the interface for all file processors.
    All file processors must inherit from this class and implement
    the required abstract methods.
    
    This class provides:
    - Common processing interface
    - File validation methods
    - Error handling utilities
    - Processing metadata collection
    
    Attributes:
        supported_extensions (List[str]): List of file extensions this processor supports.
            Must be list of lowercase extensions without dots (e.g., ['txt', 'md']).
        processor_name (str): Name of the processor for identification.
            Used in logging and error messages.
        max_file_size_bytes (int): Maximum file size this processor can handle.
            Files larger than this will be rejected. Must be positive integer.
    
    Example:
        >>> class MyProcessor(BaseProcessor):
        ...     def __init__(self):
        ...         super().__init__(['my'], 'MyProcessor', 1024*1024)
        ...     
        ...     def process_file(self, file_path: str) -> ProcessorResult:
        ...         # Implementation here
        ...         pass
    
    Raises:
        ValueError: If supported_extensions is empty or max_file_size_bytes is not positive
        TypeError: If supported_extensions is not list or processor_name is not string
    """
    
    def __init__(
        self,
        supported_extensions: List[str],
        processor_name: str,
        max_file_size_bytes: int = 10 * 1024 * 1024  # 10MB default
    ):
        """
        Initialize BaseProcessor instance.
        
        Args:
            supported_extensions (List[str]): List of supported file extensions.
                Must be list of lowercase extensions without dots.
            processor_name (str): Name of the processor for identification.
                Must be non-empty string.
            max_file_size_bytes (int, optional): Maximum file size in bytes.
                Defaults to 10MB. Must be positive integer.
        
        Raises:
            ValueError: If supported_extensions is empty or max_file_size_bytes is not positive
            TypeError: If supported_extensions is not list or processor_name is not string
        """
        # Validate supported_extensions
        if not isinstance(supported_extensions, list):
            raise TypeError("supported_extensions must be list")
        if not supported_extensions:
            raise ValueError("supported_extensions cannot be empty")
        for ext in supported_extensions:
            if not isinstance(ext, str) or not ext:
                raise ValueError("supported_extensions must contain non-empty strings")
        
        # Validate processor_name
        if not isinstance(processor_name, str):
            raise TypeError("processor_name must be string")
        if not processor_name:
            raise ValueError("processor_name cannot be empty")
        
        # Validate max_file_size_bytes
        if not isinstance(max_file_size_bytes, int):
            raise TypeError("max_file_size_bytes must be integer")
        if max_file_size_bytes <= 0:
            raise ValueError("max_file_size_bytes must be positive integer")
        
        # Set attributes
        self.supported_extensions = [ext.lower() for ext in supported_extensions]
        self.processor_name = processor_name
        self.max_file_size_bytes = max_file_size_bytes
        
        logger.debug(f"Initialized {self.processor_name} with extensions: {self.supported_extensions}")
    
    def can_process_file(self, file_path: str) -> bool:
        """
        Check if this processor can handle the given file.
        
        Args:
            file_path (str): Path to the file to check.
                Must be non-empty string.
        
        Returns:
            bool: True if processor can handle this file, False otherwise.
                Checks file extension and size.
        
        Raises:
            ValueError: If file_path is empty
            TypeError: If file_path is not string
        
        Example:
            >>> processor = TextProcessor()
            >>> processor.can_process_file("/path/file.txt")  # True
            >>> processor.can_process_file("/path/file.md")   # False
        """
        if not isinstance(file_path, str):
            raise TypeError("file_path must be string")
        if not file_path:
            raise ValueError("file_path cannot be empty")
        
        try:
            path = Path(file_path)
            if not path.exists():
                return False
            
            # Check file extension
            file_extension = path.suffix.lower().lstrip('.')
            if file_extension not in self.supported_extensions:
                return False
            
            # Check file size
            file_size = path.stat().st_size
            if file_size > self.max_file_size_bytes:
                return False
            
            return True
            
        except (OSError, ValueError) as e:
            logger.warning(f"Error checking file {file_path}: {e}")
            return False
    
    def get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Get metadata for the given file.
        
        Args:
            file_path (str): Path to the file.
                Must be existing file path.
        
        Returns:
            Dict[str, Any]: File metadata including size, modification time, etc.
                Empty dict if file cannot be accessed.
        
        Raises:
            ValueError: If file_path is empty
            TypeError: If file_path is not string
        
        Example:
            >>> processor = TextProcessor()
            >>> metadata = processor.get_file_metadata("/path/file.txt")
            >>> print(metadata["size_bytes"])  # File size in bytes
        """
        if not isinstance(file_path, str):
            raise TypeError("file_path must be string")
        if not file_path:
            raise ValueError("file_path cannot be empty")
        
        try:
            path = Path(file_path)
            stat = path.stat()
            
            return {
                "size_bytes": stat.st_size,
                "modified_time": datetime.fromtimestamp(stat.st_mtime),
                "created_time": datetime.fromtimestamp(stat.st_ctime),
                "file_extension": path.suffix.lower().lstrip('.'),
                "file_name": path.name,
                "file_path": str(path.absolute())
            }
            
        except (OSError, ValueError) as e:
            logger.warning(f"Error getting metadata for {file_path}: {e}")
            return {}
    
    @abstractmethod
    def process_file(self, file_path: str) -> ProcessorResult:
        """
        Process the given file and extract text blocks.
        
        This is the main processing method that must be implemented by all
        concrete processor classes. It should read the file, extract text
        blocks according to the file format, and return a ProcessorResult.
        
        Args:
            file_path (str): Path to the file to process.
                Must be existing file path that this processor can handle.
        
        Returns:
            ProcessorResult: Result of the processing operation.
                Contains extracted blocks, processing metadata, and status.
        
        Raises:
            FileNotFoundError: If file does not exist
            PermissionError: If file cannot be read
            ValueError: If file_path is empty or file cannot be processed
            TypeError: If file_path is not string
        
        Example:
            >>> processor = TextProcessor()
            >>> result = processor.process_file("/path/file.txt")
            >>> print(result.success)  # True if processing succeeded
            >>> print(len(result.blocks))  # Number of extracted blocks
        """
        pass
    
    def validate_file_path(self, file_path: str) -> None:
        """
        Validate file path and raise appropriate exceptions.
        
        Args:
            file_path (str): Path to validate.
                Must be non-empty string.
        
        Raises:
            ValueError: If file_path is empty
            TypeError: If file_path is not string
            FileNotFoundError: If file does not exist
            PermissionError: If file cannot be read
            ValueError: If file is too large or not supported
        
        Example:
            >>> processor = TextProcessor()
            >>> processor.validate_file_path("/path/file.txt")  # Raises exception if invalid
        """
        if not isinstance(file_path, str):
            raise TypeError("file_path must be string")
        if not file_path:
            raise ValueError("file_path cannot be empty")
        
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        try:
            if not os.access(path, os.R_OK):
                raise PermissionError(f"Cannot read file: {file_path}")
        except OSError as e:
            raise PermissionError(f"Cannot access file {file_path}: {e}")
        
        # Check file size
        try:
            file_size = path.stat().st_size
            if file_size > self.max_file_size_bytes:
                raise ValueError(
                    f"File too large: {file_size} bytes (max: {self.max_file_size_bytes})"
                )
        except OSError as e:
            raise ValueError(f"Cannot get file size for {file_path}: {e}")
        
        # Check if processor can handle this file type
        if not self.can_process_file(file_path):
            raise ValueError(f"File type not supported by {self.processor_name}: {file_path}")
    
    def __repr__(self) -> str:
        """
        String representation of BaseProcessor.
        
        Returns:
            str: Human-readable representation.
        
        Example:
            >>> processor = TextProcessor()
            >>> print(processor)  # "TextProcessor(extensions=['txt'], max_size=10485760)"
        """
        return (
            f"{self.processor_name}("
            f"extensions={self.supported_extensions}, "
            f"max_size={self.max_file_size_bytes}"
            f")"
        ) 