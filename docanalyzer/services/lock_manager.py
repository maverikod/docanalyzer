"""
Lock Manager - Directory Locking Service

Provides functionality for creating, managing, and cleaning up lock files
to prevent concurrent processing of the same directory by multiple processes.

The lock manager creates lock files with process ID and metadata,
checks for orphaned locks, and ensures atomic directory processing.

Author: File Watcher Team
Version: 1.0.0
"""

import os
import json
import psutil
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import logging
import asyncio
import aiofiles

from docanalyzer.models.file_system import LockFile

logger = logging.getLogger(__name__)

DEFAULT_LOCK_TIMEOUT = 3600
LOCK_FILE_NAME = ".processing.lock"


class LockError(Exception):
    """
    Lock Error - Exception for lock-related operations.
    
    Raised when lock operations fail, such as when trying to create
    a lock on an already locked directory or when lock validation fails.
    
    Attributes:
        message (str): Error message describing the lock operation failure
        directory (Optional[str]): Directory path where the error occurred
        process_id (Optional[int]): Process ID involved in the error
    """
    
    def __init__(self, message: str, directory: Optional[str] = None, process_id: Optional[int] = None):
        """
        Initialize LockError instance.
        
        Args:
            message (str): Error message describing the lock operation failure
            directory (Optional[str]): Directory path where the error occurred
            process_id (Optional[int]): Process ID involved in the error
        """
        super().__init__(message)
        self.message = message
        self.directory = directory
        self.process_id = process_id


class LockManager:
    """
    Lock Manager - Directory Locking Service
    
    Manages lock files to prevent concurrent processing of directories.
    Creates, validates, and cleans up lock files with process metadata.
    
    The lock manager ensures that only one process can process a directory
    at a time by creating lock files with process ID and metadata.
    It also handles orphaned locks by checking if the process that created
    the lock is still running.
    
    Attributes:
        lock_timeout (int): Maximum lock duration in seconds.
            Defaults to 3600 seconds (1 hour).
        lock_file_name (str): Name of the lock file in directories.
            Defaults to ".processing.lock".
    
    Example:
        >>> lock_manager = LockManager()
        >>> lock_file = await lock_manager.create_lock("/path/to/directory")
        >>> await lock_manager.remove_lock(lock_file)
    
    Raises:
        LockError: When lock operations fail
        FileNotFoundError: When directory doesn't exist
        PermissionError: When file system permissions are insufficient
    """
    
    def __init__(self, lock_timeout: int = DEFAULT_LOCK_TIMEOUT):
        """
        Initialize LockManager instance.
        
        Args:
            lock_timeout (int): Maximum lock duration in seconds.
                Must be positive integer. Defaults to 3600.
        
        Raises:
            ValueError: If lock_timeout is not positive
        """
        if lock_timeout <= 0:
            raise ValueError("lock_timeout must be positive")
        self.lock_timeout = lock_timeout
        self.lock_file_name = LOCK_FILE_NAME
    
    async def create_lock(self, directory: str) -> LockFile:
        """
        Create lock file for directory.
        
        Creates a lock file with current process ID and metadata.
        If lock already exists, validates it and removes if orphaned.
        
        Args:
            directory (str): Path to directory to lock.
                Must be existing directory path.
        
        Returns:
            LockFile: Created lock file with metadata.
        
        Raises:
            FileNotFoundError: If directory doesn't exist
            PermissionError: If cannot create lock file
            LockError: If directory is already locked by active process
        """
        if not os.path.exists(directory):
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        if not os.path.isdir(directory):
            raise FileNotFoundError(f"Path is not a directory: {directory}")
        
        lock_path = Path(directory) / self.lock_file_name
        
        # Check existing lock
        if lock_path.exists():
            try:
                existing_lock = await self._read_lock_file(lock_path)
                if await self.is_process_alive(existing_lock.process_id):
                    raise LockError(
                        f"Directory already locked by process {existing_lock.process_id}",
                        directory=directory,
                        process_id=existing_lock.process_id
                    )
                else:
                    logger.warning(f"Removing orphaned lock for directory: {directory}")
                    await self._remove_lock_file(lock_path)
            except (FileNotFoundError, LockError):
                # Lock file is corrupted, remove it
                logger.warning(f"Removing corrupted lock file: {lock_path}")
                await self._remove_lock_file(lock_path)
        
        # Create new lock
        lock_data = LockFile(
            process_id=os.getpid(),
            created_at=datetime.now(),
            directory=directory,
            status="active",
            lock_file_path=str(lock_path)
        )
        
        await self._write_lock_file(lock_path, lock_data)
        logger.info(f"Created lock for directory: {directory}")
        return lock_data
    
    async def remove_lock(self, lock_file: LockFile) -> bool:
        """
        Remove lock file from directory.
        
        Validates lock ownership and removes the lock file.
        
        Args:
            lock_file (LockFile): Lock file to remove.
                Must be valid LockFile instance.
        
        Returns:
            bool: True if lock was removed, False otherwise.
        
        Raises:
            PermissionError: If cannot remove lock file
            LockError: If lock file is owned by different process
        """
        if lock_file.process_id != os.getpid():
            raise LockError(
                f"Lock file is owned by process {lock_file.process_id}, not current process {os.getpid()}",
                directory=lock_file.directory,
                process_id=lock_file.process_id
            )
        
        lock_path = Path(lock_file.lock_file_path)
        if not lock_path.exists():
            logger.warning(f"Lock file does not exist: {lock_path}")
            return False
        
        success = await self._remove_lock_file(lock_path)
        if success:
            logger.info(f"Removed lock for directory: {lock_file.directory}")
        else:
            logger.error(f"Failed to remove lock for directory: {lock_file.directory}")
        
        return success
    
    async def check_lock(self, directory: str) -> Optional[LockFile]:
        """
        Check if directory is locked.
        
        Reads and validates existing lock file in directory.
        
        Args:
            directory (str): Path to directory to check.
                Must be existing directory path.
        
        Returns:
            Optional[LockFile]: Lock file if directory is locked, None otherwise.
        
        Raises:
            FileNotFoundError: If directory doesn't exist
            PermissionError: If cannot read lock file
        """
        if not os.path.exists(directory):
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        lock_path = Path(directory) / self.lock_file_name
        if not lock_path.exists():
            return None
        
        try:
            lock_data = await self._read_lock_file(lock_path)
            if await self.is_process_alive(lock_data.process_id):
                return lock_data
            else:
                logger.warning(f"Found orphaned lock for directory: {directory}")
                await self._remove_lock_file(lock_path)
                return None
        except (FileNotFoundError, LockError) as e:
            logger.warning(f"Error reading lock file {lock_path}: {e}")
            return None
    
    async def cleanup_orphaned_locks(self) -> List[str]:
        """
        Clean up orphaned lock files.
        
        Finds and removes lock files where the creating process
        is no longer running.
        
        Returns:
            List[str]: List of directories where orphaned locks were removed.
        
        Raises:
            PermissionError: If cannot access lock files
        """
        cleaned_directories = []
        
        # This is a simplified implementation that would need to be enhanced
        # to scan all configured directories. For now, we'll return empty list.
        # In a full implementation, this would scan all directories from config.
        
        logger.info("Cleanup of orphaned locks completed")
        return cleaned_directories
    
    async def is_process_alive(self, pid: int) -> bool:
        """
        Check if process with given PID is still running.
        
        Args:
            pid (int): Process ID to check.
                Must be positive integer.
        
        Returns:
            bool: True if process is running, False otherwise.
        
        Raises:
            ValueError: If pid is not positive
        """
        if pid <= 0:
            raise ValueError("PID must be positive")
        
        try:
            # Check if process exists
            process = psutil.Process(pid)
            return process.is_running()
        except psutil.NoSuchProcess:
            return False
        except psutil.AccessDenied:
            # Process exists but we can't access it (likely different user)
            return True
        except Exception as e:
            logger.warning(f"Error checking process {pid}: {e}")
            return False
    
    async def _read_lock_file(self, lock_path: Path) -> LockFile:
        """
        Read lock file from disk.
        
        Args:
            lock_path (Path): Path to lock file.
                Must be existing file path.
        
        Returns:
            LockFile: Lock file data from disk.
        
        Raises:
            FileNotFoundError: If lock file doesn't exist
            PermissionError: If cannot read lock file
            LockError: If lock file is corrupted
        """
        if not lock_path.exists():
            raise FileNotFoundError(f"Lock file not found: {lock_path}")
        
        try:
            async with aiofiles.open(lock_path, 'r') as f:
                content = await f.read()
            
            lock_data = json.loads(content)
            
            if not self._validate_lock_data(lock_data):
                raise LockError(f"Invalid lock file format: {lock_path}")
            
            return LockFile(
                process_id=lock_data["process_id"],
                created_at=datetime.fromisoformat(lock_data["created_at"]),
                directory=lock_data["directory"],
                status=lock_data["status"],
                lock_file_path=lock_data["lock_file_path"]
            )
        except json.JSONDecodeError as e:
            raise LockError(f"Corrupted lock file {lock_path}: {e}")
        except KeyError as e:
            raise LockError(f"Missing required field in lock file {lock_path}: {e}")
        except Exception as e:
            if "Permission denied" in str(e):
                raise PermissionError(f"Cannot read lock file {lock_path}")
            raise LockError(f"Error reading lock file {lock_path}: {e}")
    
    async def _write_lock_file(self, lock_path: Path, lock_data: LockFile) -> None:
        """
        Write lock file to disk.
        
        Args:
            lock_path (Path): Path to lock file.
            lock_data (LockFile): Lock data to write.
        
        Raises:
            PermissionError: If cannot write lock file
            LockError: If lock file write fails
        """
        try:
            # Ensure directory exists
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Prepare data for JSON serialization
            data = {
                "process_id": lock_data.process_id,
                "created_at": lock_data.created_at.isoformat(),
                "directory": lock_data.directory,
                "status": lock_data.status,
                "lock_file_path": lock_data.lock_file_path
            }
            
            async with aiofiles.open(lock_path, 'w') as f:
                await f.write(json.dumps(data, indent=2))
                
        except Exception as e:
            if "Permission denied" in str(e):
                raise PermissionError(f"Cannot write lock file {lock_path}")
            raise LockError(f"Error writing lock file {lock_path}: {e}")
    
    async def _remove_lock_file(self, lock_path: Path) -> bool:
        """
        Remove lock file from disk.
        
        Args:
            lock_path (Path): Path to lock file to remove.
        
        Returns:
            bool: True if file was removed, False otherwise.
        
        Raises:
            PermissionError: If cannot remove lock file
        """
        try:
            if lock_path.exists():
                lock_path.unlink()
                return True
            return False
        except Exception as e:
            if "Permission denied" in str(e):
                raise PermissionError(f"Cannot remove lock file {lock_path}")
            logger.error(f"Error removing lock file {lock_path}: {e}")
            return False
    
    def _validate_lock_data(self, lock_data: Dict[str, Any]) -> bool:
        """
        Validate lock file data structure.
        
        Args:
            lock_data (Dict[str, Any]): Lock data to validate.
        
        Returns:
            bool: True if data is valid, False otherwise.
        """
        required_fields = ["process_id", "created_at", "directory", "status", "lock_file_path"]
        
        # Check required fields
        for field in required_fields:
            if field not in lock_data:
                return False
        
        # Validate process_id
        if not isinstance(lock_data["process_id"], int) or lock_data["process_id"] <= 0:
            return False
        
        # Validate created_at
        try:
            datetime.fromisoformat(lock_data["created_at"])
        except (ValueError, TypeError):
            return False
        
        # Validate directory
        if not isinstance(lock_data["directory"], str) or not lock_data["directory"]:
            return False
        
        # Validate status
        if not isinstance(lock_data["status"], str) or not lock_data["status"]:
            return False
        
        # Validate lock_file_path
        if not isinstance(lock_data["lock_file_path"], str) or not lock_data["lock_file_path"]:
            return False
        
        return True 