"""
Filter Registry for automatic filter selection.

Manages registration and selection of appropriate filters for different file types.
"""

from pathlib import Path
from typing import Dict, List, Optional, Type
import logging

from .base import BaseFileFilter


class FilterRegistry:
    """
    Registry for managing file filters.
    
    Automatically selects the appropriate filter based on file type,
    extension, and content analysis.
    """
    
    def __init__(self):
        """Initialize the filter registry."""
        self._filters: Dict[str, Type[BaseFileFilter]] = {}
        self._extension_map: Dict[str, str] = {}
        self._mime_map: Dict[str, str] = {}
        self.logger = logging.getLogger("filter_registry")
        
        # Register built-in filters
        self._register_builtin_filters()
    
    def register(self, filter_class: Type[BaseFileFilter], name: Optional[str] = None) -> None:
        """
        Register a filter class.
        
        Args:
            filter_class: The filter class to register
            name: Optional name for the filter (defaults to filter_class.name)
        """
        filter_name = name or filter_class.name
        
        if filter_name in self._filters:
            self.logger.warning(f"Overriding existing filter: {filter_name}")
        
        self._filters[filter_name] = filter_class
        
        # Update extension and mime type mappings
        filter_instance = filter_class()
        
        for ext in filter_instance.supported_extensions:
            self._extension_map[ext.lower()] = filter_name
        
        for mime in filter_instance.supported_mime_types:
            self._mime_map[mime.lower()] = filter_name
        
        self.logger.info(f"Registered filter: {filter_name}")
    
    def get_filter(self, file_path: Path, mime_type: Optional[str] = None) -> Optional[BaseFileFilter]:
        """
        Get the appropriate filter for a file.
        
        Args:
            file_path: Path to the file
            mime_type: Optional MIME type hint
            
        Returns:
            Appropriate filter instance or None if no suitable filter found
        """
        # Try MIME type first if provided
        if mime_type:
            filter_name = self._mime_map.get(mime_type.lower())
            if filter_name and filter_name in self._filters:
                return self._filters[filter_name]()
        
        # Try file extension
        extension = file_path.suffix.lower()
        filter_name = self._extension_map.get(extension)
        
        if filter_name and filter_name in self._filters:
            filter_instance = self._filters[filter_name]()
            
            # Double-check with can_process method
            if filter_instance.can_process(file_path):
                return filter_instance
        
        # Try all registered filters
        for filter_class in self._filters.values():
            filter_instance = filter_class()
            if filter_instance.can_process(file_path):
                return filter_instance
        
        self.logger.warning(f"No suitable filter found for: {file_path}")
        return None
    
    def get_filter_by_name(self, name: str) -> Optional[BaseFileFilter]:
        """
        Get a filter by name.
        
        Args:
            name: Name of the filter
            
        Returns:
            Filter instance or None if not found
        """
        if name in self._filters:
            return self._filters[name]()
        return None
    
    def list_filters(self) -> List[str]:
        """
        Get list of all registered filter names.
        
        Returns:
            List of filter names
        """
        return list(self._filters.keys())
    
    def get_supported_extensions(self) -> List[str]:
        """
        Get list of all supported file extensions.
        
        Returns:
            List of supported extensions
        """
        return list(self._extension_map.keys())
    
    def get_supported_mime_types(self) -> List[str]:
        """
        Get list of all supported MIME types.
        
        Returns:
            List of supported MIME types
        """
        return list(self._mime_map.keys())
    
    def _register_builtin_filters(self) -> None:
        """Register built-in filters."""
        try:
            from .text_filter import TextFileFilter
            self.register(TextFileFilter)
        except ImportError:
            self.logger.warning("TextFileFilter not available")
        
        try:
            from .markdown_filter import MarkdownFileFilter
            self.register(MarkdownFileFilter)
        except ImportError:
            self.logger.warning("MarkdownFileFilter not available")
        
        try:
            from .python_filter import PythonFileFilter
            self.register(PythonFileFilter)
        except ImportError:
            self.logger.warning("PythonFileFilter not available")
        
        try:
            from .javascript_filter import JavaScriptFileFilter
            self.register(JavaScriptFileFilter)
        except ImportError:
            self.logger.warning("JavaScriptFileFilter not available")
    
    def __str__(self) -> str:
        """String representation of the registry."""
        return f"FilterRegistry({len(self._filters)} filters registered)"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"FilterRegistry("
            f"filters={list(self._filters.keys())}, "
            f"extensions={len(self._extension_map)}, "
            f"mime_types={len(self._mime_map)}"
            f")"
        ) 