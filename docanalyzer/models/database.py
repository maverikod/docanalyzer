"""
Database Models - Database Domain Models

Defines domain models for database operations including file records,
processing statistics, and database metadata.

These models represent the data structures used for storing and retrieving
information from the database, tracking processing history, and managing
statistics and metadata.

Author: DocAnalyzer Team
Version: 1.0.0
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
import uuid
import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class RecordStatus(Enum):
    """
    Database Record Status Enumeration - Record State Values
    
    Defines the possible states of database records including file records
    and processing records.
    
    Values:
        NEW: Record is newly created and not yet processed
        PROCESSING: Record is currently being processed
        COMPLETED: Record processing completed successfully
        FAILED: Record processing failed with an error
        DELETED: Record has been marked as deleted
        ARCHIVED: Record has been archived
    """
    NEW = "new"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"
    ARCHIVED = "archived"


class DatabaseFileRecord:
    """
    Database File Record Model - File Record Container
    
    Represents a file record stored in the database including file metadata,
    processing history, and database-specific information.
    
    This model is used for tracking files in the database, managing
    processing history, and providing database operations.
    
    Attributes:
        record_id (str): Unique database record identifier.
            Generated as UUID4 string for uniqueness.
        file_path (str): Absolute path to the file.
            Must be unique within the database.
        file_name (str): Name of the file including extension.
            Extracted from file_path for convenience.
        file_size_bytes (int): Size of the file in bytes.
            Must be non-negative integer.
        file_extension (str): File extension in lowercase.
            Used for filtering and categorization.
        modification_time (datetime): Last modification time of the file.
            Used for change detection and processing decisions.
        status (RecordStatus): Current status of the record.
            Tracks the processing state of the file.
        processing_count (int): Number of times file has been processed.
            Must be non-negative integer.
        last_processed_at (Optional[datetime]): Timestamp of last processing.
            None if file has never been processed.
        processing_errors (List[str]): List of processing error messages.
            Contains error messages from failed processing attempts.
        metadata (Dict[str, Any]): Additional file metadata.
            Can contain custom attributes, tags, categories, etc.
        created_at (datetime): Timestamp when record was created.
            Used for tracking record age and history.
        updated_at (datetime): Timestamp when record was last updated.
            Updated whenever record attributes change.
        vector_store_id (Optional[str]): ID in vector store if processed.
            None if file has not been processed for vector storage.
        chunk_count (int): Number of chunks created from this file.
            Must be non-negative integer.
    
    Example:
        >>> record = DatabaseFileRecord("/path/file.txt", 1024, datetime.now())
        >>> print(record.file_name)  # "file.txt"
        >>> print(record.status)  # RecordStatus.NEW
    
    Raises:
        ValueError: If file_path is empty or file_size_bytes is negative
        TypeError: If modification_time is not datetime object
    """
    
    def __init__(
        self,
        file_path: str,
        file_size_bytes: int,
        modification_time: datetime,
        record_id: Optional[str] = None,
        file_name: Optional[str] = None,
        file_extension: Optional[str] = None,
        status: RecordStatus = RecordStatus.NEW,
        processing_count: int = 0,
        last_processed_at: Optional[datetime] = None,
        processing_errors: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        vector_store_id: Optional[str] = None,
        chunk_count: int = 0
    ):
        """
        Initialize DatabaseFileRecord instance.
        
        Args:
            file_path (str): Absolute path to the file.
                Must be non-empty string and unique in database.
            file_size_bytes (int): Size of the file in bytes.
                Must be non-negative integer.
            modification_time (datetime): Last modification time.
                Must be valid datetime object.
            record_id (Optional[str], optional): Unique database record ID.
                Defaults to None. If None, UUID4 will be generated.
            file_name (Optional[str], optional): Name of the file.
                Defaults to None. If None, will be extracted from file_path.
            file_extension (Optional[str], optional): File extension.
                Defaults to None. If None, will be extracted from file_path.
            status (RecordStatus, optional): Current record status.
                Defaults to RecordStatus.NEW.
            processing_count (int, optional): Number of processing attempts.
                Defaults to 0. Must be non-negative integer.
            last_processed_at (Optional[datetime], optional): Last processing timestamp.
                Defaults to None.
            processing_errors (Optional[List[str]], optional): List of error messages.
                Defaults to None.
            metadata (Optional[Dict[str, Any]], optional): Additional metadata.
                Defaults to None.
            created_at (Optional[datetime], optional): Record creation timestamp.
                Defaults to None. If None, current time will be used.
            updated_at (Optional[datetime], optional): Last update timestamp.
                Defaults to None. If None, current time will be used.
            vector_store_id (Optional[str], optional): Vector store identifier.
                Defaults to None.
            chunk_count (int, optional): Number of chunks created.
                Defaults to 0. Must be non-negative integer.
        
        Raises:
            ValueError: If file_path is empty or file_size_bytes is negative
            TypeError: If modification_time is not datetime object
        """
        # Validate required parameters
        if not file_path or not isinstance(file_path, str):
            raise ValueError("file_path must be non-empty string")
        if not isinstance(file_size_bytes, int) or file_size_bytes < 0:
            raise ValueError("file_size_bytes must be non-negative integer")
        if not isinstance(modification_time, datetime):
            raise TypeError("modification_time must be datetime object")
        if processing_count < 0:
            raise ValueError("processing_count must be non-negative integer")
        if chunk_count < 0:
            raise ValueError("chunk_count must be non-negative integer")
        
        # Set attributes
        self.record_id = record_id or str(uuid.uuid4())
        self.file_path = file_path
        self.file_size_bytes = file_size_bytes
        self.modification_time = modification_time
        self.status = status
        self.processing_count = processing_count
        self.last_processed_at = last_processed_at
        self.processing_errors = processing_errors or []
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.vector_store_id = vector_store_id
        self.chunk_count = chunk_count
        
        # Extract file name and extension if not provided
        if file_name is None:
            self.file_name = os.path.basename(file_path)
        else:
            self.file_name = file_name
            
        if file_extension is None:
            self.file_extension = Path(file_path).suffix.lower().lstrip('.')
        else:
            self.file_extension = file_extension
    
    def mark_processing_started(self) -> None:
        """
        Mark record as processing started.
        
        Updates status to PROCESSING and increments processing count.
        
        Example:
            >>> record = DatabaseFileRecord("/path/file.txt", 1024, datetime.now())
            >>> record.mark_processing_started()
            >>> print(record.status)  # RecordStatus.PROCESSING
            >>> print(record.processing_count)  # 1
        """
        self.status = RecordStatus.PROCESSING
        self.processing_count += 1
        self.updated_at = datetime.now()
        logger.debug(f"Marked record {self.record_id} as processing started")
    
    def mark_processing_completed(self, vector_store_id: Optional[str] = None, chunk_count: int = 0) -> None:
        """
        Mark record as processing completed.
        
        Args:
            vector_store_id (Optional[str], optional): Vector store identifier.
                Defaults to None.
            chunk_count (int, optional): Number of chunks created.
                Defaults to 0. Must be non-negative integer.
        
        Raises:
            ValueError: If chunk_count is negative
        
        Example:
            >>> record = DatabaseFileRecord("/path/file.txt", 1024, datetime.now())
            >>> record.mark_processing_completed("vector_id_123", 5)
            >>> print(record.status)  # RecordStatus.COMPLETED
            >>> print(record.chunk_count)  # 5
        """
        if chunk_count < 0:
            raise ValueError("chunk_count must be non-negative integer")
        
        self.status = RecordStatus.COMPLETED
        self.last_processed_at = datetime.now()
        self.updated_at = datetime.now()
        self.vector_store_id = vector_store_id
        self.chunk_count = chunk_count
        logger.debug(f"Marked record {self.record_id} as processing completed with {chunk_count} chunks")
    
    def mark_processing_failed(self, error_message: str) -> None:
        """
        Mark record as processing failed.
        
        Args:
            error_message (str): Error message describing the failure.
                Must be non-empty string.
        
        Raises:
            ValueError: If error_message is empty
            TypeError: If error_message is not string
        
        Example:
            >>> record = DatabaseFileRecord("/path/file.txt", 1024, datetime.now())
            >>> record.mark_processing_failed("File format not supported")
            >>> print(record.status)  # RecordStatus.FAILED
            >>> print(record.processing_errors)  # ["File format not supported"]
        """
        if not isinstance(error_message, str):
            raise TypeError("error_message must be string")
        if not error_message:
            raise ValueError("error_message must be non-empty string")
        
        self.status = RecordStatus.FAILED
        self.last_processed_at = datetime.now()
        self.updated_at = datetime.now()
        self.processing_errors.append(error_message)
        logger.debug(f"Marked record {self.record_id} as processing failed: {error_message}")
    
    def add_processing_error(self, error_message: str) -> None:
        """
        Add processing error to the record.
        
        Args:
            error_message (str): Error message to add.
                Must be non-empty string.
        
        Raises:
            ValueError: If error_message is empty
            TypeError: If error_message is not string
        
        Example:
            >>> record = DatabaseFileRecord("/path/file.txt", 1024, datetime.now())
            >>> record.add_processing_error("Permission denied")
            >>> print(len(record.processing_errors))  # 1
        """
        if not isinstance(error_message, str):
            raise TypeError("error_message must be string")
        if not error_message:
            raise ValueError("error_message must be non-empty string")
        
        self.processing_errors.append(error_message)
        self.updated_at = datetime.now()
        logger.debug(f"Added processing error to record {self.record_id}: {error_message}")
    
    def update_metadata(self, new_metadata: Dict[str, Any]) -> None:
        """
        Update record metadata.
        
        Args:
            new_metadata (Dict[str, Any]): New metadata dictionary.
                Will replace existing metadata completely.
        
        Raises:
            TypeError: If new_metadata is not dictionary
        
        Example:
            >>> record = DatabaseFileRecord("/path/file.txt", 1024, datetime.now())
            >>> record.update_metadata({"category": "documentation", "priority": "high"})
        """
        if not isinstance(new_metadata, dict):
            raise TypeError("new_metadata must be dictionary")
        
        self.metadata = new_metadata.copy()
        self.updated_at = datetime.now()
        logger.debug(f"Updated metadata for record {self.record_id}")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert DatabaseFileRecord to dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary with all DatabaseFileRecord attributes.
                Includes serialized datetime objects and enum values.
        
        Example:
            >>> record = DatabaseFileRecord("/path/file.txt", 1024, datetime.now())
            >>> data = record.to_dict()
            >>> print(data["file_path"])  # "/path/file.txt"
        """
        return {
            "record_id": self.record_id,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "file_size_bytes": self.file_size_bytes,
            "file_extension": self.file_extension,
            "modification_time": self.modification_time.isoformat(),
            "status": self.status.value,
            "processing_count": self.processing_count,
            "last_processed_at": self.last_processed_at.isoformat() if self.last_processed_at else None,
            "processing_errors": self.processing_errors.copy(),
            "metadata": self.metadata.copy(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "vector_store_id": self.vector_store_id,
            "chunk_count": self.chunk_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DatabaseFileRecord':
        """
        Create DatabaseFileRecord instance from dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary with DatabaseFileRecord attributes.
                Must contain required fields: file_path, file_size_bytes, modification_time.
        
        Returns:
            DatabaseFileRecord: New DatabaseFileRecord instance.
        
        Raises:
            ValueError: If required fields are missing or invalid
            TypeError: If data types are incorrect
        
        Example:
            >>> data = {"file_path": "/path/file.txt", "file_size_bytes": 1024, ...}
            >>> record = DatabaseFileRecord.from_dict(data)
        """
        if not isinstance(data, dict):
            raise TypeError("data must be dictionary")
        
        required_fields = ["file_path", "file_size_bytes", "modification_time"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Required field '{field}' missing in data")
        
        # Parse datetime objects
        modification_time = datetime.fromisoformat(data["modification_time"])
        created_at = None
        if "created_at" in data and data["created_at"]:
            created_at = datetime.fromisoformat(data["created_at"])
        
        updated_at = None
        if "updated_at" in data and data["updated_at"]:
            updated_at = datetime.fromisoformat(data["updated_at"])
        
        last_processed_at = None
        if "last_processed_at" in data and data["last_processed_at"]:
            last_processed_at = datetime.fromisoformat(data["last_processed_at"])
        
        # Parse enum
        status = RecordStatus.NEW
        if "status" in data:
            try:
                status = RecordStatus(data["status"])
            except ValueError:
                raise ValueError(f"Invalid status: {data['status']}")
        
        return cls(
            file_path=data["file_path"],
            file_size_bytes=data["file_size_bytes"],
            modification_time=modification_time,
            record_id=data.get("record_id"),
            file_name=data.get("file_name"),
            file_extension=data.get("file_extension"),
            status=status,
            processing_count=data.get("processing_count", 0),
            last_processed_at=last_processed_at,
            processing_errors=data.get("processing_errors", []),
            metadata=data.get("metadata", {}),
            created_at=created_at,
            updated_at=updated_at,
            vector_store_id=data.get("vector_store_id"),
            chunk_count=data.get("chunk_count", 0)
        )
    
    def __eq__(self, other: object) -> bool:
        """
        Compare DatabaseFileRecord instances for equality.
        
        Args:
            other (object): Object to compare with.
        
        Returns:
            bool: True if instances are equal, False otherwise.
        
        Example:
            >>> record1 = DatabaseFileRecord("/path/file.txt", 1024, datetime.now())
            >>> record2 = DatabaseFileRecord("/path/file.txt", 1024, datetime.now())
            >>> record1 == record2  # True if same file_path and size
        """
        if not isinstance(other, DatabaseFileRecord):
            return False
        
        return (
            self.file_path == other.file_path and
            self.file_size_bytes == other.file_size_bytes and
            self.modification_time == other.modification_time and
            self.status == other.status
        )
    
    def __repr__(self) -> str:
        """
        String representation of DatabaseFileRecord.
        
        Returns:
            str: Human-readable representation.
        
        Example:
            >>> record = DatabaseFileRecord("/path/file.txt", 1024, datetime.now())
            >>> print(record)  # "DatabaseFileRecord(path='/path/file.txt', size=1024, status='new')"
        """
        return (
            f"DatabaseFileRecord("
            f"path='{self.file_path}', "
            f"size={self.file_size_bytes}, "
            f"status='{self.status.value}')"
        )


class ProcessingStatistics:
    """
    Processing Statistics Model - Statistics Container
    
    Represents processing statistics and metrics for tracking system performance,
    processing efficiency, and operational metrics.
    
    This model is used for monitoring system performance, generating reports,
    and optimizing processing operations.
    
    Attributes:
        statistics_id (str): Unique identifier for statistics record.
            Generated as UUID4 string for uniqueness.
        period_start (datetime): Start of statistics period.
            Must be valid datetime object.
        period_end (datetime): End of statistics period.
            Must be valid datetime object >= period_start.
        total_files_processed (int): Total number of files processed.
            Must be non-negative integer.
        total_files_successful (int): Number of files processed successfully.
            Must be non-negative integer <= total_files_processed.
        total_files_failed (int): Number of files that failed processing.
            Must be non-negative integer <= total_files_processed.
        total_files_skipped (int): Number of files skipped (unsupported).
            Must be non-negative integer <= total_files_processed.
        total_processing_time_seconds (float): Total processing time in seconds.
            Must be non-negative float.
        average_processing_time_seconds (float): Average processing time per file.
            Calculated as total_processing_time_seconds / total_files_processed.
        total_chunks_created (int): Total number of chunks created.
            Must be non-negative integer.
        total_characters_processed (int): Total characters processed.
            Must be non-negative integer.
        file_type_breakdown (Dict[str, int]): Breakdown by file type.
            Dictionary mapping file extensions to counts.
        error_breakdown (Dict[str, int]): Breakdown by error type.
            Dictionary mapping error types to counts.
        processing_metadata (Dict[str, Any]): Additional processing metadata.
            Can contain performance metrics, configuration info, etc.
        created_at (datetime): Timestamp when statistics were created.
            Used for tracking and debugging purposes.
    
    Example:
        >>> stats = ProcessingStatistics(datetime.now(), datetime.now(), 100, 95)
        >>> print(stats.success_rate)  # 0.95 (95%)
        >>> print(stats.total_files_processed)  # 100
    
    Raises:
        ValueError: If period_end < period_start or counts are invalid
        TypeError: If datetime objects are not datetime instances
    """
    
    def __init__(
        self,
        period_start: datetime,
        period_end: datetime,
        total_files_processed: int,
        total_files_successful: int,
        statistics_id: Optional[str] = None,
        total_files_failed: int = 0,
        total_files_skipped: int = 0,
        total_processing_time_seconds: float = 0.0,
        total_chunks_created: int = 0,
        total_characters_processed: int = 0,
        file_type_breakdown: Optional[Dict[str, int]] = None,
        error_breakdown: Optional[Dict[str, int]] = None,
        processing_metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None
    ):
        """
        Initialize ProcessingStatistics instance.
        
        Args:
            period_start (datetime): Start of statistics period.
                Must be valid datetime object.
            period_end (datetime): End of statistics period.
                Must be valid datetime object >= period_start.
            total_files_processed (int): Total number of files processed.
                Must be non-negative integer.
            total_files_successful (int): Number of successful files.
                Must be non-negative integer <= total_files_processed.
            statistics_id (Optional[str], optional): Unique statistics identifier.
                Defaults to None. If None, UUID4 will be generated.
            total_files_failed (int, optional): Number of failed files.
                Defaults to 0. Must be non-negative integer.
            total_files_skipped (int, optional): Number of skipped files.
                Defaults to 0. Must be non-negative integer.
            total_processing_time_seconds (float, optional): Total processing time.
                Defaults to 0.0. Must be non-negative float.
            total_chunks_created (int, optional): Total chunks created.
                Defaults to 0. Must be non-negative integer.
            total_characters_processed (int, optional): Total characters processed.
                Defaults to 0. Must be non-negative integer.
            file_type_breakdown (Optional[Dict[str, int]], optional): File type breakdown.
                Defaults to None.
            error_breakdown (Optional[Dict[str, int]], optional): Error type breakdown.
                Defaults to None.
            processing_metadata (Optional[Dict[str, Any]], optional): Processing metadata.
                Defaults to None.
            created_at (Optional[datetime], optional): Creation timestamp.
                Defaults to None. If None, current time will be used.
        
        Raises:
            ValueError: If period_end < period_start or counts are invalid
            TypeError: If datetime objects are not datetime instances
        """
        # Validate required parameters
        if not isinstance(period_start, datetime):
            raise TypeError("period_start must be datetime object")
        if not isinstance(period_end, datetime):
            raise TypeError("period_end must be datetime object")
        if period_end < period_start:
            raise ValueError("period_end must be >= period_start")
        if not isinstance(total_files_processed, int) or total_files_processed < 0:
            raise ValueError("total_files_processed must be non-negative integer")
        if not isinstance(total_files_successful, int) or total_files_successful < 0:
            raise ValueError("total_files_successful must be non-negative integer")
        if total_files_successful > total_files_processed:
            raise ValueError("total_files_successful cannot exceed total_files_processed")
        if not isinstance(total_files_failed, int) or total_files_failed < 0:
            raise ValueError("total_files_failed must be non-negative integer")
        if not isinstance(total_files_skipped, int) or total_files_skipped < 0:
            raise ValueError("total_files_skipped must be non-negative integer")
        if total_files_failed + total_files_skipped > total_files_processed:
            raise ValueError("sum of failed and skipped files cannot exceed total files")
        if not isinstance(total_processing_time_seconds, (int, float)) or total_processing_time_seconds < 0:
            raise ValueError("total_processing_time_seconds must be non-negative number")
        if not isinstance(total_chunks_created, int) or total_chunks_created < 0:
            raise ValueError("total_chunks_created must be non-negative integer")
        if not isinstance(total_characters_processed, int) or total_characters_processed < 0:
            raise ValueError("total_characters_processed must be non-negative integer")
        
        # Set attributes
        self.statistics_id = statistics_id or str(uuid.uuid4())
        self.period_start = period_start
        self.period_end = period_end
        self.total_files_processed = total_files_processed
        self.total_files_successful = total_files_successful
        self.total_files_failed = total_files_failed
        self.total_files_skipped = total_files_skipped
        self.total_processing_time_seconds = float(total_processing_time_seconds)
        self.total_chunks_created = total_chunks_created
        self.total_characters_processed = total_characters_processed
        self.file_type_breakdown = file_type_breakdown or {}
        self.error_breakdown = error_breakdown or {}
        self.processing_metadata = processing_metadata or {}
        self.created_at = created_at or datetime.now()
    
    @property
    def success_rate(self) -> float:
        """
        Calculate success rate as percentage.
        
        Returns:
            float: Success rate as decimal (0.0 to 1.0).
                0.0 if no files processed, 1.0 if all successful.
        
        Example:
            >>> stats = ProcessingStatistics(datetime.now(), datetime.now(), 100, 95)
            >>> print(stats.success_rate)  # 0.95
        """
        if self.total_files_processed == 0:
            return 0.0
        return self.total_files_successful / self.total_files_processed
    
    @property
    def failure_rate(self) -> float:
        """
        Calculate failure rate as percentage.
        
        Returns:
            float: Failure rate as decimal (0.0 to 1.0).
                0.0 if no files processed, 1.0 if all failed.
        
        Example:
            >>> stats = ProcessingStatistics(datetime.now(), datetime.now(), 100, 95, total_files_failed=3)
            >>> print(stats.failure_rate)  # 0.03
        """
        if self.total_files_processed == 0:
            return 0.0
        return self.total_files_failed / self.total_files_processed
    
    @property
    def average_processing_time_seconds(self) -> float:
        """
        Calculate average processing time per file.
        
        Returns:
            float: Average processing time in seconds.
                0.0 if no files processed.
        
        Example:
            >>> stats = ProcessingStatistics(datetime.now(), datetime.now(), 100, 95, total_processing_time_seconds=500.0)
            >>> print(stats.average_processing_time_seconds)  # 5.0
        """
        if self.total_files_processed == 0:
            return 0.0
        return self.total_processing_time_seconds / self.total_files_processed
    
    @property
    def period_duration_seconds(self) -> float:
        """
        Calculate duration of statistics period.
        
        Returns:
            float: Duration in seconds between period_start and period_end.
        
        Example:
            >>> start = datetime.now()
            >>> end = start + timedelta(hours=1)
            >>> stats = ProcessingStatistics(start, end, 100, 95)
            >>> print(stats.period_duration_seconds)  # 3600.0
        """
        return (self.period_end - self.period_start).total_seconds()
    
    def add_file_type_count(self, file_extension: str, count: int = 1) -> None:
        """
        Add count for specific file type.
        
        Args:
            file_extension (str): File extension to count.
                Must be non-empty string.
            count (int, optional): Count to add.
                Defaults to 1. Must be positive integer.
        
        Raises:
            ValueError: If file_extension is empty or count is not positive
            TypeError: If count is not integer
        
        Example:
            >>> stats = ProcessingStatistics(datetime.now(), datetime.now(), 100, 95)
            >>> stats.add_file_type_count("txt", 50)
            >>> print(stats.file_type_breakdown["txt"])  # 50
        """
        if not isinstance(file_extension, str):
            raise TypeError("file_extension must be string")
        if not file_extension:
            raise ValueError("file_extension must be non-empty string")
        if not isinstance(count, int):
            raise TypeError("count must be integer")
        if count <= 0:
            raise ValueError("count must be positive integer")
        
        self.file_type_breakdown[file_extension] = self.file_type_breakdown.get(file_extension, 0) + count
        logger.debug(f"Added file type count: {file_extension}={count}")
    
    def add_error_count(self, error_type: str, count: int = 1) -> None:
        """
        Add count for specific error type.
        
        Args:
            error_type (str): Error type to count.
                Must be non-empty string.
            count (int, optional): Count to add.
                Defaults to 1. Must be positive integer.
        
        Raises:
            ValueError: If error_type is empty or count is not positive
            TypeError: If count is not integer
        
        Example:
            >>> stats = ProcessingStatistics(datetime.now(), datetime.now(), 100, 95)
            >>> stats.add_error_count("FileNotFoundError", 3)
            >>> print(stats.error_breakdown["FileNotFoundError"])  # 3
        """
        if not isinstance(error_type, str):
            raise TypeError("error_type must be string")
        if not error_type:
            raise ValueError("error_type must be non-empty string")
        if not isinstance(count, int):
            raise TypeError("count must be integer")
        if count <= 0:
            raise ValueError("count must be positive integer")
        
        self.error_breakdown[error_type] = self.error_breakdown.get(error_type, 0) + count
        logger.debug(f"Added error count: {error_type}={count}")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert ProcessingStatistics to dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary with all ProcessingStatistics attributes.
                Includes serialized datetime objects and calculated properties.
        
        Example:
            >>> stats = ProcessingStatistics(datetime.now(), datetime.now(), 100, 95)
            >>> data = stats.to_dict()
            >>> print(data["total_files_processed"])  # 100
        """
        return {
            "statistics_id": self.statistics_id,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "total_files_processed": self.total_files_processed,
            "total_files_successful": self.total_files_successful,
            "total_files_failed": self.total_files_failed,
            "total_files_skipped": self.total_files_skipped,
            "total_processing_time_seconds": self.total_processing_time_seconds,
            "total_chunks_created": self.total_chunks_created,
            "total_characters_processed": self.total_characters_processed,
            "file_type_breakdown": self.file_type_breakdown.copy(),
            "error_breakdown": self.error_breakdown.copy(),
            "processing_metadata": self.processing_metadata.copy(),
            "created_at": self.created_at.isoformat(),
            "success_rate": self.success_rate,
            "failure_rate": self.failure_rate,
            "average_processing_time_seconds": self.average_processing_time_seconds,
            "period_duration_seconds": self.period_duration_seconds
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingStatistics':
        """
        Create ProcessingStatistics instance from dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary with ProcessingStatistics attributes.
                Must contain required fields: period_start, period_end, total_files_processed, total_files_successful.
        
        Returns:
            ProcessingStatistics: New ProcessingStatistics instance.
        
        Raises:
            ValueError: If required fields are missing or invalid
            TypeError: If data types are incorrect
        
        Example:
            >>> data = {"period_start": "2023-01-01T00:00:00", "period_end": "2023-01-01T01:00:00", ...}
            >>> stats = ProcessingStatistics.from_dict(data)
        """
        if not isinstance(data, dict):
            raise TypeError("data must be dictionary")
        
        required_fields = ["period_start", "period_end", "total_files_processed", "total_files_successful"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Required field '{field}' missing in data")
        
        # Parse datetime objects
        period_start = datetime.fromisoformat(data["period_start"])
        period_end = datetime.fromisoformat(data["period_end"])
        created_at = None
        if "created_at" in data and data["created_at"]:
            created_at = datetime.fromisoformat(data["created_at"])
        
        return cls(
            period_start=period_start,
            period_end=period_end,
            total_files_processed=data["total_files_processed"],
            total_files_successful=data["total_files_successful"],
            statistics_id=data.get("statistics_id"),
            total_files_failed=data.get("total_files_failed", 0),
            total_files_skipped=data.get("total_files_skipped", 0),
            total_processing_time_seconds=data.get("total_processing_time_seconds", 0.0),
            total_chunks_created=data.get("total_chunks_created", 0),
            total_characters_processed=data.get("total_characters_processed", 0),
            file_type_breakdown=data.get("file_type_breakdown", {}),
            error_breakdown=data.get("error_breakdown", {}),
            processing_metadata=data.get("processing_metadata", {}),
            created_at=created_at
        )
    
    def __eq__(self, other: object) -> bool:
        """
        Compare ProcessingStatistics instances for equality.
        
        Args:
            other (object): Object to compare with.
        
        Returns:
            bool: True if instances are equal, False otherwise.
        
        Example:
            >>> stats1 = ProcessingStatistics(datetime.now(), datetime.now(), 100, 95)
            >>> stats2 = ProcessingStatistics(datetime.now(), datetime.now(), 100, 95)
            >>> stats1 == stats2  # True if same period and counts
        """
        if not isinstance(other, ProcessingStatistics):
            return False
        
        return (
            self.period_start == other.period_start and
            self.period_end == other.period_end and
            self.total_files_processed == other.total_files_processed and
            self.total_files_successful == other.total_files_successful and
            self.total_files_failed == other.total_files_failed and
            self.total_files_skipped == other.total_files_skipped
        )
    
    def __repr__(self) -> str:
        """
        String representation of ProcessingStatistics.
        
        Returns:
            str: Human-readable representation.
        
        Example:
            >>> stats = ProcessingStatistics(datetime.now(), datetime.now(), 100, 95)
            >>> print(stats)  # "ProcessingStatistics(period='2023-01-01 00:00:00-01:00:00', files=100, success=95)"
        """
        return (
            f"ProcessingStatistics("
            f"period='{self.period_start.strftime('%Y-%m-%d %H:%M:%S')}-{self.period_end.strftime('%H:%M:%S')}', "
            f"files={self.total_files_processed}, "
            f"success={self.total_files_successful})"
        )


class DatabaseMetadata:
    """
    Database Metadata Model - Database Information Container
    
    Represents comprehensive metadata about the database including
    configuration, health status, and operational information.
    
    This model is used for database monitoring, health checks,
    and providing operational insights.
    
    Attributes:
        total_files (int): Total number of files in database.
            Must be non-negative integer.
        total_chunks (int): Total number of chunks in database.
            Must be non-negative integer.
        total_size_bytes (int): Total size of all files in bytes.
            Must be non-negative integer.
        health_status (str): Current health status of database.
            Must be valid health status string.
        vector_store_status (str): Status of vector store connection.
            Must be valid status string.
        cache_size (int): Current number of cached items.
            Must be non-negative integer.
        cache_hit_rate (float): Cache hit rate percentage.
            Must be between 0.0 and 1.0.
        last_updated (datetime): Timestamp of last metadata update.
            Used for tracking metadata freshness.
        configuration (Dict[str, Any]): Database configuration.
            Contains configuration parameters and settings.
    
    Example:
        >>> metadata = DatabaseMetadata(
        ...     total_files=1000,
        ...     total_chunks=5000,
        ...     health_status="healthy",
        ...     vector_store_status="connected"
        ... )
        >>> print(metadata.total_files)  # 1000
    
    Raises:
        ValueError: If total_files, total_chunks, or total_size_bytes are negative
        ValueError: If cache_hit_rate is not between 0.0 and 1.0
        TypeError: If last_updated is not datetime object
    """
    
    def __init__(
        self,
        total_files: int,
        total_chunks: int,
        total_size_bytes: int,
        health_status: str,
        vector_store_status: str,
        cache_size: int = 0,
        cache_hit_rate: float = 0.0,
        last_updated: Optional[datetime] = None,
        configuration: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Database Metadata.
        
        Args:
            total_files (int): Total number of files in database.
                Must be non-negative integer.
            total_chunks (int): Total number of chunks in database.
                Must be non-negative integer.
            total_size_bytes (int): Total size of all files in bytes.
                Must be non-negative integer.
            health_status (str): Current health status of database.
                Must be valid health status string.
            vector_store_status (str): Status of vector store connection.
                Must be valid status string.
            cache_size (int): Current number of cached items.
                Must be non-negative integer. Defaults to 0.
            cache_hit_rate (float): Cache hit rate percentage.
                Must be between 0.0 and 1.0. Defaults to 0.0.
            last_updated (Optional[datetime]): Timestamp of last metadata update.
                If None, uses current timestamp. Defaults to None.
            configuration (Optional[Dict[str, Any]]): Database configuration.
                If None, uses empty dictionary. Defaults to None.
        
        Raises:
            ValueError: If total_files, total_chunks, or total_size_bytes are negative
            ValueError: If cache_hit_rate is not between 0.0 and 1.0
            TypeError: If last_updated is not datetime object
        """
        if total_files < 0:
            raise ValueError("total_files must be non-negative")
        if total_chunks < 0:
            raise ValueError("total_chunks must be non-negative")
        if total_size_bytes < 0:
            raise ValueError("total_size_bytes must be non-negative")
        if cache_size < 0:
            raise ValueError("cache_size must be non-negative")
        if not 0.0 <= cache_hit_rate <= 1.0:
            raise ValueError("cache_hit_rate must be between 0.0 and 1.0")
        if last_updated is not None and not isinstance(last_updated, datetime):
            raise TypeError("last_updated must be datetime object")
        
        self.total_files = total_files
        self.total_chunks = total_chunks
        self.total_size_bytes = total_size_bytes
        self.health_status = health_status
        self.vector_store_status = vector_store_status
        self.cache_size = cache_size
        self.cache_hit_rate = cache_hit_rate
        self.last_updated = last_updated or datetime.now()
        self.configuration = configuration or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert DatabaseMetadata to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of metadata.
        
        Example:
            >>> metadata = DatabaseMetadata(1000, 5000, 1024000, "healthy", "connected")
            >>> data = metadata.to_dict()
            >>> print(data["total_files"])  # 1000
        """
        return {
            "total_files": self.total_files,
            "total_chunks": self.total_chunks,
            "total_size_bytes": self.total_size_bytes,
            "health_status": self.health_status,
            "vector_store_status": self.vector_store_status,
            "cache_size": self.cache_size,
            "cache_hit_rate": self.cache_hit_rate,
            "last_updated": self.last_updated.isoformat(),
            "configuration": self.configuration
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DatabaseMetadata':
        """
        Create DatabaseMetadata instance from dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary with DatabaseMetadata attributes.
                Must contain required fields: total_files, total_chunks, total_size_bytes,
                health_status, vector_store_status.
        
        Returns:
            DatabaseMetadata: New DatabaseMetadata instance.
        
        Raises:
            ValueError: If required fields are missing or invalid
            TypeError: If data types are incorrect
        
        Example:
            >>> data = {"total_files": 1000, "total_chunks": 5000, "health_status": "healthy", ...}
            >>> metadata = DatabaseMetadata.from_dict(data)
        """
        if not isinstance(data, dict):
            raise TypeError("data must be dictionary")
        
        required_fields = ["total_files", "total_chunks", "total_size_bytes", "health_status", "vector_store_status"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Required field '{field}' missing in data")
        
        # Parse datetime object
        last_updated = None
        if "last_updated" in data and data["last_updated"]:
            last_updated = datetime.fromisoformat(data["last_updated"])
        
        return cls(
            total_files=data["total_files"],
            total_chunks=data["total_chunks"],
            total_size_bytes=data["total_size_bytes"],
            health_status=data["health_status"],
            vector_store_status=data["vector_store_status"],
            cache_size=data.get("cache_size", 0),
            cache_hit_rate=data.get("cache_hit_rate", 0.0),
            last_updated=last_updated,
            configuration=data.get("configuration", {})
        )
    
    def __eq__(self, other: object) -> bool:
        """
        Compare DatabaseMetadata instances for equality.
        
        Args:
            other (object): Object to compare with.
        
        Returns:
            bool: True if instances are equal, False otherwise.
        
        Example:
            >>> metadata1 = DatabaseMetadata(1000, 5000, 1024000, "healthy", "connected")
            >>> metadata2 = DatabaseMetadata(1000, 5000, 1024000, "healthy", "connected")
            >>> metadata1 == metadata2  # True
        """
        if not isinstance(other, DatabaseMetadata):
            return False
        
        return (
            self.total_files == other.total_files and
            self.total_chunks == other.total_chunks and
            self.total_size_bytes == other.total_size_bytes and
            self.health_status == other.health_status and
            self.vector_store_status == other.vector_store_status and
            self.cache_size == other.cache_size and
            abs(self.cache_hit_rate - other.cache_hit_rate) < 0.001
        )
    
    def __repr__(self) -> str:
        """
        String representation of DatabaseMetadata.
        
        Returns:
            str: Human-readable representation.
        
        Example:
            >>> metadata = DatabaseMetadata(1000, 5000, 1024000, "healthy", "connected")
            >>> print(metadata)  # "DatabaseMetadata(files=1000, chunks=5000, health=healthy)"
        """
        return (
            f"DatabaseMetadata("
            f"files={self.total_files}, "
            f"chunks={self.total_chunks}, "
            f"health={self.health_status})"
        )


class DatabaseHealth:
    """
    Database Health Model - Database Health Status Container
    
    Represents the health status of the database including
    connection status, performance metrics, and error information.
    
    This model is used for health monitoring and diagnostics.
    
    Attributes:
        status (str): Overall health status.
            Must be valid health status string.
        connection_status (str): Database connection status.
            Must be valid connection status string.
        performance_metrics (Dict[str, Any]): Performance metrics.
            Contains various performance indicators.
        error_count (int): Number of recent errors.
            Must be non-negative integer.
        last_error (Optional[str]): Last error message.
            None if no recent errors.
        last_check (datetime): Timestamp of last health check.
            Used for tracking health check frequency.
    
    Example:
        >>> health = DatabaseHealth("healthy", "connected", {"response_time": 0.1})
        >>> print(health.status)  # "healthy"
    
    Raises:
        ValueError: If error_count is negative
        TypeError: If last_check is not datetime object
    """
    
    def __init__(
        self,
        status: str,
        connection_status: str,
        performance_metrics: Optional[Dict[str, Any]] = None,
        error_count: int = 0,
        last_error: Optional[str] = None,
        last_check: Optional[datetime] = None
    ):
        """
        Initialize Database Health.
        
        Args:
            status (str): Overall health status.
                Must be valid health status string.
            connection_status (str): Database connection status.
                Must be valid connection status string.
            performance_metrics (Optional[Dict[str, Any]]): Performance metrics.
                If None, uses empty dictionary. Defaults to None.
            error_count (int): Number of recent errors.
                Must be non-negative integer. Defaults to 0.
            last_error (Optional[str]): Last error message.
                None if no recent errors. Defaults to None.
            last_check (Optional[datetime]): Timestamp of last health check.
                If None, uses current timestamp. Defaults to None.
        
        Raises:
            ValueError: If error_count is negative
            TypeError: If last_check is not datetime object
        """
        if error_count < 0:
            raise ValueError("error_count must be non-negative")
        if last_check is not None and not isinstance(last_check, datetime):
            raise TypeError("last_check must be datetime object")
        
        self.status = status
        self.connection_status = connection_status
        self.performance_metrics = performance_metrics or {}
        self.error_count = error_count
        self.last_error = last_error
        self.last_check = last_check or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert DatabaseHealth to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of health status.
        
        Example:
            >>> health = DatabaseHealth("healthy", "connected", {"response_time": 0.1})
            >>> data = health.to_dict()
            >>> print(data["status"])  # "healthy"
        """
        return {
            "status": self.status,
            "connection_status": self.connection_status,
            "performance_metrics": self.performance_metrics,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "last_check": self.last_check.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DatabaseHealth':
        """
        Create DatabaseHealth instance from dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary with DatabaseHealth attributes.
                Must contain required fields: status, connection_status.
        
        Returns:
            DatabaseHealth: New DatabaseHealth instance.
        
        Raises:
            ValueError: If required fields are missing or invalid
            TypeError: If data types are incorrect
        
        Example:
            >>> data = {"status": "healthy", "connection_status": "connected", ...}
            >>> health = DatabaseHealth.from_dict(data)
        """
        if not isinstance(data, dict):
            raise TypeError("data must be dictionary")
        
        required_fields = ["status", "connection_status"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Required field '{field}' missing in data")
        
        # Parse datetime object
        last_check = None
        if "last_check" in data and data["last_check"]:
            last_check = datetime.fromisoformat(data["last_check"])
        
        return cls(
            status=data["status"],
            connection_status=data["connection_status"],
            performance_metrics=data.get("performance_metrics", {}),
            error_count=data.get("error_count", 0),
            last_error=data.get("last_error"),
            last_check=last_check
        )
    
    def __eq__(self, other: object) -> bool:
        """
        Compare DatabaseHealth instances for equality.
        
        Args:
            other (object): Object to compare with.
        
        Returns:
            bool: True if instances are equal, False otherwise.
        
        Example:
            >>> health1 = DatabaseHealth("healthy", "connected")
            >>> health2 = DatabaseHealth("healthy", "connected")
            >>> health1 == health2  # True
        """
        if not isinstance(other, DatabaseHealth):
            return False
        
        return (
            self.status == other.status and
            self.connection_status == other.connection_status and
            self.error_count == other.error_count and
            self.last_error == other.last_error
        )
    
    def __repr__(self) -> str:
        """
        String representation of DatabaseHealth.
        
        Returns:
            str: Human-readable representation.
        
        Example:
            >>> health = DatabaseHealth("healthy", "connected")
            >>> print(health)  # "DatabaseHealth(status=healthy, connection=connected)"
        """
        return (
            f"DatabaseHealth("
            f"status={self.status}, "
            f"connection={self.connection_status})"
        ) 