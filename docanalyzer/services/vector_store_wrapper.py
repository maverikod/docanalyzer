"""
Vector Store Wrapper Service - High-level vector store operations

This module provides a high-level wrapper service for vector store operations,
integrating with the VectorStoreAdapter to provide simplified interfaces for
chunk management, search, and health monitoring.

The wrapper service handles business logic, error handling, and provides
a clean interface for other DocAnalyzer components to interact with vector storage.

Author: DocAnalyzer Team
Version: 1.0.0
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import uuid

from docanalyzer.adapters.vector_store_adapter import VectorStoreAdapter
from docanalyzer.config import get_unified_config
from docanalyzer.models.processing import ProcessingBlock
from docanalyzer.models.database import DatabaseFileRecord, RecordStatus
from docanalyzer.models.errors import ProcessingError
from docanalyzer.monitoring.metrics import MetricsCollector
from docanalyzer.monitoring.health import HealthChecker
from docanalyzer.models.health import HealthStatus
from docanalyzer.models.errors import ProcessingError, ValidationError, ConnectionError, ErrorCategory

logger = logging.getLogger(__name__)

DEFAULT_OPERATION_TIMEOUT = 30.0
DEFAULT_HEALTH_CHECK_INTERVAL = 60.0


class VectorStoreWrapper:
    """
    Vector Store Wrapper Service - High-level vector store operations
    
    Provides a high-level interface for vector store operations including
    chunk creation, search, deletion, and health monitoring. Integrates
    with VectorStoreAdapter and provides business logic layer.
    
    This service handles connection management, error handling, metrics
    collection, and provides simplified interfaces for other DocAnalyzer
    components.
    
    Attributes:
        adapter (VectorStoreAdapter): Vector store adapter instance.
            Handles low-level vector store operations.
        config (DocAnalyzerConfig): DocAnalyzer configuration.
            Used for connection settings and configuration.
        metrics_collector (MetricsCollector): Metrics collection instance.
            Tracks vector store operation metrics.
        health_checker (HealthChecker): Health monitoring instance.
            Monitors vector store health status.
        operation_timeout (float): Timeout for vector store operations.
            Must be positive float. Defaults to 30.0 seconds.
        health_check_interval (float): Interval for health checks.
            Must be positive float. Defaults to 60.0 seconds.
        is_initialized (bool): Initialization status flag.
            True if service is properly initialized.
    
    Example:
        >>> wrapper = VectorStoreWrapper()
        >>> await wrapper.initialize()
        >>> chunks = await wrapper.process_file_blocks(blocks, "/path/file.txt")
        >>> results = await wrapper.search_documents("query")
        >>> await wrapper.cleanup()
    
    Raises:
        ProcessingError: If vector store operations fail
        ConnectionError: If connection to vector store fails
        ValidationError: If input data validation fails
    """
    
    def __init__(
        self,
        config: Optional[Any] = None,
        operation_timeout: float = DEFAULT_OPERATION_TIMEOUT,
        health_check_interval: float = DEFAULT_HEALTH_CHECK_INTERVAL
    ):
        """
        Initialize Vector Store Wrapper Service.
        
        Args:
            config (Optional[Any]): Configuration object. If None, uses unified config.
                Defaults to None.
            operation_timeout (float): Timeout for vector store operations.
                Must be positive float. Defaults to 30.0 seconds.
            health_check_interval (float): Interval for health checks.
                Must be positive float. Defaults to 60.0 seconds.
        
        Raises:
            ValueError: If operation_timeout or health_check_interval are invalid
        """
        if operation_timeout <= 0:
            raise ValueError("operation_timeout must be positive")
        if health_check_interval <= 0:
            raise ValueError("health_check_interval must be positive")
        
        # Use unified configuration if no config provided
        if config is None:
            self.config = get_unified_config()
        else:
            self.config = config
        
        self.adapter = VectorStoreAdapter(self.config)
        self.metrics_collector = MetricsCollector()
        self.health_checker = HealthChecker()
        self.operation_timeout = operation_timeout
        self.health_check_interval = health_check_interval
        self.is_initialized = False
        
        logger.info("Vector Store Wrapper Service initialized")
    
    async def initialize(self) -> bool:
        """
        Initialize vector store wrapper service.
        
        Establishes connection to vector store, initializes metrics
        collection, and starts health monitoring. Must be called
        before using other methods.
        
        Returns:
            bool: True if initialization successful, False otherwise.
        
        Raises:
            ConnectionError: If connection to vector store fails
            ProcessingError: If initialization fails
        """
        try:
            # Connect to vector store
            connection_success = await self.adapter.connect()
            if not connection_success:
                raise ConnectionError("Failed to connect to vector store")
            
            # Initialize health checker
            await self.health_checker.initialize()
            
            # Set initialization flag before health check
            self.is_initialized = True
            
            # Perform initial health check (now safe to call)
            try:
                health_status = await self.health_check()
                if health_status.status != "healthy":
                    logger.warning(f"Vector store health check failed: {health_status.status}")
            except Exception as e:
                logger.warning(f"Health check failed during initialization: {e}")
            
            logger.info("Vector Store Wrapper Service initialized successfully")
            return True
            
        except Exception as e:
            self.is_initialized = False
            logger.error(f"Failed to initialize Vector Store Wrapper Service: {e}")
            raise ProcessingError("initialization_error", f"Initialization failed: {e}", ErrorCategory.PROCESSING)
    
    async def cleanup(self) -> None:
        """
        Cleanup vector store wrapper service.
        
        Disconnects from vector store, stops health monitoring,
        and performs cleanup operations. Safe to call multiple times.
        
        Raises:
            ProcessingError: If cleanup fails
        """
        try:
            # Disconnect from vector store
            await self.adapter.disconnect()
            
            # Cleanup health checker
            await self.health_checker.cleanup()
            
            self.is_initialized = False
            logger.info("Vector Store Wrapper Service cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            # Don't raise error during cleanup
            self.is_initialized = False
    
    async def process_file_blocks(
        self,
        processing_blocks: List[ProcessingBlock],
        file_path: str,
        file_record: Optional[DatabaseFileRecord] = None
    ) -> Dict[str, Any]:
        """
        Process file blocks and create chunks in vector store.
        
        Converts ProcessingBlock objects to chunks and stores them
        in vector store. Handles batch processing, error recovery,
        and metrics collection.
        
        Args:
            processing_blocks (List[ProcessingBlock]): List of processing blocks.
                Must be non-empty list of valid ProcessingBlock objects.
            file_path (str): Path to source file.
                Used for chunk metadata and tracking.
            file_record (Optional[DatabaseFileRecord]): Database file record.
                If provided, uses record_id as source_id. Defaults to None.
        
        Returns:
            Dict[str, Any]: Processing results.
                Contains success status, created_count, failed_count,
                chunk_uuids, and processing metadata.
        
        Raises:
            ValidationError: If input data validation fails
            ProcessingError: If chunk creation fails
            ConnectionError: If vector store is not connected
        """
        self._validate_initialization()
        
        start_time = datetime.now()
        source_id = file_record.record_id if file_record else None
        
        try:
            # Create chunks using adapter
            response = await self.adapter.create_chunks(
                processing_blocks=processing_blocks,
                source_path=file_path,
                source_id=source_id
            )
            
            # Collect metrics
            self._collect_operation_metrics(
                operation="process_file_blocks",
                start_time=start_time,
                success=response.success,
                result_count=response.created_count or 0
            )
            
            # Prepare result
            result = {
                "success": response.success,
                "created_count": response.created_count or 0,
                "failed_count": response.failed_count or 0,
                "chunk_uuids": response.uuids,
                "file_path": file_path,
                "source_id": source_id,
                "processing_time": (datetime.now() - start_time).total_seconds()
            }
            
            logger.info(f"Processed {len(processing_blocks)} blocks for {file_path}")
            return result
            
        except Exception as e:
            self._collect_operation_metrics(
                operation="process_file_blocks",
                start_time=start_time,
                success=False,
                error_message=str(e)
            )
            self._handle_operation_error(e, "process_file_blocks", {"file_path": file_path})
    
    async def search_documents(
        self,
        query: str,
        limit: int = 10,
        relevance_threshold: float = 0.7,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search documents in vector store.
        
        Performs semantic search using text query and optional metadata
        filters. Returns formatted search results with document information.
        
        Args:
            query (str): Search query text.
                Must be non-empty string.
            limit (int): Maximum number of results to return.
                Must be positive integer. Defaults to 10.
            relevance_threshold (float): Minimum relevance score.
                Must be between 0.0 and 1.0. Defaults to 0.7.
            metadata_filter (Optional[Dict[str, Any]]): Metadata filter criteria.
                If provided, applies additional filtering. Defaults to None.
        
        Returns:
            List[Dict[str, Any]]: Search results.
                Each result contains chunk data, relevance score,
                and document metadata.
        
        Raises:
            ValidationError: If search parameters are invalid
            ProcessingError: If search operation fails
            ConnectionError: If vector store is not connected
        """
        self._validate_initialization()
        
        start_time = datetime.now()
        
        try:
            # Perform search using adapter
            if metadata_filter:
                chunks = await self.adapter.search_by_metadata(
                    metadata_filter=metadata_filter,
                    limit=limit,
                    relevance_threshold=relevance_threshold
                )
            else:
                chunks = await self.adapter.search_by_text(
                    search_text=query,
                    limit=limit,
                    relevance_threshold=relevance_threshold
                )
            
            # Format results
            results = []
            for chunk in chunks:
                result = {
                    "chunk_uuid": chunk.uuid,
                    "content": chunk.body,
                    "source_path": chunk.source_path,
                    "source_id": chunk.source_id,
                    "relevance_score": getattr(chunk, 'relevance_score', 0.0),
                    "metadata": {
                        "type": chunk.type,
                        "language": chunk.language,
                        "status": chunk.status,
                        "created_at": chunk.created_at
                    }
                }
                results.append(result)
            
            # Collect metrics
            self._collect_operation_metrics(
                operation="search_documents",
                start_time=start_time,
                success=True,
                result_count=len(results)
            )
            
            logger.info(f"Search returned {len(results)} results for query: {query}")
            return results
            
        except Exception as e:
            self._collect_operation_metrics(
                operation="search_documents",
                start_time=start_time,
                success=False,
                error_message=str(e)
            )
            self._handle_operation_error(e, "search_documents", {"query": query})
    
    async def delete_file_chunks(
        self,
        file_path: str
    ) -> bool:
        """
        Delete all chunks for a specific file.
        
        Removes all chunks associated with the specified file path
        from vector store. Handles batch deletion and error recovery.
        
        Args:
            file_path (str): Path to file whose chunks should be deleted.
                Must be non-empty string.
        
        Returns:
            bool: True if all chunks deleted successfully, False otherwise.
        
        Raises:
            ValidationError: If file_path is invalid
            ProcessingError: If deletion fails
            ConnectionError: If vector store is not connected
        """
        self._validate_initialization()
        
        start_time = datetime.now()
        
        try:
            # First, get all chunks for the file
            chunks = await self.get_file_chunks(file_path, limit=1000)
            chunk_uuids = [chunk["chunk_uuid"] for chunk in chunks]
            
            if not chunk_uuids:
                logger.info(f"No chunks found for file: {file_path}")
                return True
            
            # Delete chunks
            success = await self.adapter.delete_chunks(chunk_uuids)
            
            # Collect metrics
            self._collect_operation_metrics(
                operation="delete_file_chunks",
                start_time=start_time,
                success=success,
                result_count=len(chunk_uuids)
            )
            
            logger.info(f"Deleted {len(chunk_uuids)} chunks for file: {file_path}")
            return success
            
        except Exception as e:
            self._collect_operation_metrics(
                operation="delete_file_chunks",
                start_time=start_time,
                success=False,
                error_message=str(e)
            )
            self._handle_operation_error(e, "delete_file_chunks", {"file_path": file_path})
    
    async def get_file_chunks(
        self,
        file_path: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all chunks for a specific file.
        
        Retrieves all chunks associated with the specified file path
        from vector store. Useful for file analysis and debugging.
        
        Args:
            file_path (str): Path to file whose chunks should be retrieved.
                Must be non-empty string.
            limit (int): Maximum number of chunks to return.
                Must be positive integer. Defaults to 100.
        
        Returns:
            List[Dict[str, Any]]: List of chunks for the file.
                Each chunk contains full metadata and content.
        
        Raises:
            ValidationError: If file_path is invalid
            ProcessingError: If retrieval fails
            ConnectionError: If vector store is not connected
        """
        self._validate_initialization()
        
        start_time = datetime.now()
        
        try:
            # Search for chunks by source_path metadata
            metadata_filter = {"source_path": file_path}
            chunks = await self.adapter.search_by_metadata(
                metadata_filter=metadata_filter,
                limit=limit
            )
            
            # Format results
            results = []
            for chunk in chunks:
                result = {
                    "chunk_uuid": chunk.uuid,
                    "content": chunk.body,
                    "source_path": chunk.source_path,
                    "source_id": chunk.source_id,
                    "metadata": {
                        "type": chunk.type,
                        "language": chunk.language,
                        "status": chunk.status,
                        "created_at": chunk.created_at,
                        "start_line": getattr(chunk, 'start_line', None),
                        "end_line": getattr(chunk, 'end_line', None),
                        "start_char": getattr(chunk, 'start_char', None),
                        "end_char": getattr(chunk, 'end_char', None)
                    }
                }
                results.append(result)
            
            # Collect metrics
            self._collect_operation_metrics(
                operation="get_file_chunks",
                start_time=start_time,
                success=True,
                result_count=len(results)
            )
            
            logger.info(f"Retrieved {len(results)} chunks for file: {file_path}")
            return results
            
        except Exception as e:
            self._collect_operation_metrics(
                operation="get_file_chunks",
                start_time=start_time,
                success=False,
                error_message=str(e)
            )
            self._handle_operation_error(e, "get_file_chunks", {"file_path": file_path})
    
    async def get_vector_store_stats(self) -> Dict[str, Any]:
        """
        Get vector store statistics.
        
        Returns comprehensive statistics about vector store including
        total chunk count, health status, and performance metrics.
        
        Returns:
            Dict[str, Any]: Vector store statistics.
                Contains chunk_count, health_status, uptime,
                and performance metrics.
        
        Raises:
            ProcessingError: If statistics retrieval fails
            ConnectionError: If vector store is not connected
        """
        self._validate_initialization()
        
        try:
            # Get health status
            health_status = await self.health_check()
            
            # Get chunk count
            chunk_count = await self.adapter.get_chunk_count()
            
            # Get metrics
            metrics = self.metrics_collector.get_metrics()
            
            stats = {
                "chunk_count": chunk_count,
                "health_status": health_status.status,
                "health_details": health_status.details,
                "uptime": health_status.timestamp,
                "performance_metrics": metrics,
                "connection_status": "connected" if self.adapter.is_connected else "disconnected"
            }
            
            logger.debug(f"Vector store stats: {chunk_count} chunks, health: {health_status.status}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get vector store stats: {e}")
            self._handle_operation_error(e, "get_vector_store_stats")
    
    async def health_check(self) -> HealthStatus:
        """
        Perform health check on vector store.
        
        Validates vector store health and returns detailed status
        information. Used for monitoring and diagnostics.
        
        Returns:
            HealthStatus: Health status information.
                Contains status, details, and timestamp.
        
        Raises:
            ProcessingError: If health check fails
            ConnectionError: If vector store is not accessible
        """
        self._validate_initialization()
        
        try:
            # Perform health check using adapter
            health_response = await self.adapter.health_check()
            
            # Convert to HealthStatus
            status = "healthy" if health_response.status == "ok" else "unhealthy"
            details = {
                "vector_store_status": health_response.status,
                "version": getattr(health_response, 'version', 'unknown'),
                "uptime": getattr(health_response, 'uptime', 'unknown')
            }
            
            health_status = HealthStatus(
                status=status,
                details=details,
                timestamp=datetime.now()
            )
            
            logger.debug(f"Vector store health check: {status}")
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self._handle_operation_error(e, "health_check")
    
    def _validate_initialization(self) -> None:
        """
        Validate that service is properly initialized.
        
        Internal method to check initialization status before operations.
        Raises ProcessingError if not initialized.
        
        Raises:
            ProcessingError: If service is not initialized
        """
        if not self.is_initialized:
            raise ProcessingError("initialization_error", "Vector Store Wrapper Service is not initialized", ErrorCategory.PROCESSING)
    
    def _collect_operation_metrics(
        self,
        operation: str,
        start_time: datetime,
        success: bool,
        result_count: int = 0,
        error_message: Optional[str] = None
    ) -> None:
        """
        Collect metrics for vector store operations.
        
        Internal method to track operation performance and success rates.
        Updates metrics collector with operation data.
        
        Args:
            operation (str): Name of the operation performed.
                Used for metrics categorization.
            start_time (datetime): Operation start time.
                Used to calculate duration.
            success (bool): Whether operation was successful.
                Used for success rate tracking.
            result_count (int): Number of results returned.
                Used for throughput tracking. Defaults to 0.
            error_message (Optional[str]): Error message if operation failed.
                Used for error tracking. Defaults to None.
        """
        try:
            duration = (datetime.now() - start_time).total_seconds()
            
            # Record operation metrics
            self.metrics_collector.record_operation(
                operation_name=f"vector_store_{operation}",
                duration=duration,
                success=success,
                result_count=result_count,
                error_message=error_message
            )
            
            logger.debug(f"Recorded metrics for {operation}: duration={duration}s, success={success}")
            
        except Exception as e:
            logger.warning(f"Failed to collect metrics for {operation}: {e}")
    
    def _handle_operation_error(
        self,
        error: Exception,
        operation: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Handle operation errors and convert to ProcessingError.
        
        Internal method to handle exceptions and convert them to
        appropriate ProcessingError with context information.
        
        Args:
            error (Exception): Original exception.
                Any exception that occurred during operation.
            operation (str): Name of operation that failed.
                Used for error context.
            context (Optional[Dict[str, Any]]): Additional context information.
                Used for error details. Defaults to None.
        
        Raises:
            ProcessingError: Converted error with operation context
        """
        error_message = f"Vector store {operation} failed: {str(error)}"
        
        if context:
            context_str = ", ".join([f"{k}={v}" for k, v in context.items()])
            error_message += f" (Context: {context_str})"
        
        if isinstance(error, (ValidationError, ConnectionError)):
            raise error
        else:
            raise ProcessingError("operation_error", error_message, ErrorCategory.PROCESSING)
    
    async def create_chunk(self, chunk_id: str, content: str, metadata: Dict[str, Any]) -> bool:
        """
        Create a single chunk in vector store.
        
        Creates a chunk with the specified ID, content and metadata.
        This method is used by FileProcessor for atomic chunk creation.
        
        Args:
            chunk_id (str): UUID for the chunk.
                Must be a valid UUID string.
            content (str): Text content of the chunk.
                Must be non-empty string.
            metadata (Dict[str, Any]): Metadata for the chunk.
                Can contain any additional information.
        
        Returns:
            bool: True if chunk was created successfully.
        
        Raises:
            ProcessingError: If chunk creation fails
            ValidationError: If chunk data is invalid
        """
        self._validate_initialization()
        
        start_time = datetime.now()
        
        try:
            # Create chunk data dictionary
            chunk_data = {
                "uuid": chunk_id,
                "body": content,
                "text": content,
                "source_id": metadata.get("source_id", "unknown"),
                "type": metadata.get("type", "Draft"),
                "language": metadata.get("language", "en"),
                "metadata": metadata
            }
            
            # Convert to ProcessingBlock and use existing method
            processing_block = ProcessingBlock(
                content=content,
                block_type=metadata.get("type", "text"),
                metadata=chunk_data
            )
            
            result = await self.process_file_blocks([processing_block], metadata.get("source_path", ""))
            
            success = result.get("success", False)
            
            self._collect_operation_metrics(
                operation="create_chunk",
                start_time=start_time,
                success=success,
                result_count=1 if success else 0
            )
            
            if success:
                logger.info(f"Created chunk with UUID: {chunk_id}")
            else:
                logger.error(f"Failed to create chunk with UUID: {chunk_id}")
            
            return success
                
        except Exception as e:
            self._collect_operation_metrics(
                operation="create_chunk",
                start_time=start_time,
                success=False,
                error_message=str(e)
            )
            self._handle_operation_error(e, "create_chunk", {"chunk_id": chunk_id})
    
    async def delete_chunk(self, chunk_id: str) -> bool:
        """
        Delete a single chunk from vector store.
        
        Deletes the chunk with the specified UUID.
        This method is used by FileProcessor for atomic chunk deletion.
        
        Args:
            chunk_id (str): UUID of the chunk to delete.
                Must be a valid UUID string.
        
        Returns:
            bool: True if chunk was deleted successfully.
        
        Raises:
            ProcessingError: If chunk deletion fails
            ValidationError: If UUID is invalid
        """
        self._validate_initialization()
        
        start_time = datetime.now()
        
        try:
            # Use adapter to delete chunk
            result = await self.adapter.delete_chunks([chunk_id])
            
            success = result.success if hasattr(result, 'success') else True
            
            self._collect_operation_metrics(
                operation="delete_chunk",
                start_time=start_time,
                success=success,
                result_count=1 if success else 0
            )
            
            if success:
                logger.info(f"Deleted chunk with UUID: {chunk_id}")
            else:
                logger.warning(f"Failed to delete chunk with UUID: {chunk_id}")
            
            return success
            
        except Exception as e:
            self._collect_operation_metrics(
                operation="delete_chunk",
                start_time=start_time,
                success=False,
                error_message=str(e)
            )
            self._handle_operation_error(e, "delete_chunk", {"chunk_id": chunk_id}) 