"""
File Filters Package

Provides filtering functionality for file scanning and processing.
Includes base filter classes and specific implementations for different file types.

Author: DocAnalyzer Team
Version: 1.0.0
"""

from .file_filter import FileFilter, FileFilterResult, SupportedFileTypes

__all__ = [
    "FileFilter",
    "FileFilterResult", 
    "SupportedFileTypes"
]

__version__ = "1.0.0" 