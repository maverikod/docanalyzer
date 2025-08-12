"""
File Filter System

Provides filtering functionality for file scanning and processing.
Includes base filter classes and specific implementations for different file types.

The file filter system allows filtering files based on:
- File extensions
- File size limits
- File content type
- Custom filtering rules

Author: DocAnalyzer Team
Version: 1.0.0
"""

from typing import List, Dict, Optional, Set, Union
from pathlib import Path
from enum import Enum
import logging

from docanalyzer.models.file_system import FileInfo

logger = logging.getLogger(__name__)

DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
DEFAULT_MIN_FILE_SIZE = 0  # 0 bytes


class SupportedFileTypes(Enum):
    """
    Supported file types for processing.
    
    Defines the file extensions that are supported for processing
    by the DocAnalyzer system.
    
    Attributes:
        TEXT: Plain text files (.txt)
        MARKDOWN: Markdown files (.md, .markdown)
        PYTHON: Python source files (.py)
        JAVASCRIPT: JavaScript files (.js)
        TYPESCRIPT: TypeScript files (.ts)
        JSON: JSON data files (.json)
        YAML: YAML configuration files (.yml, .yaml)
        XML: XML files (.xml)
        HTML: HTML files (.html, .htm)
        CSS: CSS stylesheets (.css)
        SQL: SQL scripts (.sql)
        SHELL: Shell scripts (.sh, .bash)
        CONFIG: Configuration files (.conf, .config, .ini)
    """
    
    TEXT = "text"
    MARKDOWN = "markdown"
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JSON = "json"
    YAML = "yaml"
    XML = "xml"
    HTML = "html"
    CSS = "css"
    SQL = "sql"
    SHELL = "shell"
    CONFIG = "config"


class FileFilterResult:
    """
    File Filter Result - Filtering Decision
    
    Represents the result of a file filtering operation, including
    whether the file should be processed and any additional metadata.
    
    Attributes:
        should_process (bool): Whether the file should be processed.
            True if file passes all filters, False otherwise.
        reason (str): Human-readable reason for the filtering decision.
            Explains why file was accepted or rejected.
        filter_name (str): Name of the filter that made the decision.
            Identifies which filter was applied.
        metadata (Dict[str, any]): Additional metadata about the filtering.
            May include file size, type, or other relevant information.
    
    Example:
        >>> result = FileFilterResult(
        ...     should_process=True,
        ...     reason="File is supported text file",
        ...     filter_name="extension_filter"
        ... )
        >>> print(result.should_process)  # True
    """
    
    def __init__(
        self,
        should_process: bool,
        reason: str,
        filter_name: str,
        metadata: Optional[Dict[str, any]] = None
    ):
        """
        Initialize FileFilterResult instance.
        
        Args:
            should_process (bool): Whether the file should be processed.
                Must be boolean value.
            reason (str): Human-readable reason for the decision.
                Must be non-empty string.
            filter_name (str): Name of the filter that made the decision.
                Must be non-empty string.
            metadata (Optional[Dict[str, any]]): Additional metadata.
                Defaults to None. If provided, must be dictionary.
        
        Raises:
            ValueError: If should_process is not boolean or reason/filter_name are empty
            TypeError: If metadata is not None and not a dictionary
        """
        if not isinstance(should_process, bool):
            raise ValueError("should_process must be boolean")
        
        if not reason or not isinstance(reason, str):
            raise ValueError("reason must be non-empty string")
        
        if not filter_name or not isinstance(filter_name, str):
            raise ValueError("filter_name must be non-empty string")
        
        if metadata is not None and not isinstance(metadata, dict):
            raise TypeError("metadata must be dictionary or None")
        
        self.should_process = should_process
        self.reason = reason
        self.filter_name = filter_name
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, any]:
        """
        Convert result to dictionary representation.
        
        Returns:
            Dict[str, any]: Dictionary representation of the filter result.
                Format: {
                    "should_process": bool,
                    "reason": str,
                    "filter_name": str,
                    "metadata": Dict[str, any]
                }
        
        Example:
            >>> result = FileFilterResult(True, "Accepted", "test_filter")
            >>> data = result.to_dict()
            >>> print(data["should_process"])  # True
        """
        return {
            "should_process": self.should_process,
            "reason": self.reason,
            "filter_name": self.filter_name,
            "metadata": self.metadata
        }
    
    def __str__(self) -> str:
        """
        String representation of the filter result.
        
        Returns:
            str: Human-readable string representation.
                Format: "FilterResult(should_process={}, reason='{}', filter='{}')"
        
        Example:
            >>> result = FileFilterResult(True, "Accepted", "test_filter")
            >>> print(str(result))  # "FilterResult(should_process=True, reason='Accepted', filter='test_filter')"
        """
        return f"FilterResult(should_process={self.should_process}, reason='{self.reason}', filter='{self.filter_name}')"


class FileFilter:
    """
    File Filter - Base Filtering System
    
    Provides base functionality for filtering files during directory scanning.
    Supports filtering by file extension, size, and custom rules.
    
    The filter system is designed to be extensible and configurable,
    allowing different filtering strategies for different use cases.
    
    Attributes:
        supported_extensions (Set[str]): Set of supported file extensions.
            Extensions should be lowercase without leading dot.
        max_file_size (int): Maximum file size in bytes.
            Files larger than this will be rejected.
        min_file_size (int): Minimum file size in bytes.
            Files smaller than this will be rejected.
        exclude_patterns (List[str]): Patterns to exclude from processing.
            Supports glob patterns for file matching.
        include_patterns (List[str]): Patterns to include in processing.
            Supports glob patterns for file matching.
    
    Example:
        >>> filter = FileFilter(
        ...     supported_extensions={".txt", ".md"},
        ...     max_file_size=1024*1024
        ... )
        >>> result = filter.filter_file(file_info)
        >>> print(result.should_process)  # True/False
    """
    
    def __init__(
        self,
        supported_extensions: Optional[Set[str]] = None,
        max_file_size: int = DEFAULT_MAX_FILE_SIZE,
        min_file_size: int = DEFAULT_MIN_FILE_SIZE,
        exclude_patterns: Optional[List[str]] = None,
        include_patterns: Optional[List[str]] = None
    ):
        """
        Initialize FileFilter instance.
        
        Args:
            supported_extensions (Optional[Set[str]]): Set of supported extensions.
                Defaults to None (all extensions allowed). Must be set of strings.
            max_file_size (int): Maximum file size in bytes.
                Must be positive integer. Defaults to 10MB.
            min_file_size (int): Minimum file size in bytes.
                Must be non-negative integer. Defaults to 0.
            exclude_patterns (Optional[List[str]]): Patterns to exclude.
                Defaults to None. Must be list of strings if provided.
            include_patterns (Optional[List[str]]): Patterns to include.
                Defaults to None. Must be list of strings if provided.
        
        Raises:
            ValueError: If max_file_size is not positive or min_file_size is negative
            TypeError: If parameters are not of expected types
        """
        if max_file_size <= 0:
            raise ValueError("max_file_size must be positive")
        
        if min_file_size < 0:
            raise ValueError("min_file_size must be non-negative")
        
        if min_file_size > max_file_size:
            raise ValueError("min_file_size cannot be greater than max_file_size")
        
        if supported_extensions is not None and not isinstance(supported_extensions, set):
            raise TypeError("supported_extensions must be set or None")
        
        if exclude_patterns is not None and not isinstance(exclude_patterns, list):
            raise TypeError("exclude_patterns must be list or None")
        
        if include_patterns is not None and not isinstance(include_patterns, list):
            raise TypeError("include_patterns must be list or None")
        
        self.supported_extensions = supported_extensions or set()
        self.max_file_size = max_file_size
        self.min_file_size = min_file_size
        self.exclude_patterns = exclude_patterns or []
        self.include_patterns = include_patterns or []
    
    def filter_file(self, file_info: FileInfo) -> FileFilterResult:
        """
        Filter a single file based on configured rules.
        
        Applies all filtering rules to determine if the file should be processed.
        Rules are applied in order: extension, size, patterns.
        
        Args:
            file_info (FileInfo): File information to filter.
                Must be valid FileInfo instance.
        
        Returns:
            FileFilterResult: Filtering decision with metadata.
                Contains should_process flag and reason for decision.
        
        Raises:
            ValueError: If file_info is None or invalid
            FileNotFoundError: If file does not exist
            PermissionError: If file access is denied
        
        Example:
            >>> filter = FileFilter(supported_extensions={".txt"})
            >>> result = filter.filter_file(file_info)
            >>> if result.should_process:
            ...     print(f"Processing {file_info.path}")
        """
        if file_info is None:
            raise ValueError("file_info cannot be None")
        
        if not isinstance(file_info, FileInfo):
            raise ValueError("file_info must be FileInfo instance")
        
        # Check extension first
        extension_result = self._check_extension(file_info)
        if not extension_result.should_process:
            return extension_result
        
        # Check size
        size_result = self._check_size(file_info)
        if not size_result.should_process:
            return size_result
        
        # Check patterns
        pattern_result = self._check_patterns(file_info)
        if not pattern_result.should_process:
            return pattern_result
        
        # All checks passed
        return FileFilterResult(
            should_process=True,
            reason="File passes all filters",
            filter_name="file_filter",
            metadata={
                "extension": file_info.file_extension,
                "size": file_info.file_size,
                "path": file_info.file_path
            }
        )
    
    def filter_files(self, file_infos: List[FileInfo]) -> List[FileFilterResult]:
        """
        Filter multiple files based on configured rules.
        
        Applies filtering to a list of files and returns results for each.
        This method is more efficient than calling filter_file multiple times.
        
        Args:
            file_infos (List[FileInfo]): List of files to filter.
                Must be list of valid FileInfo instances.
        
        Returns:
            List[FileFilterResult]: List of filtering decisions.
                One result per input file, in same order.
        
        Raises:
            ValueError: If file_infos is None or contains invalid items
            FileNotFoundError: If any file does not exist
            PermissionError: If access to any file is denied
        
        Example:
            >>> filter = FileFilter(supported_extensions={".txt", ".md"})
            >>> results = filter.filter_files(file_list)
            >>> for file_info, result in zip(file_list, results):
            ...     if result.should_process:
            ...         print(f"Will process: {file_info.path}")
        """
        if file_infos is None:
            raise ValueError("file_infos cannot be None")
        
        if not isinstance(file_infos, list):
            raise ValueError("file_infos must be list")
        
        results = []
        for file_info in file_infos:
            try:
                result = self.filter_file(file_info)
                results.append(result)
            except Exception as e:
                # Handle case where file_info might not be a FileInfo instance
                file_path = getattr(file_info, 'file_path', str(file_info))
                logger.warning(f"Error filtering file {file_path}: {e}")
                # Create rejection result for failed files
                results.append(FileFilterResult(
                    should_process=False,
                    reason=f"Filtering error: {str(e)}",
                    filter_name="file_filter",
                    metadata={"error": str(e), "path": file_path}
                ))
        
        return results
    
    def _check_extension(self, file_info: FileInfo) -> FileFilterResult:
        """
        Check if file extension is supported.
        
        Internal method to check if the file's extension is in the
        supported extensions list.
        
        Args:
            file_info (FileInfo): File information to check.
                Must be valid FileInfo instance.
        
        Returns:
            FileFilterResult: Result of extension check.
                Should_process=True if extension is supported.
        
        Raises:
            ValueError: If file_info is None or invalid
        """
        if file_info is None:
            raise ValueError("file_info cannot be None")
        
        # If no extensions specified, all extensions are allowed
        if not self.supported_extensions:
            return FileFilterResult(
                should_process=True,
                reason="No extension restrictions",
                filter_name="extension_filter",
                metadata={"extension": file_info.extension}
            )
        
        # Check if file extension is supported
        if file_info.file_extension.lower() in {ext.lower().lstrip('.') for ext in self.supported_extensions}:
            return FileFilterResult(
                should_process=True,
                reason=f"Extension {file_info.file_extension} is supported",
                filter_name="extension_filter",
                metadata={"extension": file_info.file_extension}
            )
        else:
            return FileFilterResult(
                should_process=False,
                reason=f"Extension {file_info.file_extension} is not supported",
                filter_name="extension_filter",
                metadata={
                    "extension": file_info.file_extension,
                    "supported_extensions": list(self.supported_extensions)
                }
            )
    
    def _check_size(self, file_info: FileInfo) -> FileFilterResult:
        """
        Check if file size is within acceptable range.
        
        Internal method to check if the file's size is between
        min_file_size and max_file_size.
        
        Args:
            file_info (FileInfo): File information to check.
                Must be valid FileInfo instance.
        
        Returns:
            FileFilterResult: Result of size check.
                Should_process=True if size is acceptable.
        
        Raises:
            ValueError: If file_info is None or invalid
        """
        if file_info is None:
            raise ValueError("file_info cannot be None")
        
        file_size = file_info.file_size
        
        # Check minimum size
        if file_size < self.min_file_size:
            return FileFilterResult(
                should_process=False,
                reason=f"File size {file_size} is below minimum {self.min_file_size}",
                filter_name="size_filter",
                metadata={
                    "file_size": file_size,
                    "min_size": self.min_file_size,
                    "max_size": self.max_file_size
                }
            )
        
        # Check maximum size
        if file_size > self.max_file_size:
            return FileFilterResult(
                should_process=False,
                reason=f"File size {file_size} exceeds maximum {self.max_file_size}",
                filter_name="size_filter",
                metadata={
                    "file_size": file_size,
                    "min_size": self.min_file_size,
                    "max_size": self.max_file_size
                }
            )
        
        return FileFilterResult(
            should_process=True,
            reason=f"File size {file_size} is within acceptable range",
            filter_name="size_filter",
            metadata={
                "file_size": file_size,
                "min_size": self.min_file_size,
                "max_size": self.max_file_size
            }
        )
    
    def _check_patterns(self, file_info: FileInfo) -> FileFilterResult:
        """
        Check if file matches include/exclude patterns.
        
        Internal method to check if the file's path matches
        any include or exclude patterns.
        
        Args:
            file_info (FileInfo): File information to check.
                Must be valid FileInfo instance.
        
        Returns:
            FileFilterResult: Result of pattern check.
                Should_process=True if patterns allow processing.
        
        Raises:
            ValueError: If file_info is None or invalid
        """
        if file_info is None:
            raise ValueError("file_info cannot be None")
        
        file_path = file_info.file_path
        
        # Check exclude patterns first
        for pattern in self.exclude_patterns:
            if Path(file_path).match(pattern):
                return FileFilterResult(
                    should_process=False,
                    reason=f"File matches exclude pattern: {pattern}",
                    filter_name="pattern_filter",
                    metadata={
                        "file_path": file_path,
                        "matched_pattern": pattern,
                        "pattern_type": "exclude"
                    }
                )
        
        # Check include patterns (if any specified)
        if self.include_patterns:
            for pattern in self.include_patterns:
                if Path(file_path).match(pattern):
                    return FileFilterResult(
                        should_process=True,
                        reason=f"File matches include pattern: {pattern}",
                        filter_name="pattern_filter",
                        metadata={
                            "file_path": file_path,
                            "matched_pattern": pattern,
                            "pattern_type": "include"
                        }
                    )
            
            # No include patterns matched
            return FileFilterResult(
                should_process=False,
                reason="File does not match any include patterns",
                filter_name="pattern_filter",
                metadata={
                    "file_path": file_path,
                    "include_patterns": self.include_patterns
                }
            )
        
        # No patterns specified, allow processing
        return FileFilterResult(
            should_process=True,
            reason="No pattern restrictions",
            filter_name="pattern_filter",
            metadata={"file_path": file_path}
        )
    
    def get_supported_extensions(self) -> Set[str]:
        """
        Get the set of supported file extensions.
        
        Returns:
            Set[str]: Copy of the supported extensions set.
                Returns empty set if no restrictions.
        
        Example:
            >>> filter = FileFilter(supported_extensions={".txt", ".md"})
            >>> extensions = filter.get_supported_extensions()
            >>> print(extensions)  # {".txt", ".md"}
        """
        return self.supported_extensions.copy()
    
    def add_supported_extension(self, extension: str) -> None:
        """
        Add a supported file extension.
        
        Args:
            extension (str): Extension to add.
                Must be non-empty string, preferably with leading dot.
        
        Raises:
            ValueError: If extension is empty or invalid
            TypeError: If extension is not string
        
        Example:
            >>> filter = FileFilter()
            >>> filter.add_supported_extension(".py")
            >>> print(".py" in filter.get_supported_extensions())  # True
        """
        if not isinstance(extension, str):
            raise TypeError("extension must be string")
        
        if not extension:
            raise ValueError("extension cannot be empty")
        
        self.supported_extensions.add(extension)
    
    def remove_supported_extension(self, extension: str) -> None:
        """
        Remove a supported file extension.
        
        Args:
            extension (str): Extension to remove.
                Must be non-empty string.
        
        Raises:
            ValueError: If extension is empty
            TypeError: If extension is not string
        
        Example:
            >>> filter = FileFilter(supported_extensions={".txt", ".md"})
            >>> filter.remove_supported_extension(".txt")
            >>> print(".txt" in filter.get_supported_extensions())  # False
        """
        if not isinstance(extension, str):
            raise TypeError("extension must be string")
        
        if not extension:
            raise ValueError("extension cannot be empty")
        
        self.supported_extensions.discard(extension) 