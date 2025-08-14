"""
Semantic Chunk Model - Unified Data Model for Text Chunks

This module defines the unified SemanticChunk model that serves as the
primary data structure for representing processed text chunks with metadata
throughout the DocAnalyzer system.

The SemanticChunk model provides a consistent interface for chunk data
across all components including chunking, vector storage, and processing
pipeline operations.

Author: DocAnalyzer Team
Version: 1.0.0
"""

import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from docanalyzer.models.errors import ValidationError

# Standard metadata keys for semantic chunks
METADATA_KEYS = {
    # Block information
    "block_index": "Index of the block in the source file",
    "block_type": "Type of the block (paragraph, section, code, etc.)",
    "start_line": "Starting line number in the source file",
    "end_line": "Ending line number in the source file", 
    "start_char": "Starting character position in the source file",
    "end_char": "Ending character position in the source file",
    
    # Semantic information
    "semantic_type": "Semantic type of the content (text, code, header, etc.)",
    "language": "Programming language or content language",
    "complexity": "Complexity level of the content",
    "keywords": "Extracted keywords from the content",
    
    # Processing information
    "processing_timestamp": "Timestamp when the chunk was processed",
    "processor_version": "Version of the processor that created this chunk",
    "processing_metadata": "Additional processing-specific metadata"
}


class ChunkStatus(str, Enum):
    """
    Chunk Status Enumeration
    
    Defines the possible processing states for a semantic chunk.
    
    Attributes:
        NEW: Chunk has been created but not yet processed
        PROCESSED: Chunk has been successfully processed and stored
        ERROR: Chunk processing failed with an error
        PENDING: Chunk is queued for processing
        DELETED: Chunk has been marked for deletion
    """
    NEW = "NEW"
    PROCESSED = "PROCESSED"
    ERROR = "ERROR"
    PENDING = "PENDING"
    DELETED = "DELETED"


@dataclass
class SemanticChunk:
    """
    Semantic Chunk - Unified Data Model for Text Chunks
    
    Represents a single semantic unit extracted from a file with comprehensive
    metadata for vector storage, retrieval, and processing operations.
    
    This model serves as the primary data structure for chunk operations
    across all DocAnalyzer components, providing a consistent interface
    for chunk creation, validation, serialization, and transformation.
    
    Attributes:
        uuid (str): Unique identifier for the chunk (auto-generated UUID4).
            Used for tracking and referencing chunks across the system.
        source_path (str): Absolute path to the source file.
            Must be a valid file path string.
        source_id (str): UUID4 identifier for the source file.
            Must be a valid UUID4 string for consistency.
        content (str): Text content of the chunk.
            Must be non-empty string containing the extracted text.
        status (ChunkStatus): Current processing status of the chunk.
            Defaults to ChunkStatus.NEW.
        metadata (Dict[str, Any]): Additional metadata for the chunk.
            Can include semantic information, processing details, etc.
        created_at (datetime): Timestamp when chunk was created.
            Auto-generated during instantiation.
        updated_at (datetime): Timestamp when chunk was last updated.
            Auto-updated on modifications.
        chunk_type (Optional[str]): Type of the chunk (e.g., "text", "code").
            Optional classification for different content types.
        language (Optional[str]): Programming language or content language.
            Optional language identifier for code or text content.
        embedding_id (Optional[str]): ID of the associated embedding.
            Optional reference to vector embedding in storage.
        processing_metadata (Optional[Dict[str, Any]]): Processing-specific metadata.
            Optional metadata related to chunk processing operations.
    
    Example:
        >>> chunk = SemanticChunk(
        ...     source_path="/path/to/file.txt",
        ...     source_id="550e8400-e29b-41d4-a716-446655440000",
        ...     content="This is the chunk content",
        ...     metadata={"semantic_type": "paragraph", "position": 1}
        ... )
        >>> print(chunk.uuid)  # Auto-generated UUID4
        >>> print(chunk.status)  # ChunkStatus.NEW
    """
    
    source_path: str
    source_id: str
    content: str
    status: ChunkStatus = ChunkStatus.NEW
    metadata: Dict[str, Any] = field(default_factory=dict)
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    chunk_type: Optional[str] = None
    language: Optional[str] = None
    embedding_id: Optional[str] = None
    processing_metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """
        Post-initialization validation and setup.
        
        Performs validation of required fields and sets up default values.
        Ensures data integrity and consistency of the chunk instance.
        
        Raises:
            ValidationError: If required fields are invalid or missing
        """
        self._validate_fields()
        self._normalize_fields()
    
    def _validate_fields(self) -> None:
        """
        Validate all fields of the SemanticChunk instance.
        
        Performs comprehensive validation of all fields including
        required field presence, data type validation, and format
        validation for specialized fields like UUIDs.
        
        Raises:
            ValidationError: If any field validation fails
        """
        # Validate source_path
        if not self.source_path or not self.source_path.strip():
            raise ValidationError("source_path cannot be empty")
        
        # Validate source_id (must be valid UUID4)
        if not self.source_id or not self.source_id.strip():
            raise ValidationError("source_id cannot be empty")
        
        try:
            uuid.UUID(self.source_id.strip(), version=4)
        except ValueError:
            raise ValidationError("source_id must be a valid UUID4 string")
        
        # Validate content
        if not self.content or not self.content.strip():
            raise ValidationError("content cannot be empty")
        
        # Validate status (must be valid ChunkStatus enum)
        if not isinstance(self.status, ChunkStatus):
            raise ValidationError("Invalid status value")
        
        # Validate uuid (must be valid UUID4)
        try:
            uuid.UUID(self.uuid, version=4)
        except ValueError:
            raise ValidationError("uuid must be a valid UUID4 string")
        
        # Validate timestamps
        if not isinstance(self.created_at, datetime):
            raise ValidationError("created_at must be a datetime instance")
        
        if not isinstance(self.updated_at, datetime):
            raise ValidationError("updated_at must be a datetime instance")
    
    def _normalize_fields(self) -> None:
        """
        Normalize field values for consistency.
        
        Trims whitespace from string fields and ensures consistent
        formatting across all text-based fields.
        """
        self.source_path = self.source_path.strip()
        self.source_id = self.source_id.strip()
        self.content = self.content.strip()
        
        if self.chunk_type:
            self.chunk_type = self.chunk_type.strip()
        
        if self.language:
            self.language = self.language.strip()
        
        if self.embedding_id:
            self.embedding_id = self.embedding_id.strip()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert chunk to dictionary representation.
        
        Serializes the SemanticChunk instance to a dictionary format
        suitable for JSON serialization, database storage, or API
        communication.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the chunk.
                Format: {
                    "uuid": str,
                    "source_path": str,
                    "source_id": str,
                    "content": str,
                    "status": str,
                    "metadata": Dict[str, Any],
                    "created_at": str,
                    "updated_at": str,
                    "chunk_type": Optional[str],
                    "language": Optional[str],
                    "embedding_id": Optional[str],
                    "processing_metadata": Optional[Dict[str, Any]]
                }
        
        Example:
            >>> chunk_dict = chunk.to_dict()
            >>> print(chunk_dict["uuid"])  # UUID4 string
            >>> print(chunk_dict["status"])  # "NEW"
        """
        return {
            "uuid": self.uuid,
            "source_path": self.source_path,
            "source_id": self.source_id,
            "content": self.content,
            "status": self.status.value,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "chunk_type": self.chunk_type,
            "language": self.language,
            "embedding_id": self.embedding_id,
            "processing_metadata": self.processing_metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SemanticChunk':
        """
        Create SemanticChunk from dictionary representation.
        
        Deserializes a dictionary back to a SemanticChunk instance,
        performing validation and type conversion as needed.
        
        Args:
            data (Dict[str, Any]): Dictionary with chunk data.
                Must contain required fields: source_path, source_id, content.
                Optional fields: status, metadata, uuid, created_at, updated_at,
                chunk_type, language, embedding_id, processing_metadata.
        
        Returns:
            SemanticChunk: New chunk instance with validated data.
        
        Raises:
            ValidationError: If required fields are missing or invalid
            ValueError: If data types cannot be converted properly
        
        Example:
            >>> data = {
            ...     "source_path": "/path/to/file.txt",
            ...     "source_id": "550e8400-e29b-41d4-a716-446655440000",
            ...     "content": "Chunk content",
            ...     "status": "NEW"
            ... }
            >>> chunk = SemanticChunk.from_dict(data)
        """
        # Extract required fields
        required_fields = ["source_path", "source_id", "content"]
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")
        
        # Extract optional fields with defaults
        status_str = data.get("status", "NEW")
        try:
            status = ChunkStatus(status_str)
        except ValueError:
            raise ValidationError(f"Invalid status value: {status_str}")
        
        # Parse timestamps if provided
        created_at = datetime.now()
        if "created_at" in data:
            try:
                created_at = datetime.fromisoformat(data["created_at"])
            except ValueError:
                raise ValidationError(f"Invalid created_at format: {data['created_at']}")
        
        updated_at = datetime.now()
        if "updated_at" in data:
            try:
                updated_at = datetime.fromisoformat(data["updated_at"])
            except ValueError:
                raise ValidationError(f"Invalid updated_at format: {data['updated_at']}")
        
        return cls(
            source_path=data["source_path"],
            source_id=data["source_id"],
            content=data["content"],
            status=status,
            metadata=data.get("metadata", {}),
            uuid=data.get("uuid", str(uuid.uuid4())),
            created_at=created_at,
            updated_at=updated_at,
            chunk_type=data.get("chunk_type"),
            language=data.get("language"),
            embedding_id=data.get("embedding_id"),
            processing_metadata=data.get("processing_metadata")
        )
    
    def update_status(self, new_status: ChunkStatus) -> None:
        """
        Update the chunk status and timestamp.
        
        Updates the status field and automatically updates the updated_at
        timestamp to reflect the modification time.
        
        Args:
            new_status (ChunkStatus): New status to set.
                Must be a valid ChunkStatus enum value.
        
        Raises:
            ValidationError: If new_status is not a valid ChunkStatus
        
        Example:
            >>> chunk.update_status(ChunkStatus.PROCESSED)
            >>> print(chunk.status)  # ChunkStatus.PROCESSED
        """
        if not isinstance(new_status, ChunkStatus):
            raise ValidationError("new_status must be a ChunkStatus enum value")
        
        self.status = new_status
        self.updated_at = datetime.now()
    
    def add_metadata(self, key: str, value: Any) -> None:
        """
        Add or update metadata key-value pair.
        
        Adds a new metadata entry or updates an existing one,
        automatically updating the updated_at timestamp.
        
        Args:
            key (str): Metadata key. Must be non-empty string.
            value (Any): Metadata value. Can be any serializable type.
        
        Raises:
            ValidationError: If key is empty or invalid
        
        Example:
            >>> chunk.add_metadata("semantic_type", "paragraph")
            >>> chunk.add_metadata("position", 1)
            >>> print(chunk.metadata["semantic_type"])  # "paragraph"
        """
        if not key or not key.strip():
            raise ValidationError("metadata key cannot be empty")
        
        self.metadata[key.strip()] = value
        self.updated_at = datetime.now()
    
    def remove_metadata(self, key: str) -> bool:
        """
        Remove metadata key-value pair.
        
        Removes a metadata entry if it exists, automatically updating
        the updated_at timestamp.
        
        Args:
            key (str): Metadata key to remove. Must be non-empty string.
        
        Returns:
            bool: True if key was removed, False if key didn't exist.
        
        Raises:
            ValidationError: If key is empty or invalid
        
        Example:
            >>> chunk.remove_metadata("semantic_type")
            >>> print("semantic_type" in chunk.metadata)  # False
        """
        if not key or not key.strip():
            raise ValidationError("metadata key cannot be empty")
        
        key = key.strip()
        if key in self.metadata:
            del self.metadata[key]
            self.updated_at = datetime.now()
            return True
        return False
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get metadata value by key.
        
        Retrieves a metadata value by its key, returning a default
        value if the key doesn't exist.
        
        Args:
            key (str): Metadata key to retrieve. Must be non-empty string.
            default (Any, optional): Default value if key doesn't exist.
                Defaults to None.
        
        Returns:
            Any: Metadata value or default if key doesn't exist.
        
        Raises:
            ValidationError: If key is empty or invalid
        
        Example:
            >>> value = chunk.get_metadata("semantic_type", "unknown")
            >>> print(value)  # "paragraph" or "unknown"
        """
        if not key or not key.strip():
            raise ValidationError("metadata key cannot be empty")
        
        return self.metadata.get(key.strip(), default)
    
    def has_metadata(self, key: str) -> bool:
        """
        Check if metadata key exists.
        
        Checks whether a specific metadata key exists in the chunk.
        
        Args:
            key (str): Metadata key to check. Must be non-empty string.
        
        Returns:
            bool: True if key exists, False otherwise.
        
        Raises:
            ValidationError: If key is empty or invalid
        
        Example:
            >>> if chunk.has_metadata("semantic_type"):
            ...     print("Has semantic type metadata")
        """
        if not key or not key.strip():
            raise ValidationError("metadata key cannot be empty")
        
        return key.strip() in self.metadata
    
    def __str__(self) -> str:
        """
        String representation of the chunk.
        
        Returns:
            str: Human-readable string representation.
        """
        return f"SemanticChunk(uuid={self.uuid}, source={self.source_path}, status={self.status.value})"
    
    def __repr__(self) -> str:
        """
        Detailed string representation for debugging.
        
        Returns:
            str: Detailed representation including all fields.
        """
        return (f"SemanticChunk(uuid='{self.uuid}', source_path='{self.source_path}', "
                f"source_id='{self.source_id}', status={self.status.value}, "
                f"content_length={len(self.content)}, metadata_keys={list(self.metadata.keys())})")
    
    def __eq__(self, other: Any) -> bool:
        """
        Equality comparison with another SemanticChunk.
        
        Two chunks are considered equal if they have the same UUID.
        
        Args:
            other (Any): Object to compare with.
        
        Returns:
            bool: True if chunks have the same UUID, False otherwise.
        """
        if not isinstance(other, SemanticChunk):
            return False
        return self.uuid == other.uuid
    
    def __hash__(self) -> int:
        """
        Hash value based on UUID.
        
        Returns:
            int: Hash value for the chunk.
        """
        return hash(self.uuid) 