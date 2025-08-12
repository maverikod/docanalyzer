"""
Error Models - Error Handling Domain Models

Defines domain models for error handling including processing errors,
error handlers, and error management utilities.

These models provide structured error handling, error categorization,
and error recovery mechanisms throughout the processing pipeline.

Author: DocAnalyzer Team
Version: 1.0.0
"""

from typing import Optional, List, Dict, Any, Union, Callable
from datetime import datetime
from enum import Enum
import traceback
import json
import logging
import uuid

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """
    Error Severity Enumeration - Error Impact Levels
    
    Defines the severity levels of errors for prioritization
    and handling decisions.
    
    Values:
        LOW: Minor error that doesn't affect processing
        MEDIUM: Moderate error that may affect some operations
        HIGH: Significant error that affects processing but is recoverable
        CRITICAL: Critical error that stops processing completely
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """
    Error Category Enumeration - Error Type Classification
    
    Defines categories of errors for better organization
    and handling strategies.
    
    Values:
        FILE_SYSTEM: Errors related to file system operations
        PROCESSING: Errors related to file processing operations
        DATABASE: Errors related to database operations
        NETWORK: Errors related to network operations
        CONFIGURATION: Errors related to configuration issues
        VALIDATION: Errors related to data validation
        PERMISSION: Errors related to permission issues
        UNKNOWN: Unknown or uncategorized errors
    """
    FILE_SYSTEM = "file_system"
    PROCESSING = "processing"
    DATABASE = "database"
    NETWORK = "network"
    CONFIGURATION = "configuration"
    VALIDATION = "validation"
    PERMISSION = "permission"
    UNKNOWN = "unknown"


class ProcessingError:
    """
    Processing Error Model - Error Information Container
    
    Represents a processing error with detailed information about
    the error, its context, and handling metadata.
    
    This model is used for error tracking, error reporting,
    and error recovery throughout the processing pipeline.
    
    Attributes:
        error_id (str): Unique identifier for the error.
            Generated as UUID4 string for uniqueness.
        error_type (str): Type/class of the error.
            Usually the exception class name.
        error_message (str): Human-readable error message.
            Must be non-empty string describing the error.
        error_category (ErrorCategory): Category of the error.
            Used for error classification and handling.
        error_severity (ErrorSeverity): Severity level of the error.
            Used for prioritization and handling decisions.
        file_path (Optional[str]): Path to the file that caused the error.
            None if error is not file-specific.
        operation (Optional[str]): Operation that caused the error.
            Description of what was being done when error occurred.
        stack_trace (Optional[str]): Full stack trace of the error.
            None if stack trace is not available.
        context_data (Dict[str, Any]): Additional context information.
            Can contain relevant data, parameters, state information.
        timestamp (datetime): Timestamp when error occurred.
            Used for error tracking and debugging.
        retry_count (int): Number of retry attempts for this error.
            Must be non-negative integer.
        max_retries (int): Maximum number of retry attempts allowed.
            Must be positive integer.
        is_recoverable (bool): Whether the error is recoverable.
            True if error can be resolved, False if fatal.
        recovery_action (Optional[str]): Suggested recovery action.
            Description of how to resolve the error.
    
    Example:
        >>> error = ProcessingError("FileNotFoundError", "File not found", ErrorCategory.FILE_SYSTEM)
        >>> print(error.error_type)  # "FileNotFoundError"
        >>> print(error.error_category)  # ErrorCategory.FILE_SYSTEM
    
    Raises:
        ValueError: If error_type or error_message is empty
        TypeError: If error_category or error_severity is not enum value
    """
    
    def __init__(
        self,
        error_type: str,
        error_message: str,
        error_category: ErrorCategory,
        error_id: Optional[str] = None,
        error_severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        stack_trace: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
        retry_count: int = 0,
        max_retries: int = 3,
        is_recoverable: bool = True,
        recovery_action: Optional[str] = None
    ):
        """
        Initialize ProcessingError instance.
        
        Args:
            error_type (str): Type/class of the error.
                Must be non-empty string (usually exception class name).
            error_message (str): Human-readable error message.
                Must be non-empty string describing the error.
            error_category (ErrorCategory): Category of the error.
                Must be valid ErrorCategory enum value.
            error_id (Optional[str], optional): Unique error identifier.
                Defaults to None. If None, UUID4 will be generated.
            error_severity (ErrorSeverity, optional): Severity level.
                Defaults to ErrorSeverity.MEDIUM.
            file_path (Optional[str], optional): Path to file that caused error.
                Defaults to None.
            operation (Optional[str], optional): Operation that caused error.
                Defaults to None.
            stack_trace (Optional[str], optional): Full stack trace.
                Defaults to None.
            context_data (Optional[Dict[str, Any]], optional): Additional context.
                Defaults to None.
            timestamp (Optional[datetime], optional): Error occurrence timestamp.
                Defaults to None. If None, current time will be used.
            retry_count (int, optional): Number of retry attempts.
                Defaults to 0. Must be non-negative integer.
            max_retries (int, optional): Maximum retry attempts allowed.
                Defaults to 3. Must be positive integer.
            is_recoverable (bool, optional): Whether error is recoverable.
                Defaults to True.
            recovery_action (Optional[str], optional): Suggested recovery action.
                Defaults to None.
        
        Raises:
            ValueError: If error_type or error_message is empty
            TypeError: If error_category or error_severity is not enum value
        """
        # Validate required parameters
        if not error_type or not isinstance(error_type, str):
            raise ValueError("error_type must be non-empty string")
        if not error_message or not isinstance(error_message, str):
            raise ValueError("error_message must be non-empty string")
        if not isinstance(error_category, ErrorCategory):
            raise TypeError("error_category must be ErrorCategory enum value")
        if not isinstance(error_severity, ErrorSeverity):
            raise TypeError("error_severity must be ErrorSeverity enum value")
        if retry_count < 0:
            raise ValueError("retry_count must be non-negative integer")
        if max_retries <= 0:
            raise ValueError("max_retries must be positive integer")
        
        # Set attributes
        self.error_id = error_id or str(uuid.uuid4())
        self.error_type = error_type
        self.error_message = error_message
        self.error_category = error_category
        self.error_severity = error_severity
        self.file_path = file_path
        self.operation = operation
        self.stack_trace = stack_trace
        self.context_data = context_data or {}
        self.timestamp = timestamp or datetime.now()
        self.retry_count = retry_count
        self.max_retries = max_retries
        self.is_recoverable = is_recoverable
        self.recovery_action = recovery_action
    
    def increment_retry_count(self) -> None:
        """
        Increment retry count for this error.
        
        Increases retry_count by 1. Does not exceed max_retries.
        
        Example:
            >>> error = ProcessingError("FileNotFoundError", "File not found", ErrorCategory.FILE_SYSTEM)
            >>> error.increment_retry_count()
            >>> print(error.retry_count)  # 1
        """
        if self.retry_count < self.max_retries:
            self.retry_count += 1
            logger.debug(f"Incremented retry count for error {self.error_id}: {self.retry_count}")
    
    def can_retry(self) -> bool:
        """
        Check if error can be retried.
        
        Returns:
            bool: True if retry_count < max_retries and error is recoverable.
        
        Example:
            >>> error = ProcessingError("FileNotFoundError", "File not found", ErrorCategory.FILE_SYSTEM)
            >>> print(error.can_retry())  # True
            >>> error.increment_retry_count()
            >>> error.increment_retry_count()
            >>> error.increment_retry_count()
            >>> print(error.can_retry())  # False (max retries reached)
        """
        return self.retry_count < self.max_retries and self.is_recoverable
    
    def add_context_data(self, key: str, value: Any) -> None:
        """
        Add context data to the error.
        
        Args:
            key (str): Context data key.
                Must be non-empty string.
            value (Any): Context data value.
                Can be any serializable value.
        
        Raises:
            ValueError: If key is empty
            TypeError: If key is not string
        
        Example:
            >>> error = ProcessingError("FileNotFoundError", "File not found", ErrorCategory.FILE_SYSTEM)
            >>> error.add_context_data("file_size", 1024)
            >>> error.add_context_data("user_id", "user123")
        """
        if not isinstance(key, str):
            raise TypeError("key must be string")
        if not key:
            raise ValueError("key must be non-empty string")
        
        self.context_data[key] = value
        logger.debug(f"Added context data to error {self.error_id}: {key}={value}")
    
    def get_context_data(self, key: str, default: Any = None) -> Any:
        """
        Get context data from the error.
        
        Args:
            key (str): Context data key to retrieve.
                Must be non-empty string.
            default (Any, optional): Default value if key not found.
                Defaults to None.
        
        Returns:
            Any: Context data value or default if key not found.
        
        Raises:
            ValueError: If key is empty
            TypeError: If key is not string
        
        Example:
            >>> error = ProcessingError("FileNotFoundError", "File not found", ErrorCategory.FILE_SYSTEM)
            >>> error.add_context_data("file_size", 1024)
            >>> size = error.get_context_data("file_size", 0)  # 1024
            >>> user = error.get_context_data("user_id", "unknown")  # "unknown"
        """
        if not isinstance(key, str):
            raise TypeError("key must be string")
        if not key:
            raise ValueError("key must be non-empty string")
        
        return self.context_data.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert ProcessingError to dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary with all ProcessingError attributes.
                Includes serialized datetime objects and enum values.
        
        Example:
            >>> error = ProcessingError("FileNotFoundError", "File not found", ErrorCategory.FILE_SYSTEM)
            >>> data = error.to_dict()
            >>> print(data["error_type"])  # "FileNotFoundError"
        """
        return {
            "error_id": self.error_id,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "error_category": self.error_category.value,
            "error_severity": self.error_severity.value,
            "file_path": self.file_path,
            "operation": self.operation,
            "stack_trace": self.stack_trace,
            "context_data": self.context_data,
            "timestamp": self.timestamp.isoformat(),
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "is_recoverable": self.is_recoverable,
            "recovery_action": self.recovery_action
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingError':
        """
        Create ProcessingError instance from dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary with ProcessingError attributes.
                Must contain required fields: error_type, error_message, error_category.
        
        Returns:
            ProcessingError: New ProcessingError instance.
        
        Raises:
            ValueError: If required fields are missing or invalid
            TypeError: If data types are incorrect
        
        Example:
            >>> data = {"error_type": "FileNotFoundError", "error_message": "File not found", ...}
            >>> error = ProcessingError.from_dict(data)
        """
        if not isinstance(data, dict):
            raise TypeError("data must be dictionary")
        
        required_fields = ["error_type", "error_message", "error_category"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Required field '{field}' missing in data")
        
        # Parse datetime
        timestamp = None
        if "timestamp" in data and data["timestamp"]:
            try:
                timestamp = datetime.fromisoformat(data["timestamp"])
            except ValueError as e:
                raise ValueError(f"Invalid timestamp format: {e}")
        
        # Parse enums
        try:
            error_category = ErrorCategory(data["error_category"])
        except ValueError:
            raise ValueError(f"Invalid error_category: {data['error_category']}")
        
        error_severity = ErrorSeverity.MEDIUM
        if "error_severity" in data:
            try:
                error_severity = ErrorSeverity(data["error_severity"])
            except ValueError:
                raise ValueError(f"Invalid error_severity: {data['error_severity']}")
        
        return cls(
            error_type=data["error_type"],
            error_message=data["error_message"],
            error_category=error_category,
            error_id=data.get("error_id"),
            error_severity=error_severity,
            file_path=data.get("file_path"),
            operation=data.get("operation"),
            stack_trace=data.get("stack_trace"),
            context_data=data.get("context_data", {}),
            timestamp=timestamp,
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            is_recoverable=data.get("is_recoverable", True),
            recovery_action=data.get("recovery_action")
        )
    
    @classmethod
    def from_exception(
        cls,
        exception: Exception,
        error_category: ErrorCategory,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None
    ) -> 'ProcessingError':
        """
        Create ProcessingError from exception object.
        
        Args:
            exception (Exception): Exception object to convert.
                Must be valid exception instance.
            error_category (ErrorCategory): Category of the error.
                Must be valid ErrorCategory enum value.
            file_path (Optional[str], optional): Path to file that caused error.
                Defaults to None.
            operation (Optional[str], optional): Operation that caused error.
                Defaults to None.
            context_data (Optional[Dict[str, Any]], optional): Additional context.
                Defaults to None.
        
        Returns:
            ProcessingError: New ProcessingError instance created from exception.
        
        Raises:
            TypeError: If exception is not Exception instance
            ValueError: If error_category is not valid enum value
        
        Example:
            >>> try:
            ...     open("nonexistent.txt")
            ... except FileNotFoundError as e:
            ...     error = ProcessingError.from_exception(e, ErrorCategory.FILE_SYSTEM, "nonexistent.txt")
        """
        if not isinstance(exception, Exception):
            raise TypeError("exception must be Exception instance")
        if not isinstance(error_category, ErrorCategory):
            raise ValueError("error_category must be valid ErrorCategory enum value")
        
        # Get stack trace
        stack_trace = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
        
        return cls(
            error_type=type(exception).__name__,
            error_message=str(exception),
            error_category=error_category,
            file_path=file_path,
            operation=operation,
            stack_trace=stack_trace,
            context_data=context_data
        )
    
    def __eq__(self, other: object) -> bool:
        """
        Compare ProcessingError instances for equality.
        
        Args:
            other (object): Object to compare with.
        
        Returns:
            bool: True if instances are equal, False otherwise.
        
        Example:
            >>> error1 = ProcessingError("FileNotFoundError", "File not found", ErrorCategory.FILE_SYSTEM)
            >>> error2 = ProcessingError("FileNotFoundError", "File not found", ErrorCategory.FILE_SYSTEM)
            >>> error1 == error2  # True if same error_type and message
        """
        if not isinstance(other, ProcessingError):
            return False
        
        return (
            self.error_type == other.error_type and
            self.error_message == other.error_message and
            self.error_category == other.error_category and
            self.error_severity == other.error_severity and
            self.file_path == other.file_path and
            self.operation == other.operation
        )
    
    def __repr__(self) -> str:
        """
        String representation of ProcessingError.
        
        Returns:
            str: Human-readable representation.
        
        Example:
            >>> error = ProcessingError("FileNotFoundError", "File not found", ErrorCategory.FILE_SYSTEM)
            >>> print(error)  # "ProcessingError(type='FileNotFoundError', category='file_system', severity='medium')"
        """
        return (
            f"ProcessingError("
            f"type='{self.error_type}', "
            f"category='{self.error_category.value}', "
            f"severity='{self.error_severity.value}', "
            f"retries={self.retry_count}/{self.max_retries})"
        )


class ErrorHandler:
    """
    Error Handler Model - Error Management Utility
    
    Provides utilities for handling, categorizing, and managing
    processing errors throughout the system.
    
    This model is used for centralized error handling, error categorization,
    and error recovery strategies.
    
    Attributes:
        handler_id (str): Unique identifier for the error handler.
            Generated as UUID4 string for uniqueness.
        error_handlers (Dict[ErrorCategory, Callable]): Category-specific handlers.
            Maps error categories to handler functions.
        default_handler (Optional[Callable]): Default error handler.
            Used when no category-specific handler is available.
        error_log (List[ProcessingError]): Log of handled errors.
            Contains all errors processed by this handler.
        max_error_log_size (int): Maximum size of error log.
            Must be positive integer.
        error_counters (Dict[str, int]): Counters for different error types.
            Tracks frequency of different error types.
    
    Example:
        >>> handler = ErrorHandler()
        >>> handler.register_handler(ErrorCategory.FILE_SYSTEM, file_error_handler)
        >>> error = ProcessingError("FileNotFoundError", "File not found", ErrorCategory.FILE_SYSTEM)
        >>> handler.handle_error(error)
    
    Raises:
        ValueError: If max_error_log_size is not positive
        TypeError: If handlers are not callable functions
    """
    
    def __init__(
        self,
        handler_id: Optional[str] = None,
        error_handlers: Optional[Dict[ErrorCategory, Callable]] = None,
        default_handler: Optional[Callable] = None,
        max_error_log_size: int = 1000
    ):
        """
        Initialize ErrorHandler instance.
        
        Args:
            handler_id (Optional[str], optional): Unique handler identifier.
                Defaults to None. If None, UUID4 will be generated.
            error_handlers (Optional[Dict[ErrorCategory, Callable]], optional): Category handlers.
                Defaults to None. Maps error categories to handler functions.
            default_handler (Optional[Callable], optional): Default error handler.
                Defaults to None. Used when no category-specific handler available.
            max_error_log_size (int, optional): Maximum error log size.
                Defaults to 1000. Must be positive integer.
        
        Raises:
            ValueError: If max_error_log_size is not positive
            TypeError: If handlers are not callable functions
        """
        if max_error_log_size <= 0:
            raise ValueError("max_error_log_size must be positive integer")
        
        self.handler_id = handler_id or str(uuid.uuid4())
        self.error_handlers = error_handlers or {}
        self.default_handler = default_handler
        self.max_error_log_size = max_error_log_size
        self.error_log = []
        self.error_counters = {}
        
        # Validate handlers are callable
        for category, handler in self.error_handlers.items():
            if not callable(handler):
                raise TypeError(f"Handler for category {category} must be callable")
        
        if self.default_handler and not callable(self.default_handler):
            raise TypeError("default_handler must be callable")
    
    def register_handler(self, category: ErrorCategory, handler: Callable) -> None:
        """
        Register error handler for specific category.
        
        Args:
            category (ErrorCategory): Error category for the handler.
                Must be valid ErrorCategory enum value.
            handler (Callable): Handler function to register.
                Must be callable function that accepts ProcessingError.
        
        Raises:
            TypeError: If handler is not callable
            ValueError: If category is not valid enum value
        
        Example:
            >>> def file_error_handler(error: ProcessingError) -> None:
            ...     print(f"Handling file error: {error.error_message}")
            >>> handler = ErrorHandler()
            >>> handler.register_handler(ErrorCategory.FILE_SYSTEM, file_error_handler)
        """
        if not isinstance(category, ErrorCategory):
            raise ValueError("category must be valid ErrorCategory enum value")
        if not callable(handler):
            raise TypeError("handler must be callable")
        
        self.error_handlers[category] = handler
        logger.info(f"Registered handler for category {category.value}")
    
    def handle_error(self, error: ProcessingError) -> bool:
        """
        Handle a processing error.
        
        Args:
            error (ProcessingError): Error to handle.
                Must be valid ProcessingError instance.
        
        Returns:
            bool: True if error was handled successfully, False otherwise.
        
        Raises:
            ValueError: If error is None
            TypeError: If error is not ProcessingError instance
        
        Example:
            >>> handler = ErrorHandler()
            >>> error = ProcessingError("FileNotFoundError", "File not found", ErrorCategory.FILE_SYSTEM)
            >>> success = handler.handle_error(error)
            >>> print(success)  # True if handled successfully
        """
        if error is None:
            raise ValueError("error cannot be None")
        if not isinstance(error, ProcessingError):
            raise TypeError("error must be ProcessingError instance")
        
        try:
            # Add to error log
            self.error_log.append(error)
            if len(self.error_log) > self.max_error_log_size:
                self.error_log.pop(0)  # Remove oldest error
            
            # Update error counter
            self.error_counters[error.error_type] = self.error_counters.get(error.error_type, 0) + 1
            
            # Find and call appropriate handler
            handler = self.error_handlers.get(error.error_category, self.default_handler)
            if handler:
                handler(error)
                logger.info(f"Handled error {error.error_id} with {error.error_category.value} handler")
                return True
            else:
                logger.warning(f"No handler found for error {error.error_id} category {error.error_category.value}")
                return False
                
        except Exception as e:
            logger.error(f"Error in error handler: {e}")
            return False
    
    def get_error_count(self, error_type: str) -> int:
        """
        Get count of errors by type.
        
        Args:
            error_type (str): Error type to count.
                Must be non-empty string.
        
        Returns:
            int: Number of errors of the specified type.
                0 if no errors of this type found.
        
        Raises:
            ValueError: If error_type is empty
            TypeError: If error_type is not string
        
        Example:
            >>> handler = ErrorHandler()
            >>> error = ProcessingError("FileNotFoundError", "File not found", ErrorCategory.FILE_SYSTEM)
            >>> handler.handle_error(error)
            >>> count = handler.get_error_count("FileNotFoundError")  # 1
        """
        if not isinstance(error_type, str):
            raise TypeError("error_type must be string")
        if not error_type:
            raise ValueError("error_type must be non-empty string")
        
        return self.error_counters.get(error_type, 0)
    
    def get_errors_by_category(self, category: ErrorCategory) -> List[ProcessingError]:
        """
        Get all errors of specific category.
        
        Args:
            category (ErrorCategory): Error category to filter by.
                Must be valid ErrorCategory enum value.
        
        Returns:
            List[ProcessingError]: List of errors in the specified category.
                Empty list if no errors in this category.
        
        Raises:
            ValueError: If category is not valid enum value
        
        Example:
            >>> handler = ErrorHandler()
            >>> file_errors = handler.get_errors_by_category(ErrorCategory.FILE_SYSTEM)
            >>> print(len(file_errors))  # Number of file system errors
        """
        if not isinstance(category, ErrorCategory):
            raise ValueError("category must be valid ErrorCategory enum value")
        
        return [error for error in self.error_log if error.error_category == category]
    
    def clear_error_log(self) -> None:
        """
        Clear the error log.
        
        Removes all errors from the error log and resets counters.
        
        Example:
            >>> handler = ErrorHandler()
            >>> handler.handle_error(error1)
            >>> handler.handle_error(error2)
            >>> handler.clear_error_log()
            >>> print(len(handler.error_log))  # 0
        """
        self.error_log.clear()
        self.error_counters.clear()
        logger.info("Error log cleared")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """
        Get error handling statistics.
        
        Returns:
            Dict[str, Any]: Dictionary with error statistics including:
                - total_errors: Total number of errors handled
                - errors_by_category: Count of errors by category
                - errors_by_type: Count of errors by type
                - errors_by_severity: Count of errors by severity
                - recent_errors: List of recent errors (last 10)
        
        Example:
            >>> handler = ErrorHandler()
            >>> handler.handle_error(error1)
            >>> handler.handle_error(error2)
            >>> stats = handler.get_error_statistics()
            >>> print(stats["total_errors"])  # 2
        """
        errors_by_category = {}
        errors_by_severity = {}
        
        for error in self.error_log:
            # Count by category
            category = error.error_category.value
            errors_by_category[category] = errors_by_category.get(category, 0) + 1
            
            # Count by severity
            severity = error.error_severity.value
            errors_by_severity[severity] = errors_by_severity.get(severity, 0) + 1
        
        return {
            "total_errors": len(self.error_log),
            "errors_by_category": errors_by_category,
            "errors_by_type": self.error_counters.copy(),
            "errors_by_severity": errors_by_severity,
            "recent_errors": self.error_log[-10:] if self.error_log else []
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert ErrorHandler to dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary with ErrorHandler attributes.
                Note: Handler functions are not serialized.
        
        Example:
            >>> handler = ErrorHandler()
            >>> data = handler.to_dict()
            >>> print(data["handler_id"])  # UUID string
        """
        return {
            "handler_id": self.handler_id,
            "max_error_log_size": self.max_error_log_size,
            "error_log_size": len(self.error_log),
            "error_counters": self.error_counters.copy(),
            "registered_categories": [cat.value for cat in self.error_handlers.keys()],
            "has_default_handler": self.default_handler is not None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorHandler':
        """
        Create ErrorHandler instance from dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary with ErrorHandler attributes.
                Must contain required fields: handler_id.
        
        Returns:
            ErrorHandler: New ErrorHandler instance.
                Note: Handler functions must be re-registered.
        
        Raises:
            ValueError: If required fields are missing or invalid
            TypeError: If data types are incorrect
        
        Example:
            >>> data = {"handler_id": "uuid", "max_error_log_size": 1000}
            >>> handler = ErrorHandler.from_dict(data)
        """
        if not isinstance(data, dict):
            raise TypeError("data must be dictionary")
        
        if "handler_id" not in data:
            raise ValueError("Required field 'handler_id' missing in data")
        
        return cls(
            handler_id=data["handler_id"],
            max_error_log_size=data.get("max_error_log_size", 1000)
        )
    
    def __eq__(self, other: object) -> bool:
        """
        Compare ErrorHandler instances for equality.
        
        Args:
            other (object): Object to compare with.
        
        Returns:
            bool: True if instances are equal, False otherwise.
        
        Example:
            >>> handler1 = ErrorHandler()
            >>> handler2 = ErrorHandler()
            >>> handler1 == handler2  # True if same handler_id and configuration
        """
        if not isinstance(other, ErrorHandler):
            return False
        
        return (
            self.handler_id == other.handler_id and
            self.max_error_log_size == other.max_error_log_size and
            len(self.error_handlers) == len(other.error_handlers) and
            self.default_handler is other.default_handler
        )
    
    def __repr__(self) -> str:
        """
        String representation of ErrorHandler.
        
        Returns:
            str: Human-readable representation.
        
        Example:
            >>> handler = ErrorHandler()
            >>> print(handler)  # "ErrorHandler(id='uuid', handlers=0, errors=0)"
        """
        return (
            f"ErrorHandler("
            f"id='{self.handler_id}', "
            f"handlers={len(self.error_handlers)}, "
            f"errors={len(self.error_log)})"
        ) 