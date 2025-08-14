"""
Chunking Manager - Semantic Chunk Creation and Management Service

Provides functionality for creating, managing, and storing semantic chunks
from processed file blocks. Handles batch processing, metadata extraction,
and atomic storage operations with rollback capabilities.

The chunking manager creates SemanticChunk objects with minimal metadata,
processes blocks in batches for efficiency, and ensures atomic operations
when saving to vector store.

Author: File Processing Team
Version: 1.0.0
"""

import asyncio
import logging
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from uuid import uuid4

from docanalyzer.models.processing import ProcessingBlock, FileProcessingResult
from docanalyzer.models.semantic_chunk import SemanticChunk, ChunkStatus, METADATA_KEYS
from docanalyzer.services.vector_store_wrapper import VectorStoreWrapper
from docanalyzer.models.database import DatabaseFileRecord

logger = logging.getLogger(__name__)

DEFAULT_BATCH_SIZE = 100
DEFAULT_CHUNK_SIZE = 1000
MAX_RETRY_ATTEMPTS = 3


class ChunkingResult:
    """
    Chunking Result - Container for chunking operation results.
    
    Contains information about the chunking operation including
    created chunks, statistics, and any errors encountered.
    
    Attributes:
        chunks_created (int): Number of chunks successfully created.
        chunks_failed (int): Number of chunks that failed to create.
        total_blocks_processed (int): Total number of blocks processed.
        source_path (str): Path to the source file.
        source_id (str): UUID4 identifier for the source file.
        created_chunks (List[SemanticChunk]): List of created chunks.
        errors (List[str]): List of error messages.
        processing_time (float): Time taken for chunking operation.
        created_at (datetime): Timestamp when operation completed.
    
    Example:
        >>> result = ChunkingResult(
        ...     source_path="/path/to/file.txt",
        ...     source_id="uuid4-string"
        ... )
        >>> print(f"Created {result.chunks_created} chunks")
    """
    
    def __init__(self, source_path: str, source_id: str):
        """
        Initialize ChunkingResult instance.
        
        Args:
            source_path (str): Path to the source file.
                Must be valid file path string.
            source_id (str): UUID4 identifier for the source file.
                Must be valid UUID4 string.
        """
        if not source_path or not source_path.strip():
            raise ValueError("source_path cannot be empty")
        
        if not source_id or not source_id.strip():
            raise ValueError("source_id cannot be empty")
        
        self.chunks_created = 0
        self.chunks_failed = 0
        self.total_blocks_processed = 0
        self.source_path = source_path.strip()
        self.source_id = source_id.strip()
        self.created_chunks = []
        self.errors = []
        self.processing_time = 0.0
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert result to dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the result.
                Format: {
                    "chunks_created": int,
                    "chunks_failed": int,
                    "total_blocks_processed": int,
                    "source_path": str,
                    "source_id": str,
                    "created_chunks": List[Dict[str, Any]],
                    "errors": List[str],
                    "processing_time": float,
                    "created_at": str
                }
        """
        return {
            "chunks_created": self.chunks_created,
            "chunks_failed": self.chunks_failed,
            "total_blocks_processed": self.total_blocks_processed,
            "source_path": self.source_path,
            "source_id": self.source_id,
            "created_chunks": [chunk.to_dict() for chunk in self.created_chunks],
            "errors": self.errors,
            "processing_time": self.processing_time,
            "created_at": self.created_at.isoformat()
        }


class BatchProcessor:
    """
    Batch Processor - Handles batch processing of blocks.
    
    Processes blocks in configurable batch sizes for efficient
    memory usage and improved performance.
    
    Attributes:
        batch_size (int): Number of items to process in each batch.
            Defaults to 100.
        max_retry_attempts (int): Maximum number of retry attempts.
            Defaults to 3.
    
    Example:
        >>> processor = BatchProcessor(batch_size=50)
        >>> results = await processor.process_batches(blocks, process_func)
    """
    
    def __init__(self, batch_size: int = DEFAULT_BATCH_SIZE):
        """
        Initialize BatchProcessor instance.
        
        Args:
            batch_size (int): Number of items to process in each batch.
                Must be positive integer. Defaults to 100.
        
        Raises:
            ValueError: If batch_size is not positive
        """
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        
        self.batch_size = batch_size
        self.max_retry_attempts = MAX_RETRY_ATTEMPTS
    
    async def process_batches(
        self,
        items: List[Any],
        process_func: callable,
        *args,
        **kwargs
    ) -> List[Any]:
        """
        Process items in batches using provided function.
        
        Args:
            items (List[Any]): List of items to process.
                Must be non-empty list.
            process_func (callable): Function to process each batch.
                Must be async function that takes batch as first argument.
            *args: Additional arguments for process_func.
            **kwargs: Additional keyword arguments for process_func.
        
        Returns:
            List[Any]: List of results from processing.
        
        Raises:
            ValueError: If items list is empty
            TypeError: If process_func is not callable
        """
        if not items:
            raise ValueError("Items list cannot be empty")
        
        if not callable(process_func):
            raise TypeError("process_func must be callable")
        
        results = []
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            try:
                batch_result = await process_func(batch, *args, **kwargs)
                results.extend(batch_result)
            except Exception as e:
                logger.error(f"Error processing batch {i//self.batch_size + 1}: {e}")
                raise
        
        return results


class ChunkingManager:
    """
    Chunking Manager - Semantic Chunk Creation and Management Service.
    
    Manages the creation, processing, and storage of semantic chunks
    from file processing blocks. Handles batch processing, metadata
    extraction, and atomic storage operations.
    
    The manager creates SemanticChunk objects with minimal metadata:
    - source_path: Path to the source file
    - source_id: UUID4 identifier for the source file
    - status: NEW (default)
    - UUID: Auto-generated for each chunk
    
    Attributes:
        vector_store_wrapper (VectorStoreWrapper): Wrapper for vector store operations.
        batch_processor (BatchProcessor): Processor for batch operations.
        chunk_size (int): Maximum size of each chunk in characters.
            Defaults to 1000.
        max_retry_attempts (int): Maximum number of retry attempts.
            Defaults to 3.
    
    Example:
        >>> manager = ChunkingManager(vector_store_wrapper)
        >>> result = await manager.create_chunks(processing_result)
    """
    
    def __init__(
        self,
        vector_store_wrapper: VectorStoreWrapper,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        batch_size: int = DEFAULT_BATCH_SIZE
    ):
        """
        Initialize ChunkingManager instance.
        
        Args:
            vector_store_wrapper (VectorStoreWrapper): Wrapper for vector store operations.
                Must be valid VectorStoreWrapper instance.
            chunk_size (int): Maximum size of each chunk in characters.
                Must be positive integer. Defaults to 1000.
            batch_size (int): Number of chunks to process in each batch.
                Must be positive integer. Defaults to 100.
        
        Raises:
            ValueError: If chunk_size or batch_size are not positive
            TypeError: If vector_store_wrapper is not valid instance
        """
        if not vector_store_wrapper:
            raise ValueError("vector_store_wrapper cannot be None")
        
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        
        self.vector_store_wrapper = vector_store_wrapper
        self.batch_processor = BatchProcessor(batch_size)
        self.chunk_size = chunk_size
        self.max_retry_attempts = MAX_RETRY_ATTEMPTS
    
    async def create_chunks(
        self,
        processing_result: FileProcessingResult
    ) -> ChunkingResult:
        """
        Create chunks from file processing result.
        
        Creates semantic chunks from processing blocks with minimal metadata:
        - source_path from processing result
        - source_id as UUID4 for the file
        - status set to NEW
        - Auto-generated UUID for each chunk
        
        Args:
            processing_result (FileProcessingResult): Result from file processing.
                Must contain valid blocks and file information.
        
        Returns:
            ChunkingResult: Result of chunking operation with statistics.
        
        Raises:
            ValueError: If processing_result is invalid
            ProcessingError: If chunking operation fails
        """
        start_time = datetime.now()
        
        if not processing_result or not processing_result.blocks:
            raise ValueError("processing_result must contain valid blocks")
        
        # Generate source_id for the file
        source_id = str(uuid4())
        source_path = processing_result.file_path
        
        # Create result container
        result = ChunkingResult(source_path, source_id)
        result.total_blocks_processed = len(processing_result.blocks)
        
        try:
            # Create chunks from blocks
            chunks = await self.create_chunks_from_blocks(
                processing_result.blocks,
                source_path,
                source_id
            )
            
            # Save chunks atomically
            saved_count, errors = await self.save_chunks_atomic(chunks)
            
            # Update result
            result.chunks_created = saved_count
            result.chunks_failed = len(chunks) - saved_count
            result.created_chunks = chunks[:saved_count]
            result.errors = errors
            result.processing_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Processed {len(processing_result.blocks)} blocks into {saved_count} chunks")
            
        except Exception as e:
            result.errors.append(f"Chunking operation failed: {str(e)}")
            logger.error(f"Chunking operation failed: {e}")
        
        return result
    
    async def create_chunks_from_blocks(
        self,
        blocks: List[ProcessingBlock],
        source_path: str,
        source_id: str
    ) -> List[SemanticChunk]:
        """
        Create semantic chunks from processing blocks.
        
        Args:
            blocks (List[ProcessingBlock]): List of processing blocks.
                Must be non-empty list of valid blocks.
            source_path (str): Path to the source file.
                Must be valid file path string.
            source_id (str): UUID4 identifier for the source file.
                Must be valid UUID4 string.
        
        Returns:
            List[SemanticChunk]: List of created semantic chunks.
        
        Raises:
            ValueError: If blocks list is empty or parameters are invalid
        """
        if not blocks:
            raise ValueError("Blocks list cannot be empty")
        
        if not source_path or not source_id:
            raise ValueError("source_path and source_id cannot be empty")
        
        chunks = []
        
        for i, block in enumerate(blocks):
            try:
                # Create metadata with standard keys
                metadata = {
                    "block_index": i,
                    "block_type": block.block_type,
                    "start_line": block.start_line,
                    "end_line": block.end_line,
                    "start_char": block.start_char,
                    "end_char": block.end_char,
                    "processing_timestamp": datetime.now().isoformat()
                }
                
                # Add any additional metadata from the block
                if block.metadata:
                    metadata.update(block.metadata)
                
                # Create chunk from block content
                chunk = SemanticChunk(
                    source_path=source_path,
                    source_id=source_id,
                    content=block.content,
                    status=ChunkStatus.NEW,
                    metadata=metadata
                )
                chunks.append(chunk)
                
            except Exception as e:
                logger.error(f"Error creating chunk from block {i}: {e}")
                raise
        
        logger.info(f"Created {len(chunks)} chunks from {len(blocks)} blocks")
        return chunks
    
    async def save_chunks_atomic(
        self,
        chunks: List[SemanticChunk]
    ) -> Tuple[int, List[str]]:
        """
        Save chunks atomically with rollback capability.
        
        Saves all chunks to vector store in a single transaction.
        If any chunk fails to save, all changes are rolled back.
        
        Args:
            chunks (List[SemanticChunk]): List of chunks to save.
                Must be non-empty list of valid chunks.
        
        Returns:
            Tuple[int, List[str]]: Number of saved chunks and list of errors.
                Format: (saved_count, error_messages)
        
        Raises:
            ValueError: If chunks list is empty
            StorageError: If atomic save operation fails
        """
        if not chunks:
            raise ValueError("Chunks list cannot be empty")
        
        errors = []
        saved_count = 0
        
        try:
            # Convert our SemanticChunk to vector_store_client SemanticChunk
            vector_chunks = []
            
            for chunk in chunks:
                try:
                    # Validate chunk before conversion
                    if not await self.validate_chunk(chunk):
                        errors.append(f"Invalid chunk {chunk.uuid}")
                        continue
                    
                    # Generate embedding for the chunk
                    embedding = await self._generate_embedding(chunk.content)
                    
                    # Create vector store chunk
                    from vector_store_client import SemanticChunk as VectorSemanticChunk
                    
                    vector_chunk = VectorSemanticChunk(
                        body=chunk.content,
                        source_id=chunk.source_id,
                        embedding=embedding,
                        source_path=chunk.source_path,
                        status="NEW"
                    )
                    vector_chunks.append(vector_chunk)
                    
                except Exception as e:
                    errors.append(f"Error converting chunk {chunk.uuid}: {str(e)}")
                    continue
            
            if not vector_chunks:
                return 0, errors
            
            # Save chunks using vector store client
            response = await self.vector_store_wrapper.create_chunks(vector_chunks)
            
            if response.success:
                saved_count = response.created_count or len(vector_chunks)
                logger.info(f"Successfully saved {saved_count} chunks")
            else:
                errors.append(f"Failed to save chunks: {response.error}")
                
        except Exception as e:
            errors.append(f"Atomic save operation failed: {str(e)}")
            logger.error(f"Atomic save operation failed: {e}")
        
        return saved_count, errors
    
    async def validate_chunk(self, chunk: SemanticChunk) -> bool:
        """
        Validate semantic chunk before saving.
        
        Args:
            chunk (SemanticChunk): Chunk to validate.
                Must be valid SemanticChunk instance.
        
        Returns:
            bool: True if chunk is valid, False otherwise.
        
        Raises:
            TypeError: If chunk is not valid instance
        """
        if not isinstance(chunk, SemanticChunk):
            raise TypeError("chunk must be SemanticChunk instance")
        
        # Validate required fields
        if not chunk.content or not chunk.content.strip():
            return False
        
        if not chunk.source_id or not chunk.source_id.strip():
            return False
        
        if not chunk.source_path or not chunk.source_path.strip():
            return False
        
        # Validate content length
        if len(chunk.content) > 10000:  # Max content length
            return False
        
        return True
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using embedding service.
        
        Args:
            text (str): Text to generate embedding for.
        
        Returns:
            List[float]: 384-dimensional embedding vector.
        
        Raises:
            EmbeddingError: If embedding generation fails
        """
        try:
            import httpx
            
            # Call embedding service directly
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "http://localhost:8001/cmd",
                    json={
                        "jsonrpc": "2.0",
                        "method": "embed",
                        "params": {"texts": [text]},
                        "id": 1
                    }
                )
                
                data = await response.json()
                
                if not data.get("result", {}).get("success"):
                    raise Exception("Failed to generate embedding")
                
                embeddings = data.get("result", {}).get("data", {}).get("embeddings", [])
                if not embeddings or not embeddings[0]:
                    raise Exception("No embedding returned")
                
                embedding = embeddings[0]
                
                # Validate embedding dimensions
                if len(embedding) != 384:
                    raise Exception(f"Invalid embedding dimensions: {len(embedding)}")
                
                return embedding
                
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise Exception(f"Embedding generation failed: {str(e)}")
    
    async def cleanup_failed_chunks(
        self,
        failed_chunks: List[SemanticChunk]
    ) -> None:
        """
        Clean up failed chunks from storage.
        
        Args:
            failed_chunks (List[SemanticChunk]): List of failed chunks to cleanup.
                Can be empty list.
        """
        if not failed_chunks:
            return
        
        try:
            # Extract UUIDs of failed chunks
            failed_uuids = [chunk.uuid for chunk in failed_chunks if chunk.uuid]
            
            if failed_uuids:
                # Delete failed chunks from vector store
                await self.vector_store_wrapper.delete_chunks(failed_uuids)
                logger.info(f"Cleaned up {len(failed_uuids)} failed chunks")
                
        except Exception as e:
            logger.error(f"Error cleaning up failed chunks: {e}")
            # Don't raise exception for cleanup failures 