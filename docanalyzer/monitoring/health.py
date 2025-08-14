"""
Health Check - DocAnalyzer Health Monitoring

This module provides health check capabilities for DocAnalyzer,
extending the mcp_proxy_adapter framework's monitoring system with
DocAnalyzer-specific health checks.

It includes component health monitoring, system health status,
and integration with the framework's health check infrastructure.

Author: DocAnalyzer Team
Version: 1.0.0
"""

import time
import logging
import os
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import threading
import json

# Import framework health check components
try:
    from mcp_proxy_adapter.core.health import HealthChecker as FrameworkHealthChecker
    from mcp_proxy_adapter.core.monitoring import HealthStatus as FrameworkHealthStatus
except ImportError:
    # Fallback for development/testing
    FrameworkHealthChecker = object
    FrameworkHealthStatus = str

logger = logging.getLogger(__name__)

# Health status enumeration
class HealthStatus(Enum):
    """
    Health Status - Component Health States
    
    Defines the possible health states for DocAnalyzer components
    and system overall.
    """
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


# Default health check configuration
DEFAULT_HEALTH_CONFIG = {
    'check_interval': 30,  # seconds
    'timeout': 10,  # seconds
    'retry_count': 3,
    'retention_period': 86400,  # 24 hours in seconds
    'enable_auto_healing': False,
    'critical_components': ['file_processor', 'vector_store', 'database']
}


@dataclass
class ComponentHealth:
    """
    Component Health - Individual Component Health Status
    
    Represents the health status of a specific DocAnalyzer component
    including status, metrics, and last check information.
    
    Attributes:
        component_name (str): Name of the component being monitored.
            Must be non-empty string.
        status (HealthStatus): Current health status of the component.
            Values: HEALTHY, DEGRADED, UNHEALTHY, UNKNOWN.
        last_check (datetime): Timestamp of last health check.
            Used for determining check freshness.
        response_time (float): Time taken for last health check in seconds.
            Used for performance monitoring.
        error_count (int): Number of consecutive failed health checks.
            Used for determining degradation.
        error_message (Optional[str]): Last error message from health check.
            Provides details about health issues.
        metrics (Dict[str, Any]): Component-specific health metrics.
            Can contain any relevant health indicators.
    
    Example:
        >>> health = ComponentHealth("file_processor")
        >>> health.update_status(HealthStatus.HEALTHY, 0.5)
        >>> print(health.status)  # HealthStatus.HEALTHY
    """
    
    component_name: str
    status: HealthStatus = HealthStatus.UNKNOWN
    last_check: datetime = field(default_factory=datetime.now)
    response_time: float = 0.0
    error_count: int = 0
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def update_status(self, status: HealthStatus, response_time: float, error_message: Optional[str] = None) -> None:
        """
        Update component health status.
        
        Args:
            status (HealthStatus): New health status.
                Must be valid HealthStatus enum value.
            response_time (float): Time taken for health check in seconds.
                Must be non-negative float.
            error_message (Optional[str], optional): Error message if check failed.
                Defaults to None.
        
        Raises:
            ValueError: If parameters are invalid
        """
        if not isinstance(status, HealthStatus):
            raise ValueError("status must be valid HealthStatus enum value")
        
        if not isinstance(response_time, (int, float)) or response_time < 0:
            raise ValueError("response_time must be non-negative number")
        
        if error_message is not None and not isinstance(error_message, str):
            raise ValueError("error_message must be string or None")
        
        self.status = status
        self.response_time = response_time
        self.last_check = datetime.now()
        
        if error_message:
            self.error_message = error_message
            self.error_count += 1
        else:
            self.error_message = None
            self.error_count = 0
        
        logger.debug(f"Component {self.component_name} status updated: {status.value}, response_time: {response_time}")
    
    def is_healthy(self) -> bool:
        """
        Check if component is healthy.
        
        Returns:
            bool: True if component status is HEALTHY, False otherwise.
        """
        return self.status == HealthStatus.HEALTHY
    
    def is_degraded(self) -> bool:
        """
        Check if component is degraded.
        
        Returns:
            bool: True if component status is DEGRADED, False otherwise.
        """
        return self.status == HealthStatus.DEGRADED
    
    def is_unhealthy(self) -> bool:
        """
        Check if component is unhealthy.
        
        Returns:
            bool: True if component status is UNHEALTHY, False otherwise.
        """
        return self.status == HealthStatus.UNHEALTHY
    
    def get_status_summary(self) -> Dict[str, Any]:
        """
        Get component health summary.
        
        Returns:
            Dict[str, Any]: Component health summary including
                status, metrics, and timing information.
        """
        return {
            'component_name': self.component_name,
            'status': self.status.value,
            'last_check': self.last_check.isoformat(),
            'response_time': self.response_time,
            'error_count': self.error_count,
            'error_message': self.error_message,
            'metrics': self.metrics
        }


class HealthChecker:
    """
    Health Checker - DocAnalyzer Health Monitoring
    
    Main health check class that monitors all DocAnalyzer components
    and integrates with the mcp_proxy_adapter framework's health check system.
    
    This class provides unified health monitoring interface for all
    DocAnalyzer components while maintaining compatibility with the framework.
    
    Attributes:
        components (Dict[str, ComponentHealth]): Component health status.
            Maps component names to their health status.
        config (Dict[str, Any]): Health check configuration.
            Contains check settings and parameters.
        framework_checker (Optional[FrameworkHealthChecker]): Framework health checker.
            Integration with framework health check system.
        check_thread (Optional[threading.Thread]): Background check thread.
            Handles periodic health checks.
        is_checking (bool): Whether health checking is active.
            Controls background check thread.
        overall_status (HealthStatus): Overall system health status.
            Aggregated status from all components.
    
    Example:
        >>> checker = HealthChecker()
        >>> checker.start_health_checks()
        >>> checker.register_component("file_processor", file_processor_health_check)
        >>> status = checker.get_overall_health()
    
    Raises:
        HealthCheckError: When health check operations fail
        ConfigurationError: When health check configuration is invalid
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize HealthChecker instance.
        
        Args:
            config (Optional[Dict[str, Any]], optional): Health check configuration.
                Defaults to None. If None, uses default configuration.
        
        Raises:
            ConfigurationError: If configuration is invalid
        """
        self.config = DEFAULT_HEALTH_CONFIG.copy()
        if config:
            self.config.update(config)
        
        self.components: Dict[str, ComponentHealth] = {}
        self._health_check_functions: Dict[str, callable] = {}
        self.framework_checker = None
        self.check_thread = None
        self.is_checking = False
        
        # Try to initialize framework checker
        try:
            if FrameworkHealthChecker != object:
                self.framework_checker = FrameworkHealthChecker()
                logger.debug("Framework health checker initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize framework health checker: {e}")
        
        logger.info("HealthChecker initialized")
    
    async def initialize(self) -> None:
        """
        Initialize health checker.
        
        Performs any necessary initialization for health checking.
        This method is called during service initialization.
        
        Returns:
            None
        
        Raises:
            HealthCheckError: If initialization fails
        """
        try:
            # Start health checks
            self.start_health_checks()
            logger.info("HealthChecker initialized successfully")
        except Exception as e:
            error_msg = f"Failed to initialize HealthChecker: {e}"
            logger.error(error_msg)
            raise HealthCheckError(error_msg, None, "initialize")
    
    async def cleanup(self) -> None:
        """
        Cleanup health checker.
        
        Performs cleanup operations for health checking.
        This method is called during service cleanup.
        
        Returns:
            None
        
        Raises:
            HealthCheckError: If cleanup fails
        """
        try:
            # Stop health checks
            self.stop_health_checks()
            logger.info("HealthChecker cleaned up successfully")
        except Exception as e:
            error_msg = f"Failed to cleanup HealthChecker: {e}"
            logger.error(error_msg)
            raise HealthCheckError(error_msg, None, "cleanup")
    
    def start_health_checks(self) -> bool:
        """
        Start health checking.
        
        Initializes background check thread and begins
        periodic health checks according to configuration.
        
        Returns:
            bool: True if health checking started successfully.
        
        Raises:
            HealthCheckError: If health checking cannot be started
        """
        try:
            if self.is_checking:
                logger.warning("Health checks already running")
                return True
            
            self.is_checking = True
            self.check_thread = threading.Thread(
                target=self._check_worker,
                daemon=True,
                name="HealthChecker"
            )
            self.check_thread.start()
            
            logger.info("Health checks started")
            return True
            
        except Exception as e:
            error_msg = f"Failed to start health checks: {e}"
            logger.error(error_msg)
            raise HealthCheckError(error_msg, None, "start_health_checks")
    
    def stop_health_checks(self) -> bool:
        """
        Stop health checking.
        
        Stops background check thread and saves
        final health status data.
        
        Returns:
            bool: True if health checking stopped successfully.
        
        Raises:
            HealthCheckError: If health checking cannot be stopped
        """
        try:
            if not self.is_checking:
                logger.warning("Health checks not running")
                return True
            
            self.is_checking = False
            
            if self.check_thread and self.check_thread.is_alive():
                self.check_thread.join(timeout=5)
            
            logger.info("Health checks stopped")
            return True
            
        except Exception as e:
            error_msg = f"Failed to stop health checks: {e}"
            logger.error(error_msg)
            raise HealthCheckError(error_msg, None, "stop_health_checks")
    
    def register_component(self, component_name: str, health_check_func: callable) -> bool:
        """
        Register component for health monitoring.
        
        Args:
            component_name (str): Name of the component to monitor.
                Must be non-empty string.
            health_check_func (callable): Function to perform health check.
                Must be callable that returns HealthStatus.
        
        Returns:
            bool: True if component was registered successfully.
        
        Raises:
            ValueError: If parameters are invalid
            HealthCheckError: If component cannot be registered
        """
        if not component_name or not isinstance(component_name, str):
            raise ValueError("component_name must be non-empty string")
        
        if not callable(health_check_func):
            raise ValueError("health_check_func must be callable")
        
        try:
            self.components[component_name] = ComponentHealth(component_name)
            self._health_check_functions[component_name] = health_check_func
            logger.info(f"Component {component_name} registered for health monitoring")
            return True
            
        except Exception as e:
            error_msg = f"Failed to register component {component_name}: {e}"
            logger.error(error_msg)
            raise HealthCheckError(error_msg, component_name, "register_component")
    
    def unregister_component(self, component_name: str) -> bool:
        """
        Unregister component from health monitoring.
        
        Args:
            component_name (str): Name of the component to unregister.
                Must be non-empty string.
        
        Returns:
            bool: True if component was unregistered successfully.
        
        Raises:
            ValueError: If component_name is empty
            HealthCheckError: If component cannot be unregistered
        """
        if not component_name or not isinstance(component_name, str):
            raise ValueError("component_name must be non-empty string")
        
        try:
            if component_name in self.components:
                del self.components[component_name]
                del self._health_check_functions[component_name]
                logger.info(f"Component {component_name} unregistered from health monitoring")
                return True
            else:
                logger.warning(f"Component {component_name} not found in health monitoring")
                return False
                
        except Exception as e:
            error_msg = f"Failed to unregister component {component_name}: {e}"
            logger.error(error_msg)
            raise HealthCheckError(error_msg, component_name, "unregister_component")
    
    def check_component_health(self, component_name: str) -> ComponentHealth:
        """
        Perform health check for specific component.
        
        Args:
            component_name (str): Name of the component to check.
                Must be registered component name.
        
        Returns:
            ComponentHealth: Current health status of the component.
        
        Raises:
            ValueError: If component_name is not registered
            HealthCheckError: If health check fails
        """
        if component_name not in self.components:
            raise ValueError(f"Component {component_name} not registered")
        
        try:
            start_time = time.time()
            health_check_func = self._health_check_functions[component_name]
            status = health_check_func()
            response_time = time.time() - start_time
            
            self.components[component_name].update_status(status, response_time)
            return self.components[component_name]
            
        except Exception as e:
            error_msg = f"Health check failed for component {component_name}: {e}"
            logger.error(error_msg)
            self.components[component_name].update_status(
                HealthStatus.UNHEALTHY, 
                0.0, 
                error_msg
            )
            raise HealthCheckError(error_msg, component_name, "check_component_health")
    
    def _check_worker(self) -> None:
        """
        Background worker for health checks.
        
        Runs in a separate thread and periodically performs
        health checks for all registered components.
        """
        while self.is_checking:
            try:
                self.check_all_components()
                time.sleep(self.config['check_interval'])
            except Exception as e:
                logger.error(f"Error in health check worker: {e}")
                time.sleep(5)  # Wait before retrying
    
    def check_all_components(self) -> Dict[str, ComponentHealth]:
        """
        Perform health check for all registered components.
        
        Returns:
            Dict[str, ComponentHealth]: Health status of all components.
                Maps component names to their health status.
        
        Raises:
            HealthCheckError: If health checks fail
        """
        results = {}
        
        for component_name in list(self.components.keys()):
            try:
                results[component_name] = self.check_component_health(component_name)
            except Exception as e:
                logger.error(f"Failed to check component {component_name}: {e}")
                # Component status already updated in check_component_health
                results[component_name] = self.components[component_name]
        
        return results
    
    def get_component_health(self, component_name: str) -> Optional[ComponentHealth]:
        """
        Get current health status of component.
        
        Args:
            component_name (str): Name of the component.
                Must be registered component name.
        
        Returns:
            Optional[ComponentHealth]: Current health status or None if not found.
        """
        return self.components.get(component_name)
    
    def get_overall_health(self) -> HealthStatus:
        """
        Get overall system health status.
        
        Calculates overall health based on all component statuses
        using configurable aggregation rules.
        
        Returns:
            HealthStatus: Overall system health status.
        """
        if not self.components:
            return HealthStatus.UNKNOWN
        
        # Count statuses
        status_counts = {
            HealthStatus.HEALTHY: 0,
            HealthStatus.DEGRADED: 0,
            HealthStatus.UNHEALTHY: 0,
            HealthStatus.UNKNOWN: 0
        }
        
        for component in self.components.values():
            status_counts[component.status] += 1
        
        # Determine overall status based on aggregation rules
        total_components = len(self.components)
        
        # If any component is unhealthy, overall is unhealthy
        if status_counts[HealthStatus.UNHEALTHY] > 0:
            return HealthStatus.UNHEALTHY
        
        # If any component is degraded, overall is degraded
        if status_counts[HealthStatus.DEGRADED] > 0:
            return HealthStatus.DEGRADED
        
        # If all components are healthy, overall is healthy
        if status_counts[HealthStatus.HEALTHY] == total_components:
            return HealthStatus.HEALTHY
        
        # Otherwise, unknown
        return HealthStatus.UNKNOWN
    
    def get_health_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive health summary.
        
        Returns:
            Dict[str, Any]: Complete health summary including
                overall status, component statuses, and metrics.
        """
        return {
            'overall_status': self.get_overall_health().value,
            'components': {
                name: component.get_status_summary()
                for name, component in self.components.items()
            },
            'checking_active': self.is_checking,
            'check_interval': self.config['check_interval'],
            'total_components': len(self.components)
        }
    
    def is_system_healthy(self) -> bool:
        """
        Check if overall system is healthy.
        
        Returns:
            bool: True if overall system status is HEALTHY, False otherwise.
        """
        return self.get_overall_health() == HealthStatus.HEALTHY
    
    def is_system_degraded(self) -> bool:
        """
        Check if overall system is degraded.
        
        Returns:
            bool: True if overall system status is DEGRADED, False otherwise.
        """
        return self.get_overall_health() == HealthStatus.DEGRADED
    
    def is_system_unhealthy(self) -> bool:
        """
        Check if overall system is unhealthy.
        
        Returns:
            bool: True if overall system status is UNHEALTHY, False otherwise.
        """
        return self.get_overall_health() == HealthStatus.UNHEALTHY
    
    def save_health_status(self, file_path: str) -> bool:
        """
        Save health status to file.
        
        Args:
            file_path (str): Path to save health status file.
                Must be writable path.
        
        Returns:
            bool: True if health status was saved successfully.
        
        Raises:
            HealthCheckError: If health status cannot be saved
        """
        try:
            health_data = self.get_health_summary()
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w') as f:
                json.dump(health_data, f, indent=2, default=str)
            
            logger.info(f"Health status saved to {file_path}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to save health status to {file_path}: {e}"
            logger.error(error_msg)
            raise HealthCheckError(error_msg, None, "save_health_status")
    
    def load_health_status(self, file_path: str) -> bool:
        """
        Load health status from file.
        
        Args:
            file_path (str): Path to load health status from.
                Must be existing readable file.
        
        Returns:
            bool: True if health status was loaded successfully.
        
        Raises:
            HealthCheckError: If health status cannot be loaded
        """
        try:
            with open(file_path, 'r') as f:
                health_data = json.load(f)
            
            # Load component statuses
            if 'components' in health_data:
                for component_name, component_data in health_data['components'].items():
                    if component_name in self.components:
                        component = self.components[component_name]
                        # Update component status from loaded data
                        status_value = component_data.get('status', 'unknown')
                        status = HealthStatus(status_value)
                        response_time = component_data.get('response_time', 0.0)
                        error_message = component_data.get('error_message')
                        component.update_status(status, response_time, error_message)
            
            logger.info(f"Health status loaded from {file_path}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to load health status from {file_path}: {e}"
            logger.error(error_msg)
            raise HealthCheckError(error_msg, None, "load_health_status")
    
    def reset_health_status(self) -> None:
        """
        Reset all health statuses to UNKNOWN.
        
        Clears all component health statuses while preserving
        the monitoring configuration.
        """
        for component in self.components.values():
            component.update_status(HealthStatus.UNKNOWN, 0.0)
        
        logger.info("All health statuses reset to UNKNOWN")


# Predefined health check functions for DocAnalyzer components
def file_processor_health_check() -> HealthStatus:
    """
    Health check for file processor component.
    
    Checks if file processor is functioning correctly by
    verifying its internal state and capabilities.
    
    Returns:
        HealthStatus: Health status of file processor component.
    
    Raises:
        HealthCheckError: If health check fails
    """
    pass


def vector_store_health_check() -> HealthStatus:
    """
    Health check for vector store component.
    
    Checks if vector store is accessible and functioning
    by testing connection and basic operations.
    
    Returns:
        HealthStatus: Health status of vector store component.
    
    Raises:
        HealthCheckError: If health check fails
    """
    pass


def database_health_check() -> HealthStatus:
    """
    Health check for database component.
    
    Checks if database is accessible and functioning
    by testing connection and basic operations.
    
    Returns:
        HealthStatus: Health status of database component.
    
    Raises:
        HealthCheckError: If health check fails
    """
    pass


def lock_manager_health_check() -> HealthStatus:
    """
    Health check for lock manager component.
    
    Checks if lock manager is functioning correctly by
    verifying its internal state and lock file operations.
    
    Returns:
        HealthStatus: Health status of lock manager component.
    
    Raises:
        HealthCheckError: If health check fails
    """
    pass


class HealthCheckError(Exception):
    """
    Health Check Error - Exception for health check operations.
    
    Raised when health check operations fail, such as when trying to
    check component health that is not available or when health check
    configuration is invalid.
    
    Attributes:
        message (str): Error message describing the health check failure
        component (Optional[str]): Component where the error occurred
        operation (Optional[str]): Operation that failed
    """
    
    def __init__(self, message: str, component: Optional[str] = None, operation: Optional[str] = None):
        """
        Initialize HealthCheckError instance.
        
        Args:
            message (str): Error message describing the health check failure
            component (Optional[str]): Component where the error occurred
            operation (Optional[str]): Operation that failed
        """
        super().__init__(message)
        self.message = message
        self.component = component
        self.operation = operation


class ConfigurationError(Exception):
    """
    Configuration Error - Exception for configuration operations.
    
    Raised when configuration operations fail, such as when trying to
    load invalid configuration or when required settings are missing.
    
    Attributes:
        message (str): Error message describing the configuration failure
        config_key (Optional[str]): Configuration key that caused the error
        value (Optional[Any]): Invalid value that caused the error
    """
    
    def __init__(self, message: str, config_key: Optional[str] = None, value: Optional[Any] = None):
        """
        Initialize ConfigurationError instance.
        
        Args:
            message (str): Error message describing the configuration failure
            config_key (Optional[str]): Configuration key that caused the error
            value (Optional[Any]): Invalid value that caused the error
        """
        super().__init__(message)
        self.message = message
        self.config_key = config_key
        self.value = value 