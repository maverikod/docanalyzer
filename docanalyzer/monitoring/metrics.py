"""
Metrics Collection - DocAnalyzer Metrics System

This module provides metrics collection capabilities for DocAnalyzer,
extending the mcp_proxy_adapter framework's monitoring system with
DocAnalyzer-specific metrics.

It includes processing metrics, system metrics, and integration with
the framework's metrics infrastructure.

Author: DocAnalyzer Team
Version: 1.0.0
"""

import time
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import threading
import json
import psutil
import os

# Import framework metrics components
try:
    from mcp_proxy_adapter.core.metrics import MetricsCollector as FrameworkMetricsCollector
    from mcp_proxy_adapter.core.monitoring import MetricType, MetricValue
except ImportError:
    # Fallback for development/testing
    FrameworkMetricsCollector = object
    MetricType = str
    MetricValue = Union[int, float, str]

logger = logging.getLogger(__name__)

# Metric types for DocAnalyzer
METRIC_TYPES = {
    'COUNTER': 'counter',
    'GAUGE': 'gauge',
    'HISTOGRAM': 'histogram',
    'SUMMARY': 'summary'
}

# Default metrics configuration
DEFAULT_METRICS_CONFIG = {
    'collection_interval': 60,  # seconds
    'retention_period': 24 * 60 * 60,  # 24 hours in seconds
    'max_metrics_count': 10000,
    'enable_persistence': True,
    'persistence_file': 'metrics/docanalyzer_metrics.json'
}


@dataclass
class ProcessingMetrics:
    """
    Processing Metrics - File Processing Statistics
    
    Collects and tracks metrics related to file processing operations
    in DocAnalyzer.
    
    Attributes:
        files_processed (int): Total number of files processed.
            Incremented for each successfully processed file.
        files_failed (int): Total number of files that failed processing.
            Incremented for each failed file processing.
        processing_time_total (float): Total time spent processing files.
            Accumulated processing time in seconds.
        processing_time_avg (float): Average processing time per file.
            Calculated as total_time / files_processed.
        chunks_created (int): Total number of chunks created.
            Incremented for each chunk created from files.
        bytes_processed (int): Total number of bytes processed.
            Accumulated file sizes processed.
        last_processed_file (Optional[str]): Path of the last processed file.
            Updated after each file processing.
        processing_errors (Dict[str, int]): Count of different error types.
            Maps error type to occurrence count.
    
    Example:
        >>> metrics = ProcessingMetrics()
        >>> metrics.record_file_processed("/path/to/file.txt", 1024, 1.5)
        >>> print(metrics.files_processed)  # 1
    """
    
    files_processed: int = 0
    files_failed: int = 0
    processing_time_total: float = 0.0
    processing_time_avg: float = 0.0
    chunks_created: int = 0
    bytes_processed: int = 0
    last_processed_file: Optional[str] = None
    processing_errors: Dict[str, int] = field(default_factory=dict)
    
    def record_file_processed(self, file_path: str, file_size: int, processing_time: float) -> None:
        """
        Record successful file processing.
        
        Args:
            file_path (str): Path of the processed file.
                Must be non-empty string.
            file_size (int): Size of the processed file in bytes.
                Must be non-negative integer.
            processing_time (float): Time taken to process the file in seconds.
                Must be non-negative float.
        
        Raises:
            ValueError: If parameters are invalid
        """
        if not file_path or not isinstance(file_path, str):
            raise ValueError("file_path must be non-empty string")
        
        if not isinstance(file_size, int) or file_size < 0:
            raise ValueError("file_size must be non-negative integer")
        
        if not isinstance(processing_time, (int, float)) or processing_time < 0:
            raise ValueError("processing_time must be non-negative number")
        
        self.files_processed += 1
        self.processing_time_total += processing_time
        self.bytes_processed += file_size
        self.last_processed_file = file_path
        
        # Update average processing time
        if self.files_processed > 0:
            self.processing_time_avg = self.processing_time_total / self.files_processed
        
        logger.debug(f"Recorded file processed: {file_path}, size: {file_size}, time: {processing_time}")
    
    def record_file_failed(self, file_path: str, error_type: str) -> None:
        """
        Record failed file processing.
        
        Args:
            file_path (str): Path of the file that failed.
                Must be non-empty string.
            error_type (str): Type of error that occurred.
                Must be non-empty string.
        
        Raises:
            ValueError: If parameters are invalid
        """
        if not file_path or not isinstance(file_path, str):
            raise ValueError("file_path must be non-empty string")
        
        if not error_type or not isinstance(error_type, str):
            raise ValueError("error_type must be non-empty string")
        
        self.files_failed += 1
        self.processing_errors[error_type] = self.processing_errors.get(error_type, 0) + 1
        
        logger.debug(f"Recorded file failed: {file_path}, error: {error_type}")
    
    def record_chunks_created(self, chunk_count: int) -> None:
        """
        Record chunks created from file processing.
        
        Args:
            chunk_count (int): Number of chunks created.
                Must be non-negative integer.
        
        Raises:
            ValueError: If chunk_count is negative
        """
        if not isinstance(chunk_count, int) or chunk_count < 0:
            raise ValueError("chunk_count must be non-negative integer")
        
        self.chunks_created += chunk_count
        logger.debug(f"Recorded chunks created: {chunk_count}")
    
    def get_processing_rate(self) -> float:
        """
        Calculate files processed per minute.
        
        Returns:
            float: Processing rate in files per minute.
                Returns 0.0 if no files have been processed.
        """
        if self.files_processed == 0:
            return 0.0
        
        # For now, return a simple calculation based on total processing time
        # In a real implementation, this would track time windows
        if self.processing_time_total > 0:
            return (self.files_processed / self.processing_time_total) * 60
        else:
            return 0.0
    
    def get_error_rate(self) -> float:
        """
        Calculate error rate as percentage.
        
        Returns:
            float: Error rate as percentage of total files.
                Returns 0.0 if no files have been processed.
        """
        total_files = self.files_processed + self.files_failed
        if total_files == 0:
            return 0.0
        
        return (self.files_failed / total_files) * 100
    
    def reset(self) -> None:
        """
        Reset all processing metrics to zero.
        
        Clears all counters and statistics while preserving
        the object structure.
        """
        self.files_processed = 0
        self.files_failed = 0
        self.processing_time_total = 0.0
        self.processing_time_avg = 0.0
        self.chunks_created = 0
        self.bytes_processed = 0
        self.last_processed_file = None
        self.processing_errors.clear()
        
        logger.debug("Processing metrics reset")


@dataclass
class SystemMetrics:
    """
    System Metrics - System Resource Statistics
    
    Collects and tracks system-level metrics for DocAnalyzer
    including resource usage and performance indicators.
    
    Attributes:
        memory_usage (float): Current memory usage in MB.
            Updated periodically.
        cpu_usage (float): Current CPU usage percentage.
            Updated periodically.
        disk_usage (float): Current disk usage percentage.
            Updated periodically.
        active_processes (int): Number of active processing processes.
            Count of currently running processes.
        queue_size (int): Current size of processing queue.
            Number of items waiting to be processed.
        uptime_seconds (float): System uptime in seconds.
            Time since system started.
        last_metrics_update (datetime): Timestamp of last metrics update.
            Used for calculating update intervals.
    
    Example:
        >>> metrics = SystemMetrics()
        >>> metrics.update_system_stats()
        >>> print(metrics.memory_usage)  # 512.5
    """
    
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    disk_usage: float = 0.0
    active_processes: int = 0
    queue_size: int = 0
    uptime_seconds: float = 0.0
    last_metrics_update: datetime = field(default_factory=datetime.now)
    
    def update_system_stats(self) -> None:
        """
        Update system statistics.
        
        Collects current system resource usage including
        memory, CPU, disk, and process information.
        
        Raises:
            SystemMetricsError: If system stats cannot be collected
        """
        try:
            # Update memory usage
            memory = psutil.virtual_memory()
            self.memory_usage = memory.used / (1024 * 1024)  # Convert to MB
            
            # Update CPU usage
            self.cpu_usage = psutil.cpu_percent(interval=0.1)
            
            # Update disk usage
            disk = psutil.disk_usage('/')
            self.disk_usage = (disk.used / disk.total) * 100
            
            # Update uptime
            self.uptime_seconds = time.time() - psutil.boot_time()
            
            # Update timestamp
            self.last_metrics_update = datetime.now()
            
            logger.debug(f"System stats updated: memory={self.memory_usage:.2f}MB, cpu={self.cpu_usage:.1f}%")
            
        except Exception as e:
            error_msg = f"Failed to update system stats: {e}"
            logger.error(error_msg)
            raise SystemMetricsError(error_msg, "system_stats", "update_system_stats")
    
    def get_memory_usage_mb(self) -> float:
        """
        Get current memory usage in MB.
        
        Returns:
            float: Memory usage in megabytes.
        """
        return self.memory_usage
    
    def get_cpu_usage_percent(self) -> float:
        """
        Get current CPU usage percentage.
        
        Returns:
            float: CPU usage as percentage (0-100).
        """
        return self.cpu_usage
    
    def get_disk_usage_percent(self) -> float:
        """
        Get current disk usage percentage.
        
        Returns:
            float: Disk usage as percentage (0-100).
        """
        return self.disk_usage
    
    def get_uptime_hours(self) -> float:
        """
        Get system uptime in hours.
        
        Returns:
            float: Uptime in hours.
        """
        return self.uptime_seconds / 3600


class MetricsCollector:
    """
    Metrics Collector - DocAnalyzer Metrics Management
    
    Main metrics collection class that manages all DocAnalyzer metrics
    and integrates with the mcp_proxy_adapter framework's metrics system.
    
    This class provides unified metrics collection interface for all
    DocAnalyzer components while maintaining compatibility with the framework.
    
    Attributes:
        processing_metrics (ProcessingMetrics): File processing metrics.
            Tracks file processing statistics.
        system_metrics (SystemMetrics): System resource metrics.
            Tracks system performance indicators.
        config (Dict[str, Any]): Metrics configuration.
            Contains collection settings and parameters.
        framework_collector (Optional[FrameworkMetricsCollector]): Framework metrics collector.
            Integration with framework metrics system.
        collection_thread (Optional[threading.Thread]): Background collection thread.
            Handles periodic metrics collection.
        is_collecting (bool): Whether metrics collection is active.
            Controls background collection thread.
    
    Example:
        >>> collector = MetricsCollector()
        >>> collector.start_collection()
        >>> collector.record_file_processed("/path/to/file.txt", 1024, 1.5)
        >>> metrics = collector.get_metrics_summary()
    
    Raises:
        MetricsError: When metrics operations fail
        ConfigurationError: When metrics configuration is invalid
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize MetricsCollector instance.
        
        Args:
            config (Optional[Dict[str, Any]], optional): Metrics configuration.
                Defaults to None. If None, uses default configuration.
        
        Raises:
            ConfigurationError: If configuration is invalid
        """
        self.config = DEFAULT_METRICS_CONFIG.copy()
        if config:
            self.config.update(config)
        
        self.processing_metrics = ProcessingMetrics()
        self.system_metrics = SystemMetrics()
        self.framework_collector = None
        self.collection_thread = None
        self.is_collecting = False
        
        # Try to initialize framework collector
        try:
            if FrameworkMetricsCollector != object:
                self.framework_collector = FrameworkMetricsCollector()
                logger.debug("Framework metrics collector initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize framework metrics collector: {e}")
        
        logger.info("MetricsCollector initialized")
    
    def record_operation(self, operation: str, duration: float, success: bool, result_count: int = 0) -> None:
        """
        Record operation metrics.
        
        Args:
            operation (str): Name of the operation.
                Must be non-empty string.
            duration (float): Duration of the operation in seconds.
                Must be non-negative float.
            success (bool): Whether the operation was successful.
            result_count (int): Number of results from the operation.
                Must be non-negative integer. Defaults to 0.
        
        Raises:
            ValueError: If parameters are invalid
            MetricsError: If recording fails
        """
        try:
            if not operation or not isinstance(operation, str):
                raise ValueError("operation must be non-empty string")
            
            if duration < 0:
                raise ValueError("duration must be non-negative")
            
            if result_count < 0:
                raise ValueError("result_count must be non-negative")
            
            # Record operation metrics
            self.operation_metrics.record_operation(operation, duration, success, result_count)
            logger.debug(f"Recorded operation: {operation}, duration: {duration}s, success: {success}")
            
        except Exception as e:
            error_msg = f"Failed to record operation: {e}"
            logger.error(error_msg)
            raise MetricsError(error_msg, "record_operation", "metrics")
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics.
        
        Returns:
            Dict[str, Any]: Current metrics data.
        """
        try:
            return {
                "ops": len(self.operation_metrics.operations),
                "files": len(self.processing_metrics.processed_files),
                "errors": len(self.error_metrics.errors)
            }
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return {}
    
    def start_collection(self) -> bool:
        """
        Start metrics collection.
        
        Initializes background collection thread and begins
        periodic metrics collection according to configuration.
        
        Returns:
            bool: True if collection started successfully.
        
        Raises:
            MetricsError: If collection cannot be started
        """
        try:
            if self.is_collecting:
                logger.warning("Metrics collection already running")
                return True
            
            self.is_collecting = True
            self.collection_thread = threading.Thread(
                target=self._collection_worker,
                daemon=True,
                name="MetricsCollector"
            )
            self.collection_thread.start()
            
            logger.info("Metrics collection started")
            return True
            
        except Exception as e:
            error_msg = f"Failed to start metrics collection: {e}"
            logger.error(error_msg)
            raise MetricsError(error_msg, "start_collection", "metrics")
    
    def stop_collection(self) -> bool:
        """
        Stop metrics collection.
        
        Stops background collection thread and saves
        final metrics data.
        
        Returns:
            bool: True if collection stopped successfully.
        
        Raises:
            MetricsError: If collection cannot be stopped
        """
        try:
            if not self.is_collecting:
                logger.warning("Metrics collection not running")
                return True
            
            self.is_collecting = False
            
            if self.collection_thread and self.collection_thread.is_alive():
                self.collection_thread.join(timeout=5)
            
            logger.info("Metrics collection stopped")
            return True
            
        except Exception as e:
            error_msg = f"Failed to stop metrics collection: {e}"
            logger.error(error_msg)
            raise MetricsError(error_msg, "stop_collection", "metrics")
    
    def record_file_processed(self, file_path: str, file_size: int, processing_time: float) -> None:
        """
        Record successful file processing.
        
        Args:
            file_path (str): Path of the processed file.
                Must be non-empty string.
            file_size (int): Size of the processed file in bytes.
                Must be non-negative integer.
            processing_time (float): Time taken to process the file in seconds.
                Must be non-negative float.
        
        Raises:
            ValueError: If parameters are invalid
            MetricsError: If recording fails
        """
        try:
            self.processing_metrics.record_file_processed(file_path, file_size, processing_time)
        except Exception as e:
            error_msg = f"Failed to record file processed: {e}"
            raise MetricsError(error_msg, "record_file_processed", "processing")
    
    def _collection_worker(self) -> None:
        """
        Background worker for metrics collection.
        
        Runs in a separate thread and periodically updates
        system metrics according to configuration.
        """
        while self.is_collecting:
            try:
                self.update_system_metrics()
                time.sleep(self.config['collection_interval'])
            except Exception as e:
                logger.error(f"Error in metrics collection worker: {e}")
                time.sleep(5)  # Wait before retrying
    
    def record_file_failed(self, file_path: str, error_type: str) -> None:
        """
        Record failed file processing.
        
        Args:
            file_path (str): Path of the file that failed.
                Must be non-empty string.
            error_type (str): Type of error that occurred.
                Must be non-empty string.
        
        Raises:
            ValueError: If parameters are invalid
            MetricsError: If recording fails
        """
        try:
            self.processing_metrics.record_file_failed(file_path, error_type)
        except Exception as e:
            error_msg = f"Failed to record file failed: {e}"
            raise MetricsError(error_msg, "record_file_failed", "processing")
    
    def record_chunks_created(self, chunk_count: int) -> None:
        """
        Record chunks created from file processing.
        
        Args:
            chunk_count (int): Number of chunks created.
                Must be non-negative integer.
        
        Raises:
            ValueError: If chunk_count is negative
            MetricsError: If recording fails
        """
        try:
            self.processing_metrics.record_chunks_created(chunk_count)
        except Exception as e:
            error_msg = f"Failed to record chunks created: {e}"
            raise MetricsError(error_msg, "record_chunks_created", "processing")
    
    def update_system_metrics(self) -> None:
        """
        Update system metrics.
        
        Collects current system resource usage and updates
        system metrics accordingly.
        
        Raises:
            MetricsError: If system metrics cannot be updated
        """
        try:
            self.system_metrics.update_system_stats()
        except Exception as e:
            error_msg = f"Failed to update system metrics: {e}"
            raise MetricsError(error_msg, "update_system_metrics", "system")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive metrics summary.
        
        Returns:
            Dict[str, Any]: Complete metrics summary including
                processing metrics, system metrics, and calculated
                statistics.
        """
        return {
            'processing': {
                'files_processed': self.processing_metrics.files_processed,
                'files_failed': self.processing_metrics.files_failed,
                'processing_time_total': self.processing_metrics.processing_time_total,
                'processing_time_avg': self.processing_metrics.processing_time_avg,
                'chunks_created': self.processing_metrics.chunks_created,
                'bytes_processed': self.processing_metrics.bytes_processed,
                'last_processed_file': self.processing_metrics.last_processed_file,
                'processing_errors': self.processing_metrics.processing_errors,
                'processing_rate': self.processing_metrics.get_processing_rate(),
                'error_rate': self.processing_metrics.get_error_rate()
            },
            'system': {
                'memory_usage_mb': self.system_metrics.get_memory_usage_mb(),
                'cpu_usage_percent': self.system_metrics.get_cpu_usage_percent(),
                'disk_usage_percent': self.system_metrics.get_disk_usage_percent(),
                'uptime_hours': self.system_metrics.get_uptime_hours(),
                'last_metrics_update': self.system_metrics.last_metrics_update.isoformat() if self.system_metrics.last_metrics_update else None
            },
            'collection': {
                'is_collecting': self.is_collecting,
                'collection_interval': self.config['collection_interval']
            }
        }
    
    def get_processing_metrics(self) -> ProcessingMetrics:
        """
        Get current processing metrics.
        
        Returns:
            ProcessingMetrics: Current processing metrics instance.
        """
        return self.processing_metrics
    
    def get_system_metrics(self) -> SystemMetrics:
        """
        Get current system metrics.
        
        Returns:
            SystemMetrics: Current system metrics instance.
        """
        return self.system_metrics
    
    def save_metrics(self, file_path: str) -> bool:
        """
        Save metrics to file.
        
        Args:
            file_path (str): Path to save metrics file.
                Must be writable path.
        
        Returns:
            bool: True if metrics were saved successfully.
        
        Raises:
            MetricsError: If metrics cannot be saved
        """
        try:
            metrics_data = self.get_metrics_summary()
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w') as f:
                json.dump(metrics_data, f, indent=2, default=str)
            
            logger.info(f"Metrics saved to {file_path}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to save metrics to {file_path}: {e}"
            logger.error(error_msg)
            raise MetricsError(error_msg, "save_metrics", "persistence")
    
    def load_metrics(self, file_path: str) -> bool:
        """
        Load metrics from file.
        
        Args:
            file_path (str): Path to load metrics from.
                Must be existing readable file.
        
        Returns:
            bool: True if metrics were loaded successfully.
        
        Raises:
            MetricsError: If metrics cannot be loaded
        """
        try:
            with open(file_path, 'r') as f:
                metrics_data = json.load(f)
            
            # Load processing metrics
            if 'processing' in metrics_data:
                proc_data = metrics_data['processing']
                self.processing_metrics.files_processed = proc_data.get('files_processed', 0)
                self.processing_metrics.files_failed = proc_data.get('files_failed', 0)
                self.processing_metrics.processing_time_total = proc_data.get('processing_time_total', 0.0)
                self.processing_metrics.processing_time_avg = proc_data.get('processing_time_avg', 0.0)
                self.processing_metrics.chunks_created = proc_data.get('chunks_created', 0)
                self.processing_metrics.bytes_processed = proc_data.get('bytes_processed', 0)
                self.processing_metrics.last_processed_file = proc_data.get('last_processed_file')
                self.processing_metrics.processing_errors = proc_data.get('processing_errors', {})
            
            logger.info(f"Metrics loaded from {file_path}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to load metrics from {file_path}: {e}"
            logger.error(error_msg)
            raise MetricsError(error_msg, "load_metrics", "persistence")
    
    def reset_metrics(self) -> None:
        """
        Reset all metrics to zero.
        
        Clears all counters and statistics while preserving
        the collection configuration.
        """
        self.processing_metrics.reset()
        self.system_metrics = SystemMetrics()
        logger.info("All metrics reset")


class MetricsError(Exception):
    """
    Metrics Error - Exception for metrics operations.
    
    Raised when metrics operations fail, such as when trying to
    record metrics with invalid data or when metrics collection
    cannot be started.
    
    Attributes:
        message (str): Error message describing the metrics failure
        operation (Optional[str]): Operation that failed
        metric_type (Optional[str]): Type of metric involved in the error
    """
    
    def __init__(self, message: str, operation: Optional[str] = None, metric_type: Optional[str] = None):
        """
        Initialize MetricsError instance.
        
        Args:
            message (str): Error message describing the metrics failure
            operation (Optional[str]): Operation that failed
            metric_type (Optional[str]): Type of metric involved in the error
        """
        super().__init__(message)
        self.message = message
        self.operation = operation
        self.metric_type = metric_type


class SystemMetricsError(Exception):
    """
    System Metrics Error - Exception for system metrics operations.
    
    Raised when system metrics collection fails, such as when
    trying to access system resources that are not available
    or when system information cannot be retrieved.
    
    Attributes:
        message (str): Error message describing the system metrics failure
        resource (Optional[str]): System resource that caused the error
        operation (Optional[str]): Operation that failed
    """
    
    def __init__(self, message: str, resource: Optional[str] = None, operation: Optional[str] = None):
        """
        Initialize SystemMetricsError instance.
        
        Args:
            message (str): Error message describing the system metrics failure
            resource (Optional[str]): System resource that caused the error
            operation (Optional[str]): Operation that failed
        """
        super().__init__(message)
        self.message = message
        self.resource = resource
        self.operation = operation 