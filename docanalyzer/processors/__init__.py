"""
Processors Package - File Processing Components

This package contains file processing components for extracting and processing
text blocks from various file types. It provides a unified interface for
processing different file formats with specialized processors for each type.

The package includes:
- Base processor interface and abstract classes
- Text file processor for .txt files
- Markdown processor for .md files
- Common processing utilities and helpers

Author: DocAnalyzer Team
Version: 1.0.0
"""

from .base_processor import BaseProcessor, ProcessorResult
from .text_processor import TextProcessor
from .markdown_processor import MarkdownProcessor

__all__ = [
    "BaseProcessor",
    "ProcessorResult", 
    "TextProcessor",
    "MarkdownProcessor"
]

__version__ = "1.0.0" 