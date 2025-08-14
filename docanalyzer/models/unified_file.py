"""
Unified File Model - DocAnalyzer Unified File Representation

This module provides a unified file model that combines file system
information with database record information into a single, coherent interface.

The unified file model eliminates duplication between DatabaseFileRecord
and FileInfo and provides a consistent file representation across all
DocAnalyzer components.

Author: DocAnalyzer Team
Version: 1.0.0
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import uuid
import os

logger = logging.getLogger(__name__)


class FileStatus(Enum):
    """
    File Status - Unified File Status Enumeration
    
    Defines the possible states of files in DocAnalyzer including
    both file system and database states.
    
    Values:
        NEW: File is newly discovered and not yet processed
        PENDING: File is queued for processing
        PROCESSING: File is currently being processed
        COMPLETED: File processing completed successfully
        FAILED: File processing failed with an error
        SKIPPED: File was skipped during processing
        DELETED: File has been marked as deleted
        ARCHIVED: File has been archived
        ERROR: File encountered an error during processing
    """
    NEW = "new"
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    DELETED = "deleted"
    ARCHIVED = "archived"
    ERROR = "error"


@dataclass
class FileMetadata:
    """
    File Metadata - Additional File Information
    
    Contains additional metadata about a file including custom attributes,
    processing information, and system-specific data.
    
    Attributes:
        custom_attributes (Dict[str, Any]): Custom file attributes.
            Can contain any user-defined metadata.
        processing_info (Dict[str, Any]): Processing-related information.
            Contains processing history, errors, and statistics.
        system_info (Dict[str, Any]): System-specific information.
            Contains OS-specific file attributes and metadata.
        tags (List[str]): File tags for categorization.
            Used for organizing and filtering files.
        categories (List[str]): File categories.
            Used for classification and routing.
        priority (int): Processing priority level.
            Higher values indicate higher priority. Defaults to 0.
        checksum (Optional[str]): File checksum for integrity verification.
            Can be None if not calculated.
        mime_type (Optional[str]): MIME type of the file.
            Can be None if not determined.
        encoding (Optional[str]): File encoding.
            Can be None if not determined.
    
    Example:
        >>> metadata = FileMetadata(
        ...     custom_attributes={"author": "John Doe"},
        ...     tags=["document", "important"],
        ...     priority=5
        ... )
        >>> print(metadata.tags)  # ["document", "important"]
    """
    
    custom_attributes: Dict[str, Any] = field(default_factory=dict)
    processing_info: Dict[str, Any] = field(default_factory=dict)
    system_info: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    priority: int = 0
    checksum: Optional[str] = None
    mime_type: Optional[str] = None
    encoding: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert file metadata to dictionary.
        
        Returns:
            Dict[str, Any]: File metadata as dictionary.
        """
        return {
            "custom_attributes": self.custom_attributes,
            "processing_info": self.processing_info,
            "system_info": self.system_info,
            "tags": self.tags,
            "categories": self.categories,
            "priority": self.priority,
            "checksum": self.checksum,
            "mime_type": self.mime_type,
            "encoding": self.encoding
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileMetadata':
        """
        Create FileMetadata from dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary containing metadata.
        
        Returns:
            FileMetadata: Created FileMetadata instance.
        """
        return cls(
            custom_attributes=data.get("custom_attributes", {}),
            processing_info=data.get("processing_info", {}),
            system_info=data.get("system_info", {}),
            tags=data.get("tags", []),
            categories=data.get("categories", []),
            priority=data.get("priority", 0),
            checksum=data.get("checksum"),
            mime_type=data.get("mime_type"),
            encoding=data.get("encoding")
        )


@dataclass
class UnifiedFile:
    """
    Unified File Model - Single File Representation
    
    Represents a file in DocAnalyzer with comprehensive information
    including file system details, database record information,
    and processing metadata.
    
    This model unifies DatabaseFileRecord and FileInfo into a single
    representation that can be used across all DocAnalyzer components.
    
    Attributes:
        file_id (str): Unique file identifier.
            Generated as UUID4 string for uniqueness.
        file_path (str): Absolute path to the file in the file system.
            Must be a valid file path.
        file_name (str): Name of the file including extension.
            Extracted from file_path for convenience.
        file_size (int): Size of the file in bytes.
            Must be non-negative integer.
        file_extension (str): File extension in lowercase.
            Used for filtering and processor selection.
        modification_time (datetime): Last modification time of the file.
            Used for change detection and processing decisions.
        is_directory (bool): Whether the path represents a directory.
            False for regular files, True for directories.
        status (FileStatus): Current status of the file.
            Tracks the processing state of the file.
        processing_count (int): Number of times file has been processed.
            Must be non-negative integer. Defaults to 0.
        last_processed_at (Optional[datetime]): Timestamp of last processing.
            None if file has never been processed.
        processing_errors (List[str]): List of processing error messages.
            Contains error messages from failed processing attempts.
        metadata (FileMetadata): Comprehensive file metadata.
            Contains custom attributes, processing info, and system info.
        created_at (datetime): Timestamp when file record was created.
            Used for tracking file record age and history.
        updated_at (datetime): Timestamp when file record was last updated.
            Updated whenever file attributes change.
        vector_store_id (Optional[str]): ID in vector store if processed.
            None if file has not been processed for vector storage.
        chunk_count (int): Number of chunks created from this file.
            Must be non-negative integer. Defaults to 0.
        database_record_id (Optional[str]): Database record ID if stored.
            None if file is not yet stored in database.
    
    Example:
        >>> file = UnifiedFile(
        ...     file_path="/path/document.txt",
        ...     file_size=1024,
        ...     modification_time=datetime.now()
        ... )
        >>> print(file.file_name)  # "document.txt"
        >>> print(file.status)  # FileStatus.NEW
    
    Raises:
        ValueError: If file_path is empty or file_size is negative
        TypeError: If modification_time is not datetime object
    """
    
    file_path: str
    file_size: int
    modification_time: datetime
    file_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    file_name: str = field(init=False)
    file_extension: str = field(init=False)
    is_directory: bool = False
    status: FileStatus = FileStatus.NEW
    processing_count: int = 0
    last_processed_at: Optional[datetime] = None
    processing_errors: List[str] = field(default_factory=list)
    metadata: FileMetadata = field(default_factory=FileMetadata)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    vector_store_id: Optional[str] = None
    chunk_count: int = 0
    database_record_id: Optional[str] = None
    
    def __post_init__(self):
        """
        Post-initialization processing.
        
        Validates input parameters and sets derived attributes.
        
        Raises:
            ValueError: If file_path is empty or file_size is negative
            TypeError: If modification_time is not datetime object
        """
        # Validate input parameters
        if not self.file_path or not isinstance(self.file_path, str):
            raise ValueError("file_path must be non-empty string")
        
        if self.file_size < 0:
            raise ValueError("file_size must be non-negative")
        
        if not isinstance(self.modification_time, datetime):
            raise TypeError("modification_time must be datetime object")
        
        # Set derived attributes
        path_obj = Path(self.file_path)
        self.file_name = path_obj.name
        self.file_extension = path_obj.suffix.lower()
        
        # Validate file exists if not directory
        if not self.is_directory and not os.path.exists(self.file_path):
            logger.warning(f"File does not exist: {self.file_path}")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert unified file to dictionary.
        
        Returns:
            Dict[str, Any]: Unified file as dictionary.
        """
        return {
            "file_id": self.file_id,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "file_extension": self.file_extension,
            "modification_time": self.modification_time.isoformat(),
            "is_directory": self.is_directory,
            "status": self.status.value,
            "processing_count": self.processing_count,
            "last_processed_at": self.last_processed_at.isoformat() if self.last_processed_at else None,
            "processing_errors": self.processing_errors,
            "metadata": self.metadata.to_dict(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "vector_store_id": self.vector_store_id,
            "chunk_count": self.chunk_count,
            "database_record_id": self.database_record_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UnifiedFile':
        """
        Create UnifiedFile from dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary containing file data.
        
        Returns:
            UnifiedFile: Created UnifiedFile instance.
        
        Raises:
            ValueError: If required fields are missing or invalid
            TypeError: If datetime fields are invalid
        """
        # Parse datetime fields
        modification_time = datetime.fromisoformat(data["modification_time"])
        created_at = datetime.fromisoformat(data["created_at"])
        updated_at = datetime.fromisoformat(data["updated_at"])
        last_processed_at = None
        if data.get("last_processed_at"):
            last_processed_at = datetime.fromisoformat(data["last_processed_at"])
        
        # Create metadata
        metadata = FileMetadata.from_dict(data.get("metadata", {}))
        
        # Create unified file
        file = cls(
            file_id=data["file_id"],
            file_path=data["file_path"],
            file_size=data["file_size"],
            modification_time=modification_time,
            is_directory=data.get("is_directory", False),
            status=FileStatus(data["status"]),
            processing_count=data.get("processing_count", 0),
            last_processed_at=last_processed_at,
            processing_errors=data.get("processing_errors", []),
            metadata=metadata,
            created_at=created_at,
            updated_at=updated_at,
            vector_store_id=data.get("vector_store_id"),
            chunk_count=data.get("chunk_count", 0),
            database_record_id=data.get("database_record_id")
        )
        
        return file
    
    def update_status(self, status: FileStatus) -> None:
        """
        Update file status.
        
        Updates the file status and sets the updated_at timestamp.
        
        Args:
            status (FileStatus): New status for the file.
        """
        self.status = status
        self.updated_at = datetime.now()
        logger.debug(f"Updated file {self.file_id} status to {status.value}")
    
    def add_processing_error(self, error_message: str) -> None:
        """
        Add processing error message.
        
        Adds an error message to the processing errors list
        and updates the file status to FAILED.
        
        Args:
            error_message (str): Error message to add.
        """
        self.processing_errors.append(error_message)
        self.status = FileStatus.FAILED
        self.updated_at = datetime.now()
        logger.warning(f"Added processing error to file {self.file_id}: {error_message}")
    
    def mark_processed(self, vector_store_id: Optional[str] = None, chunk_count: int = 0) -> None:
        """
        Mark file as processed.
        
        Updates processing information and marks the file as completed.
        
        Args:
            vector_store_id (Optional[str]): Vector store ID if stored.
            chunk_count (int): Number of chunks created.
        """
        self.status = FileStatus.COMPLETED
        self.processing_count += 1
        self.last_processed_at = datetime.now()
        self.updated_at = datetime.now()
        self.vector_store_id = vector_store_id
        self.chunk_count = chunk_count
        
        # Update processing info in metadata
        self.metadata.processing_info.update({
            "last_processing_time": self.last_processed_at.isoformat(),
            "total_processing_count": self.processing_count,
            "vector_store_id": vector_store_id,
            "chunk_count": chunk_count
        })
        
        logger.info(f"Marked file {self.file_id} as processed with {chunk_count} chunks")
    
    def is_modified_since_last_processing(self) -> bool:
        """
        Check if file has been modified since last processing.
        
        Returns:
            bool: True if file has been modified since last processing.
        """
        if not self.last_processed_at:
            return True
        
        return self.modification_time > self.last_processed_at
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """
        Get processing summary information.
        
        Returns:
            Dict[str, Any]: Processing summary including status, counts, and errors.
        """
        return {
            "file_id": self.file_id,
            "file_name": self.file_name,
            "status": self.status.value,
            "processing_count": self.processing_count,
            "last_processed_at": self.last_processed_at.isoformat() if self.last_processed_at else None,
            "error_count": len(self.processing_errors),
            "chunk_count": self.chunk_count,
            "vector_store_id": self.vector_store_id,
            "is_modified": self.is_modified_since_last_processing()
        }
    
    def add_tag(self, tag: str) -> None:
        """
        Add tag to file.
        
        Args:
            tag (str): Tag to add.
        """
        if tag not in self.metadata.tags:
            self.metadata.tags.append(tag)
            self.updated_at = datetime.now()
    
    def remove_tag(self, tag: str) -> None:
        """
        Remove tag from file.
        
        Args:
            tag (str): Tag to remove.
        """
        if tag in self.metadata.tags:
            self.metadata.tags.remove(tag)
            self.updated_at = datetime.now()
    
    def add_category(self, category: str) -> None:
        """
        Add category to file.
        
        Args:
            category (str): Category to add.
        """
        if category not in self.metadata.categories:
            self.metadata.categories.append(category)
            self.updated_at = datetime.now()
    
    def remove_category(self, category: str) -> None:
        """
        Remove category from file.
        
        Args:
            category (str): Category to remove.
        """
        if category in self.metadata.categories:
            self.metadata.categories.remove(category)
            self.updated_at = datetime.now()
    
    def set_priority(self, priority: int) -> None:
        """
        Set processing priority.
        
        Args:
            priority (int): Priority level (higher values = higher priority).
        """
        self.metadata.priority = priority
        self.updated_at = datetime.now()
    
    def get_file_info_summary(self) -> Dict[str, Any]:
        """
        Get file information summary.
        
        Returns:
            Dict[str, Any]: File information summary.
        """
        return {
            "file_id": self.file_id,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "file_extension": self.file_extension,
            "modification_time": self.modification_time.isoformat(),
            "is_directory": self.is_directory,
            "tags": self.metadata.tags,
            "categories": self.metadata.categories,
            "priority": self.metadata.priority,
            "checksum": self.metadata.checksum,
            "mime_type": self.metadata.mime_type
        }


class UnifiedFileManager:
    """
    Unified File Manager - File Management Operations
    
    Provides file management operations for UnifiedFile instances
    including creation, validation, and conversion utilities.
    
    This manager ensures consistent file handling across all
    DocAnalyzer components and provides utility functions for
    file operations.
    
    Attributes:
        logger (logging.Logger): Logger for file management operations.
    
    Example:
        >>> manager = UnifiedFileManager()
        >>> file = manager.create_from_path("/path/file.txt")
        >>> summary = manager.get_summary(file)
    """
    
    def __init__(self):
        """
        Initialize unified file manager.
        """
        self.logger = logging.getLogger(__name__)
    
    def create_from_path(self, file_path: str, is_directory: bool = False) -> UnifiedFile:
        """
        Create UnifiedFile from file path.
        
        Creates a UnifiedFile instance from a file path, gathering
        file system information automatically.
        
        Args:
            file_path (str): Path to the file.
            is_directory (bool): Whether the path is a directory.
        
        Returns:
            UnifiedFile: Created UnifiedFile instance.
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file_path is invalid
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Get file information
        stat_info = os.stat(file_path)
        file_size = stat_info.st_size
        modification_time = datetime.fromtimestamp(stat_info.st_mtime)
        
        # Create unified file
        file = UnifiedFile(
            file_path=file_path,
            file_size=file_size,
            modification_time=modification_time,
            is_directory=is_directory
        )
        
        self.logger.debug(f"Created UnifiedFile from path: {file_path}")
        return file
    
    def validate_file(self, file: UnifiedFile) -> bool:
        """
        Validate UnifiedFile instance.
        
        Performs comprehensive validation of a UnifiedFile instance
        including file system checks and data integrity validation.
        
        Args:
            file (UnifiedFile): File to validate.
        
        Returns:
            bool: True if file is valid, False otherwise.
        """
        try:
            # Check if file exists
            if not os.path.exists(file.file_path):
                self.logger.warning(f"File does not exist: {file.file_path}")
                return False
            
            # Check file size
            actual_size = os.path.getsize(file.file_path)
            if actual_size != file.file_size:
                self.logger.warning(f"File size mismatch for {file.file_path}: expected {file.file_size}, got {actual_size}")
                return False
            
            # Check modification time
            actual_mtime = datetime.fromtimestamp(os.path.getmtime(file.file_path))
            if abs((actual_mtime - file.modification_time).total_seconds()) > 1:
                self.logger.warning(f"Modification time mismatch for {file.file_path}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating file {file.file_path}: {e}")
            return False
    
    def get_summary(self, file: UnifiedFile) -> Dict[str, Any]:
        """
        Get comprehensive file summary.
        
        Returns a comprehensive summary of a UnifiedFile instance
        including file information and processing status.
        
        Args:
            file (UnifiedFile): File to summarize.
        
        Returns:
            Dict[str, Any]: Comprehensive file summary.
        """
        return {
            "file_info": file.get_file_info_summary(),
            "processing_summary": file.get_processing_summary(),
            "metadata_summary": {
                "tags": file.metadata.tags,
                "categories": file.metadata.categories,
                "priority": file.metadata.priority,
                "custom_attributes_count": len(file.metadata.custom_attributes)
            }
        }


# Global file manager instance
_unified_file_manager: Optional[UnifiedFileManager] = None


def get_unified_file_manager() -> UnifiedFileManager:
    """
    Get global unified file manager instance.
    
    Returns a singleton instance of the unified file manager.
    Creates the instance if it doesn't exist.
    
    Returns:
        UnifiedFileManager: Global unified file manager instance.
    """
    global _unified_file_manager
    
    if _unified_file_manager is None:
        _unified_file_manager = UnifiedFileManager()
    
    return _unified_file_manager


def create_unified_file(
    file_path: str,
    file_size: int,
    modification_time: datetime,
    is_directory: bool = False,
    status: FileStatus = FileStatus.NEW,
    metadata: Optional[FileMetadata] = None
) -> UnifiedFile:
    """
    Create unified file with specified parameters.
    
    Convenience function to create a UnifiedFile instance with
    the specified parameters.
    
    Args:
        file_path (str): Absolute path to the file.
        file_size (int): Size of the file in bytes.
        modification_time (datetime): Last modification time.
        is_directory (bool): Whether the path is a directory.
        status (FileStatus): Initial status of the file.
        metadata (Optional[FileMetadata]): File metadata.
    
    Returns:
        UnifiedFile: Created UnifiedFile instance.
    """
    return UnifiedFile(
        file_path=file_path,
        file_size=file_size,
        modification_time=modification_time,
        is_directory=is_directory,
        status=status,
        metadata=metadata or FileMetadata()
    ) 