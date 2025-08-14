"""
Performance Models - Performance Data Structures

Defines data structures for performance metrics, optimization results,
and system performance monitoring used throughout the DocAnalyzer system.

These models provide standardized interfaces for collecting, storing,
and analyzing performance data across all system components.

Author: Performance Team
Version: 1.0.0
"""

import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class OptimizationType(Enum):
    """Types of performance optimizations."""
    
    MEMORY = "memory"
    CPU = "cpu"
    CACHE = "cache"
    BATCH_SIZE = "batch_size"
    NETWORK = "network"
    DISK_IO = "disk_io"


class PerformanceStatus(Enum):
    """Performance status levels."""
    
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class PerformanceMetrics:
    """
    System performance metrics.
    
    Comprehensive collection of system performance metrics including
    CPU, memory, disk I/O, and network usage statistics.
    
    Attributes:
        timestamp (datetime): Metrics collection timestamp.
        cpu_usage_percent (float): CPU usage percentage (0.0 to 100.0).
        memory_usage_percent (float): Memory usage percentage (0.0 to 100.0).
        memory_available_mb (float): Available memory in MB.
        memory_total_mb (float): Total memory in MB.
        disk_io_read_mb_s (float): Disk read speed in MB/s.
        disk_io_write_mb_s (float): Disk write speed in MB/s.
        network_sent_mb_s (float): Network sent speed in MB/s.
        network_recv_mb_s (float): Network received speed in MB/s.
        active_processes (int): Number of active processes.
        open_files (int): Number of open files.
        load_average_1m (float): 1-minute load average.
        load_average_5m (float): 5-minute load average.
        load_average_15m (float): 15-minute load average.
        uptime_seconds (float): System uptime in seconds.
        performance_status (PerformanceStatus): Overall performance status.
        custom_metrics (Dict[str, Any]): Additional custom metrics.
    """
    
    timestamp: datetime = field(default_factory=datetime.now)
    cpu_usage_percent: float = 0.0
    memory_usage_percent: float = 0.0
    memory_available_mb: float = 0.0
    memory_total_mb: float = 0.0
    disk_io_read_mb_s: float = 0.0
    disk_io_write_mb_s: float = 0.0
    network_sent_mb_s: float = 0.0
    network_recv_mb_s: float = 0.0
    active_processes: int = 0
    open_files: int = 0
    load_average_1m: float = 0.0
    load_average_5m: float = 0.0
    load_average_15m: float = 0.0
    uptime_seconds: float = 0.0
    performance_status: PerformanceStatus = PerformanceStatus.GOOD
    custom_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OptimizationResult:
    """
    Result of a performance optimization operation.
    
    Contains detailed information about the results of applying
    performance optimizations including success status, improvements,
    and any issues encountered.
    
    Attributes:
        optimization_type (OptimizationType): Type of optimization applied.
        success (bool): Whether optimization was successful.
        timestamp (datetime): Optimization timestamp.
        duration_ms (float): Optimization duration in milliseconds.
        improvements (Dict[str, float]): Measured improvements.
        issues (List[str]): Issues encountered during optimization.
        recommendations (List[str]): Additional recommendations.
        metrics_before (PerformanceMetrics): Metrics before optimization.
        metrics_after (PerformanceMetrics): Metrics after optimization.
        configuration_changes (Dict[str, Any]): Configuration changes made.
    """
    
    optimization_type: OptimizationType
    success: bool
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0.0
    improvements: Dict[str, float] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metrics_before: Optional[PerformanceMetrics] = None
    metrics_after: Optional[PerformanceMetrics] = None
    configuration_changes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingPerformanceMetrics:
    """
    File processing performance metrics.
    
    Specific metrics for file processing operations including
    processing speed, throughput, and efficiency measurements.
    
    Attributes:
        files_processed (int): Number of files processed.
        total_processing_time_ms (float): Total processing time in milliseconds.
        average_processing_time_ms (float): Average processing time per file.
        processing_throughput_files_s (float): Files processed per second.
        total_chunks_created (int): Total number of chunks created.
        average_chunks_per_file (float): Average chunks per file.
        memory_peak_mb (float): Peak memory usage during processing.
        cpu_peak_percent (float): Peak CPU usage during processing.
        cache_hit_rate (float): Cache hit rate (0.0 to 1.0).
        error_count (int): Number of processing errors.
        success_rate (float): Processing success rate (0.0 to 1.0).
        custom_metrics (Dict[str, Any]): Additional custom metrics.
    """
    
    files_processed: int = 0
    total_processing_time_ms: float = 0.0
    average_processing_time_ms: float = 0.0
    processing_throughput_files_s: float = 0.0
    total_chunks_created: int = 0
    average_chunks_per_file: float = 0.0
    memory_peak_mb: float = 0.0
    cpu_peak_percent: float = 0.0
    cache_hit_rate: float = 0.0
    error_count: int = 0
    success_rate: float = 1.0
    custom_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceThreshold:
    """
    Performance threshold configuration.
    
    Defines thresholds for various performance metrics to trigger
    alerts or automatic optimizations.
    
    Attributes:
        cpu_warning_threshold (float): CPU usage warning threshold (0.0 to 1.0).
        cpu_critical_threshold (float): CPU usage critical threshold (0.0 to 1.0).
        memory_warning_threshold (float): Memory usage warning threshold (0.0 to 1.0).
        memory_critical_threshold (float): Memory usage critical threshold (0.0 to 1.0).
        disk_io_warning_threshold (float): Disk I/O warning threshold in MB/s.
        disk_io_critical_threshold (float): Disk I/O critical threshold in MB/s.
        network_warning_threshold (float): Network usage warning threshold in MB/s.
        network_critical_threshold (float): Network usage critical threshold in MB/s.
        processing_time_warning_ms (float): Processing time warning threshold in ms.
        processing_time_critical_ms (float): Processing time critical threshold in ms.
        cache_hit_rate_warning (float): Cache hit rate warning threshold (0.0 to 1.0).
        cache_hit_rate_critical (float): Cache hit rate critical threshold (0.0 to 1.0).
    """
    
    cpu_warning_threshold: float = 0.7
    cpu_critical_threshold: float = 0.9
    memory_warning_threshold: float = 0.8
    memory_critical_threshold: float = 0.95
    disk_io_warning_threshold: float = 100.0
    disk_io_critical_threshold: float = 200.0
    network_warning_threshold: float = 50.0
    network_critical_threshold: float = 100.0
    processing_time_warning_ms: float = 5000.0
    processing_time_critical_ms: float = 10000.0
    cache_hit_rate_warning: float = 0.7
    cache_hit_rate_critical: float = 0.5


@dataclass
class PerformanceAlert:
    """
    Performance alert notification.
    
    Represents a performance alert triggered when metrics exceed
    configured thresholds.
    
    Attributes:
        alert_id (str): Unique alert identifier.
        alert_type (str): Type of alert (warning, critical, info).
        metric_name (str): Name of the metric that triggered alert.
        current_value (float): Current metric value.
        threshold_value (float): Threshold value that was exceeded.
        timestamp (datetime): Alert timestamp.
        message (str): Human-readable alert message.
        recommendations (List[str]): Recommended actions.
        acknowledged (bool): Whether alert has been acknowledged.
        resolved (bool): Whether alert has been resolved.
    """
    
    alert_id: str
    alert_type: str
    metric_name: str
    current_value: float
    threshold_value: float
    timestamp: datetime = field(default_factory=datetime.now)
    message: str = ""
    recommendations: List[str] = field(default_factory=list)
    acknowledged: bool = False
    resolved: bool = False


@dataclass
class PerformanceReport:
    """
    Comprehensive performance report.
    
    Complete performance report containing current metrics, historical data,
    optimization results, and recommendations.
    
    Attributes:
        report_id (str): Unique report identifier.
        generated_at (datetime): Report generation timestamp.
        time_period_start (datetime): Start of reporting period.
        time_period_end (datetime): End of reporting period.
        current_metrics (PerformanceMetrics): Current system metrics.
        historical_metrics (List[PerformanceMetrics]): Historical metrics.
        optimization_results (List[OptimizationResult]): Applied optimizations.
        processing_metrics (ProcessingPerformanceMetrics): Processing performance.
        alerts (List[PerformanceAlert]): Active performance alerts.
        recommendations (List[str]): Performance recommendations.
        summary (Dict[str, Any]): Executive summary.
    """
    
    report_id: str
    generated_at: datetime = field(default_factory=datetime.now)
    time_period_start: datetime = field(default_factory=datetime.now)
    time_period_end: datetime = field(default_factory=datetime.now)
    current_metrics: Optional[PerformanceMetrics] = None
    historical_metrics: List[PerformanceMetrics] = field(default_factory=list)
    optimization_results: List[OptimizationResult] = field(default_factory=list)
    processing_metrics: Optional[ProcessingPerformanceMetrics] = None
    alerts: List[PerformanceAlert] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict) 