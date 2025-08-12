"""
Directory Model - Directory Information Container

Represents information about a directory including its path,
contents, and processing status for batch operations.

This model is used for directory scanning, processing coordination,
and tracking directory-level operations.

Author: DocAnalyzer Team
Version: 1.0.0
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import os
import logging

from .file_info import FileInfo

logger = logging.getLogger(__name__)


class Directory:
    """
    Directory Model - Directory Information Container
    
    Represents information about a directory including its path,
    contents, and processing status for batch operations.
    
    This model is used for directory scanning, processing coordination,
    and tracking directory-level operations.
    
    Attributes:
        directory_path (str): Absolute path to the directory.
            Must be a valid directory path that exists on the system.
        directory_name (str): Name of the directory.
            Extracted from the directory_path for convenience.
        file_count (int): Number of files in the directory.
            Includes files in subdirectories if recursive.
        total_size (int): Total size of all files in bytes.
            Includes files in subdirectories if recursive.
        last_scan_time (Optional[datetime]): Timestamp of last directory scan.
            None if directory has never been scanned.
        processing_status (str): Current processing status of the directory.
            Values: 'pending', 'scanning', 'processing', 'completed', 'failed'.
        subdirectories (List[str]): List of subdirectory paths.
            Relative paths from this directory.
        supported_files (List[FileInfo]): List of supported files in directory.
            Files that match supported extensions and formats.
        unsupported_files (List[FileInfo]): List of unsupported files.
            Files that don't match supported extensions.
        scan_errors (List[str]): List of errors encountered during scanning.
            Error messages for files that couldn't be processed.
    
    Example:
        >>> directory = Directory("/path/to/docs", 10, 1024000)
        >>> print(directory.directory_name)  # "docs"
        >>> print(directory.file_count)  # 10
    
    Raises:
        ValueError: If directory_path is empty or file_count is negative
        FileNotFoundError: If directory_path doesn't exist
        NotADirectoryError: If path exists but is not a directory
    """
    
    def __init__(
        self,
        directory_path: str,
        file_count: int,
        total_size: int,
        last_scan_time: Optional[datetime] = None,
        processing_status: str = "pending",
        subdirectories: Optional[List[str]] = None,
        supported_files: Optional[List[FileInfo]] = None,
        unsupported_files: Optional[List[FileInfo]] = None,
        scan_errors: Optional[List[str]] = None
    ):
        """
        Initialize Directory instance.
        
        Args:
            directory_path (str): Absolute path to the directory.
                Must be non-empty string and directory must exist.
            file_count (int): Number of files in directory.
                Must be non-negative integer.
            total_size (int): Total size of all files in bytes.
                Must be non-negative integer.
            last_scan_time (Optional[datetime], optional): Last scan timestamp.
                Defaults to None.
            processing_status (str, optional): Current processing status.
                Defaults to "pending". Valid values: pending, scanning, processing, completed, failed.
            subdirectories (Optional[List[str]], optional): List of subdirectory paths.
                Defaults to None.
            supported_files (Optional[List[FileInfo]], optional): List of supported files.
                Defaults to None.
            unsupported_files (Optional[List[FileInfo]], optional): List of unsupported files.
                Defaults to None.
            scan_errors (Optional[List[str]], optional): List of scan errors.
                Defaults to None.
        
        Raises:
            ValueError: If directory_path is empty or file_count is negative
            FileNotFoundError: If directory_path doesn't exist
            NotADirectoryError: If path exists but is not a directory
        """
        # Validate input parameters
        if not directory_path or not isinstance(directory_path, str):
            raise ValueError("directory_path must be non-empty string")
        
        if not isinstance(file_count, int) or file_count < 0:
            raise ValueError("file_count must be non-negative integer")
        
        if not isinstance(total_size, int) or total_size < 0:
            raise ValueError("total_size must be non-negative integer")
        
        # Validate directory exists
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        if not os.path.isdir(directory_path):
            raise NotADirectoryError(f"Path is not a directory: {directory_path}")
        
        # Validate processing status
        valid_statuses = ["pending", "scanning", "processing", "completed", "failed"]
        if processing_status not in valid_statuses:
            raise ValueError(f"processing_status must be one of: {valid_statuses}")
        
        # Set instance attributes
        self.directory_path = directory_path
        self.file_count = file_count
        self.total_size = total_size
        self.last_scan_time = last_scan_time
        self.processing_status = processing_status
        self.subdirectories = subdirectories or []
        self.supported_files = supported_files or []
        self.unsupported_files = unsupported_files or []
        self.scan_errors = scan_errors or []
        
        logger.debug(f"Created Directory for: {directory_path}")
    
    @property
    def directory_name(self) -> str:
        """
        Get directory name from directory path.
        
        Returns:
            str: Directory name.
        
        Example:
            >>> directory = Directory("/path/to/docs", 10, 1024000)
            >>> print(directory.directory_name)  # "docs"
        """
        return Path(self.directory_path).name
    
    def add_file(self, file_info: FileInfo, is_supported: bool = True) -> None:
        """
        Add file to directory's file lists.
        
        Args:
            file_info (FileInfo): File information to add.
                Must be valid FileInfo instance.
            is_supported (bool, optional): Whether file is supported.
                Defaults to True. If True, adds to supported_files, else to unsupported_files.
        
        Raises:
            ValueError: If file_info is None
            TypeError: If file_info is not FileInfo instance
        
        Example:
            >>> directory = Directory("/path/to/docs", 0, 0)
            >>> file_info = FileInfo("/path/to/docs/file.txt", 1024, datetime.now())
            >>> directory.add_file(file_info, is_supported=True)
        """
        if file_info is None:
            raise ValueError("file_info cannot be None")
        
        if not isinstance(file_info, FileInfo):
            raise TypeError("file_info must be FileInfo instance")
        
        if is_supported:
            self.supported_files.append(file_info)
        else:
            self.unsupported_files.append(file_info)
        
        logger.debug(f"Added file {file_info.file_name} to directory {self.directory_name}")
    
    def add_scan_error(self, error_message: str) -> None:
        """
        Add scan error to directory's error list.
        
        Args:
            error_message (str): Error message to add.
                Must be non-empty string.
        
        Raises:
            ValueError: If error_message is empty
            TypeError: If error_message is not string
        
        Example:
            >>> directory = Directory("/path/to/docs", 0, 0)
            >>> directory.add_scan_error("Permission denied: /path/to/docs/private.txt")
        """
        if not isinstance(error_message, str):
            raise TypeError("error_message must be string")
        
        if not error_message:
            raise ValueError("error_message must be non-empty string")
        
        self.scan_errors.append(error_message)
        logger.debug(f"Added scan error to directory {self.directory_name}: {error_message}")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Directory to dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary with all Directory attributes.
                Includes serialized FileInfo objects and datetime objects.
        
        Example:
            >>> directory = Directory("/path/to/docs", 10, 1024000)
            >>> data = directory.to_dict()
            >>> print(data["directory_path"])  # "/path/to/docs"
        """
        return {
            "directory_path": self.directory_path,
            "directory_name": self.directory_name,
            "file_count": self.file_count,
            "total_size": self.total_size,
            "last_scan_time": self.last_scan_time.isoformat() if self.last_scan_time else None,
            "processing_status": self.processing_status,
            "subdirectories": self.subdirectories,
            "supported_files": [f.to_dict() for f in self.supported_files],
            "unsupported_files": [f.to_dict() for f in self.unsupported_files],
            "scan_errors": self.scan_errors
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Directory':
        """
        Create Directory instance from dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary with Directory attributes.
                Must contain required fields: directory_path, file_count, total_size.
        
        Returns:
            Directory: New Directory instance.
        
        Raises:
            ValueError: If required fields are missing or invalid
            TypeError: If data types are incorrect
        
        Example:
            >>> data = {"directory_path": "/path/to/docs", "file_count": 10, ...}
            >>> directory = Directory.from_dict(data)
        """
        # Validate required fields
        required_fields = ["directory_path", "file_count", "total_size"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Parse datetime fields
        last_scan_time = None
        if data.get("last_scan_time"):
            last_scan_time = datetime.fromisoformat(data["last_scan_time"])
        
        # Parse FileInfo objects
        supported_files = []
        if data.get("supported_files"):
            supported_files = [FileInfo.from_dict(f) for f in data["supported_files"]]
        
        unsupported_files = []
        if data.get("unsupported_files"):
            unsupported_files = [FileInfo.from_dict(f) for f in data["unsupported_files"]]
        
        return cls(
            directory_path=data["directory_path"],
            file_count=data["file_count"],
            total_size=data["total_size"],
            last_scan_time=last_scan_time,
            processing_status=data.get("processing_status", "pending"),
            subdirectories=data.get("subdirectories", []),
            supported_files=supported_files,
            unsupported_files=unsupported_files,
            scan_errors=data.get("scan_errors", [])
        )
    
    def __eq__(self, other: object) -> bool:
        """
        Compare Directory instances for equality.
        
        Args:
            other (object): Object to compare with.
        
        Returns:
            bool: True if instances are equal, False otherwise.
        
        Example:
            >>> dir1 = Directory("/path/docs", 10, 1024000)
            >>> dir2 = Directory("/path/docs", 10, 1024000)
            >>> dir1 == dir2  # True if same path and file count
        """
        if not isinstance(other, Directory):
            return False
        
        return (
            self.directory_path == other.directory_path and
            self.file_count == other.file_count and
            self.total_size == other.total_size
        )
    
    def __repr__(self) -> str:
        """
        String representation of Directory.
        
        Returns:
            str: Human-readable representation.
        
        Example:
            >>> directory = Directory("/path/docs", 10, 1024000)
            >>> print(directory)  # "Directory(path='/path/docs', files=10, size=1024000, status='pending')"
        """
        return (
            f"Directory(path='{self.directory_path}', "
            f"files={self.file_count}, "
            f"size={self.total_size}, "
            f"status='{self.processing_status}')"
        ) 