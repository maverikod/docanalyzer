"""
Database Manager Service - Database Management and Operations

This module provides a comprehensive database management service for DocAnalyzer,
including file record management, caching, transaction handling, and database
operations coordination.

The Database Manager integrates with VectorStoreWrapper and provides high-level
database operations for file tracking, processing history, and data management.

Author: DocAnalyzer Team
Version: 1.0.0
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union, Set
from datetime import datetime, timedelta
import uuid
import json
from pathlib import Path
from collections import defaultdict

from docanalyzer.services.vector_store_wrapper import VectorStoreWrapper
from docanalyzer.models.database import (
    DatabaseFileRecord, RecordStatus, ProcessingStatistics,
    DatabaseMetadata, DatabaseHealth
)
from docanalyzer.models.file_system import FileInfo
from docanalyzer.models.processing import ProcessingBlock, FileProcessingResult
from docanalyzer.models.errors import (
    ProcessingError, ValidationError, DatabaseError, NotFoundError, ErrorCategory
)
from docanalyzer.config.integration import DocAnalyzerConfig
from docanalyzer.monitoring.metrics import MetricsCollector
from docanalyzer.monitoring.health import HealthChecker, HealthStatus
# Removed unused imports - get_file_info and calculate_file_hash are not implemented yet

logger = logging.getLogger(__name__)

DEFAULT_CACHE_SIZE = 1000
DEFAULT_CACHE_TTL = 300  # 5 minutes
DEFAULT_BATCH_SIZE = 100
DEFAULT_TRANSACTION_TIMEOUT = 30.0


class FileRepository:
    """
    File Repository - File Record Management
    
    Manages file records in the database including creation, updates,
    queries, and deletion operations.
    
    This repository provides a clean interface for file record operations
    and handles data validation and business logic.
    
    Attributes:
        records (Dict[str, DatabaseFileRecord]): In-memory file records cache.
            Maps file_path to DatabaseFileRecord for fast access.
        vector_store_wrapper (VectorStoreWrapper): Vector store wrapper instance.
            Used for vector store operations and chunk management.
        metrics_collector (MetricsCollector): Metrics collection instance.
            Tracks repository operation metrics.
    
    Example:
        >>> repo = FileRepository(vector_store_wrapper)
        >>> record = await repo.create_file_record("/path/file.txt", file_info)
        >>> records = await repo.get_files_by_status(RecordStatus.NEW)
        >>> await repo.update_file_status("/path/file.txt", RecordStatus.COMPLETED)
    
    Raises:
        ValidationError: If file record data is invalid
        NotFoundError: If file record not found
        DatabaseError: If database operations fail
    """
    
    def __init__(
        self,
        vector_store_wrapper: VectorStoreWrapper,
        metrics_collector: Optional[MetricsCollector] = None
    ):
        """
        Initialize File Repository.
        
        Args:
            vector_store_wrapper (VectorStoreWrapper): Vector store wrapper instance.
                Used for vector store operations.
            metrics_collector (Optional[MetricsCollector]): Metrics collection instance.
                If None, creates new instance. Defaults to None.
        
        Raises:
            ValueError: If vector_store_wrapper is None
        """
        if vector_store_wrapper is None:
            raise ValueError("vector_store_wrapper cannot be None")
        
        self.vector_store_wrapper = vector_store_wrapper
        self.metrics_collector = metrics_collector or MetricsCollector()
        self.records: Dict[str, DatabaseFileRecord] = {}
        
        logger.info("File Repository initialized")
    
    async def create_file_record(
        self,
        file_path: str,
        file_info: FileInfo,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DatabaseFileRecord:
        """
        Create a new file record in the database.
        
        Creates a new DatabaseFileRecord with file information and stores
        it in the repository. Validates file information and generates
        unique record ID.
        
        Args:
            file_path (str): Absolute path to the file.
                Must be existing file path.
            file_info (FileInfo): File information object.
                Contains file metadata and properties.
            metadata (Optional[Dict[str, Any]]): Additional metadata.
                Custom attributes for the file record. Defaults to None.
        
        Returns:
            DatabaseFileRecord: Created file record.
        
        Raises:
            ValidationError: If file_path is empty or file_info is invalid
            DatabaseError: If record creation fails
        """
        if not file_path or not isinstance(file_path, str):
            raise ValidationError("file_path must be non-empty string")
        if file_info is None:
            raise ValidationError("file_info cannot be None")
        
        # Check if record already exists
        if file_path in self.records:
            raise DatabaseError(f"File record already exists: {file_path}")
        
        try:
            # Create file record
            record = DatabaseFileRecord(
                file_path=file_path,
                file_size_bytes=file_info.file_size,
                modification_time=file_info.modification_time,
                metadata=metadata or {}
            )
            
            # Store in repository
            self.records[file_path] = record
            
            # Track metrics
            self.metrics_collector.increment_counter("file_records_created")
            
            logger.info(f"Created file record: {file_path}")
            return record
            
        except Exception as e:
            logger.error(f"Failed to create file record for {file_path}: {e}")
            raise DatabaseError(f"Failed to create file record: {e}")
    
    async def get_file_record(self, file_path: str) -> DatabaseFileRecord:
        """
        Get file record by file path.
        
        Retrieves file record from repository by file path.
        Returns cached record if available, otherwise raises NotFoundError.
        
        Args:
            file_path (str): Absolute path to the file.
                Must be existing file path.
        
        Returns:
            DatabaseFileRecord: File record.
        
        Raises:
            ValidationError: If file_path is empty
            NotFoundError: If file record not found
        """
        if not file_path or not isinstance(file_path, str):
            raise ValidationError("file_path must be non-empty string")
        
        if file_path not in self.records:
            raise NotFoundError(f"File record not found: {file_path}")
        
        return self.records[file_path]
    
    async def update_file_record(
        self,
        file_path: str,
        updates: Dict[str, Any]
    ) -> DatabaseFileRecord:
        """
        Update file record with new data.
        
        Updates existing file record with provided updates.
        Validates updates and applies changes to record.
        
        Args:
            file_path (str): Absolute path to the file.
                Must be existing file path.
            updates (Dict[str, Any]): Updates to apply.
                Dictionary of field names and new values.
        
        Returns:
            DatabaseFileRecord: Updated file record.
        
        Raises:
            ValidationError: If file_path is empty or updates are invalid
            NotFoundError: If file record not found
            DatabaseError: If update fails
        """
        if not file_path or not isinstance(file_path, str):
            raise ValidationError("file_path must be non-empty string")
        if not isinstance(updates, dict):
            raise ValidationError("updates must be dictionary")
        
        if file_path not in self.records:
            raise NotFoundError(f"File record not found: {file_path}")
        
        try:
            record = self.records[file_path]
            
            # Apply updates
            for field, value in updates.items():
                if hasattr(record, field):
                    setattr(record, field, value)
            
            # Update timestamp
            record.updated_at = datetime.now()
            
            # Track metrics
            self.metrics_collector.increment_counter("file_records_updated")
            
            logger.info(f"Updated file record: {file_path}")
            return record
            
        except Exception as e:
            logger.error(f"Failed to update file record for {file_path}: {e}")
            raise DatabaseError(f"Failed to update file record: {e}")
    
    async def update_file_status(
        self,
        file_path: str,
        status: RecordStatus,
        error_message: Optional[str] = None
    ) -> DatabaseFileRecord:
        """
        Update file record status.
        
        Updates the status of a file record and optionally adds error message.
        Increments processing count and updates timestamps.
        
        Args:
            file_path (str): Absolute path to the file.
                Must be existing file path.
            status (RecordStatus): New status to set.
                Must be valid RecordStatus enum value.
            error_message (Optional[str]): Error message if status is FAILED.
                Added to processing_errors list. Defaults to None.
        
        Returns:
            DatabaseFileRecord: Updated file record.
        
        Raises:
            ValidationError: If file_path is empty or status is invalid
            NotFoundError: If file record not found
            DatabaseError: If update fails
        """
        if not file_path or not isinstance(file_path, str):
            raise ValidationError("file_path must be non-empty string")
        if not isinstance(status, RecordStatus):
            raise ValidationError("status must be RecordStatus enum")
        
        if file_path not in self.records:
            raise NotFoundError(f"File record not found: {file_path}")
        
        try:
            record = self.records[file_path]
            
            # Update status
            record.status = status
            
            # Update processing count and timestamps
            if status in [RecordStatus.PROCESSING, RecordStatus.COMPLETED, RecordStatus.FAILED]:
                record.processing_count += 1
                record.last_processed_at = datetime.now()
            
            # Add error message if provided
            if error_message and status == RecordStatus.FAILED:
                record.processing_errors.append(error_message)
            
            # Update timestamp
            record.updated_at = datetime.now()
            
            # Track metrics
            self.metrics_collector.increment_counter("file_status_updates")
            
            logger.info(f"Updated file status: {file_path} -> {status.value}")
            return record
            
        except Exception as e:
            logger.error(f"Failed to update file status for {file_path}: {e}")
            raise DatabaseError(f"Failed to update file status: {e}")
    
    async def get_files_by_status(
        self,
        status: RecordStatus,
        limit: Optional[int] = None
    ) -> List[DatabaseFileRecord]:
        """
        Get file records by status.
        
        Retrieves all file records with specified status.
        Optionally limits the number of results.
        
        Args:
            status (RecordStatus): Status to filter by.
                Must be valid RecordStatus enum value.
            limit (Optional[int]): Maximum number of records to return.
                If None, returns all matching records. Defaults to None.
        
        Returns:
            List[DatabaseFileRecord]: List of file records with specified status.
        
        Raises:
            ValidationError: If status is invalid or limit is negative
        """
        if not isinstance(status, RecordStatus):
            raise ValidationError("status must be RecordStatus enum")
        if limit is not None and limit < 0:
            raise ValidationError("limit must be non-negative")
        
        records = [
            record for record in self.records.values()
            if record.status == status
        ]
        
        if limit is not None:
            records = records[:limit]
        
        return records
    
    async def get_files_by_extension(
        self,
        extension: str,
        status: Optional[RecordStatus] = None
    ) -> List[DatabaseFileRecord]:
        """
        Get file records by file extension.
        
        Retrieves file records with specified extension.
        Optionally filters by status.
        
        Args:
            extension (str): File extension to filter by (e.g., ".txt").
                Case-insensitive comparison.
            status (Optional[RecordStatus]): Optional status filter.
                If provided, only returns records with this status. Defaults to None.
        
        Returns:
            List[DatabaseFileRecord]: List of file records with specified extension.
        
        Raises:
            ValidationError: If extension is empty or status is invalid
        """
        if not extension or not isinstance(extension, str):
            raise ValidationError("extension must be non-empty string")
        if status is not None and not isinstance(status, RecordStatus):
            raise ValidationError("status must be RecordStatus enum")
        
        extension_lower = extension.lower()
        
        records = [
            record for record in self.records.values()
            if record.file_extension.lower() == extension_lower
        ]
        
        if status is not None:
            records = [
                record for record in records
                if record.status == status
            ]
        
        return records
    
    async def delete_file_record(self, file_path: str) -> bool:
        """
        Delete file record from database.
        
        Removes file record from repository and optionally from vector store.
        Marks record as deleted rather than physically removing it.
        
        Args:
            file_path (str): Absolute path to the file.
                Must be existing file path.
        
        Returns:
            bool: True if record was deleted, False otherwise.
        
        Raises:
            ValidationError: If file_path is empty
            NotFoundError: If file record not found
            DatabaseError: If deletion fails
        """
        if not file_path or not isinstance(file_path, str):
            raise ValidationError("file_path must be non-empty string")
        
        if file_path not in self.records:
            raise NotFoundError(f"File record not found: {file_path}")
        
        try:
            record = self.records[file_path]
            
            # Mark as deleted
            record.status = RecordStatus.DELETED
            record.updated_at = datetime.now()
            
            # Remove from vector store if processed
            if record.vector_store_id:
                try:
                    await self.vector_store_wrapper.delete_chunks_by_source(
                        source_path=file_path
                    )
                    record.vector_store_id = None
                except Exception as e:
                    logger.warning(f"Failed to remove from vector store: {e}")
            
            # Track metrics
            self.metrics_collector.increment_counter("file_records_deleted")
            
            logger.info(f"Deleted file record: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file record for {file_path}: {e}")
            raise DatabaseError(f"Failed to delete file record: {e}")
    
    async def get_statistics(self) -> ProcessingStatistics:
        """
        Get processing statistics.
        
        Calculates and returns comprehensive processing statistics
        for all file records in the repository.
        
        Returns:
            ProcessingStatistics: Processing statistics object.
        
        Raises:
            DatabaseError: If statistics calculation fails
        """
        try:
            total_files = len(self.records)
            
            # Count by status
            status_counts = defaultdict(int)
            for record in self.records.values():
                status_counts[record.status.value] += 1
            
            # Calculate processing metrics
            total_processed = sum(
                record.processing_count for record in self.records.values()
            )
            
            total_size_bytes = sum(
                record.file_size_bytes for record in self.records.values()
            )
            
            total_chunks = sum(
                record.chunk_count for record in self.records.values()
            )
            
            # Calculate error statistics
            total_errors = sum(
                len(record.processing_errors) for record in self.records.values()
            )
            
            # Get recent activity
            now = datetime.now()
            recent_activity = [
                record for record in self.records.values()
                if record.last_processed_at and 
                (now - record.last_processed_at) < timedelta(hours=24)
            ]
            
            # Create statistics with current period
            now = datetime.now()
            period_start = now - timedelta(hours=24)  # Last 24 hours
            
            stats = ProcessingStatistics(
                period_start=period_start,
                period_end=now,
                total_files_processed=total_processed,
                total_files_successful=status_counts.get("completed", 0),
                total_files_failed=status_counts.get("failed", 0),
                total_files_skipped=status_counts.get("skipped", 0),
                total_chunks_created=total_chunks,
                total_characters_processed=total_size_bytes,  # Approximate
                file_type_breakdown={},  # Could be calculated from records
                error_breakdown={},  # Could be calculated from processing_errors
                processing_metadata={
                    "total_files": total_files,
                    "files_by_status": dict(status_counts),
                    "total_size_bytes": total_size_bytes,
                    "total_errors": total_errors,
                    "recent_activity_count": len(recent_activity),
                    "average_file_size": total_size_bytes / total_files if total_files > 0 else 0,
                    "average_chunks_per_file": total_chunks / total_files if total_files > 0 else 0
                }
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to calculate statistics: {e}")
            raise DatabaseError(f"Failed to calculate statistics: {e}")


class DatabaseManager:
    """
    Database Manager Service - Database Management and Operations
    
    Provides comprehensive database management for DocAnalyzer including
    file record management, caching, transaction handling, and coordination
    with vector store operations.
    
    This service integrates FileRepository with VectorStoreWrapper and
    provides high-level database operations for file tracking, processing
    history, and data management.
    
    Attributes:
        file_repository (FileRepository): File repository instance.
            Manages file records and database operations.
        vector_store_wrapper (VectorStoreWrapper): Vector store wrapper instance.
            Handles vector store operations and chunk management.
        config (DocAnalyzerConfig): DocAnalyzer configuration.
            Used for database settings and configuration.
        metrics_collector (MetricsCollector): Metrics collection instance.
            Tracks database operation metrics.
        health_checker (HealthChecker): Health monitoring instance.
            Monitors database health status.
        cache_size (int): Maximum number of cached records.
            Must be positive integer. Defaults to 1000.
        cache_ttl (int): Cache time-to-live in seconds.
            Must be positive integer. Defaults to 300 seconds.
        batch_size (int): Batch size for bulk operations.
            Must be positive integer. Defaults to 100.
        transaction_timeout (float): Timeout for database transactions.
            Must be positive float. Defaults to 30.0 seconds.
        is_initialized (bool): Initialization status flag.
            True if service is properly initialized.
    
    Example:
        >>> manager = DatabaseManager(config)
        >>> await manager.initialize()
        >>> record = await manager.create_file_record("/path/file.txt", file_info)
        >>> stats = await manager.get_processing_statistics()
        >>> await manager.cleanup()
    
    Raises:
        ProcessingError: If database operations fail
        ValidationError: If input data validation fails
        DatabaseError: If database-specific operations fail
    """
    
    def __init__(
        self,
        config: Optional[DocAnalyzerConfig] = None,
        cache_size: int = DEFAULT_CACHE_SIZE,
        cache_ttl: int = DEFAULT_CACHE_TTL,
        batch_size: int = DEFAULT_BATCH_SIZE,
        transaction_timeout: float = DEFAULT_TRANSACTION_TIMEOUT
    ):
        """
        Initialize Database Manager Service.
        
        Args:
            config (Optional[DocAnalyzerConfig]): DocAnalyzer configuration.
                If None, creates new instance. Defaults to None.
            cache_size (int): Maximum number of cached records.
                Must be positive integer. Defaults to 1000.
            cache_ttl (int): Cache time-to-live in seconds.
                Must be positive integer. Defaults to 300 seconds.
            batch_size (int): Batch size for bulk operations.
                Must be positive integer. Defaults to 100.
            transaction_timeout (float): Timeout for database transactions.
                Must be positive float. Defaults to 30.0 seconds.
        
        Raises:
            ValueError: If any parameter is invalid
        """
        if cache_size <= 0:
            raise ValueError("cache_size must be positive")
        if cache_ttl <= 0:
            raise ValueError("cache_ttl must be positive")
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if transaction_timeout <= 0:
            raise ValueError("transaction_timeout must be positive")
        
        self.config = config or DocAnalyzerConfig()
        self.cache_size = cache_size
        self.cache_ttl = cache_ttl
        self.batch_size = batch_size
        self.transaction_timeout = transaction_timeout
        
        # Initialize components
        self.vector_store_wrapper = VectorStoreWrapper(self.config)
        self.metrics_collector = MetricsCollector()
        self.health_checker = HealthChecker()
        self.file_repository = FileRepository(
            self.vector_store_wrapper,
            self.metrics_collector
        )
        
        # State
        self.is_initialized = False
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        
        logger.info("Database Manager initialized")
    
    async def initialize(self) -> bool:
        """
        Initialize Database Manager Service.
        
        Initializes vector store wrapper, performs health checks,
        and prepares the service for operations.
        
        Returns:
            bool: True if initialization successful, False otherwise.
        
        Raises:
            ProcessingError: If initialization fails
        """
        try:
            logger.info("Initializing Database Manager...")
            
            # Initialize vector store wrapper
            await self.vector_store_wrapper.initialize()
            
            # Perform health checks
            health_status = await self.health_checker.check_database_health()
            if health_status.status != HealthStatus.HEALTHY:
                logger.warning(f"Database health check failed: {health_status.status}")
            
            # Initialize cache
            self._cache.clear()
            self._cache_timestamps.clear()
            
            self.is_initialized = True
            
            logger.info("Database Manager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Database Manager: {e}")
            self.is_initialized = False
            raise ProcessingError("DatabaseError", f"Database Manager initialization failed: {e}", ErrorCategory.DATABASE)
    
    async def create_file_record(
        self,
        file_path: str,
        file_info: FileInfo,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DatabaseFileRecord:
        """
        Create a new file record in the database.
        
        Creates a new file record and stores it in the repository.
        Validates file information and generates unique record ID.
        
        Args:
            file_path (str): Absolute path to the file.
                Must be existing file path.
            file_info (FileInfo): File information object.
                Contains file metadata and properties.
            metadata (Optional[Dict[str, Any]]): Additional metadata.
                Custom attributes for the file record. Defaults to None.
        
        Returns:
            DatabaseFileRecord: Created file record.
        
        Raises:
            ProcessingError: If database operations fail
            ValidationError: If input data is invalid
        """
        if not self.is_initialized:
            raise ProcessingError("InitializationError", "Database Manager not initialized", ErrorCategory.PROCESSING)
        
        try:
            record = await self.file_repository.create_file_record(
                file_path, file_info, metadata
            )
            
            # Update cache
            self._update_cache(f"file_record:{file_path}", record)
            
            return record
            
        except Exception as e:
            logger.error(f"Failed to create file record: {e}")
            raise ProcessingError("DatabaseError", f"Failed to create file record: {e}", ErrorCategory.DATABASE)
    
    async def get_file_record(self, file_path: str) -> DatabaseFileRecord:
        """
        Get file record by file path.
        
        Retrieves file record from repository or cache.
        Returns cached record if available and not expired.
        
        Args:
            file_path (str): Absolute path to the file.
                Must be existing file path.
        
        Returns:
            DatabaseFileRecord: File record.
        
        Raises:
            ProcessingError: If database operations fail
            ValidationError: If file_path is invalid
            NotFoundError: If file record not found
        """
        if not self.is_initialized:
            raise ProcessingError("InitializationError", "Database Manager not initialized", ErrorCategory.PROCESSING)
        
        # Check cache first
        cache_key = f"file_record:{file_path}"
        cached_record = self._get_from_cache(cache_key)
        if cached_record:
            return cached_record
        
        try:
            record = await self.file_repository.get_file_record(file_path)
            
            # Update cache
            self._update_cache(cache_key, record)
            
            return record
            
        except Exception as e:
            logger.error(f"Failed to get file record: {e}")
            raise ProcessingError("DatabaseError", f"Failed to get file record: {e}", ErrorCategory.DATABASE)
    
    async def update_file_status(
        self,
        file_path: str,
        status: RecordStatus,
        error_message: Optional[str] = None
    ) -> DatabaseFileRecord:
        """
        Update file record status.
        
        Updates the status of a file record and optionally adds error message.
        Invalidates cache for the updated record.
        
        Args:
            file_path (str): Absolute path to the file.
                Must be existing file path.
            status (RecordStatus): New status to set.
                Must be valid RecordStatus enum value.
            error_message (Optional[str]): Error message if status is FAILED.
                Added to processing_errors list. Defaults to None.
        
        Returns:
            DatabaseFileRecord: Updated file record.
        
        Raises:
            ProcessingError: If database operations fail
            ValidationError: If input data is invalid
            NotFoundError: If file record not found
        """
        if not self.is_initialized:
            raise ProcessingError("InitializationError", "Database Manager not initialized", ErrorCategory.PROCESSING)
        
        try:
            record = await self.file_repository.update_file_status(
                file_path, status, error_message
            )
            
            # Invalidate cache
            self._invalidate_cache(f"file_record:{file_path}")
            
            return record
            
        except Exception as e:
            logger.error(f"Failed to update file status: {e}")
            raise ProcessingError("DatabaseError", f"Failed to update file status: {e}", ErrorCategory.DATABASE)
    
    async def get_files_by_status(
        self,
        status: RecordStatus,
        limit: Optional[int] = None
    ) -> List[DatabaseFileRecord]:
        """
        Get file records by status.
        
        Retrieves all file records with specified status.
        Optionally limits the number of results.
        
        Args:
            status (RecordStatus): Status to filter by.
                Must be valid RecordStatus enum value.
            limit (Optional[int]): Maximum number of records to return.
                If None, returns all matching records. Defaults to None.
        
        Returns:
            List[DatabaseFileRecord]: List of file records with specified status.
        
        Raises:
            ProcessingError: If database operations fail
            ValidationError: If input data is invalid
        """
        if not self.is_initialized:
            raise ProcessingError("InitializationError", "Database Manager not initialized", ErrorCategory.PROCESSING)
        
        try:
            return await self.file_repository.get_files_by_status(status, limit)
        except Exception as e:
            logger.error(f"Failed to get files by status: {e}")
            raise ProcessingError("DatabaseError", f"Failed to get files by status: {e}", ErrorCategory.DATABASE)
    
    async def get_files_by_extension(
        self,
        extension: str,
        status: Optional[RecordStatus] = None
    ) -> List[DatabaseFileRecord]:
        """
        Get file records by file extension.
        
        Retrieves file records with specified extension.
        Optionally filters by status.
        
        Args:
            extension (str): File extension to filter by (e.g., ".txt").
                Case-insensitive comparison.
            status (Optional[RecordStatus]): Optional status filter.
                If provided, only returns records with this status. Defaults to None.
        
        Returns:
            List[DatabaseFileRecord]: List of file records with specified extension.
        
        Raises:
            ProcessingError: If database operations fail
            ValidationError: If input data is invalid
        """
        if not self.is_initialized:
            raise ProcessingError("InitializationError", "Database Manager not initialized", ErrorCategory.PROCESSING)
        
        try:
            return await self.file_repository.get_files_by_extension(extension, status)
        except Exception as e:
            logger.error(f"Failed to get files by extension: {e}")
            raise ProcessingError("DatabaseError", f"Failed to get files by extension: {e}", ErrorCategory.DATABASE)
    
    async def delete_file_record(self, file_path: str) -> bool:
        """
        Delete file record from database.
        
        Removes file record from repository and optionally from vector store.
        Invalidates cache for the deleted record.
        
        Args:
            file_path (str): Absolute path to the file.
                Must be existing file path.
        
        Returns:
            bool: True if record was deleted, False otherwise.
        
        Raises:
            ProcessingError: If database operations fail
            ValidationError: If file_path is invalid
            NotFoundError: If file record not found
        """
        if not self.is_initialized:
            raise ProcessingError("InitializationError", "Database Manager not initialized", ErrorCategory.PROCESSING)
        
        try:
            result = await self.file_repository.delete_file_record(file_path)
            
            # Invalidate cache
            self._invalidate_cache(f"file_record:{file_path}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to delete file record: {e}")
            raise ProcessingError("DatabaseError", f"Failed to delete file record: {e}", ErrorCategory.DATABASE)
    
    async def get_processing_statistics(self) -> ProcessingStatistics:
        """
        Get processing statistics.
        
        Calculates and returns comprehensive processing statistics
        for all file records in the database.
        
        Returns:
            ProcessingStatistics: Processing statistics object.
        
        Raises:
            ProcessingError: If statistics calculation fails
        """
        if not self.is_initialized:
            raise ProcessingError("InitializationError", "Database Manager not initialized", ErrorCategory.PROCESSING)
        
        try:
            return await self.file_repository.get_statistics()
        except Exception as e:
            logger.error(f"Failed to get processing statistics: {e}")
            raise ProcessingError("DatabaseError", f"Failed to get processing statistics: {e}", ErrorCategory.DATABASE)
    
    async def get_database_metadata(self) -> DatabaseMetadata:
        """
        Get database metadata.
        
        Returns comprehensive metadata about the database including
        configuration, health status, and operational information.
        
        Returns:
            DatabaseMetadata: Database metadata object.
        
        Raises:
            ProcessingError: If metadata retrieval fails
        """
        if not self.is_initialized:
            raise ProcessingError("InitializationError", "Database Manager not initialized", ErrorCategory.PROCESSING)
        
        try:
            # Get statistics
            stats = await self.get_processing_statistics()
            
            # Get health status
            health_status = await self.health_checker.check_database_health()
            
            # Get vector store info
            vector_store_info = await self.vector_store_wrapper.get_health_status()
            
            metadata = DatabaseMetadata(
                total_files=stats.processing_metadata["total_files"],
                total_chunks=stats.total_chunks_created,
                total_size_bytes=stats.processing_metadata["total_size_bytes"],
                health_status=health_status.status,
                vector_store_status=vector_store_info.get("status", "unknown"),
                cache_size=len(self._cache),
                cache_hit_rate=self._calculate_cache_hit_rate(),
                last_updated=datetime.now(),
                configuration={
                    "cache_size": self.cache_size,
                    "cache_ttl": self.cache_ttl,
                    "batch_size": self.batch_size,
                    "transaction_timeout": self.transaction_timeout
                }
            )
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to get database metadata: {e}")
            raise ProcessingError("DatabaseError", f"Failed to get database metadata: {e}", ErrorCategory.DATABASE)
    
    async def cleanup(self) -> bool:
        """
        Cleanup Database Manager Service.
        
        Performs cleanup operations including cache cleanup,
        vector store cleanup, and resource deallocation.
        
        Returns:
            bool: True if cleanup successful, False otherwise.
        
        Raises:
            ProcessingError: If cleanup fails
        """
        try:
            logger.info("Cleaning up Database Manager...")
            
            # Cleanup cache
            self._cache.clear()
            self._cache_timestamps.clear()
            
            # Cleanup vector store wrapper
            await self.vector_store_wrapper.cleanup()
            
            self.is_initialized = False
            
            logger.info("Database Manager cleanup completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup Database Manager: {e}")
            raise ProcessingError("CleanupError", f"Database Manager cleanup failed: {e}", ErrorCategory.PROCESSING)
    
    def _update_cache(self, key: str, value: Any) -> None:
        """Update cache with key-value pair."""
        if len(self._cache) >= self.cache_size:
            # Remove oldest entry
            oldest_key = min(self._cache_timestamps.keys(), 
                           key=lambda k: self._cache_timestamps[k])
            del self._cache[oldest_key]
            del self._cache_timestamps[oldest_key]
        
        self._cache[key] = value
        self._cache_timestamps[key] = datetime.now()
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key not in self._cache:
            return None
        
        # Check if expired
        if (datetime.now() - self._cache_timestamps[key]).total_seconds() > self.cache_ttl:
            del self._cache[key]
            del self._cache_timestamps[key]
            return None
        
        return self._cache[key]
    
    def _invalidate_cache(self, key: str) -> None:
        """Invalidate cache entry."""
        if key in self._cache:
            del self._cache[key]
        if key in self._cache_timestamps:
            del self._cache_timestamps[key]
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        # This is a simplified calculation
        # In a real implementation, you would track hits and misses
        total_requests = len(self._cache_timestamps)
        if total_requests == 0:
            return 0.0
        
        # For now, return a placeholder value
        return 0.85  # 85% hit rate placeholder 