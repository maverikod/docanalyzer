"""
File Filters Module.

Contains base classes and implementations for parsing different file types
into structured text blocks for chunking and processing.
"""

from .base import BaseFileFilter, TextBlock, FileStructure
from .registry import FilterRegistry
from .text_filter import TextFileFilter
from .markdown_filter import MarkdownFileFilter  
from .python_filter import PythonFileFilter
from .javascript_filter import JavaScriptFileFilter

__all__ = [
    "BaseFileFilter",
    "TextBlock",
    "FileStructure", 
    "FilterRegistry",
    "TextFileFilter",
    "MarkdownFileFilter",
    "PythonFileFilter",
    "JavaScriptFileFilter"
] 