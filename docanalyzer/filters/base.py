"""
Base classes for file filters and text block structures.

This module defines the core abstractions for parsing files into
structured text blocks that can be chunked and processed.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
import hashlib
from datetime import datetime, timezone

from chunk_metadata_adapter.data_types import ChunkType, LanguageEnum, BlockType


class BlockTypeExtended(str, Enum):
    """Extended block types for file parsing."""
    
    # Basic text blocks
    PARAGRAPH = "paragraph"
    HEADING = "heading"
    LIST_ITEM = "list_item"
    QUOTE = "quote"
    
    # Code blocks
    CODE_BLOCK = "code_block"
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    COMMENT = "comment"
    DOCSTRING = "docstring"
    
    # Document structure
    SECTION = "section"
    CHAPTER = "chapter"
    TITLE = "title"
    SUBTITLE = "subtitle"
    
    # Special blocks
    TABLE = "table"
    IMAGE = "image"
    LINK = "link"
    METADATA = "metadata"
    IMPORT = "import"
    VARIABLE = "variable"


@dataclass
class TextBlock:
    """
    Represents a structured text block extracted from a file.
    
    This is the fundamental unit that gets passed to the chunking system.
    Each block represents a semantically coherent piece of content.
    """
    
    # Content
    content: str
    block_type: BlockTypeExtended
    language: LanguageEnum = LanguageEnum.UNKNOWN
    
    # Position in file
    start_line: int = 0
    end_line: int = 0
    start_offset: int = 0
    end_offset: int = 0
    
    # Hierarchy and structure
    level: int = 0  # Nesting level (0 = top level)
    parent_id: Optional[str] = None
    block_id: str = field(default_factory=lambda: str(hash(datetime.now())))
    
    # Metadata
    title: Optional[str] = None  # For headings, functions, classes
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    # Quality metrics
    complexity_score: float = 0.0  # Code complexity, text readability
    importance_score: float = 0.5  # Relative importance (0-1)
    
    def __post_init__(self):
        """Generate block ID based on content and position."""
        if not self.block_id or self.block_id == str(hash(datetime.now())):
            content_hash = hashlib.md5(
                f"{self.content[:100]}{self.start_line}{self.start_offset}".encode()
            ).hexdigest()[:8]
            self.block_id = f"{self.block_type.value}_{content_hash}"
    
    @property
    def chunk_type(self) -> ChunkType:
        """Map block type to chunk type for metadata adapter."""
        if self.block_type in [BlockTypeExtended.CODE_BLOCK, BlockTypeExtended.FUNCTION, 
                              BlockTypeExtended.CLASS, BlockTypeExtended.METHOD]:
            return ChunkType.CODE_BLOCK
        elif self.block_type in [BlockTypeExtended.COMMENT, BlockTypeExtended.DOCSTRING]:
            return ChunkType.COMMENT
        else:
            return ChunkType.DOC_BLOCK
    
    @property
    def block_type_for_metadata(self) -> BlockType:
        """Map to standard BlockType for metadata."""
        mapping = {
            BlockTypeExtended.PARAGRAPH: BlockType.PARAGRAPH,
            BlockTypeExtended.HEADING: BlockType.HEADING,
            BlockTypeExtended.LIST_ITEM: BlockType.LIST,
            BlockTypeExtended.CODE_BLOCK: BlockType.CODE,
            BlockTypeExtended.FUNCTION: BlockType.CODE,
            BlockTypeExtended.CLASS: BlockType.CODE,
            BlockTypeExtended.METHOD: BlockType.CODE,
            BlockTypeExtended.TABLE: BlockType.TABLE,
            BlockTypeExtended.QUOTE: BlockType.QUOTE,
        }
        return mapping.get(self.block_type, BlockType.PARAGRAPH)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "content": self.content,
            "block_type": self.block_type.value,
            "language": self.language.value,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
            "level": self.level,
            "parent_id": self.parent_id,
            "block_id": self.block_id,
            "title": self.title,
            "metadata": self.metadata,
            "tags": self.tags,
            "complexity_score": self.complexity_score,
            "importance_score": self.importance_score
        }


@dataclass
class FileStructure:
    """
    Represents the complete structure of a parsed file.
    
    Contains all text blocks extracted from the file along with
    file-level metadata and processing information.
    """
    
    # File information
    file_path: Path
    file_size: int
    file_hash: str  # SHA256 of file content
    modified_at: datetime
    
    # Parsing results
    blocks: List[TextBlock] = field(default_factory=list)
    language: LanguageEnum = LanguageEnum.UNKNOWN
    encoding: str = "utf-8"
    
    # File metadata
    title: Optional[str] = None  # Extracted from file (e.g., # Title in markdown)
    description: Optional[str] = None
    author: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    # Processing metadata
    filter_name: str = ""
    filter_version: str = ""
    parsed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    processing_time: float = 0.0  # seconds
    
    # Statistics
    total_lines: int = 0
    total_characters: int = 0
    block_count: int = 0
    
    def __post_init__(self):
        """Update statistics after initialization."""
        self.block_count = len(self.blocks)
        self.total_characters = sum(len(block.content) for block in self.blocks)
    
    def get_blocks_by_type(self, block_type: BlockTypeExtended) -> List[TextBlock]:
        """Get all blocks of a specific type."""
        return [block for block in self.blocks if block.block_type == block_type]
    
    def get_blocks_by_level(self, level: int) -> List[TextBlock]:
        """Get all blocks at a specific nesting level."""
        return [block for block in self.blocks if block.level == level]
    
    def get_top_level_blocks(self) -> List[TextBlock]:
        """Get all top-level blocks (level 0)."""
        return self.get_blocks_by_level(0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "file_path": str(self.file_path),
            "file_size": self.file_size,
            "file_hash": self.file_hash,
            "modified_at": self.modified_at.isoformat(),
            "blocks": [block.to_dict() for block in self.blocks],
            "language": self.language.value,
            "encoding": self.encoding,
            "title": self.title,
            "description": self.description,
            "author": self.author,
            "tags": self.tags,
            "filter_name": self.filter_name,
            "filter_version": self.filter_version,
            "parsed_at": self.parsed_at.isoformat(),
            "processing_time": self.processing_time,
            "total_lines": self.total_lines,
            "total_characters": self.total_characters,
            "block_count": self.block_count
        }


class BaseFileFilter(ABC):
    """
    Abstract base class for file filters.
    
    Each filter is responsible for parsing a specific type of file
    and extracting structured text blocks that can be chunked.
    """
    
    # Filter metadata
    name: str = "base_filter"
    version: str = "1.0.0"
    supported_extensions: List[str] = []
    supported_mime_types: List[str] = []
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the filter with optional configuration.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.setup()
    
    def setup(self) -> None:
        """
        Setup method called after initialization.
        Override in subclasses for specific setup logic.
        """
        pass
    
    @abstractmethod
    def can_process(self, file_path: Path) -> bool:
        """
        Check if this filter can process the given file.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if this filter can process the file
        """
        pass
    
    @abstractmethod
    def parse(self, file_path: Path, content: Optional[str] = None) -> FileStructure:
        """
        Parse a file and extract structured text blocks.
        
        Args:
            file_path: Path to the file to parse
            content: Optional pre-loaded file content
            
        Returns:
            FileStructure containing all extracted blocks
        """
        pass
    
    def _load_file_content(self, file_path: Path) -> str:
        """
        Load file content with encoding detection.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File content as string
        """
        try:
            # Try UTF-8 first
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Fallback to other encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            
            # Last resort - read as binary and decode with errors='replace'
            with open(file_path, 'rb') as f:
                return f.read().decode('utf-8', errors='replace')
    
    def _calculate_file_hash(self, content: str) -> str:
        """Calculate SHA256 hash of file content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _detect_language(self, file_path: Path) -> LanguageEnum:
        """
        Detect language from file extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Detected language enum
        """
        extension = file_path.suffix.lower()
        
        language_map = {
            '.py': LanguageEnum.PYTHON,
            '.js': LanguageEnum.JAVASCRIPT,
            '.ts': LanguageEnum.TYPESCRIPT,
            '.md': LanguageEnum.MARKDOWN,
            '.txt': LanguageEnum.EN,
            '.rst': LanguageEnum.EN,
            '.java': LanguageEnum.JAVA,
            '.cpp': LanguageEnum.CPP,
            '.c': LanguageEnum.C,
            '.cs': LanguageEnum.CSHARP,
            '.go': LanguageEnum.GO,
            '.rs': LanguageEnum.RUST,
            '.php': LanguageEnum.PHP,
            '.rb': LanguageEnum.RUBY,
            '.html': LanguageEnum.HTML,
            '.css': LanguageEnum.CSS,
            '.json': LanguageEnum.JSON,
            '.xml': LanguageEnum.XML,
            '.yaml': LanguageEnum.YAML,
            '.yml': LanguageEnum.YAML,
        }
        
        return language_map.get(extension, LanguageEnum.UNKNOWN)
    
    def _create_file_structure(self, file_path: Path, content: str) -> FileStructure:
        """
        Create base FileStructure with file metadata.
        
        Args:
            file_path: Path to the file
            content: File content
            
        Returns:
            FileStructure with basic metadata filled
        """
        file_stat = file_path.stat()
        
        return FileStructure(
            file_path=file_path,
            file_size=file_stat.st_size,
            file_hash=self._calculate_file_hash(content),
            modified_at=datetime.fromtimestamp(file_stat.st_mtime, tz=timezone.utc),
            language=self._detect_language(file_path),
            total_lines=content.count('\n') + 1,
            total_characters=len(content),
            filter_name=self.name,
            filter_version=self.version
        ) 