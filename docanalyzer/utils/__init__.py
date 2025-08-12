"""
Utils Module - Utility Functions

Provides utility functions for file system operations and other common tasks.

Author: File Watcher Team
Version: 1.0.0
"""

from .file_utils import (
    is_directory,
    is_file,
    is_readable,
    is_writable,
    get_file_metadata,
    safe_create_directory,
    safe_remove_file,
    get_file_size,
    get_file_modified_time,
    normalize_path,
    ensure_directory_exists,
)

__all__ = [
    "is_directory",
    "is_file", 
    "is_readable",
    "is_writable",
    "get_file_metadata",
    "safe_create_directory",
    "safe_remove_file",
    "get_file_size",
    "get_file_modified_time",
    "normalize_path",
    "ensure_directory_exists",
] 