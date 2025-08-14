"""
Processing Models - File Processing Domain Models

Defines domain models for file processing operations including processing blocks,
file processing results, and processing metadata.

These models represent the core data structures used during file processing,
chunking, and result tracking throughout the processing pipeline.

Author: DocAnalyzer Team
Version: 1.0.0
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
import uuid
import json
import logging

logger = logging.getLogger(__name__)


class ProcessingStatus(Enum):
    """
    Processing Status Enumeration - Processing State Values
    
    Defines the possible states of file and block processing operations.
    Used throughout the system to track processing progress and status.
    
    Values:
        PENDING: Processing has not started yet
        PROCESSING: Processing is currently in progress
        COMPLETED: Processing completed successfully
        FAILED: Processing failed with an error
        SKIPPED: Processing was skipped (e.g., unsupported file type)
        CANCELLED: Processing was cancelled by user or system
    """
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class ProcessingBlock:
    """
    Processing Block Model - Text Block Container
    
    Represents a block of text extracted from a file during processing.
    Each block contains text content, metadata, and processing information.
    
    This model is used for chunking operations, semantic analysis,
    and vector storage preparation.
    
    Attributes:
        block_id (str): Unique identifier for the block.
            Generated as UUID4 string for uniqueness.
        content (str): Text content of the block.
            Must be non-empty string with actual text content.
        block_type (str): Type of the block (e.g., 'paragraph', 'code', 'header').
            Used for semantic analysis and processing decisions.
        start_line (int): Starting line number in the original file.
            Must be positive integer indicating line position.
        end_line (int): Ending line number in the original file.
            Must be positive integer >= start_line.
        start_char (int): Starting character position in the original file.
            Must be non-negative integer.
        end_char (int): Ending character position in the original file.
            Must be non-negative integer >= start_char.
        metadata (Dict[str, Any]): Additional block metadata.
            Can contain language, formatting, semantic tags, etc.
        processing_status (ProcessingStatus): Current processing status.
            Tracks the state of block processing operations.
        created_at (datetime): Timestamp when block was created.
            Used for tracking and debugging purposes.
        modified_at (datetime): Timestamp when block was last modified.
            Updated when block content or metadata changes.
    
    Example:
        >>> block = ProcessingBlock("Hello world", "paragraph", 1, 1, 0, 11)
        >>> print(block.block_id)  # UUID string
        >>> print(block.content)  # "Hello world"
    
    Raises:
        ValueError: If content is empty or line/char positions are invalid
        TypeError: If content is not string or positions are not integers
    """
    
    def __init__(
        self,
        content: str,
        block_type: str,
        start_line: int,
        end_line: int,
        start_char: int,
        end_char: int,
        block_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        processing_status: ProcessingStatus = ProcessingStatus.PENDING,
        created_at: Optional[datetime] = None,
        modified_at: Optional[datetime] = None
    ):
        """
        Initialize ProcessingBlock instance.
        
        Args:
            content (str): Text content of the block.
                Must be non-empty string with actual text content.
            block_type (str): Type of the block (e.g., 'paragraph', 'code', 'header').
                Must be non-empty string.
            start_line (int): Starting line number in the original file.
                Must be positive integer.
            end_line (int): Ending line number in the original file.
                Must be positive integer >= start_line.
            start_char (int): Starting character position in the original file.
                Must be non-negative integer.
            end_char (int): Ending character position in the original file.
                Must be non-negative integer >= start_char.
            block_id (Optional[str], optional): Unique identifier for the block.
                Defaults to None. If None, will be generated as UUID4.
            metadata (Optional[Dict[str, Any]], optional): Additional block metadata.
                Defaults to None.
            processing_status (ProcessingStatus, optional): Current processing status.
                Defaults to ProcessingStatus.PENDING.
            created_at (Optional[datetime], optional): Timestamp when block was created.
                Defaults to None. If None, will be set to current time.
            modified_at (Optional[datetime], optional): Timestamp when block was last modified.
                Defaults to None. If None, will be set to current time.
        
        Raises:
            ValueError: If content is empty or line/char positions are invalid
            TypeError: If content is not string or positions are not integers
        """
        # Validate input parameters
        if not isinstance(content, str):
            raise TypeError("content must be string")
        
        if not content:
            raise ValueError("content must be non-empty string")
        
        if not isinstance(block_type, str):
            raise TypeError("block_type must be string")
        
        if not block_type:
            raise ValueError("block_type must be non-empty string")
        
        if not isinstance(start_line, int) or start_line <= 0:
            raise ValueError("start_line must be positive integer")
        
        if not isinstance(end_line, int) or end_line < start_line:
            raise ValueError("end_line must be >= start_line")
        
        if not isinstance(start_char, int) or start_char < 0:
            raise ValueError("start_char must be non-negative integer")
        
        if not isinstance(end_char, int) or end_char < start_char:
            raise ValueError("end_char must be >= start_char")
        
        if not isinstance(processing_status, ProcessingStatus):
            raise ValueError("processing_status must be ProcessingStatus enum value")
        
        # Set instance attributes
        self.content = content
        self.block_type = block_type
        self.start_line = start_line
        self.end_line = end_line
        self.start_char = start_char
        self.end_char = end_char
        self.block_id = block_id or str(uuid.uuid4())
        self.metadata = metadata or {}
        self.processing_status = processing_status
        self.created_at = created_at or datetime.now()
        self.modified_at = modified_at or datetime.now()
        
        logger.debug(f"Created ProcessingBlock: {self.block_id}")
    
    @property
    def content_length(self) -> int:
        """
        Get length of block content in characters.
        
        Returns:
            int: Number of characters in the block content.
        
        Example:
            >>> block = ProcessingBlock("Hello world", "paragraph", 1, 1, 0, 11)
            >>> print(block.content_length)  # 11
        """
        return len(self.content)
    
    @property
    def line_count(self) -> int:
        """
        Get number of lines in the block.
        
        Returns:
            int: Number of lines from start_line to end_line.
        
        Example:
            >>> block = ProcessingBlock("Hello\nworld", "paragraph", 1, 2, 0, 11)
            >>> print(block.line_count)  # 2
        """
        return self.end_line - self.start_line + 1
    
    def update_content(self, new_content: str) -> None:
        """
        Update block content and metadata.
        
        Args:
            new_content (str): New text content for the block.
                Must be non-empty string.
        
        Raises:
            ValueError: If new_content is empty
            TypeError: If new_content is not string
        
        Example:
            >>> block = ProcessingBlock("Hello", "paragraph", 1, 1, 0, 5)
            >>> block.update_content("Hello world")
            >>> print(block.content)  # "Hello world"
        """
        if not isinstance(new_content, str):
            raise TypeError("new_content must be string")
        if not new_content:
            raise ValueError("new_content must be non-empty string")
        
        self.content = new_content
        self.end_char = self.start_char + len(new_content)
        self.modified_at = datetime.now()
    
    def update_metadata(self, new_metadata: Dict[str, Any]) -> None:
        """
        Update block metadata.
        
        Args:
            new_metadata (Dict[str, Any]): New metadata dictionary.
                Will replace existing metadata completely.
        
        Raises:
            TypeError: If new_metadata is not dictionary
        
        Example:
            >>> block = ProcessingBlock("Hello", "paragraph", 1, 1, 0, 5)
            >>> block.update_metadata({"language": "en", "sentiment": "positive"})
        """
        if not isinstance(new_metadata, dict):
            raise TypeError("new_metadata must be dictionary")
        
        self.metadata = new_metadata.copy()
        self.modified_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert ProcessingBlock to dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary with all ProcessingBlock attributes.
                Includes serialized datetime objects and enum values.
        
        Example:
            >>> block = ProcessingBlock("Hello", "paragraph", 1, 1, 0, 5)
            >>> data = block.to_dict()
            >>> print(data["content"])  # "Hello"
        """
        return {
            "content": self.content,
            "block_type": self.block_type,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "block_id": self.block_id,
            "metadata": self.metadata.copy() if self.metadata else {},
            "processing_status": self.processing_status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingBlock':
        """
        Create ProcessingBlock instance from dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary with ProcessingBlock attributes.
                Must contain required fields: content, block_type, start_line, end_line, start_char, end_char.
        
        Returns:
            ProcessingBlock: New ProcessingBlock instance.
        
        Raises:
            ValueError: If required fields are missing or invalid
            TypeError: If data types are incorrect
        
        Example:
            >>> data = {"content": "Hello", "block_type": "paragraph", ...}
            >>> block = ProcessingBlock.from_dict(data)
        """
        required_fields = ["content", "block_type", "start_line", "end_line", "start_char", "end_char"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        return cls(
            content=data["content"],
            block_type=data["block_type"],
            start_line=data["start_line"],
            end_line=data["end_line"],
            start_char=data["start_char"],
            end_char=data["end_char"],
            block_id=data.get("block_id"),
            metadata=data.get("metadata"),
            processing_status=ProcessingStatus(data.get("processing_status", "pending")),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            modified_at=datetime.fromisoformat(data["modified_at"]) if data.get("modified_at") else None
        )
    
    def __eq__(self, other: object) -> bool:
        """
        Compare ProcessingBlock instances for equality.
        
        Args:
            other (object): Object to compare with.
        
        Returns:
            bool: True if instances are equal, False otherwise.
        
        Example:
            >>> block1 = ProcessingBlock("Hello", "paragraph", 1, 1, 0, 5)
            >>> block2 = ProcessingBlock("Hello", "paragraph", 1, 1, 0, 5)
            >>> block1 == block2  # True if same content and positions
        """
        if not isinstance(other, ProcessingBlock):
            return False
        
        return (
            self.content == other.content and
            self.block_type == other.block_type and
            self.start_line == other.start_line and
            self.end_line == other.end_line and
            self.start_char == other.start_char and
            self.end_char == other.end_char and
            self.metadata == other.metadata and
            self.processing_status == other.processing_status
        )
    
    def __repr__(self) -> str:
        """
        String representation of ProcessingBlock.
        
        Returns:
            str: Human-readable representation.
        
        Example:
            >>> block = ProcessingBlock("Hello", "paragraph", 1, 1, 0, 5)
            >>> print(block)  # "ProcessingBlock(id='uuid', type='paragraph', lines=1-1, status='pending')"
        """
        return (
            f"ProcessingBlock("
            f"id='{self.block_id}', "
            f"type='{self.block_type}', "
            f"lines={self.start_line}-{self.end_line}, "
            f"status='{self.processing_status.value}'"
            f")"
        )


class FileProcessingResult:
    """
    File Processing Result Model - Processing Outcome Container
    
    Represents the result of processing a single file including
    extracted blocks, processing statistics, and outcome information.
    
    This model is used to track processing results, store processing
    metadata, and provide feedback on processing operations.
    
    Attributes:
        file_path (str): Path to the processed file.
            Must match the original file path that was processed.
        processing_id (str): Unique identifier for this processing operation.
            Generated as UUID4 string for uniqueness.
        processing_status (ProcessingStatus): Overall processing status.
            Indicates success, failure, or other processing states.
        blocks (List[ProcessingBlock]): List of extracted processing blocks.
            Contains all text blocks extracted from the file.
        total_blocks (int): Total number of blocks extracted.
            Must match length of blocks list.
        total_characters (int): Total number of characters in all blocks.
            Sum of content lengths of all blocks.
        processing_time_seconds (float): Time taken for processing in seconds.
            Must be non-negative float.
        error_message (Optional[str]): Error message if processing failed.
            None if processing was successful.
        processing_metadata (Dict[str, Any]): Additional processing metadata.
            Can contain file type, processing options, performance metrics, etc.
        started_at (datetime): Timestamp when processing started.
            Used for performance tracking and debugging.
        completed_at (Optional[datetime]): Timestamp when processing completed.
            None if processing is still in progress or failed.
        file_size_bytes (int): Size of the processed file in bytes.
            Must be non-negative integer.
        supported_file_type (bool): Whether file type is supported.
            True if file was processed, False if skipped due to unsupported type.
    
    Example:
        >>> result = FileProcessingResult("/path/file.txt", [block1, block2])
        >>> print(result.total_blocks)  # 2
        >>> print(result.processing_status)  # ProcessingStatus.COMPLETED
    
    Raises:
        ValueError: If file_path is empty or blocks list is invalid
        TypeError: If blocks list contains non-ProcessingBlock objects
    """
    
    def __init__(
        self,
        file_path: str,
        blocks: List[ProcessingBlock],
        processing_id: Optional[str] = None,
        processing_status: ProcessingStatus = ProcessingStatus.PENDING,
        processing_time_seconds: float = 0.0,
        error_message: Optional[str] = None,
        processing_metadata: Optional[Dict[str, Any]] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        file_size_bytes: int = 0,
        supported_file_type: bool = True
    ):
        """
        Initialize FileProcessingResult instance.
        
        Args:
            file_path (str): Path to the processed file.
                Must be non-empty string matching original file path.
            blocks (List[ProcessingBlock]): List of extracted processing blocks.
                Must be list of valid ProcessingBlock instances.
            processing_id (Optional[str], optional): Unique processing identifier.
                Defaults to None. If None, UUID4 will be generated.
            processing_status (ProcessingStatus, optional): Overall processing status.
                Defaults to ProcessingStatus.PENDING.
            processing_time_seconds (float, optional): Processing time in seconds.
                Defaults to 0.0. Must be non-negative float.
            error_message (Optional[str], optional): Error message if failed.
                Defaults to None.
            processing_metadata (Optional[Dict[str, Any]], optional): Processing metadata.
                Defaults to None.
            started_at (Optional[datetime], optional): Processing start timestamp.
                Defaults to None. If None, current time will be used.
            completed_at (Optional[datetime], optional): Processing completion timestamp.
                Defaults to None.
            file_size_bytes (int, optional): Size of processed file in bytes.
                Defaults to 0. Must be non-negative integer.
            supported_file_type (bool, optional): Whether file type is supported.
                Defaults to True.
        
        Raises:
            ValueError: If file_path is empty or blocks list is invalid
            TypeError: If blocks list contains non-ProcessingBlock objects
        """
        # Validate file_path
        if not isinstance(file_path, str):
            raise TypeError("file_path must be string")
        if not file_path:
            raise ValueError("file_path must be non-empty string")
        
        # Validate blocks
        if not isinstance(blocks, list):
            raise TypeError("blocks must be list")
        for block in blocks:
            if not isinstance(block, ProcessingBlock):
                raise TypeError("blocks must contain ProcessingBlock instances")
        
        # Validate processing_status
        if not isinstance(processing_status, ProcessingStatus):
            raise ValueError("processing_status must be ProcessingStatus enum value")
        
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
        self.file_path = file_path
        self.blocks = blocks.copy()
        self.processing_id = processing_id or str(uuid.uuid4())
        self.processing_status = processing_status
        self.processing_time_seconds = float(processing_time_seconds)
        self.error_message = error_message
        self.processing_metadata = processing_metadata.copy() if processing_metadata else {}
        self.started_at = started_at or datetime.now()
        self.completed_at = completed_at
        self.file_size_bytes = file_size_bytes
        self.supported_file_type = supported_file_type
    
    @property
    def total_blocks(self) -> int:
        """
        Get total number of blocks in the result.
        
        Returns:
            int: Number of blocks in the blocks list.
        
        Example:
            >>> result = FileProcessingResult("/path/file.txt", [block1, block2])
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
            >>> result = FileProcessingResult("/path/file.txt", [block1, block2])
            >>> print(result.total_characters)  # Sum of all block content lengths
        """
        return sum(block.content_length for block in self.blocks)
    
    def add_block(self, block: ProcessingBlock) -> None:
        """
        Add a processing block to the result.
        
        Args:
            block (ProcessingBlock): Processing block to add.
                Must be valid ProcessingBlock instance.
        
        Raises:
            ValueError: If block is None
            TypeError: If block is not ProcessingBlock instance
        
        Example:
            >>> result = FileProcessingResult("/path/file.txt", [])
            >>> block = ProcessingBlock("New content", "paragraph", 1, 1, 0, 10)
            >>> result.add_block(block)
        """
        if block is None:
            raise ValueError("block cannot be None")
        if not isinstance(block, ProcessingBlock):
            raise TypeError("block must be ProcessingBlock instance")
        
        self.blocks.append(block)
    
    def mark_completed(self, processing_time_seconds: float) -> None:
        """
        Mark processing as completed with timing information.
        
        Args:
            processing_time_seconds (float): Total processing time in seconds.
                Must be non-negative float.
        
        Raises:
            ValueError: If processing_time_seconds is negative
            TypeError: If processing_time_seconds is not float
        
        Example:
            >>> result = FileProcessingResult("/path/file.txt", [block1])
            >>> result.mark_completed(1.5)
            >>> print(result.processing_status)  # ProcessingStatus.COMPLETED
        """
        if not isinstance(processing_time_seconds, (int, float)):
            raise TypeError("processing_time_seconds must be float")
        if processing_time_seconds < 0:
            raise ValueError("processing_time_seconds must be non-negative float")
        
        self.processing_status = ProcessingStatus.COMPLETED
        self.processing_time_seconds = float(processing_time_seconds)
        self.completed_at = datetime.now()
    
    def mark_failed(self, error_message: str) -> None:
        """
        Mark processing as failed with error message.
        
        Args:
            error_message (str): Error message describing the failure.
                Must be non-empty string.
        
        Raises:
            ValueError: If error_message is empty
            TypeError: If error_message is not string
        
        Example:
            >>> result = FileProcessingResult("/path/file.txt", [])
            >>> result.mark_failed("File format not supported")
            >>> print(result.processing_status)  # ProcessingStatus.FAILED
        """
        if not isinstance(error_message, str):
            raise TypeError("error_message must be string")
        if not error_message:
            raise ValueError("error_message must be non-empty string")
        
        self.processing_status = ProcessingStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert FileProcessingResult to dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary with all FileProcessingResult attributes.
                Includes serialized ProcessingBlock objects and datetime objects.
        
        Example:
            >>> result = FileProcessingResult("/path/file.txt", [block1])
            >>> data = result.to_dict()
            >>> print(data["file_path"])  # "/path/file.txt"
        """
        return {
            "file_path": self.file_path,
            "blocks": [block.to_dict() for block in self.blocks],
            "processing_id": self.processing_id,
            "processing_status": self.processing_status.value,
            "processing_time_seconds": self.processing_time_seconds,
            "error_message": self.error_message,
            "processing_metadata": self.processing_metadata.copy(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "file_size_bytes": self.file_size_bytes,
            "supported_file_type": self.supported_file_type,
            "total_blocks": self.total_blocks,
            "total_characters": self.total_characters
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileProcessingResult':
        """
        Create FileProcessingResult instance from dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary with FileProcessingResult attributes.
                Must contain required fields: file_path, blocks.
        
        Returns:
            FileProcessingResult: New FileProcessingResult instance.
        
        Raises:
            ValueError: If required fields are missing or invalid
            TypeError: If data types are incorrect
        
        Example:
            >>> data = {"file_path": "/path/file.txt", "blocks": [...], ...}
            >>> result = FileProcessingResult.from_dict(data)
        """
        required_fields = ["file_path", "blocks"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        blocks = [ProcessingBlock.from_dict(block_data) for block_data in data["blocks"]]
        
        return cls(
            file_path=data["file_path"],
            blocks=blocks,
            processing_id=data.get("processing_id"),
            processing_status=ProcessingStatus(data.get("processing_status", "pending")),
            processing_time_seconds=data.get("processing_time_seconds", 0.0),
            error_message=data.get("error_message"),
            processing_metadata=data.get("processing_metadata"),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            file_size_bytes=data.get("file_size_bytes", 0),
            supported_file_type=data.get("supported_file_type", True)
        )
    
    def __eq__(self, other: object) -> bool:
        """
        Compare FileProcessingResult instances for equality.
        
        Args:
            other (object): Object to compare with.
        
        Returns:
            bool: True if instances are equal, False otherwise.
        
        Example:
            >>> result1 = FileProcessingResult("/path/file.txt", [block1])
            >>> result2 = FileProcessingResult("/path/file.txt", [block1])
            >>> result1 == result2  # True if same file_path and blocks
        """
        if not isinstance(other, FileProcessingResult):
            return False
        
        return (
            self.file_path == other.file_path and
            self.blocks == other.blocks and
            self.processing_status == other.processing_status and
            self.processing_time_seconds == other.processing_time_seconds and
            self.error_message == other.error_message and
            self.processing_metadata == other.processing_metadata and
            self.file_size_bytes == other.file_size_bytes and
            self.supported_file_type == other.supported_file_type
        )
    
    def __repr__(self) -> str:
        """
        String representation of FileProcessingResult.
        
        Returns:
            str: Human-readable representation.
        
        Example:
            >>> result = FileProcessingResult("/path/file.txt", [block1, block2])
            >>> print(result)  # "FileProcessingResult(path='/path/file.txt', blocks=2, status='completed')"
        """
        return (
            f"FileProcessingResult("
            f"path='{self.file_path}', "
            f"blocks={len(self.blocks)}, "
            f"status='{self.processing_status.value}', "
            f"processing_id='{self.processing_id}', "
            f"time={self.processing_time_seconds:.2f}s"
            f")"
        )


class ProcessingResult:
    """
    Processing Result Model - Generic Processing Result Container
    
    Represents a generic result of any processing operation.
    Used for operations that don't fit the specific FileProcessingResult model.
    
    Attributes:
        success (bool): Whether the processing operation was successful.
        message (str): Human-readable message about the result.
        data (Optional[Dict[str, Any]]): Additional result data.
        processing_time (float): Time taken for processing in seconds.
        error_details (Optional[str]): Detailed error information if failed.
        metadata (Dict[str, Any]): Additional metadata about the operation.
    """
    
    def __init__(
        self,
        success: bool,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        processing_time: float = 0.0,
        error_details: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize ProcessingResult instance.
        
        Args:
            success (bool): Whether the processing operation was successful.
            message (str): Human-readable message about the result.
            data (Optional[Dict[str, Any]]): Additional result data.
                Defaults to None.
            processing_time (float): Time taken for processing in seconds.
                Defaults to 0.0.
            error_details (Optional[str]): Detailed error information if failed.
                Defaults to None.
            metadata (Optional[Dict[str, Any]]): Additional metadata about the operation.
                Defaults to None.
        """
        self.success = success
        self.message = message
        self.data = data or {}
        self.processing_time = processing_time
        self.error_details = error_details
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert ProcessingResult to dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary with ProcessingResult attributes.
        """
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data.copy(),
            "processing_time": self.processing_time,
            "error_details": self.error_details,
            "metadata": self.metadata.copy()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingResult':
        """
        Create ProcessingResult instance from dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary with ProcessingResult attributes.
                Must contain required fields: success, message.
        
        Returns:
            ProcessingResult: New ProcessingResult instance.
        
        Raises:
            ValueError: If required fields are missing
        """
        if not isinstance(data, dict):
            raise ValueError("data must be dictionary")
        
        required_fields = ["success", "message"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Required field '{field}' missing in data")
        
        return cls(
            success=data["success"],
            message=data["message"],
            data=data.get("data"),
            processing_time=data.get("processing_time", 0.0),
            error_details=data.get("error_details"),
            metadata=data.get("metadata")
        )
    
    def __eq__(self, other: object) -> bool:
        """
        Compare ProcessingResult instances for equality.
        
        Args:
            other (object): Object to compare with.
        
        Returns:
            bool: True if instances are equal, False otherwise.
        """
        if not isinstance(other, ProcessingResult):
            return False
        
        return (
            self.success == other.success and
            self.message == other.message and
            self.data == other.data and
            self.processing_time == other.processing_time and
            self.error_details == other.error_details and
            self.metadata == other.metadata
        )
    
    def __repr__(self) -> str:
        """
        String representation of ProcessingResult.
        
        Returns:
            str: Human-readable representation.
        """
        return (
            f"ProcessingResult("
            f"success={self.success}, "
            f"message='{self.message}', "
            f"time={self.processing_time:.2f}s"
            f")"
        ) 