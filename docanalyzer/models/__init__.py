"""
Models Package - Core Domain Models

This package contains all core domain models for the DocAnalyzer system
including file system models, processing models, database models, and error models.

Author: DocAnalyzer Team
Version: 1.0.0
"""

# File System Models
from .file_system import FileInfo, Directory, LockFile

# Processing Models
from .processing import ProcessingStatus, ProcessingBlock, FileProcessingResult, ProcessingResult

# Database Models
from .database import RecordStatus, DatabaseFileRecord, ProcessingStatistics

# Error Models
from .errors import ErrorSeverity, ErrorCategory, ProcessingError, ErrorHandler

# Semantic Chunk Models
from .semantic_chunk import ChunkStatus, SemanticChunk

__all__ = [
    # File System Models
    "FileInfo",
    "Directory", 
    "LockFile",
    
    # Processing Models
    "ProcessingStatus",
    "ProcessingBlock",
    "FileProcessingResult",
    "ProcessingResult",
    
    # Database Models
    "RecordStatus",
    "DatabaseFileRecord",
    "ProcessingStatistics",
    
    # Error Models
    "ErrorSeverity",
    "ErrorCategory",
    "ProcessingError",
    "ErrorHandler",
    
    # Semantic Chunk Models
    "ChunkStatus",
    "SemanticChunk",
] 