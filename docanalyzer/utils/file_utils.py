"""
File Utilities - File System Operations

Provides utility functions for file system operations including
file validation, metadata extraction, and safe file operations.

Author: File Watcher Team
Version: 1.0.0
"""

import os
import stat
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def is_directory(path: str) -> bool:
    """
    Check if path is a directory.
    
    Args:
        path (str): Path to check.
            Must be valid file system path.
    
    Returns:
        bool: True if path is a directory, False otherwise.
    
    Raises:
        OSError: If path cannot be accessed
    """
    try:
        return os.path.isdir(path)
    except OSError as e:
        logger.error(f"Error checking if path is directory {path}: {e}")
        raise


def is_file(path: str) -> bool:
    """
    Check if path is a regular file.
    
    Args:
        path (str): Path to check.
            Must be valid file system path.
    
    Returns:
        bool: True if path is a regular file, False otherwise.
    
    Raises:
        OSError: If path cannot be accessed
    """
    try:
        return os.path.isfile(path)
    except OSError as e:
        logger.error(f"Error checking if path is file {path}: {e}")
        raise


def is_readable(path: str) -> bool:
    """
    Check if path is readable.
    
    Args:
        path (str): Path to check.
            Must be valid file system path.
    
    Returns:
        bool: True if path is readable, False otherwise.
    
    Raises:
        OSError: If path cannot be accessed
    """
    try:
        return os.access(path, os.R_OK)
    except OSError as e:
        logger.error(f"Error checking if path is readable {path}: {e}")
        raise


def is_writable(path: str) -> bool:
    """
    Check if path is writable.
    
    Args:
        path (str): Path to check.
            Must be valid file system path.
    
    Returns:
        bool: True if path is writable, False otherwise.
    
    Raises:
        OSError: If path cannot be accessed
    """
    try:
        return os.access(path, os.W_OK)
    except OSError as e:
        logger.error(f"Error checking if path is writable {path}: {e}")
        raise


def get_file_metadata(path: str) -> Dict[str, Any]:
    """
    Get file metadata.
    
    Args:
        path (str): Path to file.
            Must be existing file path.
    
    Returns:
        Dict[str, Any]: File metadata including size, modification time, etc.
            Format: {
                "size": int,
                "modified_time": datetime,
                "created_time": datetime,
                "permissions": str,
                "owner": str,
                "group": str
            }
    
    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If cannot access file
        OSError: If file system error occurs
    """
    try:
        stat_info = os.stat(path)
        
        metadata = {
            "size": stat_info.st_size,
            "modified_time": datetime.fromtimestamp(stat_info.st_mtime),
            "created_time": datetime.fromtimestamp(stat_info.st_ctime),
            "permissions": oct(stat_info.st_mode)[-3:],
        }
        
        # Try to get owner and group info
        try:
            import pwd
            import grp
            owner = pwd.getpwuid(stat_info.st_uid).pw_name
            group = grp.getgrgid(stat_info.st_gid).gr_name
            metadata.update({
                "owner": owner,
                "group": group
            })
        except (ImportError, KeyError):
            # pwd/grp modules not available or user/group not found
            metadata.update({
                "owner": str(stat_info.st_uid),
                "group": str(stat_info.st_gid)
            })
        
        return metadata
    except FileNotFoundError:
        raise
    except PermissionError:
        raise
    except OSError as e:
        logger.error(f"Error getting file metadata {path}: {e}")
        raise


def safe_create_directory(path: str) -> bool:
    """
    Safely create directory if it doesn't exist.
    
    Args:
        path (str): Directory path to create.
            Must be valid directory path.
    
    Returns:
        bool: True if directory was created or already exists, False otherwise.
    
    Raises:
        PermissionError: If cannot create directory
        OSError: If file system error occurs
    """
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except PermissionError:
        raise
    except OSError as e:
        logger.error(f"Error creating directory {path}: {e}")
        raise


def safe_remove_file(path: str) -> bool:
    """
    Safely remove file if it exists.
    
    Args:
        path (str): File path to remove.
            Must be valid file path.
    
    Returns:
        bool: True if file was removed or didn't exist, False otherwise.
    
    Raises:
        PermissionError: If cannot remove file
        OSError: If file system error occurs
    """
    try:
        path_obj = Path(path)
        if path_obj.exists():
            path_obj.unlink()
            return True
        return True  # File didn't exist, consider it "removed"
    except PermissionError:
        raise
    except OSError as e:
        logger.error(f"Error removing file {path}: {e}")
        raise


def get_file_size(path: str) -> int:
    """
    Get file size in bytes.
    
    Args:
        path (str): Path to file.
            Must be existing file path.
    
    Returns:
        int: File size in bytes.
    
    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If cannot access file
        OSError: If file system error occurs
    """
    try:
        return os.path.getsize(path)
    except FileNotFoundError:
        raise
    except PermissionError:
        raise
    except OSError as e:
        logger.error(f"Error getting file size {path}: {e}")
        raise


def get_file_modified_time(path: str) -> datetime:
    """
    Get file modification time.
    
    Args:
        path (str): Path to file.
            Must be existing file path.
    
    Returns:
        datetime: File modification time.
    
    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If cannot access file
        OSError: If file system error occurs
    """
    try:
        stat_info = os.stat(path)
        return datetime.fromtimestamp(stat_info.st_mtime)
    except FileNotFoundError:
        raise
    except PermissionError:
        raise
    except OSError as e:
        logger.error(f"Error getting file modified time {path}: {e}")
        raise


def normalize_path(path: str) -> str:
    """
    Normalize file path.
    
    Args:
        path (str): Path to normalize.
            Must be valid file system path.
    
    Returns:
        str: Normalized absolute path.
    
    Raises:
        OSError: If path cannot be resolved
    """
    try:
        return str(Path(path).resolve())
    except OSError as e:
        logger.error(f"Error normalizing path {path}: {e}")
        raise


def ensure_directory_exists(path: str) -> None:
    """
    Ensure directory exists, create if necessary.
    
    Args:
        path (str): Directory path to ensure.
            Must be valid directory path.
    
    Raises:
        PermissionError: If cannot create directory
        OSError: If file system error occurs
    """
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
    except PermissionError:
        raise
    except OSError as e:
        logger.error(f"Error ensuring directory exists {path}: {e}")
        raise 