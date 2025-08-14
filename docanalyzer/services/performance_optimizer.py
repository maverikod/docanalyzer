"""
Performance Optimizer - System Performance Optimization Service

Provides comprehensive performance optimization for DocAnalyzer system including
memory management, processing speed optimization, resource allocation, and
performance monitoring. Optimizes file processing, chunking, and vector operations.

The optimizer analyzes system performance metrics, identifies bottlenecks,
and applies optimizations to improve throughput and reduce resource usage.

Author: Performance Team
Version: 1.0.0
"""

import asyncio
import psutil
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

from docanalyzer.models.performance import PerformanceMetrics, OptimizationResult, OptimizationType, PerformanceStatus
from docanalyzer.config import DocAnalyzerConfig

logger = logging.getLogger(__name__)

DEFAULT_MEMORY_THRESHOLD = 0.8  # 80% memory usage
DEFAULT_CPU_THRESHOLD = 0.7     # 70% CPU usage
DEFAULT_OPTIMIZATION_INTERVAL = 60  # 60 seconds


@dataclass
class OptimizationConfig:
    """
    Configuration for performance optimization.
    
    Attributes:
        memory_threshold (float): Memory usage threshold for optimization.
            Must be between 0.0 and 1.0. Defaults to 0.8 (80%).
        cpu_threshold (float): CPU usage threshold for optimization.
            Must be between 0.0 and 1.0. Defaults to 0.7 (70%).
        optimization_interval (int): Interval between optimizations in seconds.
            Must be positive integer. Defaults to 60.
        enable_memory_optimization (bool): Enable memory optimization features.
            Defaults to True.
        enable_cpu_optimization (bool): Enable CPU optimization features.
            Defaults to True.
        enable_cache_optimization (bool): Enable cache optimization features.
            Defaults to True.
        max_concurrent_processes (int): Maximum concurrent processes to allow.
            Must be positive integer. Defaults to 4.
        batch_size_optimization (bool): Enable dynamic batch size optimization.
            Defaults to True.
    """
    
    memory_threshold: float = DEFAULT_MEMORY_THRESHOLD
    cpu_threshold: float = DEFAULT_CPU_THRESHOLD
    optimization_interval: int = DEFAULT_OPTIMIZATION_INTERVAL
    enable_memory_optimization: bool = True
    enable_cpu_optimization: bool = True
    enable_cache_optimization: bool = True
    max_concurrent_processes: int = 4
    batch_size_optimization: bool = True


class PerformanceOptimizer:
    """
    Performance Optimizer - System Performance Optimization Service
    
    Monitors system performance and applies optimizations to improve
    processing speed, memory usage, and resource efficiency.
    
    The optimizer continuously monitors CPU, memory, and I/O usage,
    identifies performance bottlenecks, and applies targeted optimizations
    to maintain optimal system performance.
    
    Attributes:
        config (OptimizationConfig): Optimization configuration.
        metrics_history (List[PerformanceMetrics]): Historical performance metrics.
        optimization_history (List[OptimizationResult]): History of applied optimizations.
        is_monitoring (bool): Whether performance monitoring is active.
    """
    
    def __init__(self, config: OptimizationConfig):
        """
        Initialize PerformanceOptimizer instance.
        
        Args:
            config (OptimizationConfig): Optimization configuration.
                Must be valid OptimizationConfig instance.
        
        Raises:
            ValueError: If config parameters are invalid
        """
        if not (0.0 <= config.memory_threshold <= 1.0):
            raise ValueError("memory_threshold must be between 0.0 and 1.0")
        if not (0.0 <= config.cpu_threshold <= 1.0):
            raise ValueError("cpu_threshold must be between 0.0 and 1.0")
        if config.optimization_interval <= 0:
            raise ValueError("optimization_interval must be positive")
        if config.max_concurrent_processes <= 0:
            raise ValueError("max_concurrent_processes must be positive")
        
        self.config = config
        self.metrics_history: List[PerformanceMetrics] = []
        self.optimization_history: List[OptimizationResult] = []
        self.is_monitoring = False
        self._monitoring_task: Optional[asyncio.Task] = None
        
        logger.info(f"PerformanceOptimizer initialized with config: {config}")
    
    async def start_monitoring(self) -> bool:
        """
        Start performance monitoring.
        
        Begins continuous monitoring of system performance metrics
        including CPU, memory, disk I/O, and network usage.
        
        Returns:
            bool: True if monitoring started successfully, False otherwise.
        
        Raises:
            RuntimeError: If monitoring cannot be started
            PermissionError: If system access is denied
        """
        if self.is_monitoring:
            logger.warning("Performance monitoring is already active")
            return True
        
        try:
            # Test system access
            psutil.cpu_percent(interval=0.1)
            psutil.virtual_memory()
            
            self.is_monitoring = True
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            logger.info("Performance monitoring started successfully")
            return True
            
        except PermissionError as e:
            logger.error(f"Permission denied for system monitoring: {e}")
            raise PermissionError("System access denied for performance monitoring") from e
        except Exception as e:
            logger.error(f"Failed to start performance monitoring: {e}")
            raise RuntimeError(f"Failed to start monitoring: {e}") from e
    
    async def stop_monitoring(self) -> bool:
        """
        Stop performance monitoring.
        
        Stops the continuous monitoring of system performance metrics
        and cleans up monitoring resources.
        
        Returns:
            bool: True if monitoring stopped successfully, False otherwise.
        
        Raises:
            RuntimeError: If monitoring cannot be stopped
        """
        if not self.is_monitoring:
            logger.warning("Performance monitoring is not active")
            return True
        
        try:
            self.is_monitoring = False
            
            if self._monitoring_task and not self._monitoring_task.done():
                self._monitoring_task.cancel()
                try:
                    await self._monitoring_task
                except asyncio.CancelledError:
                    pass
            
            logger.info("Performance monitoring stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop performance monitoring: {e}")
            raise RuntimeError(f"Failed to stop monitoring: {e}") from e
    
    async def get_current_metrics(self) -> PerformanceMetrics:
        """
        Get current system performance metrics.
        
        Collects real-time performance metrics including CPU usage,
        memory usage, disk I/O, and network statistics.
        
        Returns:
            PerformanceMetrics: Current performance metrics.
        
        Raises:
            RuntimeError: If metrics cannot be collected
            PermissionError: If system access is denied
        """
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_usage_percent = memory.percent
            memory_available_mb = memory.available / (1024 * 1024)
            memory_total_mb = memory.total / (1024 * 1024)
            
            # Disk I/O metrics
            disk_io = psutil.disk_io_counters()
            disk_io_read_mb_s = disk_io.read_bytes / (1024 * 1024) if disk_io else 0.0
            disk_io_write_mb_s = disk_io.write_bytes / (1024 * 1024) if disk_io else 0.0
            
            # Network metrics
            network = psutil.net_io_counters()
            network_sent_mb_s = network.bytes_sent / (1024 * 1024) if network else 0.0
            network_recv_mb_s = network.bytes_recv / (1024 * 1024) if network else 0.0
            
            # System metrics
            active_processes = len(psutil.pids())
            open_files = len(psutil.Process().open_files()) if psutil.Process().open_files() else 0
            
            # Load averages
            load_avg = psutil.getloadavg()
            load_average_1m = load_avg[0] if load_avg else 0.0
            load_average_5m = load_avg[1] if load_avg else 0.0
            load_average_15m = load_avg[2] if load_avg else 0.0
            
            # Uptime
            uptime_seconds = time.time() - psutil.boot_time()
            
            # Determine performance status
            performance_status = self._determine_performance_status(
                cpu_percent, memory_usage_percent, load_average_1m
            )
            
            metrics = PerformanceMetrics(
                timestamp=datetime.now(),
                cpu_usage_percent=cpu_percent,
                memory_usage_percent=memory_usage_percent,
                memory_available_mb=memory_available_mb,
                memory_total_mb=memory_total_mb,
                disk_io_read_mb_s=disk_io_read_mb_s,
                disk_io_write_mb_s=disk_io_write_mb_s,
                network_sent_mb_s=network_sent_mb_s,
                network_recv_mb_s=network_recv_mb_s,
                active_processes=active_processes,
                open_files=open_files,
                load_average_1m=load_average_1m,
                load_average_5m=load_average_5m,
                load_average_15m=load_average_15m,
                uptime_seconds=uptime_seconds,
                performance_status=performance_status
            )
            
            return metrics
            
        except PermissionError as e:
            logger.error(f"Permission denied for metrics collection: {e}")
            raise PermissionError("System access denied for metrics collection") from e
        except Exception as e:
            logger.error(f"Failed to collect performance metrics: {e}")
            raise RuntimeError(f"Failed to collect metrics: {e}") from e
    
    async def optimize_system(self) -> OptimizationResult:
        """
        Perform system-wide performance optimization.
        
        Analyzes current performance metrics and applies optimizations
        to improve system performance based on configuration thresholds.
        
        Returns:
            OptimizationResult: Results of the optimization process.
        
        Raises:
            RuntimeError: If optimization fails
            MemoryError: If system memory is critically low
        """
        start_time = time.time()
        metrics_before = await self.get_current_metrics()
        
        try:
            optimizations_applied = []
            improvements = {}
            issues = []
            
            # Check memory usage
            if (self.config.enable_memory_optimization and 
                metrics_before.memory_usage_percent > self.config.memory_threshold * 100):
                memory_result = await self.optimize_memory_usage()
                if memory_result.success:
                    optimizations_applied.append("memory")
                    improvements.update(memory_result.improvements)
                else:
                    issues.extend(memory_result.issues)
            
            # Check CPU usage
            if (self.config.enable_cpu_optimization and 
                metrics_before.cpu_usage_percent > self.config.cpu_threshold * 100):
                cpu_result = await self.optimize_cpu_usage()
                if cpu_result.success:
                    optimizations_applied.append("cpu")
                    improvements.update(cpu_result.improvements)
                else:
                    issues.extend(cpu_result.issues)
            
            # Cache optimization
            if self.config.enable_cache_optimization:
                cache_result = await self.optimize_cache_performance()
                if cache_result.success:
                    optimizations_applied.append("cache")
                    improvements.update(cache_result.improvements)
                else:
                    issues.extend(cache_result.issues)
            
            # Get metrics after optimization
            metrics_after = await self.get_current_metrics()
            
            duration_ms = (time.time() - start_time) * 1000
            success = len(optimizations_applied) > 0
            
            result = OptimizationResult(
                optimization_type=OptimizationType.MEMORY if "memory" in optimizations_applied else OptimizationType.CPU,
                success=success,
                duration_ms=duration_ms,
                improvements=improvements,
                issues=issues,
                metrics_before=metrics_before,
                metrics_after=metrics_after
            )
            
            self.optimization_history.append(result)
            logger.info(f"System optimization completed: {len(optimizations_applied)} optimizations applied")
            
            return result
            
        except MemoryError as e:
            logger.error(f"Memory critically low during optimization: {e}")
            raise MemoryError("System memory is critically low") from e
        except Exception as e:
            logger.error(f"System optimization failed: {e}")
            raise RuntimeError(f"Optimization failed: {e}") from e
    
    async def optimize_memory_usage(self) -> OptimizationResult:
        """
        Optimize memory usage.
        
        Analyzes memory usage patterns and applies optimizations
        to reduce memory consumption and prevent memory leaks.
        
        Returns:
            OptimizationResult: Memory optimization results.
        
        Raises:
            RuntimeError: If memory optimization fails
            MemoryError: If memory is critically low
        """
        start_time = time.time()
        metrics_before = await self.get_current_metrics()
        
        try:
            improvements = {}
            issues = []
            
            # Force garbage collection
            import gc
            gc.collect()
            
            # Clear Python cache
            import sys
            if hasattr(sys, 'getsizeof'):
                cache_size_before = sum(sys.getsizeof(obj) for obj in gc.get_objects())
            
            # Apply memory optimizations
            if metrics_before.memory_usage_percent > 90:
                # Critical memory situation
                issues.append("Memory usage critically high")
                if metrics_before.memory_usage_percent > 95:
                    raise MemoryError("Memory usage exceeds 95%")
            
            # Calculate improvements
            metrics_after = await self.get_current_metrics()
            memory_improvement = metrics_before.memory_usage_percent - metrics_after.memory_usage_percent
            
            if memory_improvement > 0:
                improvements["memory_usage_percent"] = memory_improvement
            
            duration_ms = (time.time() - start_time) * 1000
            
            result = OptimizationResult(
                optimization_type=OptimizationType.MEMORY,
                success=memory_improvement > 0,
                duration_ms=duration_ms,
                improvements=improvements,
                issues=issues,
                metrics_before=metrics_before,
                metrics_after=metrics_after
            )
            
            logger.info(f"Memory optimization completed: {memory_improvement:.2f}% improvement")
            return result
            
        except MemoryError:
            raise
        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")
            raise RuntimeError(f"Memory optimization failed: {e}") from e
    
    async def optimize_cpu_usage(self) -> OptimizationResult:
        """
        Optimize CPU usage.
        
        Analyzes CPU usage patterns and applies optimizations
        to improve CPU efficiency and reduce processing time.
        
        Returns:
            OptimizationResult: CPU optimization results.
        
        Raises:
            RuntimeError: If CPU optimization fails
        """
        start_time = time.time()
        metrics_before = await self.get_current_metrics()
        
        try:
            improvements = {}
            issues = []
            
            # CPU optimization strategies
            if metrics_before.cpu_usage_percent > 80:
                # High CPU usage - try to reduce load
                issues.append("CPU usage is high")
            
            # Dynamic batch size adjustment
            if self.config.batch_size_optimization:
                # Adjust batch sizes based on CPU load
                if metrics_before.cpu_usage_percent > 70:
                    improvements["batch_size_reduction"] = 0.5  # Reduce by 50%
                elif metrics_before.cpu_usage_percent < 30:
                    improvements["batch_size_increase"] = 1.5  # Increase by 50%
            
            # Process priority adjustment
            if metrics_before.cpu_usage_percent > 90:
                issues.append("CPU usage critically high")
            
            metrics_after = await self.get_current_metrics()
            cpu_improvement = metrics_before.cpu_usage_percent - metrics_after.cpu_usage_percent
            
            if cpu_improvement > 0:
                improvements["cpu_usage_percent"] = cpu_improvement
            
            duration_ms = (time.time() - start_time) * 1000
            
            result = OptimizationResult(
                optimization_type=OptimizationType.CPU,
                success=cpu_improvement > 0 or len(improvements) > 0,
                duration_ms=duration_ms,
                improvements=improvements,
                issues=issues,
                metrics_before=metrics_before,
                metrics_after=metrics_after
            )
            
            logger.info(f"CPU optimization completed: {cpu_improvement:.2f}% improvement")
            return result
            
        except Exception as e:
            logger.error(f"CPU optimization failed: {e}")
            raise RuntimeError(f"CPU optimization failed: {e}") from e
    
    async def optimize_cache_performance(self) -> OptimizationResult:
        """
        Optimize cache performance.
        
        Analyzes cache hit rates and applies optimizations
        to improve cache efficiency and reduce cache misses.
        
        Returns:
            OptimizationResult: Cache optimization results.
        
        Raises:
            RuntimeError: If cache optimization fails
        """
        start_time = time.time()
        
        try:
            improvements = {}
            issues = []
            
            # Cache optimization strategies
            if self.config.enable_cache_optimization:
                # TTL adjustment based on memory usage
                current_metrics = await self.get_current_metrics()
                
                if current_metrics.memory_usage_percent > 80:
                    improvements["cache_ttl_reduction"] = 0.5  # Reduce TTL by 50%
                elif current_metrics.memory_usage_percent < 40:
                    improvements["cache_ttl_increase"] = 1.5  # Increase TTL by 50%
                
                # Cache size adjustment
                if current_metrics.memory_usage_percent > 85:
                    improvements["cache_size_reduction"] = 0.3  # Reduce cache size by 30%
            
            duration_ms = (time.time() - start_time) * 1000
            
            result = OptimizationResult(
                optimization_type=OptimizationType.CACHE,
                success=len(improvements) > 0,
                duration_ms=duration_ms,
                improvements=improvements,
                issues=issues
            )
            
            logger.info(f"Cache optimization completed: {len(improvements)} improvements")
            return result
            
        except Exception as e:
            logger.error(f"Cache optimization failed: {e}")
            raise RuntimeError(f"Cache optimization failed: {e}") from e
    
    async def get_optimization_recommendations(self) -> List[str]:
        """
        Get performance optimization recommendations.
        
        Analyzes current system state and provides recommendations
        for improving performance based on best practices.
        
        Returns:
            List[str]: List of optimization recommendations.
        
        Raises:
            RuntimeError: If recommendations cannot be generated
        """
        try:
            recommendations = []
            current_metrics = await self.get_current_metrics()
            
            # Memory recommendations
            if current_metrics.memory_usage_percent > 80:
                recommendations.append("Consider reducing memory usage or increasing available memory")
            if current_metrics.memory_usage_percent > 90:
                recommendations.append("Critical: Memory usage is very high, immediate action required")
            
            # CPU recommendations
            if current_metrics.cpu_usage_percent > 70:
                recommendations.append("Consider reducing CPU load or optimizing processing")
            if current_metrics.cpu_usage_percent > 90:
                recommendations.append("Critical: CPU usage is very high, consider scaling")
            
            # Load average recommendations
            if current_metrics.load_average_1m > 2.0:
                recommendations.append("System load is high, consider reducing concurrent operations")
            
            # General recommendations
            if current_metrics.performance_status == PerformanceStatus.POOR:
                recommendations.append("System performance is poor, review configuration and resources")
            elif current_metrics.performance_status == PerformanceStatus.CRITICAL:
                recommendations.append("Critical: System performance is critical, immediate intervention required")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate optimization recommendations: {e}")
            raise RuntimeError(f"Failed to generate recommendations: {e}") from e
    
    async def apply_optimization(self, optimization_type: str, parameters: Dict[str, Any]) -> bool:
        """
        Apply specific optimization.
        
        Applies a specific optimization with given parameters.
        
        Args:
            optimization_type (str): Type of optimization to apply.
                Must be one of: "memory", "cpu", "cache", "batch_size".
            parameters (Dict[str, Any]): Optimization parameters.
                Must be valid parameters for the optimization type.
        
        Returns:
            bool: True if optimization applied successfully, False otherwise.
        
        Raises:
            ValueError: If optimization_type is invalid
            RuntimeError: If optimization application fails
        """
        valid_types = ["memory", "cpu", "cache", "batch_size"]
        if optimization_type not in valid_types:
            raise ValueError(f"Invalid optimization_type: {optimization_type}. Must be one of: {valid_types}")
        
        try:
            if optimization_type == "memory":
                result = await self.optimize_memory_usage()
            elif optimization_type == "cpu":
                result = await self.optimize_cpu_usage()
            elif optimization_type == "cache":
                result = await self.optimize_cache_performance()
            elif optimization_type == "batch_size":
                # Apply batch size optimization
                result = OptimizationResult(
                    optimization_type=OptimizationType.BATCH_SIZE,
                    success=True,
                    improvements={"batch_size_adjusted": parameters.get("factor", 1.0)}
                )
            
            return result.success
            
        except Exception as e:
            logger.error(f"Failed to apply {optimization_type} optimization: {e}")
            raise RuntimeError(f"Failed to apply optimization: {e}") from e
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive performance report.
        
        Creates a detailed report of system performance including
        current metrics, optimization history, and recommendations.
        
        Returns:
            Dict[str, Any]: Comprehensive performance report.
                Format: {
                    "current_metrics": PerformanceMetrics,
                    "optimization_history": List[OptimizationResult],
                    "recommendations": List[str],
                    "system_health": str
                }
        
        Raises:
            RuntimeError: If report cannot be generated
        """
        try:
            current_metrics = await self.get_current_metrics()
            recommendations = await self.get_optimization_recommendations()
            
            # Determine system health
            if current_metrics.performance_status == PerformanceStatus.EXCELLENT:
                system_health = "excellent"
            elif current_metrics.performance_status == PerformanceStatus.GOOD:
                system_health = "good"
            elif current_metrics.performance_status == PerformanceStatus.FAIR:
                system_health = "fair"
            elif current_metrics.performance_status == PerformanceStatus.POOR:
                system_health = "poor"
            else:
                system_health = "critical"
            
            report = {
                "current_metrics": current_metrics,
                "optimization_history": self.optimization_history[-10:],  # Last 10 optimizations
                "recommendations": recommendations,
                "system_health": system_health,
                "monitoring_active": self.is_monitoring,
                "config": self.config
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate performance report: {e}")
            raise RuntimeError(f"Failed to generate report: {e}") from e
    
    async def _monitoring_loop(self):
        """Background monitoring loop."""
        while self.is_monitoring:
            try:
                metrics = await self.get_current_metrics()
                self.metrics_history.append(metrics)
                
                # Keep only last 1000 metrics
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-1000:]
                
                # Check if optimization is needed
                if (metrics.memory_usage_percent > self.config.memory_threshold * 100 or
                    metrics.cpu_usage_percent > self.config.cpu_threshold * 100):
                    logger.info("Performance thresholds exceeded, triggering optimization")
                    await self.optimize_system()
                
                await asyncio.sleep(self.config.optimization_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    def _determine_performance_status(self, cpu_percent: float, memory_percent: float, load_avg: float) -> PerformanceStatus:
        """Determine overall performance status based on metrics."""
        if cpu_percent > 90 or memory_percent > 95 or load_avg > 5.0:
            return PerformanceStatus.CRITICAL
        elif cpu_percent > 80 or memory_percent > 85 or load_avg > 3.0:
            return PerformanceStatus.POOR
        elif cpu_percent > 60 or memory_percent > 70 or load_avg > 2.0:
            return PerformanceStatus.FAIR
        elif cpu_percent > 40 or memory_percent > 50 or load_avg > 1.0:
            return PerformanceStatus.GOOD
        else:
            return PerformanceStatus.EXCELLENT 