"""
FileInfo Model - File Information Container

Represents metadata about a file in the file system including path,
size, modification time, and processing status.

This model is used throughout the system to track file information
during scanning, processing, and storage operations.

Author: DocAnalyzer Team
Version: 1.0.0
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)


class FileInfo:
    """
    File Information Model - File Metadata Container
    
    Represents metadata about a file in the file system including path,
    size, modification time, and processing status.
    
    This model is used throughout the system to track file information
    during scanning, processing, and storage operations.
    
    Attributes:
        file_path (str): Absolute path to the file in the file system.
            Must be a valid file path that exists on the system.
        file_name (str): Name of the file including extension.
            Extracted from the file_path for convenience.
        file_size (int): Size of the file in bytes.
            Must be non-negative integer.
        modification_time (datetime): Last modification time of the file.
            Used for change detection and processing decisions.
        file_extension (str): File extension in lowercase.
            Used for filtering and processor selection.
        is_directory (bool): Whether the path represents a directory.
            False for regular files, True for directories.
        processing_status (str): Current processing status of the file.
            Values: 'pending', 'processing', 'completed', 'failed', 'skipped'.
        last_processed (Optional[datetime]): Timestamp of last processing attempt.
            None if file has never been processed.
        metadata (Dict[str, Any]): Additional file metadata.
            Can contain custom attributes specific to file type.
    
    Example:
        >>> file_info = FileInfo("/path/to/document.txt", 1024, datetime.now())
        >>> print(file_info.file_name)  # "document.txt"
        >>> print(file_info.file_extension)  # "txt"
    
    Raises:
        ValueError: If file_path is empty or file_size is negative
        FileNotFoundError: If file_path doesn't exist on the system
    """
    
    def __init__(
        self,
        file_path: str,
        file_size: int,
        modification_time: datetime,
        is_directory: bool = False,
        processing_status: str = "pending",
        last_processed: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize FileInfo instance.
        
        Args:
            file_path (str): Absolute path to the file.
                Must be non-empty string and file must exist.
            file_size (int): Size of the file in bytes.
                Must be non-negative integer.
            modification_time (datetime): Last modification time.
                Must be valid datetime object.
            is_directory (bool, optional): Whether path is directory.
                Defaults to False.
            processing_status (str, optional): Current processing status.
                Defaults to "pending". Valid values: pending, processing, completed, failed, skipped.
            last_processed (Optional[datetime], optional): Last processing timestamp.
                Defaults to None.
            metadata (Optional[Dict[str, Any]], optional): Additional metadata.
                Defaults to None.
        
        Raises:
            ValueError: If file_path is empty or file_size is negative
            FileNotFoundError: If file_path doesn't exist
            TypeError: If modification_time is not datetime object
        """
        # Validate input parameters
        if not file_path or not isinstance(file_path, str):
            raise ValueError("file_path must be non-empty string")
        
        if not isinstance(file_size, int) or file_size < 0:
            raise ValueError("file_size must be non-negative integer")
        
        if not isinstance(modification_time, datetime):
            raise TypeError("modification_time must be datetime object")
        
        # Validate file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Validate processing status
        valid_statuses = ["pending", "processing", "completed", "failed", "skipped"]
        if processing_status not in valid_statuses:
            raise ValueError(f"processing_status must be one of: {valid_statuses}")
        
        # Set instance attributes
        self.file_path = file_path
        self.file_size = file_size
        self.modification_time = modification_time
        self.is_directory = is_directory
        self.processing_status = processing_status
        self.last_processed = last_processed
        self.metadata = metadata or {}
        
        logger.debug(f"Created FileInfo for: {file_path}")
    
    @property
    def file_name(self) -> str:
        """
        Get file name from file path.
        
        Returns:
            str: File name including extension.
        
        Example:
            >>> file_info = FileInfo("/path/to/document.txt", 1024, datetime.now())
            >>> print(file_info.file_name)  # "document.txt"
        """
        return Path(self.file_path).name
    
    @property
    def file_extension(self) -> str:
        """
        Get file extension in lowercase.
        
        Returns:
            str: File extension without dot, in lowercase.
        
        Example:
            >>> file_info = FileInfo("/path/to/document.TXT", 1024, datetime.now())
            >>> print(file_info.file_extension)  # "txt"
        """
        return Path(self.file_path).suffix.lower().lstrip('.')
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert FileInfo to dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary with all FileInfo attributes.
                Includes serialized datetime objects.
        
        Example:
            >>> file_info = FileInfo("/path/to/file.txt", 1024, datetime.now())
            >>> data = file_info.to_dict()
            >>> print(data["file_path"])  # "/path/to/file.txt"
        """
        return {
            "file_path": self.file_path,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "file_extension": self.file_extension,
            "modification_time": self.modification_time.isoformat(),
            "is_directory": self.is_directory,
            "processing_status": self.processing_status,
            "last_processed": self.last_processed.isoformat() if self.last_processed else None,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileInfo':
        """
        Create FileInfo instance from dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary with FileInfo attributes.
                Must contain required fields: file_path, file_size, modification_time.
        
        Returns:
            FileInfo: New FileInfo instance.
        
        Raises:
            ValueError: If required fields are missing or invalid
            TypeError: If data types are incorrect
        
        Example:
            >>> data = {"file_path": "/path/to/file.txt", "file_size": 1024, ...}
            >>> file_info = FileInfo.from_dict(data)
        """
        # Validate required fields
        required_fields = ["file_path", "file_size", "modification_time"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Parse datetime fields
        modification_time = datetime.fromisoformat(data["modification_time"])
        last_processed = None
        if data.get("last_processed"):
            last_processed = datetime.fromisoformat(data["last_processed"])
        
        return cls(
            file_path=data["file_path"],
            file_size=data["file_size"],
            modification_time=modification_time,
            is_directory=data.get("is_directory", False),
            processing_status=data.get("processing_status", "pending"),
            last_processed=last_processed,
            metadata=data.get("metadata", {})
        )
    
    def __eq__(self, other: object) -> bool:
        """
        Compare FileInfo instances for equality.
        
        Args:
            other (object): Object to compare with.
        
        Returns:
            bool: True if instances are equal, False otherwise.
        
        Example:
            >>> file1 = FileInfo("/path/file.txt", 1024, datetime.now())
            >>> file2 = FileInfo("/path/file.txt", 1024, datetime.now())
            >>> file1 == file2  # True if same path and size
        """
        if not isinstance(other, FileInfo):
            return False
        
        return (
            self.file_path == other.file_path and
            self.file_size == other.file_size and
            self.modification_time == other.modification_time and
            self.is_directory == other.is_directory
        )
    
    def __repr__(self) -> str:
        """
        String representation of FileInfo.
        
        Returns:
            str: Human-readable representation.
        
        Example:
            >>> file_info = FileInfo("/path/file.txt", 1024, datetime.now())
            >>> print(file_info)  # "FileInfo(path='/path/file.txt', size=1024, status='pending')"
        """
        return (
            f"FileInfo(path='{self.file_path}', "
            f"size={self.file_size}, "
            f"status='{self.processing_status}')"
        ) 