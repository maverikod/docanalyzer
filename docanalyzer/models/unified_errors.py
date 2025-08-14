"""
Unified Errors - DocAnalyzer Unified Error Handling

This module provides a unified error handling system for DocAnalyzer,
combining all error types into a single, coherent interface.

The unified error system eliminates duplication and provides
consistent error handling across all DocAnalyzer components.

Author: DocAnalyzer Team
Version: 1.0.0
"""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """
    Error Category - Classification of Error Types
    
    Defines the different categories of errors that can occur
    in DocAnalyzer components.
    """
    CONFIGURATION = "configuration"
    CONNECTION = "connection"
    PROCESSING = "processing"
    VALIDATION = "validation"
    SYSTEM = "system"
    PERMISSION = "permission"
    RESOURCE = "resource"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """
    Error Severity - Error Impact Levels
    
    Defines the severity levels of errors to help determine
    appropriate handling and response strategies.
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorContext:
    """
    Error Context - Additional Error Information
    
    Provides additional context information about an error
    including component, operation, and metadata.
    
    Attributes:
        component (str): Component where the error occurred.
            Must be non-empty string identifying the component.
        operation (str): Operation being performed when error occurred.
            Must be non-empty string describing the operation.
        timestamp (datetime): When the error occurred.
            Defaults to current timestamp.
        metadata (Dict[str, Any]): Additional error metadata.
            Can contain any relevant error information.
        user_id (Optional[str]): User ID if applicable.
            Can be None if not user-specific error.
        session_id (Optional[str]): Session ID if applicable.
            Can be None if not session-specific error.
    
    Example:
        >>> context = ErrorContext("file_processor", "process_file", metadata={"file_path": "/path/file.txt"})
        >>> print(context.component)  # "file_processor"
    """
    
    component: str
    operation: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert error context to dictionary.
        
        Returns:
            Dict[str, Any]: Error context as dictionary.
        """
        return {
            "component": self.component,
            "operation": self.operation,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "user_id": self.user_id,
            "session_id": self.session_id
        }


@dataclass
class UnifiedError:
    """
    Unified Error - Single Error Representation
    
    Represents any error that can occur in DocAnalyzer with
    consistent structure and comprehensive error information.
    
    Attributes:
        error_id (str): Unique error identifier.
            Must be non-empty string for error tracking.
        message (str): Human-readable error message.
            Must be non-empty string describing the error.
        category (ErrorCategory): Category of the error.
            Helps classify and handle errors appropriately.
        severity (ErrorSeverity): Severity level of the error.
            Helps determine appropriate response strategy.
        context (ErrorContext): Error context information.
            Provides additional details about the error.
        original_error (Optional[Exception]): Original exception if available.
            Can be None if no original exception exists.
        stack_trace (Optional[str]): Stack trace if available.
            Can be None if no stack trace available.
        retryable (bool): Whether the error can be retried.
            Defaults to False.
        max_retries (int): Maximum number of retry attempts.
            Must be non-negative integer. Defaults to 0.
    
    Example:
        >>> error = UnifiedError(
        ...     error_id="file_not_found_001",
        ...     message="File not found: /path/file.txt",
        ...     category=ErrorCategory.RESOURCE,
        ...     severity=ErrorSeverity.MEDIUM,
        ...     context=ErrorContext("file_processor", "process_file")
        ... )
        >>> print(error.message)  # "File not found: /path/file.txt"
    """
    
    error_id: str
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    context: ErrorContext
    original_error: Optional[Exception] = None
    stack_trace: Optional[str] = None
    retryable: bool = False
    max_retries: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert unified error to dictionary.
        
        Returns:
            Dict[str, Any]: Unified error as dictionary.
        """
        return {
            "error_id": self.error_id,
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "context": self.context.to_dict(),
            "original_error": str(self.original_error) if self.original_error else None,
            "stack_trace": self.stack_trace,
            "retryable": self.retryable,
            "max_retries": self.max_retries
        }
    
    def __str__(self) -> str:
        """
        String representation of unified error.
        
        Returns:
            str: Formatted error string.
        """
        return f"[{self.category.value.upper()}] {self.message} (ID: {self.error_id})"


class UnifiedErrorHandler:
    """
    Unified Error Handler - Centralized Error Management
    
    Provides centralized error handling capabilities for DocAnalyzer
    including error creation, logging, and response generation.
    
    This handler ensures consistent error handling across all
    DocAnalyzer components and provides comprehensive error tracking.
    
    Attributes:
        logger (logging.Logger): Logger for error handling.
            Used for error logging and debugging.
        error_registry (Dict[str, UnifiedError]): Registry of handled errors.
            Tracks errors for analysis and debugging.
        error_counters (Dict[str, int]): Error occurrence counters.
            Tracks frequency of different error types.
    
    Example:
        >>> handler = UnifiedErrorHandler()
        >>> error = handler.create_error("file_not_found", "File not found", ErrorCategory.RESOURCE)
        >>> handler.log_error(error)
        >>> response = handler.create_error_response(error)
    """
    
    def __init__(self):
        """
        Initialize unified error handler.
        
        Sets up logging, error registry, and error counters
        for comprehensive error management.
        """
        self.logger = logging.getLogger(__name__)
        self.error_registry: Dict[str, UnifiedError] = {}
        self.error_counters: Dict[str, int] = {}
    
    def create_error(
        self,
        error_id: str,
        message: str,
        category: ErrorCategory,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        component: str = "unknown",
        operation: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
        retryable: bool = False,
        max_retries: int = 0
    ) -> UnifiedError:
        """
        Create a unified error instance.
        
        Creates a new unified error with the specified parameters
        and generates appropriate error context.
        
        Args:
            error_id (str): Unique error identifier.
                Must be non-empty string for error tracking.
            message (str): Human-readable error message.
                Must be non-empty string describing the error.
            category (ErrorCategory): Category of the error.
                Helps classify and handle errors appropriately.
            severity (ErrorSeverity): Severity level of the error.
                Defaults to MEDIUM.
            component (str): Component where the error occurred.
                Defaults to "unknown".
            operation (str): Operation being performed when error occurred.
                Defaults to "unknown".
            metadata (Optional[Dict[str, Any]]): Additional error metadata.
                Can be None if no additional metadata.
            original_error (Optional[Exception]): Original exception if available.
                Can be None if no original exception exists.
            retryable (bool): Whether the error can be retried.
                Defaults to False.
            max_retries (int): Maximum number of retry attempts.
                Must be non-negative integer. Defaults to 0.
        
        Returns:
            UnifiedError: Created unified error instance.
        
        Raises:
            ValueError: If error_id or message is empty
        """
        if not error_id or not message:
            raise ValueError("error_id and message must be non-empty")
        
        # Create error context
        context = ErrorContext(
            component=component,
            operation=operation,
            metadata=metadata or {}
        )
        
        # Get stack trace if original error provided
        stack_trace = None
        if original_error:
            import traceback
            stack_trace = ''.join(traceback.format_exception(
                type(original_error), original_error, original_error.__traceback__
            ))
        
        # Create unified error
        error = UnifiedError(
            error_id=error_id,
            message=message,
            category=category,
            severity=severity,
            context=context,
            original_error=original_error,
            stack_trace=stack_trace,
            retryable=retryable,
            max_retries=max_retries
        )
        
        # Register error
        self.error_registry[error_id] = error
        
        # Update error counter
        error_type = f"{category.value}_{severity.value}"
        self.error_counters[error_type] = self.error_counters.get(error_type, 0) + 1
        
        return error
    
    def log_error(self, error: UnifiedError) -> None:
        """
        Log unified error with appropriate level.
        
        Logs the error with severity-appropriate log level
        and includes comprehensive error information.
        
        Args:
            error (UnifiedError): Error to log.
                Must be valid UnifiedError instance.
        """
        log_message = f"Error {error.error_id}: {error.message}"
        log_data = {
            "error_id": error.error_id,
            "category": error.category.value,
            "severity": error.severity.value,
            "component": error.context.component,
            "operation": error.context.operation,
            "retryable": error.retryable,
            "metadata": error.context.metadata
        }
        
        # Log with appropriate level based on severity
        if error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message, extra=log_data)
        elif error.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message, extra=log_data)
        elif error.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message, extra=log_data)
        else:  # LOW
            self.logger.info(log_message, extra=log_data)
        
        # Log stack trace if available
        if error.stack_trace:
            self.logger.debug(f"Stack trace for {error.error_id}:\n{error.stack_trace}")
    
    def create_error_response(self, error: UnifiedError) -> Dict[str, Any]:
        """
        Create standardized error response.
        
        Creates a standardized error response that can be returned
        to clients or used for error reporting.
        
        Args:
            error (UnifiedError): Error to create response for.
                Must be valid UnifiedError instance.
        
        Returns:
            Dict[str, Any]: Standardized error response.
        """
        return {
            "success": False,
            "error": error.to_dict(),
            "timestamp": datetime.now().isoformat(),
            "retryable": error.retryable,
            "suggested_action": self._get_suggested_action(error)
        }
    
    def _get_suggested_action(self, error: UnifiedError) -> str:
        """
        Get suggested action for error.
        
        Provides a suggested action based on the error category
        and severity to help users resolve the issue.
        
        Args:
            error (UnifiedError): Error to get suggestion for.
                Must be valid UnifiedError instance.
        
        Returns:
            str: Suggested action for the error.
        """
        suggestions = {
            ErrorCategory.CONFIGURATION: {
                ErrorSeverity.LOW: "Check configuration settings",
                ErrorSeverity.MEDIUM: "Review and update configuration",
                ErrorSeverity.HIGH: "Immediately fix configuration issues",
                ErrorSeverity.CRITICAL: "Critical configuration error - immediate action required"
            },
            ErrorCategory.CONNECTION: {
                ErrorSeverity.LOW: "Check network connectivity",
                ErrorSeverity.MEDIUM: "Verify service availability",
                ErrorSeverity.HIGH: "Service connection failed - check service status",
                ErrorSeverity.CRITICAL: "Critical connection failure - service unavailable"
            },
            ErrorCategory.PROCESSING: {
                ErrorSeverity.LOW: "Retry the operation",
                ErrorSeverity.MEDIUM: "Check input data and retry",
                ErrorSeverity.HIGH: "Processing error - review input and configuration",
                ErrorSeverity.CRITICAL: "Critical processing failure - system may be unstable"
            },
            ErrorCategory.VALIDATION: {
                ErrorSeverity.LOW: "Check input format",
                ErrorSeverity.MEDIUM: "Validate input data",
                ErrorSeverity.HIGH: "Input validation failed - review data format",
                ErrorSeverity.CRITICAL: "Critical validation error - invalid system state"
            },
            ErrorCategory.SYSTEM: {
                ErrorSeverity.LOW: "Check system resources",
                ErrorSeverity.MEDIUM: "Monitor system performance",
                ErrorSeverity.HIGH: "System error - check logs and resources",
                ErrorSeverity.CRITICAL: "Critical system failure - immediate intervention required"
            },
            ErrorCategory.PERMISSION: {
                ErrorSeverity.LOW: "Check file permissions",
                ErrorSeverity.MEDIUM: "Verify access rights",
                ErrorSeverity.HIGH: "Permission denied - check user privileges",
                ErrorSeverity.CRITICAL: "Critical permission error - security issue"
            },
            ErrorCategory.RESOURCE: {
                ErrorSeverity.LOW: "Check resource availability",
                ErrorSeverity.MEDIUM: "Free up system resources",
                ErrorSeverity.HIGH: "Resource unavailable - check system capacity",
                ErrorSeverity.CRITICAL: "Critical resource failure - system overloaded"
            },
            ErrorCategory.TIMEOUT: {
                ErrorSeverity.LOW: "Retry with longer timeout",
                ErrorSeverity.MEDIUM: "Check system performance",
                ErrorSeverity.HIGH: "Operation timeout - system may be overloaded",
                ErrorSeverity.CRITICAL: "Critical timeout - system unresponsive"
            }
        }
        
        category_suggestions = suggestions.get(error.category, {})
        return category_suggestions.get(error.severity, "Review error details and take appropriate action")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """
        Get error handling statistics.
        
        Returns comprehensive statistics about error handling
        including error counts, categories, and severity distribution.
        
        Returns:
            Dict[str, Any]: Error handling statistics.
        """
        total_errors = len(self.error_registry)
        
        # Count by category
        category_counts = {}
        for error in self.error_registry.values():
            category = error.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Count by severity
        severity_counts = {}
        for error in self.error_registry.values():
            severity = error.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Count by component
        component_counts = {}
        for error in self.error_registry.values():
            component = error.context.component
            component_counts[component] = component_counts.get(component, 0) + 1
        
        return {
            "total_errors": total_errors,
            "category_distribution": category_counts,
            "severity_distribution": severity_counts,
            "component_distribution": component_counts,
            "error_counters": self.error_counters,
            "timestamp": datetime.now().isoformat()
        }
    
    def clear_error_registry(self) -> None:
        """
        Clear error registry and counters.
        
        Removes all registered errors and resets error counters.
        Useful for testing or periodic cleanup.
        """
        self.error_registry.clear()
        self.error_counters.clear()
        self.logger.info("Error registry and counters cleared")


# Global error handler instance
_unified_error_handler: Optional[UnifiedErrorHandler] = None


def get_unified_error_handler() -> UnifiedErrorHandler:
    """
    Get global unified error handler instance.
    
    Returns a singleton instance of the unified error handler.
    Creates the instance if it doesn't exist.
    
    Returns:
        UnifiedErrorHandler: Global unified error handler instance.
    """
    global _unified_error_handler
    
    if _unified_error_handler is None:
        _unified_error_handler = UnifiedErrorHandler()
    
    return _unified_error_handler


def create_error(
    error_id: str,
    message: str,
    category: ErrorCategory,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    component: str = "unknown",
    operation: str = "unknown",
    metadata: Optional[Dict[str, Any]] = None,
    original_error: Optional[Exception] = None,
    retryable: bool = False,
    max_retries: int = 0
) -> UnifiedError:
    """
    Create unified error using global handler.
    
    Convenience function to create a unified error using
    the global error handler instance.
    
    Args:
        error_id (str): Unique error identifier.
        message (str): Human-readable error message.
        category (ErrorCategory): Category of the error.
        severity (ErrorSeverity): Severity level of the error.
        component (str): Component where the error occurred.
        operation (str): Operation being performed when error occurred.
        metadata (Optional[Dict[str, Any]]): Additional error metadata.
        original_error (Optional[Exception]): Original exception if available.
        retryable (bool): Whether the error can be retried.
        max_retries (int): Maximum number of retry attempts.
    
    Returns:
        UnifiedError: Created unified error instance.
    """
    handler = get_unified_error_handler()
    return handler.create_error(
        error_id=error_id,
        message=message,
        category=category,
        severity=severity,
        component=component,
        operation=operation,
        metadata=metadata,
        original_error=original_error,
        retryable=retryable,
        max_retries=max_retries
    )


def log_error(error: UnifiedError) -> None:
    """
    Log unified error using global handler.
    
    Convenience function to log a unified error using
    the global error handler instance.
    
    Args:
        error (UnifiedError): Error to log.
    """
    handler = get_unified_error_handler()
    handler.log_error(error)


def create_error_response(error: UnifiedError) -> Dict[str, Any]:
    """
    Create error response using global handler.
    
    Convenience function to create an error response using
    the global error handler instance.
    
    Args:
        error (UnifiedError): Error to create response for.
    
    Returns:
        Dict[str, Any]: Standardized error response.
    """
    handler = get_unified_error_handler()
    return handler.create_error_response(error) 