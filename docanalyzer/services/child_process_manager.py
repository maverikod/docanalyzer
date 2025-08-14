"""
Child Process Manager - Directory Scanning Process Management

Manages child processes that perform directory scanning operations.
Handles process lifecycle, communication, and error recovery for
directory scanning workers.

The child process manager coordinates with the main process manager
to execute directory scanning tasks in isolated processes, ensuring
fault tolerance and resource isolation.

Author: File Watcher Team
Version: 1.0.0
"""

import asyncio
import multiprocessing
import signal
import sys
import os
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import logging
from datetime import datetime
import json

from docanalyzer.models.file_system import Directory, FileInfo
from docanalyzer.services.directory_scanner import DirectoryScanner
from docanalyzer.services.lock_manager import LockManager
from docanalyzer.models.processing import ProcessingResult
from docanalyzer.models.errors import (
    ProcessingError, 
    ProcessManagementError, 
    ProcessNotFoundError, 
    ResourceLimitError
)

logger = logging.getLogger(__name__)

DEFAULT_WORKER_TIMEOUT = 300
DEFAULT_MAX_WORKERS = 4
DEFAULT_CHUNK_SIZE = 100


class ChildProcessConfig:
    """
    Configuration for child process management.
    
    Contains settings for worker processes, timeouts, and resource limits.
    
    Attributes:
        max_workers (int): Maximum number of concurrent worker processes.
            Must be positive integer. Defaults to 4.
        worker_timeout (int): Timeout for worker processes in seconds.
            Must be positive integer. Defaults to 300.
        chunk_size (int): Number of files to process in each chunk.
            Must be positive integer. Defaults to 100.
        enable_graceful_shutdown (bool): Whether to enable graceful shutdown.
            Defaults to True.
        auto_restart_failed_workers (bool): Whether to automatically restart failed workers.
            Defaults to True.
        max_restart_attempts (int): Maximum number of restart attempts for failed workers.
            Must be non-negative integer. Defaults to 3.
    """
    
    def __init__(
        self,
        max_workers: int = DEFAULT_MAX_WORKERS,
        worker_timeout: int = DEFAULT_WORKER_TIMEOUT,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        enable_graceful_shutdown: bool = True,
        auto_restart_failed_workers: bool = True,
        max_restart_attempts: int = 3
    ):
        """
        Initialize ChildProcessConfig instance.
        
        Args:
            max_workers (int): Maximum number of concurrent worker processes.
                Must be positive integer. Defaults to 4.
            worker_timeout (int): Timeout for worker processes in seconds.
                Must be positive integer. Defaults to 300.
            chunk_size (int): Number of files to process in each chunk.
                Must be positive integer. Defaults to 100.
            enable_graceful_shutdown (bool): Whether to enable graceful shutdown.
                Defaults to True.
            auto_restart_failed_workers (bool): Whether to automatically restart failed workers.
                Defaults to True.
            max_restart_attempts (int): Maximum number of restart attempts for failed workers.
                Must be non-negative integer. Defaults to 3.
        
        Raises:
            ValueError: If any parameter has invalid value
        """
        if max_workers <= 0:
            raise ValueError("max_workers must be positive")
        if worker_timeout <= 0:
            raise ValueError("worker_timeout must be positive")
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if max_restart_attempts < 0:
            raise ValueError("max_restart_attempts must be non-negative")
        
        self.max_workers = max_workers
        self.worker_timeout = worker_timeout
        self.chunk_size = chunk_size
        self.enable_graceful_shutdown = enable_graceful_shutdown
        self.auto_restart_failed_workers = auto_restart_failed_workers
        self.max_restart_attempts = max_restart_attempts


class WorkerProcessInfo:
    """
    Information about a worker process.
    
    Contains details about worker process status, performance, and health.
    
    Attributes:
        process_id (int): Process ID of the worker.
        start_time (datetime): When the worker was started.
        status (str): Current status of the worker (running, stopped, failed).
        directory_path (str): Directory being scanned by this worker.
        files_processed (int): Number of files processed so far.
        last_activity (datetime): Last activity timestamp.
        restart_count (int): Number of times this worker has been restarted.
        error_message (Optional[str]): Last error message if any.
    """
    
    def __init__(
        self,
        process_id: int,
        start_time: datetime,
        status: str,
        directory_path: str,
        files_processed: int = 0,
        last_activity: Optional[datetime] = None,
        restart_count: int = 0,
        error_message: Optional[str] = None
    ):
        """
        Initialize WorkerProcessInfo instance.
        
        Args:
            process_id (int): Process ID of the worker.
            start_time (datetime): When the worker was started.
            status (str): Current status of the worker.
            directory_path (str): Directory being scanned by this worker.
            files_processed (int): Number of files processed so far.
                Defaults to 0.
            last_activity (Optional[datetime]): Last activity timestamp.
                Defaults to None.
            restart_count (int): Number of times this worker has been restarted.
                Defaults to 0.
            error_message (Optional[str]): Last error message if any.
                Defaults to None.
        """
        self.process_id = process_id
        self.start_time = start_time
        self.status = status
        self.directory_path = directory_path
        self.files_processed = files_processed
        self.last_activity = last_activity or datetime.now()
        self.restart_count = restart_count
        self.error_message = error_message
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary representation of worker info.
        """
        return {
            "process_id": self.process_id,
            "start_time": self.start_time.isoformat(),
            "status": self.status,
            "directory_path": self.directory_path,
            "files_processed": self.files_processed,
            "last_activity": self.last_activity.isoformat(),
            "restart_count": self.restart_count,
            "error_message": self.error_message
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkerProcessInfo':
        """
        Create instance from dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary data.
        
        Returns:
            WorkerProcessInfo: Created instance.
        
        Raises:
            ValueError: If data is invalid
        """
        if not isinstance(data, dict):
            raise ValueError("data must be dictionary")
        
        required_fields = ["process_id", "start_time", "status", "directory_path"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Required field '{field}' missing in data")
        
        return cls(
            process_id=data["process_id"],
            start_time=datetime.fromisoformat(data["start_time"]),
            status=data["status"],
            directory_path=data["directory_path"],
            files_processed=data.get("files_processed", 0),
            last_activity=datetime.fromisoformat(data["last_activity"]) if data.get("last_activity") else None,
            restart_count=data.get("restart_count", 0),
            error_message=data.get("error_message")
        )


class ChildProcessResult:
    """
    Result of child process operation.
    
    Contains information about the success/failure of child process operations.
    
    Attributes:
        success (bool): Whether the operation was successful.
        worker_info (Optional[WorkerProcessInfo]): Information about the worker process.
        error_message (Optional[str]): Error message if operation failed.
        processing_result (Optional[ProcessingResult]): Result of processing if available.
        execution_time (float): Time taken for the operation in seconds.
    """
    
    def __init__(
        self,
        success: bool,
        worker_info: Optional[WorkerProcessInfo] = None,
        error_message: Optional[str] = None,
        processing_result: Optional[ProcessingResult] = None,
        execution_time: float = 0.0
    ):
        """
        Initialize ChildProcessResult instance.
        
        Args:
            success (bool): Whether the operation was successful.
            worker_info (Optional[WorkerProcessInfo]): Information about the worker process.
                Defaults to None.
            error_message (Optional[str]): Error message if operation failed.
                Defaults to None.
            processing_result (Optional[ProcessingResult]): Result of processing if available.
                Defaults to None.
            execution_time (float): Time taken for the operation in seconds.
                Defaults to 0.0.
        """
        self.success = success
        self.worker_info = worker_info
        self.error_message = error_message
        self.processing_result = processing_result
        self.execution_time = execution_time
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary representation of result.
        """
        return {
            "success": self.success,
            "worker_info": self.worker_info.to_dict() if self.worker_info else None,
            "error_message": self.error_message,
            "processing_result": self.processing_result.to_dict() if self.processing_result else None,
            "execution_time": self.execution_time
        }


class ChildProcessManager:
    """
    Child Process Manager - Directory Scanning Process Management
    
    Manages child processes that perform directory scanning operations.
    Handles process lifecycle, communication, and error recovery.
    
    The manager coordinates with the main process manager to execute
    directory scanning tasks in isolated processes, ensuring fault
    tolerance and resource isolation.
    
    Attributes:
        config (ChildProcessConfig): Configuration for child process management.
        active_workers (Dict[int, WorkerProcessInfo]): Currently active worker processes.
        directory_scanner (DirectoryScanner): Directory scanner instance.
        lock_manager (LockManager): Lock manager instance.
    
    Example:
        >>> config = ChildProcessConfig(max_workers=2)
        >>> manager = ChildProcessManager(config)
        >>> result = await manager.start_worker("/path/to/directory")
        >>> await manager.stop_worker(worker_id)
    """
    
    def __init__(self, config: ChildProcessConfig):
        """
        Initialize ChildProcessManager instance.
        
        Args:
            config (ChildProcessConfig): Configuration for child process management.
                Must be valid ChildProcessConfig instance.
        
        Raises:
            ValueError: If config is invalid
        """
        if not isinstance(config, ChildProcessConfig):
            raise ValueError("config must be ChildProcessConfig instance")
        
        self.config = config
        self.active_workers: Dict[int, WorkerProcessInfo] = {}
        self.lock_manager = LockManager()
        
        # Import FileFilter here to avoid circular imports
        from docanalyzer.filters.file_filter import FileFilter
        file_filter = FileFilter()
        self.directory_scanner = DirectoryScanner(file_filter, self.lock_manager)
        
        self._monitoring_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        logger.info(f"ChildProcessManager initialized with max_workers={config.max_workers}")
    
    async def start_worker(self, directory_path: str) -> ChildProcessResult:
        """
        Start a worker process for directory scanning.
        
        Creates a new worker process to scan the specified directory.
        The worker runs in isolation and communicates results back
        to the main process.
        
        Args:
            directory_path (str): Path to directory to scan.
                Must be existing directory path.
        
        Returns:
            ChildProcessResult: Result of starting the worker process.
        
        Raises:
            FileNotFoundError: If directory doesn't exist
            ProcessManagementError: If cannot start worker process
            ResourceLimitError: If maximum workers limit reached
        """
        start_time = datetime.now()
        
        try:
            # Check if directory exists
            if not os.path.exists(directory_path):
                raise FileNotFoundError(f"Directory not found: {directory_path}")
            
            # Check if we can start more workers
            if len(self.active_workers) >= self.config.max_workers:
                raise ResourceLimitError(
                    f"Maximum workers limit reached: {len(self.active_workers)}/{self.config.max_workers}",
                    resource_type="workers",
                    current_usage=len(self.active_workers),
                    limit=self.config.max_workers
                )
            
            # Create lock for directory
            lock_file = await self.lock_manager.create_lock(directory_path)
            
            # Start worker process
            process = multiprocessing.Process(
                target=self._worker_process_target,
                args=(directory_path, self.config.chunk_size)
            )
            process.start()
            
            # Create worker info
            worker_info = WorkerProcessInfo(
                process_id=process.pid,
                start_time=start_time,
                status="running",
                directory_path=directory_path
            )
            
            # Add to active workers
            self.active_workers[process.pid] = worker_info
            
            # Start monitoring if not already started
            if self._monitoring_task is None:
                self._monitoring_task = asyncio.create_task(self._monitor_worker_health())
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Started worker process {process.pid} for directory: {directory_path}")
            
            return ChildProcessResult(
                success=True,
                worker_info=worker_info,
                execution_time=execution_time
            )
            
        except (FileNotFoundError, ResourceLimitError) as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return ChildProcessResult(
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Failed to start worker for {directory_path}: {e}")
            return ChildProcessResult(
                success=False,
                error_message=f"ProcessManagementError: {str(e)}",
                execution_time=execution_time
            )
    
    async def stop_worker(self, worker_id: int) -> ChildProcessResult:
        """
        Stop a worker process.
        
        Gracefully stops the specified worker process and cleans up
        associated resources.
        
        Args:
            worker_id (int): ID of the worker process to stop.
                Must be valid worker process ID.
        
        Returns:
            ChildProcessResult: Result of stopping the worker process.
        
        Raises:
            ProcessNotFoundError: If worker process not found
            ProcessManagementError: If cannot stop worker process
        """
        start_time = datetime.now()
        
        try:
            if worker_id not in self.active_workers:
                raise ProcessNotFoundError(
                    f"Worker process {worker_id} not found",
                    process_id=worker_id,
                    operation="stop"
                )
            
            worker_info = self.active_workers[worker_id]
            
            # Try to terminate process gracefully
            try:
                import psutil
                process = psutil.Process(worker_id)
                
                if self.config.enable_graceful_shutdown:
                    process.terminate()
                    process.wait(timeout=10)  # Wait up to 10 seconds
                else:
                    process.kill()
                    process.wait(timeout=5)
                    
            except psutil.NoSuchProcess:
                # Process already terminated
                pass
            except psutil.TimeoutExpired:
                # Force kill if graceful shutdown fails
                try:
                    process.kill()
                    process.wait(timeout=5)
                except psutil.NoSuchProcess:
                    pass
            
            # Remove lock for directory
            try:
                await self.lock_manager.remove_lock_by_directory(worker_info.directory_path)
            except Exception as e:
                logger.warning(f"Failed to remove lock for directory {worker_info.directory_path}: {e}")
            
            # Remove from active workers
            del self.active_workers[worker_id]
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Stopped worker process {worker_id}")
            
            return ChildProcessResult(
                success=True,
                worker_info=worker_info,
                execution_time=execution_time
            )
            
        except ProcessNotFoundError as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return ChildProcessResult(
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Failed to stop worker {worker_id}: {e}")
            return ChildProcessResult(
                success=False,
                error_message=f"ProcessManagementError: {str(e)}",
                execution_time=execution_time
            )
    
    async def get_worker_status(self, worker_id: int) -> Optional[WorkerProcessInfo]:
        """
        Get status of a worker process.
        
        Retrieves current status and information about the specified
        worker process.
        
        Args:
            worker_id (int): ID of the worker process.
                Must be valid worker process ID.
        
        Returns:
            Optional[WorkerProcessInfo]: Worker process information if found.
        
        Raises:
            ProcessNotFoundError: If worker process not found
        """
        if worker_id not in self.active_workers:
            raise ProcessNotFoundError(
                f"Worker process {worker_id} not found",
                process_id=worker_id,
                operation="get_status"
            )
        
        worker_info = self.active_workers[worker_id]
        
        # Update last activity
        worker_info.last_activity = datetime.now()
        
        return worker_info
    
    async def get_all_workers_status(self) -> List[WorkerProcessInfo]:
        """
        Get status of all worker processes.
        
        Retrieves current status and information about all active
        worker processes.
        
        Returns:
            List[WorkerProcessInfo]: List of all worker process information.
        """
        return list(self.active_workers.values())
    
    async def restart_worker(self, worker_id: int) -> ChildProcessResult:
        """
        Restart a worker process.
        
        Stops the specified worker process and starts a new one
        with the same configuration.
        
        Args:
            worker_id (int): ID of the worker process to restart.
                Must be valid worker process ID.
        
        Returns:
            ChildProcessResult: Result of restarting the worker process.
        
        Raises:
            ProcessNotFoundError: If worker process not found
            ProcessManagementError: If cannot restart worker process
        """
        start_time = datetime.now()
        
        try:
            if worker_id not in self.active_workers:
                raise ProcessNotFoundError(
                    f"Worker process {worker_id} not found",
                    process_id=worker_id,
                    operation="restart"
                )
            
            worker_info = self.active_workers[worker_id]
            directory_path = worker_info.directory_path
            
            # Stop the worker
            stop_result = await self.stop_worker(worker_id)
            if not stop_result.success:
                return stop_result
            
            # Start a new worker
            start_result = await self.start_worker(directory_path)
            if start_result.success and start_result.worker_info:
                start_result.worker_info.restart_count = worker_info.restart_count + 1
            
            execution_time = (datetime.now() - start_time).total_seconds()
            start_result.execution_time = execution_time
            
            return start_result
            
        except ProcessNotFoundError as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return ChildProcessResult(
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Failed to restart worker {worker_id}: {e}")
            return ChildProcessResult(
                success=False,
                error_message=f"ProcessManagementError: {str(e)}",
                execution_time=execution_time
            )
    
    async def cleanup_failed_workers(self) -> int:
        """
        Clean up failed worker processes.
        
        Identifies and removes failed worker processes, optionally
        restarting them based on configuration.
        
        Returns:
            int: Number of workers cleaned up.
        """
        cleaned_count = 0
        failed_workers = []
        
        # Identify failed workers
        for worker_id, worker_info in list(self.active_workers.items()):
            try:
                import psutil
                process = psutil.Process(worker_id)
                if not process.is_running():
                    failed_workers.append((worker_id, worker_info))
            except psutil.NoSuchProcess:
                failed_workers.append((worker_id, worker_info))
        
        # Clean up failed workers
        for worker_id, worker_info in failed_workers:
            try:
                await self._handle_worker_failure(worker_id, Exception("Process terminated"))
                cleaned_count += 1
            except Exception as e:
                logger.error(f"Error cleaning up failed worker {worker_id}: {e}")
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} failed worker processes")
        
        return cleaned_count
    
    async def shutdown_all_workers(self) -> ChildProcessResult:
        """
        Shutdown all worker processes.
        
        Gracefully stops all active worker processes and cleans up
        all associated resources.
        
        Returns:
            ChildProcessResult: Result of shutting down all workers.
        """
        start_time = datetime.now()
        
        try:
            # Stop monitoring task
            if self._monitoring_task and not self._monitoring_task.done():
                self._monitoring_task.cancel()
                try:
                    await self._monitoring_task
                except asyncio.CancelledError:
                    pass
            
            # Stop all workers
            worker_ids = list(self.active_workers.keys())
            stopped_count = 0
            
            for worker_id in worker_ids:
                try:
                    result = await self.stop_worker(worker_id)
                    if result.success:
                        stopped_count += 1
                except Exception as e:
                    logger.error(f"Error stopping worker {worker_id}: {e}")
                    # Remove from active workers even if stop failed
                    if worker_id in self.active_workers:
                        del self.active_workers[worker_id]
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Shutdown {stopped_count}/{len(worker_ids)} worker processes")
            
            return ChildProcessResult(
                success=stopped_count == len(worker_ids),
                error_message=f"Failed to stop {len(worker_ids) - stopped_count} workers" if stopped_count < len(worker_ids) else None,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Error during shutdown: {e}")
            return ChildProcessResult(
                success=False,
                error_message=f"ShutdownError: {str(e)}",
                execution_time=execution_time
            )
    
    async def _monitor_worker_health(self) -> None:
        """
        Monitor health of all worker processes.
        
        Background task that continuously monitors the health of
        all active worker processes and takes corrective actions
        if needed.
        """
        while not self._shutdown_event.is_set():
            try:
                # Check each worker's health
                for worker_id, worker_info in list(self.active_workers.items()):
                    try:
                        import psutil
                        process = psutil.Process(worker_id)
                        
                        # Check if process is still running
                        if not process.is_running():
                            await self._handle_worker_failure(worker_id, Exception("Process not running"))
                            continue
                        
                        # Check if process is responsive (not zombie)
                        if process.status() == psutil.STATUS_ZOMBIE:
                            await self._handle_worker_failure(worker_id, Exception("Process is zombie"))
                            continue
                        
                        # Check timeout
                        if (datetime.now() - worker_info.last_activity).total_seconds() > self.config.worker_timeout:
                            await self._handle_worker_failure(worker_id, Exception("Process timeout"))
                            continue
                        
                        # Update last activity
                        worker_info.last_activity = datetime.now()
                        
                    except psutil.NoSuchProcess:
                        await self._handle_worker_failure(worker_id, Exception("Process not found"))
                    except Exception as e:
                        logger.error(f"Error monitoring worker {worker_id}: {e}")
                
                # Clean up failed workers
                await self.cleanup_failed_workers()
                
                # Wait before next check
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in worker health monitoring: {e}")
                await asyncio.sleep(10)  # Wait longer on error
    
    def _worker_process_target(self, directory_path: str, chunk_size: int) -> None:
        """
        Target function for worker process.
        
        This function runs in the worker process and performs
        the actual directory scanning and processing.
        
        Args:
            directory_path (str): Directory to scan.
            chunk_size (int): Size of processing chunks.
        """
        try:
            # Set up logging for worker process
            logging.basicConfig(level=logging.INFO)
            worker_logger = logging.getLogger(f"worker_{os.getpid()}")
            
            worker_logger.info(f"Worker process {os.getpid()} started for directory: {directory_path}")
            
            # Import and run worker
            from docanalyzer.workers.directory_scanner_worker import DirectoryScannerWorker, WorkerConfig
            
            config = WorkerConfig(batch_size=chunk_size)
            worker = DirectoryScannerWorker(config)
            
            # Run scanning
            asyncio.run(worker.start_scanning(directory_path))
            
            worker_logger.info(f"Worker process {os.getpid()} completed successfully")
            
        except Exception as e:
            logging.error(f"Worker process {os.getpid()} failed: {e}")
            sys.exit(1)
    
    async def _handle_worker_failure(self, worker_id: int, error: Exception) -> None:
        """
        Handle worker process failure.
        
        Processes worker failures and takes appropriate actions
        such as restarting or logging errors.
        
        Args:
            worker_id (int): ID of the failed worker process.
            error (Exception): Error that caused the failure.
        """
        if worker_id not in self.active_workers:
            return
        
        worker_info = self.active_workers[worker_id]
        worker_info.status = "failed"
        worker_info.error_message = str(error)
        worker_info.last_activity = datetime.now()
        
        logger.error(f"Worker {worker_id} failed: {error}")
        
        # Auto-restart if enabled and within limits
        if (self.config.auto_restart_failed_workers and 
            worker_info.restart_count < self.config.max_restart_attempts):
            
            logger.info(f"Attempting to restart worker {worker_id} (attempt {worker_info.restart_count + 1})")
            
            try:
                # Remove from active workers
                del self.active_workers[worker_id]
                
                # Restart worker
                result = await self.start_worker(worker_info.directory_path)
                if result.success and result.worker_info:
                    result.worker_info.restart_count = worker_info.restart_count + 1
                    logger.info(f"Successfully restarted worker {worker_id}")
                else:
                    logger.error(f"Failed to restart worker {worker_id}: {result.error_message}")
                    
            except Exception as restart_error:
                logger.error(f"Error during worker restart {worker_id}: {restart_error}")
        else:
            logger.warning(f"Worker {worker_id} exceeded restart attempts or auto-restart disabled")
            # Remove from active workers
            if worker_id in self.active_workers:
                del self.active_workers[worker_id] 