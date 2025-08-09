"""
DocAnalyzer - Document Analysis and Chunking System.

A comprehensive system for monitoring file systems, parsing documents,
and creating semantic chunks for vector storage.
"""

__version__ = "1.0.0"
__author__ = "Vasily Zdanovskiy"
__email__ = "vasilyvz@gmail.com"

from .filters.base import BaseFileFilter, TextBlock, FileStructure
from .filters.registry import FilterRegistry

__all__ = [
    "BaseFileFilter",
    "TextBlock", 
    "FileStructure",
    "FilterRegistry",
    "__version__",
    "__author__",
    "__email__"
] 