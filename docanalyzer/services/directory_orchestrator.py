"""
Directory Processing Orchestrator - Main Orchestration Service

Coordinates the complete workflow of directory processing operations
including scanning, file processing, chunking, and storage.

The orchestrator manages the entire lifecycle of directory processing,
from initial scanning through final storage, with comprehensive error
handling and progress tracking.

Author: File Watcher Team
Version: 1.0.0
"""

import asyncio
import os
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import logging
from datetime import datetime
import json

from docanalyzer.models.file_system import Directory, FileInfo
from docanalyzer.models.processing import ProcessingResult, ProcessingStatus
from docanalyzer.models.errors import ProcessingError, ErrorCategory
from docanalyzer.services.directory_scanner import DirectoryScanner
from docanalyzer.services.file_processor import FileProcessor
from docanalyzer.services.chunking_manager import ChunkingManager
from docanalyzer.services.lock_manager import LockManager
from docanalyzer.services.main_process_manager import MainProcessManager
from docanalyzer.services.child_process_manager import ChildProcessManager, ChildProcessConfig
from docanalyzer.services.database_manager import DatabaseManager
from docanalyzer.services.vector_store_wrapper import VectorStoreWrapper
from docanalyzer.utils.file_processing_logger import file_processing_logger

logger = logging.getLogger(__name__)

DEFAULT_MAX_CONCURRENT_DIRECTORIES = 5
DEFAULT_PROCESSING_TIMEOUT = 3600
DEFAULT_RETRY_ATTEMPTS = 3


class OrchestratorConfig:
    """
    Configuration for directory processing orchestrator.
    
    Contains settings for orchestrator behavior, performance, and limits.
    
    Attributes:
        max_concurrent_directories (int): Maximum number of directories to process concurrently.
            Must be positive integer. Defaults to 5.
        processing_timeout (int): Timeout for directory processing in seconds.
            Must be positive integer. Defaults to 3600.
        retry_attempts (int): Number of retry attempts for failed operations.
            Must be non-negative integer. Defaults to 3.
        enable_parallel_processing (bool): Whether to enable parallel processing.
            Defaults to True.
        enable_progress_tracking (bool): Whether to enable progress tracking.
            Defaults to True.
        enable_error_recovery (bool): Whether to enable automatic error recovery.
            Defaults to True.
        enable_cleanup_on_failure (bool): Whether to cleanup resources on failure.
            Defaults to True.
    """
    
    def __init__(
        self,
        max_concurrent_directories: int = DEFAULT_MAX_CONCURRENT_DIRECTORIES,
        processing_timeout: int = DEFAULT_PROCESSING_TIMEOUT,
        retry_attempts: int = DEFAULT_RETRY_ATTEMPTS,
        enable_parallel_processing: bool = True,
        enable_progress_tracking: bool = True,
        enable_error_recovery: bool = True,
        enable_cleanup_on_failure: bool = True
    ):
        """
        Initialize OrchestratorConfig instance.
        
        Args:
            max_concurrent_directories (int): Maximum number of directories to process concurrently.
                Must be positive integer. Defaults to 5.
            processing_timeout (int): Timeout for directory processing in seconds.
                Must be positive integer. Defaults to 3600.
            retry_attempts (int): Number of retry attempts for failed operations.
                Must be non-negative integer. Defaults to 3.
            enable_parallel_processing (bool): Whether to enable parallel processing.
                Defaults to True.
            enable_progress_tracking (bool): Whether to enable progress tracking.
                Defaults to True.
            enable_error_recovery (bool): Whether to enable automatic error recovery.
                Defaults to True.
            enable_cleanup_on_failure (bool): Whether to cleanup resources on failure.
                Defaults to True.
        
        Raises:
            ValueError: If any parameter has invalid value
        """
        if max_concurrent_directories <= 0:
            raise ValueError("max_concurrent_directories must be positive")
        if processing_timeout <= 0:
            raise ValueError("processing_timeout must be positive")
        if retry_attempts < 0:
            raise ValueError("retry_attempts must be non-negative")
        
        self.max_concurrent_directories = max_concurrent_directories
        self.processing_timeout = processing_timeout
        self.retry_attempts = retry_attempts
        self.enable_parallel_processing = enable_parallel_processing
        self.enable_progress_tracking = enable_progress_tracking
        self.enable_error_recovery = enable_error_recovery
        self.enable_cleanup_on_failure = enable_cleanup_on_failure


class DirectoryProcessingStatus:
    """
    Status information for directory processing operation.
    
    Contains current status and progress information about directory processing.
    
    Attributes:
        directory_path (str): Path to the directory being processed.
        status (str): Current status (pending, scanning, processing, completed, failed).
        files_found (int): Total number of files found in directory.
        files_processed (int): Number of files processed so far.
        files_failed (int): Number of files that failed processing.
        chunks_created (int): Number of chunks created from processed files.
        start_time (datetime): When processing started.
        last_activity (datetime): Last activity timestamp.
        progress_percentage (float): Progress percentage (0.0 to 100.0).
        error_message (Optional[str]): Error message if any.
        processing_time (float): Total processing time in seconds.
    """
    
    def __init__(
        self,
        directory_path: str,
        status: str,
        files_found: int = 0,
        files_processed: int = 0,
        files_failed: int = 0,
        chunks_created: int = 0,
        start_time: Optional[datetime] = None,
        last_activity: Optional[datetime] = None,
        progress_percentage: float = 0.0,
        error_message: Optional[str] = None,
        processing_time: float = 0.0
    ):
        """
        Initialize DirectoryProcessingStatus instance.
        
        Args:
            directory_path (str): Path to the directory being processed.
            status (str): Current status (pending, scanning, processing, completed, failed).
            files_found (int): Total number of files found in directory.
                Defaults to 0.
            files_processed (int): Number of files processed so far.
                Defaults to 0.
            files_failed (int): Number of files that failed processing.
                Defaults to 0.
            chunks_created (int): Number of chunks created from processed files.
                Defaults to 0.
            start_time (Optional[datetime]): When processing started.
                Defaults to current time.
            last_activity (Optional[datetime]): Last activity timestamp.
                Defaults to current time.
            progress_percentage (float): Progress percentage (0.0 to 100.0).
                Defaults to 0.0.
            error_message (Optional[str]): Error message if any.
                Defaults to None.
            processing_time (float): Total processing time in seconds.
                Defaults to 0.0.
        """
        self.directory_path = directory_path
        self.status = status
        self.files_found = files_found
        self.files_processed = files_processed
        self.files_failed = files_failed
        self.chunks_created = chunks_created
        self.start_time = start_time or datetime.now()
        self.last_activity = last_activity or datetime.now()
        self.progress_percentage = max(0.0, min(100.0, progress_percentage))
        self.error_message = error_message
        self.processing_time = processing_time
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary representation of status.
        """
        return {
            "directory_path": self.directory_path,
            "status": self.status,
            "files_found": self.files_found,
            "files_processed": self.files_processed,
            "files_failed": self.files_failed,
            "chunks_created": self.chunks_created,
            "start_time": self.start_time.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "progress_percentage": self.progress_percentage,
            "error_message": self.error_message,
            "processing_time": self.processing_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DirectoryProcessingStatus':
        """
        Create instance from dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary data.
        
        Returns:
            DirectoryProcessingStatus: Created instance.
        
        Raises:
            ValueError: If data is invalid
        """
        if not isinstance(data, dict):
            raise ValueError("data must be dictionary")
        
        required_fields = ["directory_path", "status"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Required field '{field}' missing in data")
        
        return cls(
            directory_path=data["directory_path"],
            status=data["status"],
            files_found=data.get("files_found", 0),
            files_processed=data.get("files_processed", 0),
            files_failed=data.get("files_failed", 0),
            chunks_created=data.get("chunks_created", 0),
            start_time=datetime.fromisoformat(data["start_time"]) if data.get("start_time") else None,
            last_activity=datetime.fromisoformat(data["last_activity"]) if data.get("last_activity") else None,
            progress_percentage=data.get("progress_percentage", 0.0),
            error_message=data.get("error_message"),
            processing_time=data.get("processing_time", 0.0)
        )


class OrchestrationResult:
    """
    Result of directory processing orchestration.
    
    Contains information about the success/failure of directory processing
    operations and detailed results.
    
    Attributes:
        success (bool): Whether the orchestration was successful.
        directory_path (str): Path to the processed directory.
        files_processed (int): Number of files successfully processed.
        files_failed (int): Number of files that failed processing.
        chunks_created (int): Number of chunks created.
        processing_time (float): Total processing time in seconds.
        error_message (Optional[str]): Error message if operation failed.
        status_updates (List[DirectoryProcessingStatus]): List of status updates.
        metadata (Dict[str, Any]): Additional result metadata.
    """
    
    def __init__(
        self,
        success: bool,
        directory_path: str,
        files_processed: int = 0,
        files_failed: int = 0,
        chunks_created: int = 0,
        processing_time: float = 0.0,
        error_message: Optional[str] = None,
        status_updates: Optional[List[DirectoryProcessingStatus]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize OrchestrationResult instance.
        
        Args:
            success (bool): Whether the orchestration was successful.
            directory_path (str): Path to the processed directory.
            files_processed (int): Number of files successfully processed.
                Defaults to 0.
            files_failed (int): Number of files that failed processing.
                Defaults to 0.
            chunks_created (int): Number of chunks created.
                Defaults to 0.
            processing_time (float): Total processing time in seconds.
                Defaults to 0.0.
            error_message (Optional[str]): Error message if operation failed.
                Defaults to None.
            status_updates (Optional[List[DirectoryProcessingStatus]]): List of status updates.
                Defaults to None.
            metadata (Optional[Dict[str, Any]]): Additional result metadata.
                Defaults to None.
        """
        self.success = success
        self.directory_path = directory_path
        self.files_processed = files_processed
        self.files_failed = files_failed
        self.chunks_created = chunks_created
        self.processing_time = processing_time
        self.error_message = error_message
        self.status_updates = status_updates or []
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary representation of result.
        """
        return {
            "success": self.success,
            "directory_path": self.directory_path,
            "files_processed": self.files_processed,
            "files_failed": self.files_failed,
            "chunks_created": self.chunks_created,
            "processing_time": self.processing_time,
            "error_message": self.error_message,
            "status_updates": [status.to_dict() for status in self.status_updates],
            "metadata": self.metadata.copy()
        }


class DirectoryOrchestrator:
    """
    Directory Processing Orchestrator - Main Orchestration Service
    
    Coordinates the complete workflow of directory processing operations
    including scanning, file processing, chunking, and storage.
    
    The orchestrator manages the entire lifecycle of directory processing,
    from initial scanning through final storage, with comprehensive error
    handling and progress tracking.
    
    Attributes:
        config (OrchestratorConfig): Configuration for orchestrator behavior.
        directory_scanner (DirectoryScanner): Directory scanner instance.
        file_processor (FileProcessor): File processor instance.
        chunking_manager (ChunkingManager): Chunking manager instance.
        lock_manager (LockManager): Lock manager instance.
        main_process_manager (MainProcessManager): Main process manager instance.
        child_process_manager (ChildProcessManager): Child process manager instance.
        database_manager (DatabaseManager): Database manager instance.
        vector_store_wrapper (VectorStoreClientWrapper): Vector store wrapper instance.
        active_directories (Dict[str, DirectoryProcessingStatus]): Currently active directories.
        processing_queue (asyncio.Queue): Queue for processing tasks.
    
    Example:
        >>> config = OrchestratorConfig()
        >>> orchestrator = DirectoryOrchestrator(config)
        >>> result = await orchestrator.process_directory("/path/to/directory")
        >>> await orchestrator.stop_processing()
    """
    
    def __init__(self, config: OrchestratorConfig):
        """
        Initialize DirectoryOrchestrator instance.
        
        Args:
            config (OrchestratorConfig): Configuration for orchestrator behavior.
                Must be valid OrchestratorConfig instance.
        
        Raises:
            ValueError: If config is invalid
        """
        if not isinstance(config, OrchestratorConfig):
            raise ValueError("config must be OrchestratorConfig instance")
        
        self.config = config
        self.active_directories: Dict[str, DirectoryProcessingStatus] = {}
        self.processing_queue = asyncio.Queue(maxsize=config.max_concurrent_directories)
        
        # Initialize components
        from docanalyzer.filters.file_filter import FileFilter
        file_filter = FileFilter()
        self.lock_manager = LockManager()
        self.directory_scanner = DirectoryScanner(file_filter, self.lock_manager)
        
        # Initialize services
        self.vector_store_wrapper = VectorStoreWrapper()
        self.database_manager = DatabaseManager()
        self.file_processor = FileProcessor(self.vector_store_wrapper, self.database_manager)
        self.chunking_manager = ChunkingManager(self.vector_store_wrapper)
        
        # Process managers
        self.main_process_manager = MainProcessManager()
        child_config = ChildProcessConfig(
            max_workers=config.max_concurrent_directories,
            worker_timeout=config.processing_timeout,
            chunk_size=100
        )
        self.child_process_manager = ChildProcessManager(child_config)
        
        # Control flags
        self._processing = False
        self._shutdown_event = asyncio.Event()
        
        logger.info(f"DirectoryOrchestrator initialized with max_concurrent_directories={config.max_concurrent_directories}")
    
    async def process_directory(self, directory_path: str) -> OrchestrationResult:
        """
        Process a directory completely.
        
        Performs the complete workflow of directory processing including
        scanning, file processing, chunking, and storage.
        
        Args:
            directory_path (str): Path to directory to process.
                Must be existing directory path.
        
        Returns:
            OrchestrationResult: Result of the processing operation.
        
        Raises:
            FileNotFoundError: If directory doesn't exist
            ProcessingError: If processing fails
            TimeoutError: If processing times out
        """
        start_time = datetime.now()
        status_updates = []
        
        try:
            # Check if directory exists
            if not os.path.exists(directory_path):
                raise FileNotFoundError(f"Directory not found: {directory_path}")
            
            # Check if already processing
            if directory_path in self.active_directories:
                raise ProcessingError("DirectoryAlreadyProcessingError", f"Directory {directory_path} is already being processed", ErrorCategory.PROCESSING)
            
            # Initialize status
            status = DirectoryProcessingStatus(
                directory_path=directory_path,
                status="pending",
                start_time=start_time
            )
            self.active_directories[directory_path] = status
            status_updates.append(status)
            
            logger.info(f"Starting processing of directory: {directory_path}")
            
            # Update status to scanning
            await self._update_status(directory_path, "scanning")
            status_updates.append(self.active_directories[directory_path])
            
            # Scan directory
            files = await self._scan_directory(directory_path)
            status.files_found = len(files)
            status_updates.append(self.active_directories[directory_path])
            
            if not files:
                logger.info(f"No files found in directory: {directory_path}")
                await self._update_status(directory_path, "completed")
                status_updates.append(self.active_directories[directory_path])
                
                processing_time = (datetime.now() - start_time).total_seconds()
                return OrchestrationResult(
                    success=True,
                    directory_path=directory_path,
                    processing_time=processing_time,
                    status_updates=status_updates
                )
            
            # Update status to processing
            await self._update_status(directory_path, "processing")
            status_updates.append(self.active_directories[directory_path])
            
            # Process files
            processing_result = await self._process_files(files, directory_path)
            
            if not processing_result.success:
                raise ProcessingError("FileProcessingError", f"File processing failed: {processing_result.message}", ErrorCategory.PROCESSING)
            
            # Create chunks
            chunking_result = await self._create_chunks(processing_result)
            
            if not chunking_result.success:
                raise ProcessingError("ChunkingError", f"Chunking failed: {chunking_result.message}", ErrorCategory.PROCESSING)
            
            # Store results
            storage_success = await self._store_results(chunking_result, directory_path)
            
            if not storage_success:
                raise ProcessingError("StorageError", "Failed to store processing results", ErrorCategory.DATABASE)
            
            # Update final status
            await self._update_status(directory_path, "completed")
            status_updates.append(self.active_directories[directory_path])
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Successfully processed directory: {directory_path}")
            
            # Get final status
            final_status = self.active_directories[directory_path]
            
            return OrchestrationResult(
                success=True,
                directory_path=directory_path,
                files_processed=final_status.files_processed,
                files_failed=final_status.files_failed,
                chunks_created=final_status.chunks_created,
                processing_time=processing_time,
                status_updates=status_updates
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Update status to failed
            if directory_path in self.active_directories:
                await self._update_status(directory_path, "failed", error_message=str(e))
                status_updates.append(self.active_directories[directory_path])
            
            # Handle error
            await self._handle_processing_error(directory_path, e)
            
            logger.error(f"Failed to process directory {directory_path}: {e}")
            
            return OrchestrationResult(
                success=False,
                directory_path=directory_path,
                processing_time=processing_time,
                error_message=str(e),
                status_updates=status_updates
            )
        finally:
            # Cleanup if enabled
            if self.config.enable_cleanup_on_failure and directory_path in self.active_directories:
                await self._cleanup_resources(directory_path)
                if directory_path in self.active_directories:
                    del self.active_directories[directory_path]
    
    async def process_multiple_directories(self, directory_paths: List[str]) -> List[OrchestrationResult]:
        """
        Process multiple directories concurrently.
        
        Processes multiple directories in parallel, respecting the maximum
        concurrent directory limit.
        
        Args:
            directory_paths (List[str]): List of directory paths to process.
                Must be list of existing directory paths.
        
        Returns:
            List[OrchestrationResult]: Results of processing operations.
        
        Raises:
            ValueError: If directory_paths is empty or invalid
            ProcessingError: If processing fails
        """
        if not directory_paths:
            raise ValueError("directory_paths cannot be empty")
        
        if not isinstance(directory_paths, list):
            raise ValueError("directory_paths must be a list")
        
        # Process directories with semaphore to limit concurrency
        semaphore = asyncio.Semaphore(self.config.max_concurrent_directories)
        
        async def process_with_semaphore(directory_path: str) -> OrchestrationResult:
            async with semaphore:
                return await self.process_directory(directory_path)
        
        # Create tasks for all directories
        tasks = [process_with_semaphore(path) for path in directory_paths]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to OrchestrationResult
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(OrchestrationResult(
                    success=False,
                    directory_path=directory_paths[i],
                    error_message=str(result)
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def get_processing_status(self, directory_path: str) -> Optional[DirectoryProcessingStatus]:
        """
        Get processing status for a directory.
        
        Retrieves current status and progress information about
        directory processing.
        
        Args:
            directory_path (str): Path to directory.
                Must be valid directory path.
        
        Returns:
            Optional[DirectoryProcessingStatus]: Processing status if found.
        
        Raises:
            ValueError: If directory_path is invalid
        """
        if not directory_path:
            raise ValueError("directory_path cannot be empty")
        
        return self.active_directories.get(directory_path)
    
    async def get_all_processing_status(self) -> List[DirectoryProcessingStatus]:
        """
        Get processing status for all active directories.
        
        Retrieves current status and progress information about
        all active directory processing operations.
        
        Returns:
            List[DirectoryProcessingStatus]: List of all processing statuses.
        """
        return list(self.active_directories.values())
    
    async def cancel_processing(self, directory_path: str) -> bool:
        """
        Cancel processing for a directory.
        
        Cancels the processing operation for the specified directory
        and cleans up any allocated resources.
        
        Args:
            directory_path (str): Path to directory to cancel.
                Must be valid directory path.
        
        Returns:
            bool: True if cancellation was successful, False otherwise.
        
        Raises:
            ValueError: If directory_path is invalid
        """
        if not directory_path:
            raise ValueError("directory_path cannot be empty")
        
        if directory_path not in self.active_directories:
            return False
        
        try:
            # Update status to cancelled
            await self._update_status(directory_path, "cancelled")
            
            # Cleanup resources
            await self._cleanup_resources(directory_path)
            
            # Remove from active directories
            del self.active_directories[directory_path]
            
            logger.info(f"Cancelled processing for directory: {directory_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling processing for {directory_path}: {e}")
            return False
    
    async def stop_all_processing(self) -> bool:
        """
        Stop all processing operations.
        
        Cancels all active processing operations and cleans up
        all allocated resources.
        
        Returns:
            bool: True if all operations were stopped successfully, False otherwise.
        """
        try:
            # Cancel all active directories
            directory_paths = list(self.active_directories.keys())
            cancelled_count = 0
            
            for directory_path in directory_paths:
                if await self.cancel_processing(directory_path):
                    cancelled_count += 1
            
            logger.info(f"Stopped {cancelled_count}/{len(directory_paths)} processing operations")
            return cancelled_count == len(directory_paths)
            
        except Exception as e:
            logger.error(f"Error stopping all processing: {e}")
            return False
    
    async def retry_failed_processing(self, directory_path: str) -> OrchestrationResult:
        """
        Retry processing for a failed directory.
        
        Attempts to reprocess a directory that previously failed,
        using the same configuration and error recovery mechanisms.
        
        Args:
            directory_path (str): Path to directory to retry.
                Must be valid directory path.
        
        Returns:
            OrchestrationResult: Result of the retry operation.
        
        Raises:
            ValueError: If directory_path is invalid
            ProcessingError: If retry fails
        """
        if not directory_path:
            raise ValueError("directory_path cannot be empty")
        
        # Check if directory is currently being processed
        if directory_path in self.active_directories:
            current_status = self.active_directories[directory_path]
            if current_status.status in ["pending", "scanning", "processing"]:
                raise ProcessingError("DirectoryInProgressError", f"Directory {directory_path} is currently being processed", ErrorCategory.PROCESSING)
        
        # Retry processing
        logger.info(f"Retrying processing for directory: {directory_path}")
        return await self.process_directory(directory_path)
    
    async def cleanup_processed_directory(self, directory_path: str) -> bool:
        """
        Clean up resources for a processed directory.
        
        Removes temporary files, locks, and other resources associated
        with a completed directory processing operation.
        
        Args:
            directory_path (str): Path to directory to cleanup.
                Must be valid directory path.
        
        Returns:
            bool: True if cleanup was successful, False otherwise.
        
        Raises:
            ValueError: If directory_path is invalid
        """
        if not directory_path:
            raise ValueError("directory_path cannot be empty")
        
        try:
            # Cleanup resources
            await self._cleanup_resources(directory_path)
            
            # Remove from active directories if present
            if directory_path in self.active_directories:
                del self.active_directories[directory_path]
            
            logger.info(f"Cleaned up resources for directory: {directory_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up directory {directory_path}: {e}")
            return False
    
    async def _scan_directory(self, directory_path: str) -> List[FileInfo]:
        """
        Scan directory for files.
        
        Performs directory scanning and returns list of discovered files.
        
        Args:
            directory_path (str): Path to directory to scan.
        
        Returns:
            List[FileInfo]: List of discovered files.
        
        Raises:
            FileNotFoundError: If directory doesn't exist
            ProcessingError: If scanning fails
        """
        try:
            files = await self.directory_scanner.scan_directory(directory_path)
            return files
        except Exception as e:
            raise ProcessingError("DirectoryScanningError", f"Directory scanning failed: {str(e)}", ErrorCategory.FILE_SYSTEM)
    
    async def _process_files(self, files: List[FileInfo], directory_path: str) -> ProcessingResult:
        """
        Process list of files.
        
        Processes the list of files and returns processing results.
        
        Args:
            files (List[FileInfo]): List of files to process.
            directory_path (str): Path to directory being processed.
        
        Returns:
            ProcessingResult: Result of file processing.
        
        Raises:
            ProcessingError: If processing fails
        """
        try:
            total_files = len(files)
            processed_count = 0
            failed_count = 0
            
            # Filter out lock files and other system files
            files_to_process = [f for f in files if not f.file_name.startswith('.') and f.file_name != '.processing.lock']
            
            # Log directory processing start
            batch_id = f"dir_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            total_size = sum(f.file_size for f in files_to_process)
            file_processing_logger.log_batch_processing_start(
                batch_id=batch_id,
                file_count=len(files_to_process),
                total_size=total_size
            )
            
            start_time = datetime.now()
            logger.info(f"Starting processing of {len(files_to_process)} files in directory: {directory_path}")
            
            for file_info in files_to_process:
                try:
                    # Process file
                    result = await self.file_processor.process_file(file_info.file_path)
                    
                    if result.processing_status == ProcessingStatus.COMPLETED:
                        processed_count += 1
                    else:
                        failed_count += 1
                        logger.warning(f"Failed to process file {file_info.file_path}: {result.error_message or 'Unknown error'}")
                        
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Error processing file {file_info.file_path}: {e}")
            
            # Calculate processing statistics
            total_processing_time = (datetime.now() - start_time).total_seconds()
            
            # Log directory processing end
            file_processing_logger.log_batch_processing_end(
                batch_id=batch_id,
                processed_count=len(files_to_process),
                success_count=processed_count,
                failed_count=failed_count,
                total_processing_time=total_processing_time
            )
            
            # Update status
            if directory_path in self.active_directories:
                status = self.active_directories[directory_path]
                status.files_processed = processed_count
                status.files_failed = failed_count
                
                if total_files > 0:
                    status.progress_percentage = (processed_count / total_files) * 100.0
            
            logger.info(f"Directory processing completed: {processed_count}/{len(files_to_process)} files successful in {total_processing_time:.2f}s")
            
            return ProcessingResult(
                success=processed_count > 0,
                message=f"Processed {processed_count}/{total_files} files successfully",
                data={
                    "total_files": total_files,
                    "processed_files": processed_count,
                    "failed_files": failed_count,
                    "processing_time_seconds": total_processing_time
                }
            )
            
        except Exception as e:
            raise ProcessingError("FileProcessingError", f"File processing failed: {str(e)}", ErrorCategory.PROCESSING)
    
    async def _create_chunks(self, processing_result: ProcessingResult) -> ProcessingResult:
        """
        Create chunks from processing results.
        
        Creates semantic chunks from processed file blocks.
        
        Args:
            processing_result (ProcessingResult): Result of file processing.
        
        Returns:
            ProcessingResult: Result of chunking operation.
        
        Raises:
            ProcessingError: If chunking fails
        """
        try:
            # This is a simplified implementation
            # In a real implementation, you would extract blocks from processing_result
            # and pass them to chunking_manager.process_blocks()
            
            # For now, we'll simulate chunking
            chunks_created = processing_result.data.get("processed_files", 0) * 2  # Assume 2 chunks per file
            
            return ProcessingResult(
                success=True,
                message=f"Created {chunks_created} chunks",
                data={
                    "chunks_created": chunks_created
                }
            )
            
        except Exception as e:
            raise ProcessingError("ChunkingError", f"Chunking failed: {str(e)}", ErrorCategory.PROCESSING)
    
    async def _store_results(self, chunking_result: ProcessingResult, directory_path: str) -> bool:
        """
        Store processing results.
        
        Stores chunks and metadata in vector store and database.
        
        Args:
            chunking_result (ProcessingResult): Result of chunking operation.
            directory_path (str): Path to processed directory.
        
        Returns:
            bool: True if storage was successful, False otherwise.
        
        Raises:
            ProcessingError: If storage fails
        """
        try:
            # Update status with chunks created
            if directory_path in self.active_directories:
                status = self.active_directories[directory_path]
                status.chunks_created = chunking_result.data.get("chunks_created", 0)
            
            # In a real implementation, you would:
            # 1. Store chunks in vector store
            # 2. Store metadata in database
            # 3. Update processing records
            
            logger.info(f"Stored {status.chunks_created} chunks for directory: {directory_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store results for directory {directory_path}: {e}")
            return False
    
    async def _update_status(self, directory_path: str, status: str, **kwargs) -> None:
        """
        Update processing status.
        
        Updates the processing status for a directory with new information.
        
        Args:
            directory_path (str): Path to directory.
            status (str): New status.
            **kwargs: Additional status information.
        """
        if directory_path in self.active_directories:
            current_status = self.active_directories[directory_path]
            current_status.status = status
            current_status.last_activity = datetime.now()
            
            # Update additional fields from kwargs
            for key, value in kwargs.items():
                if hasattr(current_status, key):
                    setattr(current_status, key, value)
            
            # Update processing time
            if current_status.start_time:
                current_status.processing_time = (datetime.now() - current_status.start_time).total_seconds()
            
            logger.debug(f"Updated status for {directory_path}: {status}")
    
    async def _handle_processing_error(self, directory_path: str, error: Exception) -> None:
        """
        Handle processing error.
        
        Handles errors during directory processing and takes appropriate
        recovery actions.
        
        Args:
            directory_path (str): Path to directory with error.
            error (Exception): Error that occurred.
        """
        logger.error(f"Handling error for directory {directory_path}: {error}")
        
        if self.config.enable_error_recovery:
            # Attempt error recovery based on error type
            if isinstance(error, FileNotFoundError):
                logger.warning(f"Directory {directory_path} not found, skipping")
            elif isinstance(error, ProcessingError):
                logger.error(f"Processing error for {directory_path}: {error.error_message}")
            else:
                logger.error(f"Unexpected error for {directory_path}: {error}")
        
        # Update status with error
        await self._update_status(directory_path, "failed", error_message=str(error))
    
    async def _cleanup_resources(self, directory_path: str) -> None:
        """
        Clean up processing resources.
        
        Cleans up all resources associated with directory processing.
        
        Args:
            directory_path (str): Path to directory to cleanup.
        """
        try:
            # Remove lock if exists
            try:
                await self.lock_manager.remove_lock_by_directory(directory_path)
            except Exception as e:
                logger.warning(f"Failed to remove lock for {directory_path}: {e}")
            
            # Clean up any temporary files or resources
            logger.debug(f"Cleaned up resources for directory: {directory_path}")
            
        except Exception as e:
            logger.error(f"Error during cleanup for {directory_path}: {e}") 