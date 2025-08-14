"""
Directory Scanner Worker - Child Process for Directory Scanning

Implements a worker process that performs directory scanning operations
in isolation from the main process.

The worker process handles directory scanning, file processing, and
result communication back to the parent process through IPC mechanisms.

Author: File Watcher Team
Version: 1.0.0
"""

import asyncio
import multiprocessing
import signal
import sys
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import logging
from datetime import datetime
import json
import os

from docanalyzer.models.file_system import Directory, FileInfo
from docanalyzer.services.directory_scanner import DirectoryScanner
from docanalyzer.services.lock_manager import LockManager
from docanalyzer.services.file_processor import FileProcessor
from docanalyzer.services.chunking_manager import ChunkingManager
from docanalyzer.models.processing import ProcessingResult
from docanalyzer.models.errors import ProcessingError, ErrorCategory
from docanalyzer.services.process_communication import ProcessCommunication, ProcessCommunicationConfig

logger = logging.getLogger(__name__)

DEFAULT_SCAN_TIMEOUT = 600
DEFAULT_BATCH_SIZE = 50
DEFAULT_PROGRESS_INTERVAL = 10


class WorkerConfig:
    """
    Configuration for directory scanner worker.
    
    Contains settings for worker process behavior and performance.
    
    Attributes:
        scan_timeout (int): Timeout for scanning operations in seconds.
            Must be positive integer. Defaults to 600.
        batch_size (int): Number of files to process in each batch.
            Must be positive integer. Defaults to 50.
        progress_interval (int): Interval for progress updates in seconds.
            Must be positive integer. Defaults to 10.
        enable_detailed_logging (bool): Whether to enable detailed logging.
            Defaults to True.
        enable_progress_reports (bool): Whether to enable progress reporting.
            Defaults to True.
        max_retry_attempts (int): Maximum number of retry attempts for failed operations.
            Must be non-negative integer. Defaults to 3.
    """
    
    def __init__(
        self,
        scan_timeout: int = DEFAULT_SCAN_TIMEOUT,
        batch_size: int = DEFAULT_BATCH_SIZE,
        progress_interval: int = DEFAULT_PROGRESS_INTERVAL,
        enable_detailed_logging: bool = True,
        enable_progress_reports: bool = True,
        max_retry_attempts: int = 3
    ):
        """
        Initialize WorkerConfig instance.
        
        Args:
            scan_timeout (int): Timeout for scanning operations in seconds.
                Must be positive integer. Defaults to 600.
            batch_size (int): Number of files to process in each batch.
                Must be positive integer. Defaults to 50.
            progress_interval (int): Interval for progress updates in seconds.
                Must be positive integer. Defaults to 10.
            enable_detailed_logging (bool): Whether to enable detailed logging.
                Defaults to True.
            enable_progress_reports (bool): Whether to enable progress reporting.
                Defaults to True.
            max_retry_attempts (int): Maximum number of retry attempts for failed operations.
                Must be non-negative integer. Defaults to 3.
        
        Raises:
            ValueError: If any parameter has invalid value
        """
        if scan_timeout <= 0:
            raise ValueError("scan_timeout must be positive")
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if progress_interval <= 0:
            raise ValueError("progress_interval must be positive")
        if max_retry_attempts < 0:
            raise ValueError("max_retry_attempts must be non-negative")
        
        self.scan_timeout = scan_timeout
        self.batch_size = batch_size
        self.progress_interval = progress_interval
        self.enable_detailed_logging = enable_detailed_logging
        self.enable_progress_reports = enable_progress_reports
        self.max_retry_attempts = max_retry_attempts


class WorkerStatus:
    """
    Status information for directory scanner worker.
    
    Contains current status and progress information about the worker process.
    
    Attributes:
        worker_id (int): Unique identifier for the worker.
        status (str): Current status (idle, scanning, processing, completed, failed).
        directory_path (str): Directory being scanned.
        files_found (int): Total number of files found.
        files_processed (int): Number of files processed so far.
        files_failed (int): Number of files that failed processing.
        start_time (datetime): When scanning started.
        last_activity (datetime): Last activity timestamp.
        progress_percentage (float): Progress percentage (0.0 to 100.0).
        error_message (Optional[str]): Error message if any.
    """
    
    def __init__(
        self,
        worker_id: int,
        status: str,
        directory_path: str,
        files_found: int = 0,
        files_processed: int = 0,
        files_failed: int = 0,
        start_time: Optional[datetime] = None,
        last_activity: Optional[datetime] = None,
        progress_percentage: float = 0.0,
        error_message: Optional[str] = None
    ):
        """
        Initialize WorkerStatus instance.
        
        Args:
            worker_id (int): Unique identifier for the worker.
            status (str): Current status (idle, scanning, processing, completed, failed).
            directory_path (str): Directory being scanned.
            files_found (int): Total number of files found.
                Defaults to 0.
            files_processed (int): Number of files processed so far.
                Defaults to 0.
            files_failed (int): Number of files that failed processing.
                Defaults to 0.
            start_time (Optional[datetime]): When scanning started.
                Defaults to current time.
            last_activity (Optional[datetime]): Last activity timestamp.
                Defaults to current time.
            progress_percentage (float): Progress percentage (0.0 to 100.0).
                Defaults to 0.0.
            error_message (Optional[str]): Error message if any.
                Defaults to None.
        """
        self.worker_id = worker_id
        self.status = status
        self.directory_path = directory_path
        self.files_found = files_found
        self.files_processed = files_processed
        self.files_failed = files_failed
        self.start_time = start_time or datetime.now()
        self.last_activity = last_activity or datetime.now()
        self.progress_percentage = max(0.0, min(100.0, progress_percentage))
        self.error_message = error_message
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary representation of status.
        """
        return {
            "worker_id": self.worker_id,
            "status": self.status,
            "directory_path": self.directory_path,
            "files_found": self.files_found,
            "files_processed": self.files_processed,
            "files_failed": self.files_failed,
            "start_time": self.start_time.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "progress_percentage": self.progress_percentage,
            "error_message": self.error_message
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkerStatus':
        """
        Create instance from dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary data.
        
        Returns:
            WorkerStatus: Created instance.
        
        Raises:
            ValueError: If data is invalid
        """
        if not isinstance(data, dict):
            raise ValueError("data must be dictionary")
        
        required_fields = ["worker_id", "status", "directory_path"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Required field '{field}' missing in data")
        
        return cls(
            worker_id=data["worker_id"],
            status=data["status"],
            directory_path=data["directory_path"],
            files_found=data.get("files_found", 0),
            files_processed=data.get("files_processed", 0),
            files_failed=data.get("files_failed", 0),
            start_time=datetime.fromisoformat(data["start_time"]) if data.get("start_time") else None,
            last_activity=datetime.fromisoformat(data["last_activity"]) if data.get("last_activity") else None,
            progress_percentage=data.get("progress_percentage", 0.0),
            error_message=data.get("error_message")
        )


class DirectoryScannerWorker:
    """
    Directory Scanner Worker - Child Process for Directory Scanning
    
    Implements a worker process that performs directory scanning operations
    in isolation from the main process.
    
    The worker process handles directory scanning, file processing, and
    result communication back to the parent process through IPC mechanisms.
    
    Attributes:
        config (WorkerConfig): Configuration for worker behavior.
        communication (ProcessCommunication): Communication interface.
        directory_scanner (DirectoryScanner): Directory scanner instance.
        lock_manager (LockManager): Lock manager instance.
        file_processor (FileProcessor): File processor instance.
        chunking_manager (ChunkingManager): Chunking manager instance.
        status (WorkerStatus): Current worker status.
        worker_id (int): Unique identifier for this worker.
    
    Example:
        >>> config = WorkerConfig()
        >>> worker = DirectoryScannerWorker(config)
        >>> await worker.start_scanning("/path/to/directory")
        >>> await worker.stop_scanning()
    """
    
    def __init__(self, config: WorkerConfig):
        """
        Initialize DirectoryScannerWorker instance.
        
        Args:
            config (WorkerConfig): Configuration for worker behavior.
                Must be valid WorkerConfig instance.
        
        Raises:
            ValueError: If config is invalid
        """
        if not isinstance(config, WorkerConfig):
            raise ValueError("config must be WorkerConfig instance")
        
        self.config = config
        self.worker_id = os.getpid()
        
        # Initialize components
        from docanalyzer.filters.file_filter import FileFilter
        file_filter = FileFilter()
        self.lock_manager = LockManager()
        self.directory_scanner = DirectoryScanner(file_filter, self.lock_manager)
        self.file_processor = FileProcessor()
        self.chunking_manager = ChunkingManager()
        
        # Communication
        comm_config = ProcessCommunicationConfig()
        self.communication = ProcessCommunication(comm_config)
        
        # Status tracking
        self.status = WorkerStatus(
            worker_id=self.worker_id,
            status="idle",
            directory_path=""
        )
        
        # Control flags
        self._scanning = False
        self._paused = False
        self._shutdown_event = asyncio.Event()
    
    async def start_scanning(self, directory_path: str) -> ProcessingResult:
        """
        Start scanning directory.
        
        Begins the directory scanning process. The worker will scan
        the specified directory, process files, and communicate results
        back to the parent process.
        
        Args:
            directory_path (str): Path to directory to scan.
                Must be existing directory path.
        
        Returns:
            ProcessingResult: Result of the scanning operation.
        
        Raises:
            FileNotFoundError: If directory doesn't exist
            ProcessingError: If scanning fails
            TimeoutError: If scanning times out
        """
        start_time = datetime.now()
        
        try:
            if self._scanning:
                raise ProcessingError("ScanningInProgressError", "Scanning already in progress", ErrorCategory.PROCESSING)
            
            if not os.path.exists(directory_path):
                raise FileNotFoundError(f"Directory not found: {directory_path}")
            
            # Check for cancellation before starting
            if self._shutdown_event.is_set():
                return ProcessingResult(
                    success=False,
                    message="Scanning cancelled",
                    processing_time=(datetime.now() - start_time).total_seconds()
                )
            
            self._scanning = True
            self._paused = False
            self._shutdown_event.clear()
            
            # Update status
            self.status = WorkerStatus(
                worker_id=self.worker_id,
                status="scanning",
                directory_path=directory_path,
                start_time=start_time
            )
            
            logger.info(f"Worker {self.worker_id} started scanning directory: {directory_path}")
            
            # Start communication
            await self.communication.start_heartbeat()
            
            # Scan directory
            files = await self._scan_directory(directory_path)
            self.status.files_found = len(files)
            
            if self._shutdown_event.is_set():
                return ProcessingResult(
                    success=False,
                    message="Scanning cancelled",
                    processing_time=(datetime.now() - start_time).total_seconds()
                )
            
            # Process files
            self.status.status = "processing"
            result = await self._process_files(files)
            
            # Check for cancellation after processing
            if self._shutdown_event.is_set() or not result.success:
                return ProcessingResult(
                    success=False,
                    message="Scanning cancelled" if self._shutdown_event.is_set() else result.message,
                    processing_time=(datetime.now() - start_time).total_seconds()
                )
            
            # Update final status
            self.status.status = "completed" if result.success else "failed"
            self.status.last_activity = datetime.now()
            
            processing_time = (datetime.now() - start_time).total_seconds()
            result.processing_time = processing_time
            
            logger.info(f"Worker {self.worker_id} completed scanning: {result.message}")
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            self.status.status = "failed"
            self.status.error_message = str(e)
            self.status.last_activity = datetime.now()
            
            logger.error(f"Worker {self.worker_id} failed scanning: {e}")
            return ProcessingResult(
                success=False,
                message=f"Scanning failed: {str(e)}",
                processing_time=processing_time,
                error_details=str(e)
            )
        finally:
            self._scanning = False
            await self.communication.stop_heartbeat()
            await self.communication.cleanup()
    
    async def stop_scanning(self) -> bool:
        """
        Stop scanning operation.
        
        Gracefully stops the current scanning operation and cleans up
        any resources.
        
        Returns:
            bool: True if scanning was stopped successfully, False otherwise.
        """
        if not self._scanning:
            return True
        
        try:
            self._shutdown_event.set()
            self._scanning = False
            self._paused = False
            
            self.status.status = "stopped"
            self.status.last_activity = datetime.now()
            
            await self.communication.stop_heartbeat()
            await self.communication.cleanup()
            
            logger.info(f"Worker {self.worker_id} stopped scanning")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping scanning: {e}")
            return False
    
    async def get_status(self) -> WorkerStatus:
        """
        Get current worker status.
        
        Returns the current status and progress information about
        the worker process.
        
        Returns:
            WorkerStatus: Current worker status.
        """
        self.status.last_activity = datetime.now()
        
        # Calculate progress percentage
        if self.status.files_found > 0:
            self.status.progress_percentage = (self.status.files_processed / self.status.files_found) * 100.0
        
        return self.status
    
    async def pause_scanning(self) -> bool:
        """
        Pause scanning operation.
        
        Temporarily pauses the scanning operation. Can be resumed
        with resume_scanning().
        
        Returns:
            bool: True if scanning was paused successfully, False otherwise.
        """
        if not self._scanning:
            return False
        
        self._paused = True
        self.status.status = "paused"
        self.status.last_activity = datetime.now()
        
        logger.info(f"Worker {self.worker_id} paused scanning")
        return True
    
    async def resume_scanning(self) -> bool:
        """
        Resume scanning operation.
        
        Resumes a previously paused scanning operation.
        
        Returns:
            bool: True if scanning was resumed successfully, False otherwise.
        """
        if not self._scanning:
            return False
        
        self._paused = False
        self.status.status = "scanning"
        self.status.last_activity = datetime.now()
        
        logger.info(f"Worker {self.worker_id} resumed scanning")
        return True
    
    async def _scan_directory(self, directory_path: str) -> List[FileInfo]:
        """
        Scan directory for files.
        
        Performs the actual directory scanning operation and returns
        a list of discovered files.
        
        Args:
            directory_path (str): Path to directory to scan.
        
        Returns:
            List[FileInfo]: List of discovered files.
        
        Raises:
            FileNotFoundError: If directory doesn't exist
            ProcessingError: If scanning fails
        """
        try:
            result = await self.directory_scanner.scan_directory(directory_path)
            return result.files
        except Exception as e:
            raise ProcessingError("DirectoryScanningError", f"Directory scanning failed: {str(e)}", ErrorCategory.FILE_SYSTEM, operation="directory_scanning")
    
    async def _process_files(self, files: List[FileInfo]) -> ProcessingResult:
        """
        Process discovered files.
        
        Processes the list of discovered files in batches and
        communicates results back to the parent process.
        
        Args:
            files (List[FileInfo]): List of files to process.
        
        Returns:
            ProcessingResult: Result of processing operation.
        
        Raises:
            ProcessingError: If processing fails
        """
        try:
            total_files = len(files)
            processed_count = 0
            failed_count = 0
            
            # Check for cancellation before processing
            if self._shutdown_event.is_set():
                return ProcessingResult(
                    success=False,
                    message="Processing cancelled"
                )
            
            # Process files in batches
            for i in range(0, total_files, self.config.batch_size):
                if self._shutdown_event.is_set():
                    break
                
                batch = files[i:i + self.config.batch_size]
                batch_result = await self._process_file_batch(batch)
                
                processed_count += batch_result["processed"]
                failed_count += batch_result["failed"]
                
                # Update progress
                await self._update_progress(processed_count, total_files)
                
                # Send result to parent
                result = ProcessingResult(
                    success=True,
                    message=f"Processed batch {i//self.config.batch_size + 1}",
                    data=batch_result
                )
                await self.communication.send_result(result)
                
                # Check for pause
                while self._paused and not self._shutdown_event.is_set():
                    await asyncio.sleep(0.1)
            
            return ProcessingResult(
                success=True,
                message=f"Processing completed: {processed_count} processed, {failed_count} failed",
                data={
                    "total_files": total_files,
                    "processed_files": processed_count,
                    "failed_files": failed_count
                }
            )
            
        except Exception as e:
            raise ProcessingError("FileProcessingError", f"File processing failed: {str(e)}", ErrorCategory.PROCESSING)
    
    async def _process_file_batch(self, batch: List[FileInfo]) -> Dict[str, Any]:
        """
        Process a batch of files.
        
        Processes a batch of files and returns the results.
        
        Args:
            batch (List[FileInfo]): Batch of files to process.
        
        Returns:
            Dict[str, Any]: Processing results for the batch.
        
        Raises:
            ProcessingError: If batch processing fails
        """
        processed_count = 0
        failed_count = 0
        
        for file_info in batch:
            try:
                # Process file
                process_result = await self.file_processor.process_file(file_info.file_path)
                
                if process_result.success and process_result.data:
                    # Chunk the processed blocks
                    chunk_result = await self.chunking_manager.process_blocks(
                        process_result.data.get("blocks", [])
                    )
                    
                    if chunk_result.success:
                        processed_count += 1
                    else:
                        failed_count += 1
                        logger.warning(f"Failed to chunk file {file_info.file_path}: {chunk_result.message}")
                else:
                    failed_count += 1
                    logger.warning(f"Failed to process file {file_info.file_path}: {process_result.message}")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"Error processing file {file_info.file_path}: {e}")
        
        return {
            "processed": processed_count,
            "failed": failed_count,
            "total": len(batch)
        }
    
    async def _update_progress(self, files_processed: int, total_files: int) -> None:
        """
        Update progress information.
        
        Updates the progress information and sends status updates
        to the parent process.
        
        Args:
            files_processed (int): Number of files processed so far.
            total_files (int): Total number of files to process.
        """
        self.status.files_processed = files_processed
        
        if total_files > 0:
            self.status.progress_percentage = (files_processed / total_files) * 100.0
        
        self.status.last_activity = datetime.now()
        
        # Send status update if enabled
        if self.config.enable_progress_reports:
            await self._send_status_update()
    
    async def _send_status_update(self) -> None:
        """
        Send status update to parent process.
        
        Sends current status information to the parent process
        through the communication interface.
        """
        try:
            status_data = self.status.to_dict()
            await self.communication.send_status_update(status_data)
        except Exception as e:
            logger.error(f"Failed to send status update: {e}")
    
    async def _handle_signal(self, signum: int, frame) -> None:
        """
        Handle process signals.
        
        Handles system signals such as SIGTERM and SIGINT for
        graceful shutdown.
        
        Args:
            signum (int): Signal number.
            frame: Current stack frame.
        """
        logger.info(f"Worker {self.worker_id} received signal {signum}")
        
        if signum in (signal.SIGTERM, signal.SIGINT):
            await self.stop_scanning()
            await self._cleanup_resources()
            sys.exit(0)
    
    async def _cleanup_resources(self) -> None:
        """
        Clean up worker resources.
        
        Cleans up any allocated resources and performs final
        cleanup operations.
        """
        try:
            await self.communication.cleanup()
            logger.info(f"Worker {self.worker_id} cleaned up resources")
        except Exception as e:
            logger.error(f"Error during resource cleanup: {e}")


def main():
    """
    Main entry point for worker process.
    
    This function is called when the worker process is started.
    It initializes the worker and begins the scanning operation.
    """
    try:
        # Parse command line arguments
        if len(sys.argv) < 2:
            print("Usage: python directory_scanner_worker.py <directory_path>")
            sys.exit(1)
        
        directory_path = sys.argv[1]
        
        # Initialize worker
        config = WorkerConfig()
        worker = DirectoryScannerWorker(config)
        
        # Set up signal handlers
        signal.signal(signal.SIGTERM, lambda s, f: asyncio.create_task(worker._handle_signal(s, f)))
        signal.signal(signal.SIGINT, lambda s, f: asyncio.create_task(worker._handle_signal(s, f)))
        
        # Start scanning
        asyncio.run(worker.start_scanning(directory_path))
        
    except Exception as e:
        logger.error(f"Worker process failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 