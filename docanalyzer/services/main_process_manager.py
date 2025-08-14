"""
Main Process Manager - Process Coordination Service

Provides functionality for coordinating the main process, managing child processes,
and orchestrating the overall file watching and processing workflow.

The main process manager is responsible for:
- Starting and stopping child processes
- Monitoring process health and status
- Coordinating communication between processes
- Managing process lifecycle and cleanup
- Handling process failures and recovery

Author: File Watcher Team
Version: 1.0.0
"""

import asyncio
import logging
import multiprocessing
import os
import signal
import sys
from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import psutil

from docanalyzer.models.file_system import Directory
from docanalyzer.services.lock_manager import LockManager
from docanalyzer.services.directory_scanner import DirectoryScanner
from docanalyzer.services.file_processor import FileProcessor
from docanalyzer.services.chunking_manager import ChunkingManager
from docanalyzer.monitoring.health import HealthChecker
from docanalyzer.monitoring.metrics import MetricsCollector

logger = logging.getLogger(__name__)

DEFAULT_MAX_CHILD_PROCESSES = 4
DEFAULT_PROCESS_TIMEOUT = 300  # 5 minutes
DEFAULT_HEALTH_CHECK_INTERVAL = 30  # 30 seconds


class ProcessStatus(Enum):
    """Process status enumeration."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


@dataclass
class ProcessInfo:
    """
    Process information container.
    
    Contains metadata about a child process including its ID, status,
    start time, and performance metrics.
    
    Attributes:
        process_id (int): Operating system process ID
        status (ProcessStatus): Current status of the process
        start_time (datetime): When the process was started
        end_time (Optional[datetime]): When the process ended (if completed)
        directory (Optional[str]): Directory being processed by this process
        memory_usage (Optional[float]): Memory usage in MB
        cpu_usage (Optional[float]): CPU usage percentage
        error_message (Optional[str]): Error message if process failed
        exit_code (Optional[int]): Process exit code
    """
    process_id: int
    status: ProcessStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    directory: Optional[str] = None
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    error_message: Optional[str] = None
    exit_code: Optional[int] = None


@dataclass
class MainProcessConfig:
    """
    Configuration for main process manager.
    
    Contains settings for process management, timeouts, and resource limits.
    
    Attributes:
        max_child_processes (int): Maximum number of concurrent child processes
        process_timeout (int): Timeout for child processes in seconds
        health_check_interval (int): Interval between health checks in seconds
        enable_auto_recovery (bool): Whether to automatically restart failed processes
        max_retry_attempts (int): Maximum number of retry attempts for failed processes
        graceful_shutdown_timeout (int): Timeout for graceful shutdown in seconds
    """
    max_child_processes: int = DEFAULT_MAX_CHILD_PROCESSES
    process_timeout: int = DEFAULT_PROCESS_TIMEOUT
    health_check_interval: int = DEFAULT_HEALTH_CHECK_INTERVAL
    enable_auto_recovery: bool = True
    max_retry_attempts: int = 3
    graceful_shutdown_timeout: int = 60


@dataclass
class ProcessManagementResult:
    """
    Result of process management operations.
    
    Contains information about the success/failure of process operations
    and any relevant metadata.
    
    Attributes:
        success (bool): Whether the operation was successful
        message (str): Human-readable message about the operation
        process_info (Optional[ProcessInfo]): Information about the affected process
        error_details (Optional[str]): Detailed error information if failed
        timestamp (datetime): When the operation was performed
    """
    success: bool
    message: str
    process_info: Optional[ProcessInfo] = None
    error_details: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class MainProcessManager:
    """
    Main Process Manager - Process Coordination Service
    
    Manages the main process lifecycle, coordinates child processes,
    and orchestrates the overall file watching and processing workflow.
    
    The manager is responsible for:
    - Starting and stopping child processes for directory processing
    - Monitoring process health and performance
    - Coordinating communication between processes
    - Handling process failures and recovery
    - Managing resource allocation and limits
    
    Attributes:
        config (MainProcessConfig): Configuration for process management
        active_processes (Dict[int, ProcessInfo]): Currently active child processes
        process_history (List[ProcessInfo]): History of all processes
        health_checker (HealthChecker): Health monitoring component
        metrics_collector (MetricsCollector): Metrics collection component
        lock_manager (LockManager): Lock management for directories
        directory_scanner (DirectoryScanner): Directory scanning component
        file_processor (FileProcessor): File processing component
        chunking_manager (ChunkingManager): Chunking management component
        shutdown_event (asyncio.Event): Event for graceful shutdown
        health_check_task (Optional[asyncio.Task]): Health check monitoring task
    
    Example:
        >>> manager = MainProcessManager()
        >>> await manager.start()
        >>> result = await manager.start_child_process("/path/to/directory")
        >>> await manager.stop()
    
    Raises:
        ProcessManagementError: When process management operations fail
        ResourceLimitError: When resource limits are exceeded
        HealthCheckError: When health monitoring fails
    """
    
    def __init__(self, config: Optional[MainProcessConfig] = None):
        """
        Initialize MainProcessManager instance.
        
        Args:
            config (Optional[MainProcessConfig]): Configuration for process management.
                If None, uses default configuration.
        
        Raises:
            ValueError: If configuration parameters are invalid
            ProcessManagementError: If initialization fails
        """
        self.config = config or MainProcessConfig()
        
        # Validate configuration
        if self.config.max_child_processes <= 0:
            raise ValueError("max_child_processes must be positive")
        if self.config.process_timeout <= 0:
            raise ValueError("process_timeout must be positive")
        if self.config.health_check_interval <= 0:
            raise ValueError("health_check_interval must be positive")
        if self.config.max_retry_attempts < 0:
            raise ValueError("max_retry_attempts must be non-negative")
        if self.config.graceful_shutdown_timeout <= 0:
            raise ValueError("graceful_shutdown_timeout must be positive")
        
        # Initialize components
        self.active_processes: Dict[int, ProcessInfo] = {}
        self.process_history: List[ProcessInfo] = []
        self.shutdown_event = asyncio.Event()
        self.health_check_task: Optional[asyncio.Task] = None
        
        # Initialize service components
        try:
            self.lock_manager = LockManager()
            
            # Initialize services with proper dependencies
            from docanalyzer.filters.file_filter import FileFilter
            file_filter = FileFilter()
            self.directory_scanner = DirectoryScanner(file_filter, self.lock_manager)
            
            # Note: FileProcessor and ChunkingManager require external dependencies
            # that should be injected, so we'll initialize them as None for now
            self.file_processor = None
            self.chunking_manager = None
            
            self.health_checker = HealthChecker()
            self.metrics_collector = MetricsCollector()
        except Exception as e:
            raise ProcessManagementError(f"Failed to initialize components: {e}")
        
        logger.info("MainProcessManager initialized successfully")
    
    async def start(self) -> ProcessManagementResult:
        """
        Start the main process manager.
        
        Initializes all components, starts health monitoring,
        and prepares the manager for processing directories.
        
        Returns:
            ProcessManagementResult: Result of the start operation
        
        Raises:
            ProcessManagementError: If startup fails
            HealthCheckError: If health monitoring cannot be started
        """
        try:
            logger.info("Starting MainProcessManager")
            
            # Start health monitoring
            self.health_check_task = asyncio.create_task(self._monitor_process_health())
            
            # Initialize metrics collection
            await self.metrics_collector.start()
            
            logger.info("MainProcessManager started successfully")
            return ProcessManagementResult(
                success=True,
                message="MainProcessManager started successfully"
            )
            
        except Exception as e:
            logger.error(f"Failed to start MainProcessManager: {e}")
            raise ProcessManagementError(f"Startup failed: {e}")
    
    async def stop(self) -> ProcessManagementResult:
        """
        Stop the main process manager.
        
        Performs graceful shutdown of all child processes,
        stops health monitoring, and cleans up resources.
        
        Returns:
            ProcessManagementResult: Result of the stop operation
        
        Raises:
            ProcessManagementError: If shutdown fails
            TimeoutError: If graceful shutdown times out
        """
        try:
            logger.info("Stopping MainProcessManager")
            
            # Signal shutdown
            self.shutdown_event.set()
            
            # Stop health monitoring
            if self.health_check_task:
                self.health_check_task.cancel()
                try:
                    await self.health_check_task
                except asyncio.CancelledError:
                    pass
            
            # Stop all child processes
            if self.active_processes:
                await self._stop_all_child_processes()
            
            # Stop metrics collection
            await self.metrics_collector.stop()
            
            logger.info("MainProcessManager stopped successfully")
            return ProcessManagementResult(
                success=True,
                message="MainProcessManager stopped successfully"
            )
            
        except Exception as e:
            logger.error(f"Failed to stop MainProcessManager: {e}")
            raise ProcessManagementError(f"Shutdown failed: {e}")
    
    async def start_child_process(self, directory: str) -> ProcessManagementResult:
        """
        Start a child process for directory processing.
        
        Creates a new child process to handle directory scanning,
        file processing, and chunking for the specified directory.
        
        Args:
            directory (str): Path to directory to process.
                Must be existing directory path.
        
        Returns:
            ProcessManagementResult: Result with process information
        
        Raises:
            ProcessManagementError: If process creation fails
            ResourceLimitError: If maximum processes limit reached
            FileNotFoundError: If directory doesn't exist
            LockError: If directory is already locked
        """
        try:
            # Check if directory exists
            if not os.path.exists(directory):
                raise FileNotFoundError(f"Directory not found: {directory}")
            
            # Check process limit
            if len(self.active_processes) >= self.config.max_child_processes:
                raise ResourceLimitError(
                    f"Maximum child processes limit reached ({self.config.max_child_processes})"
                )
            
            # Check if directory is already being processed
            for process_info in self.active_processes.values():
                if process_info.directory == directory:
                    raise ProcessManagementError(f"Directory already being processed: {directory}")
            
            # Create lock for directory
            lock_file = await self.lock_manager.create_lock(directory)
            
            # Start child process
            process = multiprocessing.Process(
                target=self._child_process_worker,
                args=(directory,)
            )
            process.start()
            
            # Create process info
            process_info = ProcessInfo(
                process_id=process.pid,
                status=ProcessStatus.RUNNING,
                start_time=datetime.now(),
                directory=directory
            )
            
            # Add to active processes
            self.active_processes[process.pid] = process_info
            
            logger.info(f"Started child process {process.pid} for directory: {directory}")
            
            return ProcessManagementResult(
                success=True,
                message=f"Child process {process.pid} started successfully",
                process_info=process_info
            )
            
        except (FileNotFoundError, ResourceLimitError, ProcessManagementError):
            # Re-raise specific exceptions without wrapping
            raise
        except Exception as e:
            logger.error(f"Failed to start child process for {directory}: {e}")
            raise ProcessManagementError(f"Process creation failed: {e}")
    
    async def stop_child_process(self, process_id: int) -> ProcessManagementResult:
        """
        Stop a specific child process.
        
        Terminates the specified child process gracefully
        and cleans up associated resources.
        
        Args:
            process_id (int): ID of the process to stop.
                Must be valid active process ID.
        
        Returns:
            ProcessManagementResult: Result of the stop operation
        
        Raises:
            ProcessManagementError: If process termination fails
            ProcessNotFoundError: If process ID doesn't exist
            TimeoutError: If graceful termination times out
        """
        try:
            if process_id not in self.active_processes:
                raise ProcessNotFoundError(f"Process {process_id} not found")
            
            process_info = self.active_processes[process_id]
            
            # Try graceful termination first
            try:
                process = psutil.Process(process_id)
                process.terminate()
                
                # Wait for graceful termination
                process.wait(timeout=self.config.graceful_shutdown_timeout)
                
            except (psutil.TimeoutExpired, Exception):
                # Force kill if graceful termination times out or fails
                try:
                    process.kill()
                    process.wait()
                except (psutil.NoSuchProcess, Exception):
                    # Process already terminated or kill failed
                    pass
                
            except psutil.NoSuchProcess:
                # Process already terminated
                pass
            
            # Update process info
            process_info.status = ProcessStatus.TERMINATED
            process_info.end_time = datetime.now()
            
            # Move to history
            self.process_history.append(process_info)
            del self.active_processes[process_id]
            
            # Remove lock if directory was being processed
            if process_info.directory:
                try:
                    await self.lock_manager.remove_lock_by_directory(process_info.directory)
                except Exception as e:
                    logger.warning(f"Failed to remove lock for {process_info.directory}: {e}")
            
            logger.info(f"Stopped child process {process_id}")
            
            return ProcessManagementResult(
                success=True,
                message=f"Child process {process_id} stopped successfully",
                process_info=process_info
            )
            
        except ProcessNotFoundError:
            # Re-raise specific exception without wrapping
            raise
        except Exception as e:
            logger.error(f"Failed to stop child process {process_id}: {e}")
            raise ProcessManagementError(f"Process termination failed: {e}")
    
    async def get_process_status(self, process_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get status of processes.
        
        Returns status information for a specific process
        or all active processes if no ID specified.
        
        Args:
            process_id (Optional[int]): Specific process ID to check.
                If None, returns status of all active processes.
        
        Returns:
            Dict[str, Any]: Process status information
        
        Raises:
            ProcessNotFoundError: If specified process ID doesn't exist
        """
        try:
            if process_id is not None:
                if process_id not in self.active_processes:
                    raise ProcessNotFoundError(f"Process {process_id} not found")
                
                process_info = self.active_processes[process_id]
                return {
                    "process_id": process_info.process_id,
                    "status": process_info.status.value,
                    "start_time": process_info.start_time.isoformat(),
                    "directory": process_info.directory,
                    "memory_usage": process_info.memory_usage,
                    "cpu_usage": process_info.cpu_usage,
                    "error_message": process_info.error_message
                }
            else:
                # Return all active processes
                processes = []
                for pid, process_info in self.active_processes.items():
                    processes.append({
                        "process_id": pid,
                        "status": process_info.status.value,
                        "start_time": process_info.start_time.isoformat(),
                        "directory": process_info.directory,
                        "memory_usage": process_info.memory_usage,
                        "cpu_usage": process_info.cpu_usage
                    })
                
                return {
                    "active_processes": processes,
                    "total_active": len(processes),
                    "max_processes": self.config.max_child_processes
                }
                
        except Exception as e:
            logger.error(f"Failed to get process status: {e}")
            raise
    
    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of the main process manager.
        
        Returns comprehensive health information including
        process status, resource usage, and system metrics.
        
        Returns:
            Dict[str, Any]: Health status information
        
        Raises:
            HealthCheckError: If health check fails
        """
        try:
            # Get system metrics
            system_metrics = await self.metrics_collector.get_system_metrics()
            
            # Get process metrics
            process_metrics = {
                "active_processes": len(self.active_processes),
                "max_processes": self.config.max_child_processes,
                "process_history_count": len(self.process_history)
            }
            
            # Get health status
            health_status = await self.health_checker.get_health_status()
            
            return {
                "status": "healthy" if health_status["overall_health"] else "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "system_metrics": system_metrics,
                "process_metrics": process_metrics,
                "health_details": health_status
            }
            
        except Exception as e:
            logger.error(f"Failed to get health status: {e}")
            raise HealthCheckError(f"Health check failed: {e}")
    
    async def restart_failed_processes(self) -> ProcessManagementResult:
        """
        Restart failed child processes.
        
        Automatically restarts processes that have failed
        within the retry limit configuration.
        
        Returns:
            ProcessManagementResult: Result of restart operations
        
        Raises:
            ProcessManagementError: If restart operations fail
            ResourceLimitError: If restart would exceed process limits
        """
        try:
            restarted_count = 0
            
            # Find failed processes in history
            for process_info in self.process_history:
                if (process_info.status == ProcessStatus.FAILED and 
                    process_info.directory and
                    not self._has_reached_retry_limit(process_info)):
                    
                    try:
                        await self.start_child_process(process_info.directory)
                        restarted_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to restart process for {process_info.directory}: {e}")
            
            return ProcessManagementResult(
                success=True,
                message=f"Restarted {restarted_count} failed processes"
            )
            
        except Exception as e:
            logger.error(f"Failed to restart failed processes: {e}")
            raise ProcessManagementError(f"Restart operations failed: {e}")
    
    async def cleanup_orphaned_processes(self) -> ProcessManagementResult:
        """
        Clean up orphaned child processes.
        
        Identifies and terminates child processes that are
        no longer responding or have become orphaned.
        
        Returns:
            ProcessManagementResult: Result of cleanup operations
        
        Raises:
            ProcessManagementError: If cleanup operations fail
        """
        try:
            cleaned_count = 0
            
            # Check each active process
            for process_id in list(self.active_processes.keys()):
                try:
                    process = psutil.Process(process_id)
                    
                    # Check if process is still running
                    if not process.is_running():
                        await self.stop_child_process(process_id)
                        cleaned_count += 1
                    
                    # Check if process is responsive
                    elif not self._is_process_responsive(process):
                        await self.stop_child_process(process_id)
                        cleaned_count += 1
                        
                except psutil.NoSuchProcess:
                    # Process no longer exists
                    await self.stop_child_process(process_id)
                    cleaned_count += 1
                except Exception as e:
                    logger.warning(f"Error checking process {process_id}: {e}")
                    # Consider process as orphaned if we can't check it
                    try:
                        await self.stop_child_process(process_id)
                        cleaned_count += 1
                    except Exception as stop_error:
                        logger.error(f"Failed to stop orphaned process {process_id}: {stop_error}")
            
            return ProcessManagementResult(
                success=True,
                message=f"Cleaned up {cleaned_count} orphaned processes"
            )
            
        except Exception as e:
            logger.error(f"Failed to cleanup orphaned processes: {e}")
            raise ProcessManagementError(f"Cleanup operations failed: {e}")
    
    async def _monitor_process_health(self) -> None:
        """
        Monitor health of child processes.
        
        Background task that continuously monitors the health
        and performance of all child processes.
        
        Raises:
            HealthCheckError: If health monitoring fails
        """
        try:
            while not self.shutdown_event.is_set():
                try:
                    # Update process metrics
                    await self._update_process_metrics()
                    
                    # Check for orphaned processes
                    await self.cleanup_orphaned_processes()
                    
                    # Wait for next check
                    await asyncio.sleep(self.config.health_check_interval)
                    
                except Exception as e:
                    logger.error(f"Error in health monitoring: {e}")
                    await asyncio.sleep(5)  # Short delay before retry
                    
        except asyncio.CancelledError:
            logger.info("Health monitoring cancelled")
        except Exception as e:
            logger.error(f"Health monitoring failed: {e}")
            raise HealthCheckError(f"Health monitoring failed: {e}")
    
    async def _handle_process_completion(self, process_id: int, exit_code: int) -> None:
        """
        Handle completion of a child process.
        
        Processes the completion of a child process, updates
        status, and triggers any necessary recovery actions.
        
        Args:
            process_id (int): ID of the completed process
            exit_code (int): Exit code of the process
        
        Raises:
            ProcessManagementError: If completion handling fails
        """
        try:
            if process_id not in self.active_processes:
                return
            
            process_info = self.active_processes[process_id]
            process_info.end_time = datetime.now()
            process_info.exit_code = exit_code
            
            if exit_code == 0:
                process_info.status = ProcessStatus.COMPLETED
                logger.info(f"Child process {process_id} completed successfully")
            else:
                process_info.status = ProcessStatus.FAILED
                process_info.error_message = f"Process exited with code {exit_code}"
                logger.error(f"Child process {process_id} failed with exit code {exit_code}")
            
            # Move to history
            self.process_history.append(process_info)
            del self.active_processes[process_id]
            
            # Remove lock
            if process_info.directory:
                try:
                    await self.lock_manager.remove_lock_by_directory(process_info.directory)
                except Exception as e:
                    logger.warning(f"Failed to remove lock for {process_info.directory}: {e}")
            
        except Exception as e:
            logger.error(f"Failed to handle process completion for {process_id}: {e}")
            raise ProcessManagementError(f"Completion handling failed: {e}")
    
    async def _handle_process_failure(self, process_id: int, error: Exception) -> None:
        """
        Handle failure of a child process.
        
        Processes the failure of a child process, logs the error,
        and initiates recovery procedures if enabled.
        
        Args:
            process_id (int): ID of the failed process
            error (Exception): Error that caused the failure
        
        Raises:
            ProcessManagementError: If failure handling fails
        """
        try:
            if process_id not in self.active_processes:
                return
            
            process_info = self.active_processes[process_id]
            process_info.status = ProcessStatus.FAILED
            process_info.end_time = datetime.now()
            process_info.error_message = str(error)
            
            logger.error(f"Child process {process_id} failed: {error}")
            
            # Move to history
            self.process_history.append(process_info)
            del self.active_processes[process_id]
            
            # Remove lock
            if process_info.directory:
                try:
                    await self.lock_manager.remove_lock_by_directory(process_info.directory)
                except Exception as e:
                    logger.warning(f"Failed to remove lock for {process_info.directory}: {e}")
            
            # Auto-recovery if enabled
            if (self.config.enable_auto_recovery and 
                process_info.directory and
                not self._has_reached_retry_limit(process_info)):
                
                try:
                    await self.start_child_process(process_info.directory)
                    logger.info(f"Auto-restarted process for {process_info.directory}")
                except Exception as restart_error:
                    logger.error(f"Auto-restart failed for {process_info.directory}: {restart_error}")
            
        except Exception as e:
            logger.error(f"Failed to handle process failure for {process_id}: {e}")
            raise ProcessManagementError(f"Failure handling failed: {e}")
    
    def _child_process_worker(self, directory: str) -> None:
        """
        Worker function for child processes.
        
        This function runs in a separate process and handles
        directory scanning, file processing, and chunking.
        
        Args:
            directory (str): Directory to process
        """
        try:
            # Set up logging for child process
            logging.basicConfig(level=logging.INFO)
            logger = logging.getLogger(__name__)
            
            logger.info(f"Child process started for directory: {directory}")
            
            # TODO: Implement actual directory processing logic
            # This would involve:
            # 1. Scanning the directory
            # 2. Processing files
            # 3. Creating chunks
            # 4. Saving to vector store
            
            logger.info(f"Child process completed for directory: {directory}")
            
        except Exception as e:
            logger.error(f"Child process failed for {directory}: {e}")
            sys.exit(1)
    
    async def _stop_all_child_processes(self) -> None:
        """Stop all active child processes."""
        for process_id in list(self.active_processes.keys()):
            try:
                await self.stop_child_process(process_id)
            except Exception as e:
                logger.error(f"Failed to stop process {process_id}: {e}")
    
    async def _update_process_metrics(self) -> None:
        """Update metrics for all active processes."""
        for process_id, process_info in self.active_processes.items():
            try:
                process = psutil.Process(process_id)
                process_info.memory_usage = process.memory_info().rss / 1024 / 1024  # MB
                process_info.cpu_usage = process.cpu_percent()
            except psutil.NoSuchProcess:
                # Process no longer exists
                pass
            except Exception as e:
                logger.warning(f"Failed to update metrics for process {process_id}: {e}")
    
    def _is_process_responsive(self, process: psutil.Process) -> bool:
        """Check if a process is responsive."""
        try:
            # Try to get process status
            process.status()
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def _has_reached_retry_limit(self, process_info: ProcessInfo) -> bool:
        """Check if process has reached retry limit."""
        if not self.config.enable_auto_recovery:
            return True
        
        # Count previous failures for this directory
        failure_count = 0
        for history_info in self.process_history:
            if (history_info.directory == process_info.directory and
                history_info.status == ProcessStatus.FAILED):
                failure_count += 1
        
        return failure_count >= self.config.max_retry_attempts


class ProcessManagementError(Exception):
    """Exception raised for process management errors."""
    pass


class ProcessNotFoundError(ProcessManagementError):
    """Exception raised when a process is not found."""
    pass


class ResourceLimitError(ProcessManagementError):
    """Exception raised when resource limits are exceeded."""
    pass


class HealthCheckError(ProcessManagementError):
    """Exception raised when health monitoring fails."""
    pass 