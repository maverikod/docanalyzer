"""
LockFile Model - Process Coordination Lock

Represents a lock file used to prevent concurrent processing
of the same directory by multiple processes.

This model is used for process coordination, preventing race conditions,
and ensuring atomic directory processing operations.

Author: DocAnalyzer Team
Version: 1.0.0
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class LockFile:
    """
    Lock File Model - Process Coordination Lock
    
    Represents a lock file used to prevent concurrent processing
    of the same directory by multiple processes.
    
    This model is used for process coordination, preventing race conditions,
    and ensuring atomic directory processing operations.
    
    Attributes:
        process_id (int): ID of the process that created the lock.
            Used to identify the process that owns the lock.
        created_at (datetime): Timestamp when lock was created.
            Used for lock timeout calculations.
        directory (str): Path to the directory being locked.
            Must match the directory path being processed.
        status (str): Current status of the lock.
            Values: 'active', 'expired', 'orphaned', 'released'.
        lock_file_path (str): Full path to the lock file.
            Used for lock file management operations.
        metadata (Dict[str, Any]): Additional lock metadata.
            Can contain process information, configuration, etc.
        timeout_seconds (int): Lock timeout in seconds.
            Used to determine if lock has expired.
    
    Example:
        >>> lock = LockFile(12345, datetime.now(), "/path/to/docs")
        >>> print(lock.process_id)  # 12345
        >>> print(lock.status)  # "active"
    
    Raises:
        ValueError: If process_id is negative or directory is empty
        TypeError: If created_at is not datetime object
    """
    
    def __init__(
        self,
        process_id: int,
        created_at: datetime,
        directory: str,
        status: str = "active",
        lock_file_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 3600
    ):
        """
        Initialize LockFile instance.
        
        Args:
            process_id (int): ID of the process that created the lock.
                Must be positive integer.
            created_at (datetime): Timestamp when lock was created.
                Must be valid datetime object.
            directory (str): Path to the directory being locked.
                Must be non-empty string.
            status (str, optional): Current status of the lock.
                Defaults to "active". Valid values: active, expired, orphaned, released.
            lock_file_path (Optional[str], optional): Full path to lock file.
                Defaults to None. If None, will be generated from directory path.
            metadata (Optional[Dict[str, Any]], optional): Additional metadata.
                Defaults to None.
            timeout_seconds (int, optional): Lock timeout in seconds.
                Defaults to 3600 (1 hour). Must be positive integer.
        
        Raises:
            ValueError: If process_id is negative or directory is empty
            TypeError: If created_at is not datetime object
        """
        # Validate input parameters
        if not isinstance(process_id, int) or process_id <= 0:
            raise ValueError("process_id must be positive integer")
        
        if not isinstance(created_at, datetime):
            raise TypeError("created_at must be datetime object")
        
        if not directory or not isinstance(directory, str):
            raise ValueError("directory must be non-empty string")
        
        # Validate status
        valid_statuses = ["active", "expired", "orphaned", "released"]
        if status not in valid_statuses:
            raise ValueError(f"status must be one of: {valid_statuses}")
        
        # Validate timeout
        if not isinstance(timeout_seconds, int) or timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive integer")
        
        # Set instance attributes
        self.process_id = process_id
        self.created_at = created_at
        self.directory = directory
        self.status = status
        self.timeout_seconds = timeout_seconds
        self.metadata = metadata or {}
        
        # Generate lock file path if not provided
        if lock_file_path is None:
            self.lock_file_path = str(Path(directory) / ".processing.lock")
        else:
            self.lock_file_path = lock_file_path
        
        logger.debug(f"Created LockFile for directory: {directory}, process: {process_id}")
    
    def is_expired(self) -> bool:
        """
        Check if lock has expired based on timeout.
        
        Returns:
            bool: True if lock has expired, False otherwise.
        
        Example:
            >>> lock = LockFile(12345, datetime.now(), "/path/to/docs")
            >>> if lock.is_expired():
            ...     print("Lock has expired")
        """
        age_seconds = self.get_age_seconds()
        return age_seconds > self.timeout_seconds
    
    def get_age_seconds(self) -> int:
        """
        Get age of lock in seconds.
        
        Returns:
            int: Age of lock in seconds since creation.
        
        Example:
            >>> lock = LockFile(12345, datetime.now(), "/path/to/docs")
            >>> age = lock.get_age_seconds()
            >>> print(f"Lock is {age} seconds old")
        """
        now = datetime.now()
        age_delta = now - self.created_at
        return int(age_delta.total_seconds())
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert LockFile to dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary with all LockFile attributes.
                Includes serialized datetime objects.
        
        Example:
            >>> lock = LockFile(12345, datetime.now(), "/path/to/docs")
            >>> data = lock.to_dict()
            >>> print(data["process_id"])  # 12345
        """
        return {
            "process_id": self.process_id,
            "created_at": self.created_at.isoformat(),
            "directory": self.directory,
            "status": self.status,
            "lock_file_path": self.lock_file_path,
            "timeout_seconds": self.timeout_seconds,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LockFile':
        """
        Create LockFile instance from dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary with LockFile attributes.
                Must contain required fields: process_id, created_at, directory.
        
        Returns:
            LockFile: New LockFile instance.
        
        Raises:
            ValueError: If required fields are missing or invalid
            TypeError: If data types are incorrect
        
        Example:
            >>> data = {"process_id": 12345, "created_at": "2023-01-01T00:00:00", ...}
            >>> lock = LockFile.from_dict(data)
        """
        # Validate required fields
        required_fields = ["process_id", "created_at", "directory"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Parse datetime field
        created_at = datetime.fromisoformat(data["created_at"])
        
        return cls(
            process_id=data["process_id"],
            created_at=created_at,
            directory=data["directory"],
            status=data.get("status", "active"),
            lock_file_path=data.get("lock_file_path"),
            metadata=data.get("metadata", {}),
            timeout_seconds=data.get("timeout_seconds", 3600)
        )
    
    def __eq__(self, other: object) -> bool:
        """
        Compare LockFile instances for equality.
        
        Args:
            other (object): Object to compare with.
        
        Returns:
            bool: True if instances are equal, False otherwise.
        
        Example:
            >>> lock1 = LockFile(12345, datetime.now(), "/path/docs")
            >>> lock2 = LockFile(12345, datetime.now(), "/path/docs")
            >>> lock1 == lock2  # True if same process_id and directory
        """
        if not isinstance(other, LockFile):
            return False
        
        return (
            self.process_id == other.process_id and
            self.directory == other.directory and
            self.created_at == other.created_at
        )
    
    def __repr__(self) -> str:
        """
        String representation of LockFile.
        
        Returns:
            str: Human-readable representation.
        
        Example:
            >>> lock = LockFile(12345, datetime.now(), "/path/docs")
            >>> print(lock)  # "LockFile(pid=12345, dir='/path/docs', status='active')"
        """
        return (
            f"LockFile(pid={self.process_id}, "
            f"dir='{self.directory}', "
            f"status='{self.status}')"
        ) 