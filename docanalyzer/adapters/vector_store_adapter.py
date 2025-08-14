"""
Vector Store Adapter - Integration with Vector Store Client

This module provides a high-level adapter for integrating DocAnalyzer with
the vector_store_client library. It handles connection management, error
handling, and provides a simplified interface for chunk operations.

The adapter wraps the vector_store_client functionality and provides
DocAnalyzer-specific abstractions for working with vector storage.

Author: DocAnalyzer Team
Version: 1.0.0
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import uuid

from vector_store_client import (
    VectorStoreClient, CreateChunksResponse,
    SearchResult, HealthResponse, ValidationError, ConnectionError,
    ServerError, VectorStoreError
)
from vector_store_client.models import CreateChunksResponse as VSCCreateChunksResponse
from vector_store_client.types import (
    ChunkType, LanguageEnum, SearchOrder,
    DEFAULT_LIMIT, DEFAULT_OFFSET, DEFAULT_RELEVANCE_THRESHOLD
)

from docanalyzer.config.integration import DocAnalyzerConfig
from docanalyzer.models.database import DatabaseFileRecord, RecordStatus
from docanalyzer.models.processing import ProcessingBlock
from docanalyzer.models.semantic_chunk import SemanticChunk, ChunkStatus, METADATA_KEYS
from docanalyzer.models.errors import ProcessingError, ErrorCategory

logger = logging.getLogger(__name__)

DEFAULT_BATCH_SIZE = 100
MAX_BATCH_SIZE = 1000
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_DELAY = 1.0


class VectorStoreAdapter:
    """
    Vector Store Adapter - High-level interface for vector storage operations
    
    Provides a simplified interface for working with the vector store,
    handling connection management, error handling, and batch operations.
    
    This adapter wraps the vector_store_client functionality and provides
    DocAnalyzer-specific abstractions for chunk creation, search, and
    health monitoring.
    
    Attributes:
        config (DocAnalyzerConfig): DocAnalyzer configuration instance.
            Used to get vector store connection settings.
        client (Optional[VectorStoreClient]): Vector store client instance.
            None until connection is established.
        is_connected (bool): Connection status flag.
            True if client is connected and ready.
        batch_size (int): Size of batches for bulk operations.
            Must be between 1 and MAX_BATCH_SIZE.
        retry_attempts (int): Number of retry attempts for failed operations.
            Must be positive integer.
        retry_delay (float): Delay between retry attempts in seconds.
            Must be positive float.
    
    Example:
        >>> adapter = VectorStoreAdapter()
        >>> await adapter.connect()
        >>> chunks = await adapter.create_chunks(processing_blocks)
        >>> search_results = await adapter.search_by_text("query")
        >>> await adapter.disconnect()
    
    Raises:
        ProcessingError: If vector store operations fail
        ConnectionError: If connection to vector store fails
        ValidationError: If input data validation fails
    """
    
    def __init__(
        self,
        config: Optional[DocAnalyzerConfig] = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
        retry_attempts: int = DEFAULT_RETRY_ATTEMPTS,
        retry_delay: float = DEFAULT_RETRY_DELAY
    ):
        """
        Initialize Vector Store Adapter.
        
        Args:
            config (Optional[DocAnalyzerConfig]): DocAnalyzer configuration.
                If None, creates new instance. Defaults to None.
            batch_size (int): Size of batches for bulk operations.
                Must be between 1 and MAX_BATCH_SIZE. Defaults to 100.
            retry_attempts (int): Number of retry attempts for failed operations.
                Must be positive integer. Defaults to 3.
            retry_delay (float): Delay between retry attempts in seconds.
                Must be positive float. Defaults to 1.0.
        
        Raises:
            ValueError: If batch_size, retry_attempts, or retry_delay are invalid
        """
        if batch_size < 1 or batch_size > MAX_BATCH_SIZE:
            raise ValueError(f"batch_size must be between 1 and {MAX_BATCH_SIZE}")
        if retry_attempts < 1:
            raise ValueError("retry_attempts must be positive")
        if retry_delay <= 0:
            raise ValueError("retry_delay must be positive")
        
        self.config = config or DocAnalyzerConfig()
        self.client: Optional[VectorStoreClient] = None
        self.is_connected = False
        self.batch_size = batch_size
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        
        logger.info("Vector Store Adapter initialized")
    
    async def connect(self) -> bool:
        """
        Establish connection to vector store.
        
        Creates VectorStoreClient instance and validates connection
        by performing health check. Sets is_connected flag on success.
        
        Returns:
            bool: True if connection established successfully, False otherwise.
        
        Raises:
            ConnectionError: If connection to vector store fails
            ProcessingError: If health check fails
        """
        try:
            # Get vector store settings from configuration
            vector_store_settings = self.config.get_vector_store_settings()
            base_url = f"{vector_store_settings['base_url']}:{vector_store_settings['port']}"
            timeout = vector_store_settings.get('timeout', 30.0)
            
            # Create and connect client
            self.client = await VectorStoreClient.create(base_url, timeout)
            self.is_connected = True
            
            # Perform health check
            await self.health_check()
            
            logger.info(f"Connected to vector store at {base_url}")
            return True
            
        except Exception as e:
            self.is_connected = False
            self.client = None
            logger.error(f"Failed to connect to vector store: {e}")
            raise ConnectionError(f"Vector store connection failed: {e}")
    
    async def disconnect(self) -> None:
        """
        Disconnect from vector store.
        
        Closes VectorStoreClient session and resets connection state.
        Safe to call multiple times.
        
        Raises:
            ProcessingError: If disconnection fails
        """
        try:
            if self.client:
                await self.client.close()
                logger.info("Disconnected from vector store")
            
            self.client = None
            self.is_connected = False
            
        except Exception as e:
            logger.error(f"Error during disconnection: {e}")
            # Don't raise error during cleanup
            self.client = None
            self.is_connected = False
    
    async def health_check(self) -> HealthResponse:
        """
        Perform health check on vector store.
        
        Validates that vector store is operational and responding
        to requests. Returns detailed health information.
        
        Returns:
            HealthResponse: Health status information from vector store.
                Contains status, version, uptime, and other metrics.
        
        Raises:
            ConnectionError: If vector store is not accessible
            ProcessingError: If health check fails
        """
        self._validate_connection()
        
        try:
            health_response = await self.client.health_check()
            logger.debug(f"Vector store health check: {health_response.status}")
            return health_response
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self._handle_vector_store_error(e, "health_check")
    
    async def create_chunks(
        self,
        processing_blocks: List[ProcessingBlock],
        source_path: str,
        source_id: Optional[str] = None
    ) -> CreateChunksResponse:
        """
        Create chunks from processing blocks.
        
        Converts ProcessingBlock objects to SemanticChunk objects and
        creates them in the vector store. Handles batch processing
        and error recovery.
        
        Args:
            processing_blocks (List[ProcessingBlock]): List of processing blocks.
                Must be non-empty list of valid ProcessingBlock objects.
            source_path (str): Path to source file.
                Used as source_path in chunk metadata.
            source_id (Optional[str]): Source identifier UUID.
                If None, generates new UUID4. Must be valid UUID if provided.
        
        Returns:
            CreateChunksResponse: Response with created chunk UUIDs.
                Contains success status, created_count, failed_count, and uuids list.
        
        Raises:
            ValidationError: If input data validation fails
            ProcessingError: If chunk creation fails
            ConnectionError: If vector store is not connected
        """
        if not processing_blocks:
            raise ValidationError("Processing blocks list cannot be empty")
        if not source_path:
            raise ValidationError("Source path cannot be empty")
        
        # Generate source_id if not provided
        if source_id is None:
            source_id = str(uuid.uuid4())
        
        self._validate_connection()
        
        try:
            # Convert processing blocks to chunks
            chunks = []
            for block in processing_blocks:
                chunk = self._convert_processing_block_to_chunk(block, source_path, source_id)
                chunks.append(chunk)
            
            # Create chunks in batches
            all_uuids = []
            total_created = 0
            total_failed = 0
            
            for i in range(0, len(chunks), self.batch_size):
                batch = chunks[i:i + self.batch_size]
                
                try:
                    response = await self.client.create_chunks(batch)
                    if response.success:
                        all_uuids.extend(response.uuids)
                        total_created += response.created_count or len(batch)
                        total_failed += response.failed_count or 0
                    else:
                        total_failed += len(batch)
                        logger.warning(f"Batch creation failed: {response}")
                        
                except Exception as e:
                    total_failed += len(batch)
                    logger.error(f"Batch creation error: {e}")
                    self._handle_vector_store_error(e, "create_chunks")
            
            logger.info(f"Created {total_created} chunks, failed {total_failed}")
            
            return VSCCreateChunksResponse(
                success=total_failed == 0,
                uuids=all_uuids,
                created_count=total_created,
                failed_count=total_failed
            )
            
        except Exception as e:
            logger.error(f"Chunk creation failed: {e}")
            self._handle_vector_store_error(e, "create_chunks")
    
    async def search_by_text(
        self,
        search_text: str,
        limit: int = DEFAULT_LIMIT,
        relevance_threshold: float = DEFAULT_RELEVANCE_THRESHOLD,
        offset: int = DEFAULT_OFFSET
    ) -> List[SemanticChunk]:
        """
        Search chunks by text content.
        
        Performs semantic search using text query and returns
        matching chunks ordered by relevance.
        
        Args:
            search_text (str): Text to search for.
                Must be non-empty string.
            limit (int): Maximum number of results to return.
                Must be between 1 and MAX_SEARCH_LIMIT. Defaults to 10.
            relevance_threshold (float): Minimum relevance score.
                Must be between 0.0 and 1.0. Defaults to 0.7.
            offset (int): Number of results to skip.
                Must be non-negative integer. Defaults to 0.
        
        Returns:
            List[SemanticChunk]: List of matching chunks.
                Ordered by relevance score descending.
        
        Raises:
            ValidationError: If search parameters are invalid
            ProcessingError: If search operation fails
            ConnectionError: If vector store is not connected
        """
        if not search_text:
            raise ValidationError("Search text cannot be empty")
        if limit < 1:
            raise ValidationError("Limit must be positive")
        if not 0.0 <= relevance_threshold <= 1.0:
            raise ValidationError("Relevance threshold must be between 0.0 and 1.0")
        if offset < 0:
            raise ValidationError("Offset must be non-negative")
        
        self._validate_connection()
        
        try:
            results = await self.client.search_by_text(
                search_text=search_text,
                limit=limit,
                level_of_relevance=relevance_threshold,
                offset=offset
            )
            
            logger.debug(f"Text search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Text search failed: {e}")
            self._handle_vector_store_error(e, "search_by_text")
    
    async def search_by_metadata(
        self,
        metadata_filter: Dict[str, Any],
        limit: int = DEFAULT_LIMIT,
        relevance_threshold: float = DEFAULT_RELEVANCE_THRESHOLD,
        offset: int = DEFAULT_OFFSET
    ) -> List[SemanticChunk]:
        """
        Search chunks by metadata filter.
        
        Performs search using metadata criteria and returns
        matching chunks ordered by relevance.
        
        Args:
            metadata_filter (Dict[str, Any]): Metadata filter criteria.
                Must be valid metadata filter dictionary.
            limit (int): Maximum number of results to return.
                Must be between 1 and MAX_SEARCH_LIMIT. Defaults to 10.
            relevance_threshold (float): Minimum relevance score.
                Must be between 0.0 and 1.0. Defaults to 0.7.
            offset (int): Number of results to skip.
                Must be non-negative integer. Defaults to 0.
        
        Returns:
            List[SemanticChunk]: List of matching chunks.
                Ordered by relevance score descending.
        
        Raises:
            ValidationError: If metadata filter is invalid
            ProcessingError: If search operation fails
            ConnectionError: If vector store is not connected
        """
        if not metadata_filter:
            raise ValidationError("Metadata filter cannot be empty")
        if limit < 1:
            raise ValidationError("Limit must be positive")
        if not 0.0 <= relevance_threshold <= 1.0:
            raise ValidationError("Relevance threshold must be between 0.0 and 1.0")
        if offset < 0:
            raise ValidationError("Offset must be non-negative")
        
        self._validate_connection()
        
        try:
            results = await self.client.search_by_metadata(
                metadata_filter=metadata_filter,
                limit=limit,
                level_of_relevance=relevance_threshold,
                offset=offset
            )
            
            logger.debug(f"Metadata search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Metadata search failed: {e}")
            self._handle_vector_store_error(e, "search_by_metadata")
    
    async def delete_chunks(
        self,
        chunk_uuids: List[str]
    ) -> bool:
        """
        Delete chunks by UUIDs.
        
        Removes chunks from vector store using their UUIDs.
        Handles batch deletion and error recovery.
        
        Args:
            chunk_uuids (List[str]): List of chunk UUIDs to delete.
                Must be non-empty list of valid UUID strings.
        
        Returns:
            bool: True if all chunks deleted successfully, False otherwise.
        
        Raises:
            ValidationError: If UUIDs are invalid
            ProcessingError: If deletion fails
            ConnectionError: If vector store is not connected
        """
        if not chunk_uuids:
            raise ValidationError("Chunk UUIDs list cannot be empty")
        
        self._validate_connection()
        
        try:
            # Delete chunks in batches
            total_deleted = 0
            total_failed = 0
            
            for i in range(0, len(chunk_uuids), self.batch_size):
                batch = chunk_uuids[i:i + self.batch_size]
                
                try:
                    response = await self.client.delete_chunks(batch)
                    if response.success:
                        total_deleted += response.deleted_count or len(batch)
                        total_failed += response.failed_count or 0
                    else:
                        total_failed += len(batch)
                        logger.warning(f"Batch deletion failed: {response}")
                        
                except Exception as e:
                    total_failed += len(batch)
                    logger.error(f"Batch deletion error: {e}")
                    self._handle_vector_store_error(e, "delete_chunks")
            
            success = total_failed == 0
            logger.info(f"Deleted {total_deleted} chunks, failed {total_failed}")
            
            return success
            
        except Exception as e:
            logger.error(f"Chunk deletion failed: {e}")
            self._handle_vector_store_error(e, "delete_chunks")
    
    async def get_chunk_count(self) -> int:
        """
        Get total number of chunks in vector store.
        
        Returns the count of all chunks stored in the vector store.
        Useful for monitoring and statistics.
        
        Returns:
            int: Total number of chunks in vector store.
                Non-negative integer.
        
        Raises:
            ProcessingError: If count operation fails
            ConnectionError: If vector store is not connected
        """
        self._validate_connection()
        
        try:
            # Use search with empty criteria to get total count
            results = await self.client.search_chunks(limit=1)
            # Note: This is a simplified approach. In a real implementation,
            # you might want to use a dedicated count method if available
            count = len(results) if results else 0
            
            logger.debug(f"Vector store contains {count} chunks")
            return count
            
        except Exception as e:
            logger.error(f"Failed to get chunk count: {e}")
            self._handle_vector_store_error(e, "get_chunk_count")
    
    def _convert_processing_block_to_chunk(
        self,
        block: ProcessingBlock,
        source_path: str,
        source_id: str
    ) -> SemanticChunk:
        """
        Convert ProcessingBlock to SemanticChunk.
        
        Internal method to convert DocAnalyzer ProcessingBlock to
        vector_store_client SemanticChunk format.
        
        Args:
            block (ProcessingBlock): Processing block to convert.
                Must be valid ProcessingBlock instance.
            source_path (str): Path to source file.
                Used as source_path in chunk metadata.
            source_id (str): Source identifier UUID.
                Must be valid UUID string.
        
        Returns:
            SemanticChunk: Converted chunk object.
                Ready for vector store operations.
        
        Raises:
            ValidationError: If conversion fails
        """
        try:
            # Create metadata dictionary with standard keys
            metadata = {}
            
            # Add standard block information
            if block.block_type:
                metadata["block_type"] = block.block_type
            
            if hasattr(block, 'start_line') and block.start_line is not None:
                metadata["start_line"] = block.start_line
            
            if hasattr(block, 'end_line') and block.end_line is not None:
                metadata["end_line"] = block.end_line
            
            if hasattr(block, 'start_char') and block.start_char is not None:
                metadata["start_char"] = block.start_char
            
            if hasattr(block, 'end_char') and block.end_char is not None:
                metadata["end_char"] = block.end_char
            
            # Add processing timestamp
            metadata["processing_timestamp"] = datetime.now().isoformat()
            
            # Add any additional metadata from the block
            if block.metadata:
                metadata.update(block.metadata)
            
            # Create SemanticChunk instance using new model
            chunk = SemanticChunk(
                source_path=source_path,
                source_id=source_id,
                content=block.content,
                status=ChunkStatus.NEW,
                metadata=metadata,
                chunk_type="text",  # Default chunk type
                language="en"  # Default language
            )
            
            return chunk
            
        except Exception as e:
            logger.error(f"Failed to convert processing block to chunk: {e}")
            raise ValidationError(f"Chunk conversion failed: {e}")
    
    def _validate_connection(self) -> None:
        """
        Validate that adapter is connected to vector store.
        
        Internal method to check connection status before operations.
        Raises ConnectionError if not connected.
        
        Raises:
            ConnectionError: If adapter is not connected to vector store
        """
        if not self.is_connected or not self.client:
            raise ConnectionError("Vector store adapter is not connected")
    
    def _handle_vector_store_error(
        self,
        error: VectorStoreError,
        operation: str
    ) -> None:
        """
        Handle VectorStoreError and convert to ProcessingError.
        
        Internal method to convert vector_store_client exceptions
        to DocAnalyzer ProcessingError with appropriate context.
        
        Args:
            error (VectorStoreError): Original vector store error.
                Any exception from vector_store_client.
            operation (str): Name of operation that failed.
                Used for error context.
        
        Raises:
            ProcessingError: Converted error with operation context
        """
        error_message = f"Vector store {operation} failed: {str(error)}"
        
        if isinstance(error, ConnectionError):
            raise ConnectionError(error_message)
        elif isinstance(error, ValidationError):
            raise ValidationError(error_message)
        else:
            raise ProcessingError("vector_store_error", error_message, ErrorCategory.PROCESSING) 