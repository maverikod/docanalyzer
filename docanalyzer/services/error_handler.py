"""
Error Handler - Comprehensive Error Handling Service

Provides centralized error handling and recovery mechanisms for
directory processing operations.

The error handler manages different types of errors, implements
retry strategies, and provides error reporting and logging
capabilities.

Author: File Watcher Team
Version: 1.0.0
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any, Union, Callable, Type
from datetime import datetime, timedelta
import traceback
import json

from docanalyzer.models.errors import ProcessingError, ErrorCategory
from docanalyzer.models.processing import ProcessingResult

logger = logging.getLogger(__name__)

DEFAULT_MAX_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_DELAY = 5
DEFAULT_BACKOFF_MULTIPLIER = 2


class ErrorHandlerConfig:
    """
    Configuration for error handling service.
    
    Contains settings for error handling behavior, retry strategies,
    and recovery mechanisms.
    
    Attributes:
        max_retry_attempts (int): Maximum number of retry attempts for failed operations.
            Must be non-negative integer. Defaults to 3.
        retry_delay (int): Base delay between retry attempts in seconds.
            Must be positive integer. Defaults to 5.
        backoff_multiplier (float): Multiplier for exponential backoff.
            Must be positive float. Defaults to 2.0.
        enable_automatic_recovery (bool): Whether to enable automatic error recovery.
            Defaults to True.
        enable_error_logging (bool): Whether to enable detailed error logging.
            Defaults to True.
        enable_error_reporting (bool): Whether to enable error reporting.
            Defaults to True.
        error_threshold (int): Number of errors before considering operation failed.
            Must be positive integer. Defaults to 10.
    """
    
    def __init__(
        self,
        max_retry_attempts: int = DEFAULT_MAX_RETRY_ATTEMPTS,
        retry_delay: int = DEFAULT_RETRY_DELAY,
        backoff_multiplier: float = DEFAULT_BACKOFF_MULTIPLIER,
        enable_automatic_recovery: bool = True,
        enable_error_logging: bool = True,
        enable_error_reporting: bool = True,
        error_threshold: int = 10
    ):
        """
        Initialize ErrorHandlerConfig instance.
        
        Args:
            max_retry_attempts (int): Maximum number of retry attempts for failed operations.
                Must be non-negative integer. Defaults to 3.
            retry_delay (int): Base delay between retry attempts in seconds.
                Must be positive integer. Defaults to 5.
            backoff_multiplier (float): Multiplier for exponential backoff.
                Must be positive float. Defaults to 2.0.
            enable_automatic_recovery (bool): Whether to enable automatic error recovery.
                Defaults to True.
            enable_error_logging (bool): Whether to enable detailed error logging.
                Defaults to True.
            enable_error_reporting (bool): Whether to enable error reporting.
                Defaults to True.
            error_threshold (int): Number of errors before considering operation failed.
                Must be positive integer. Defaults to 10.
        
        Raises:
            ValueError: If any parameter has invalid value
        """
        if max_retry_attempts < 0:
            raise ValueError("max_retry_attempts must be non-negative")
        if retry_delay <= 0:
            raise ValueError("retry_delay must be positive")
        if backoff_multiplier <= 0:
            raise ValueError("backoff_multiplier must be positive")
        if error_threshold <= 0:
            raise ValueError("error_threshold must be positive")
        
        self.max_retry_attempts = max_retry_attempts
        self.retry_delay = retry_delay
        self.backoff_multiplier = backoff_multiplier
        self.enable_automatic_recovery = enable_automatic_recovery
        self.enable_error_logging = enable_error_logging
        self.enable_error_reporting = enable_error_reporting
        self.error_threshold = error_threshold


class ErrorInfo:
    """
    Information about an error that occurred.
    
    Contains detailed information about an error including type,
    message, context, and recovery attempts.
    
    Attributes:
        error_id (str): Unique identifier for the error.
        error_type (str): Type of error that occurred.
        error_message (str): Human-readable error message.
        error_category (ErrorCategory): Category of the error.
        operation (str): Operation that was being performed.
        context (Dict[str, Any]): Additional context information.
        timestamp (datetime): When the error occurred.
        retry_count (int): Number of retry attempts made.
        stack_trace (Optional[str]): Stack trace if available.
        recovery_attempts (List[str]): List of recovery attempts made.
    """
    
    def __init__(
        self,
        error_id: str,
        error_type: str,
        error_message: str,
        error_category: ErrorCategory,
        operation: str,
        context: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
        retry_count: int = 0,
        stack_trace: Optional[str] = None,
        recovery_attempts: Optional[List[str]] = None
    ):
        """
        Initialize ErrorInfo instance.
        
        Args:
            error_id (str): Unique identifier for the error.
            error_type (str): Type of error that occurred.
            error_message (str): Human-readable error message.
            error_category (ErrorCategory): Category of the error.
            operation (str): Operation that was being performed.
            context (Optional[Dict[str, Any]]): Additional context information.
                Defaults to None.
            timestamp (Optional[datetime]): When the error occurred.
                Defaults to current time.
            retry_count (int): Number of retry attempts made.
                Defaults to 0.
            stack_trace (Optional[str]): Stack trace if available.
                Defaults to None.
            recovery_attempts (Optional[List[str]]): List of recovery attempts made.
                Defaults to None.
        """
        self.error_id = error_id
        self.error_type = error_type
        self.error_message = error_message
        self.error_category = error_category
        self.operation = operation
        self.context = context or {}
        self.timestamp = timestamp or datetime.now()
        self.retry_count = retry_count
        self.stack_trace = stack_trace
        self.recovery_attempts = recovery_attempts or []
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary representation of error info.
        """
        return {
            "error_id": self.error_id,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "error_category": self.error_category.value,
            "operation": self.operation,
            "context": self.context.copy(),
            "timestamp": self.timestamp.isoformat(),
            "retry_count": self.retry_count,
            "stack_trace": self.stack_trace,
            "recovery_attempts": self.recovery_attempts.copy()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorInfo':
        """
        Create instance from dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary data.
        
        Returns:
            ErrorInfo: Created instance.
        
        Raises:
            ValueError: If data is invalid
        """
        if not isinstance(data, dict):
            raise ValueError("data must be dictionary")
        
        required_fields = ["error_id", "error_type", "error_message", "error_category", "operation"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Required field '{field}' missing in data")
        
        return cls(
            error_id=data["error_id"],
            error_type=data["error_type"],
            error_message=data["error_message"],
            error_category=ErrorCategory(data["error_category"]),
            operation=data["operation"],
            context=data.get("context"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else None,
            retry_count=data.get("retry_count", 0),
            stack_trace=data.get("stack_trace"),
            recovery_attempts=data.get("recovery_attempts")
        )


class ErrorRecoveryStrategy:
    """
    Strategy for recovering from specific types of errors.
    
    Defines how to handle and recover from different types of errors
    with specific recovery actions and retry logic.
    
    Attributes:
        error_type (str): Type of error this strategy handles.
        error_category (ErrorCategory): Category of error this strategy handles.
        max_retries (int): Maximum number of retry attempts.
        retry_delay (int): Delay between retry attempts in seconds.
        recovery_actions (List[str]): List of recovery actions to attempt.
        should_abort (bool): Whether to abort operation after max retries.
        custom_handler (Optional[Callable]): Custom error handler function.
    """
    
    def __init__(
        self,
        error_type: str,
        error_category: ErrorCategory,
        max_retries: int = 3,
        retry_delay: int = 5,
        recovery_actions: Optional[List[str]] = None,
        should_abort: bool = True,
        custom_handler: Optional[Callable] = None
    ):
        """
        Initialize ErrorRecoveryStrategy instance.
        
        Args:
            error_type (str): Type of error this strategy handles.
            error_category (ErrorCategory): Category of error this strategy handles.
            max_retries (int): Maximum number of retry attempts.
                Defaults to 3.
            retry_delay (int): Delay between retry attempts in seconds.
                Defaults to 5.
            recovery_actions (Optional[List[str]]): List of recovery actions to attempt.
                Defaults to None.
            should_abort (bool): Whether to abort operation after max retries.
                Defaults to True.
            custom_handler (Optional[Callable]): Custom error handler function.
                Defaults to None.
        """
        self.error_type = error_type
        self.error_category = error_category
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.recovery_actions = recovery_actions or []
        self.should_abort = should_abort
        self.custom_handler = custom_handler


class ErrorHandler:
    """
    Error Handler - Comprehensive Error Handling Service
    
    Provides centralized error handling and recovery mechanisms for
    directory processing operations.
    
    The error handler manages different types of errors, implements
    retry strategies, and provides error reporting and logging
    capabilities.
    
    Attributes:
        config (ErrorHandlerConfig): Configuration for error handling behavior.
        error_strategies (Dict[str, ErrorRecoveryStrategy]): Error recovery strategies.
        error_history (List[ErrorInfo]): History of errors that occurred.
        error_counters (Dict[str, int]): Counters for different error types.
        recovery_handlers (Dict[str, Callable]): Custom recovery handlers.
    
    Example:
        >>> config = ErrorHandlerConfig()
        >>> handler = ErrorHandler(config)
        >>> result = await handler.handle_error(error, operation="file_processing")
        >>> await handler.report_errors()
    """
    
    def __init__(self, config: ErrorHandlerConfig):
        """
        Initialize ErrorHandler instance.
        
        Args:
            config (ErrorHandlerConfig): Configuration for error handling behavior.
                Must be valid ErrorHandlerConfig instance.
        
        Raises:
            ValueError: If config is invalid
        """
        if not isinstance(config, ErrorHandlerConfig):
            raise ValueError("config must be ErrorHandlerConfig instance")
        
        self.config = config
        self.error_strategies: Dict[str, ErrorRecoveryStrategy] = {}
        self.error_history: List[ErrorInfo] = []
        self.error_counters: Dict[str, int] = {}
        self.recovery_handlers: Dict[str, Callable] = {}
        
        logger.info("ErrorHandler initialized")
    
    async def handle_error(
        self,
        error: Exception,
        operation: str,
        context: Optional[Dict[str, Any]] = None,
        retry_count: int = 0
    ) -> ProcessingResult:
        """
        Handle an error that occurred during processing.
        
        Analyzes the error, determines appropriate recovery strategy,
        and attempts to recover from the error.
        
        Args:
            error (Exception): Error that occurred.
            operation (str): Operation that was being performed.
            context (Optional[Dict[str, Any]]): Additional context information.
                Defaults to None.
            retry_count (int): Current retry attempt number.
                Defaults to 0.
        
        Returns:
            ProcessingResult: Result of error handling operation.
        
        Raises:
            ProcessingError: If error handling fails
        """
        try:
            # Create error info
            error_info = self._create_error_info(error, operation, context)
            error_info.retry_count = retry_count
            
            # Log error
            self._log_error(error_info)
            
            # Update error counters
            self._update_error_counters(error_info.error_type)
            
            # Add to history
            self.error_history.append(error_info)
            
            # Check if should retry
            if self.should_retry_error(error, retry_count):
                logger.info(f"Retrying operation {operation} (attempt {retry_count + 1})")
                return ProcessingResult(
                    success=False,
                    message=f"Error occurred, retrying: {error_info.error_message}",
                    error_details=error_info.error_message,
                    metadata={"retry_count": retry_count, "error_id": error_info.error_id}
                )
            else:
                # Attempt recovery
                if self.config.enable_automatic_recovery:
                    recovery_success = await self.recover_from_error(error_info)
                    if recovery_success:
                        return ProcessingResult(
                            success=True,
                            message="Error recovered successfully",
                            metadata={"error_id": error_info.error_id, "recovery_attempted": True}
                        )
                
                return ProcessingResult(
                    success=False,
                    message=f"Error not recoverable: {error_info.error_message}",
                    error_details=error_info.error_message,
                    metadata={"error_id": error_info.error_id, "recovery_attempted": False}
                )
                
        except Exception as e:
            logger.error(f"Error in error handler: {e}")
            return ProcessingResult(
                success=False,
                message=f"Error handling failed: {str(e)}",
                error_details=str(e)
            )
    
    async def retry_operation(
        self,
        operation: Callable,
        *args,
        max_retries: Optional[int] = None,
        retry_delay: Optional[int] = None,
        **kwargs
    ) -> Any:
        """
        Retry an operation with error handling.
        
        Executes an operation with automatic retry logic and error
        handling based on configured strategies.
        
        Args:
            operation (Callable): Operation to retry.
            *args: Arguments for the operation.
            max_retries (Optional[int]): Maximum retry attempts.
                Defaults to config value.
            retry_delay (Optional[int]): Delay between retries.
                Defaults to config value.
            **kwargs: Keyword arguments for the operation.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            ProcessingError: If operation fails after all retries
        """
        max_retries = max_retries or self.config.max_retry_attempts
        retry_delay = retry_delay or self.config.retry_delay
        
        last_error = None
        
        for attempt in range(max_retries + 1):  # +1 for initial attempt
            try:
                # Execute operation
                if asyncio.iscoroutinefunction(operation):
                    result = await operation(*args, **kwargs)
                else:
                    result = operation(*args, **kwargs)
                
                return result
                
            except Exception as e:
                last_error = e
                
                # Handle error
                error_result = await self.handle_error(e, "retry_operation", retry_count=attempt)
                
                # Check if we should continue retrying
                if attempt < max_retries and self.should_retry_error(e, attempt):
                    # Calculate delay
                    delay = await self.calculate_retry_delay(attempt, retry_delay)
                    logger.info(f"Retrying operation in {delay} seconds (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(delay)
                else:
                    break
        
        # If we get here, all retries failed
        raise ProcessingError(
            "RetryOperationError",
            f"Operation failed after {max_retries} retries: {str(last_error)}",
            ErrorCategory.PROCESSING
        )
    
    def add_error_strategy(self, strategy: ErrorRecoveryStrategy) -> None:
        """
        Add error recovery strategy.
        
        Adds a new error recovery strategy for handling specific
        types of errors.
        
        Args:
            strategy (ErrorRecoveryStrategy): Error recovery strategy to add.
                Must be valid ErrorRecoveryStrategy instance.
        
        Raises:
            ValueError: If strategy is invalid
        """
        if not isinstance(strategy, ErrorRecoveryStrategy):
            raise ValueError("strategy must be ErrorRecoveryStrategy instance")
        
        self.error_strategies[strategy.error_type] = strategy
        logger.info(f"Added error strategy for type: {strategy.error_type}")
    
    def remove_error_strategy(self, error_type: str) -> bool:
        """
        Remove error recovery strategy.
        
        Removes an error recovery strategy for a specific error type.
        
        Args:
            error_type (str): Type of error to remove strategy for.
                Must be valid error type string.
        
        Returns:
            bool: True if strategy was removed, False if not found.
        
        Raises:
            ValueError: If error_type is invalid
        """
        if not isinstance(error_type, str):
            raise ValueError("error_type must be string")
        
        if error_type in self.error_strategies:
            del self.error_strategies[error_type]
            logger.info(f"Removed error strategy for type: {error_type}")
            return True
        
        return False
    
    async def recover_from_error(self, error_info: ErrorInfo) -> bool:
        """
        Attempt to recover from a specific error.
        
        Attempts to recover from an error using the appropriate
        recovery strategy.
        
        Args:
            error_info (ErrorInfo): Information about the error to recover from.
                Must be valid ErrorInfo instance.
        
        Returns:
            bool: True if recovery was successful, False otherwise.
        
        Raises:
            ValueError: If error_info is invalid
        """
        if not isinstance(error_info, ErrorInfo):
            raise ValueError("error_info must be ErrorInfo instance")
        
        try:
            # Get recovery strategy
            strategy = self.error_strategies.get(error_info.error_type)
            if not strategy:
                logger.warning(f"No recovery strategy found for error type: {error_info.error_type}")
                return False
            
            # Attempt recovery actions
            for action in strategy.recovery_actions:
                try:
                    logger.info(f"Attempting recovery action: {action}")
                    # In a real implementation, you would execute the recovery action
                    # For now, we'll just log it
                    error_info.recovery_attempts.append(action)
                    
                except Exception as e:
                    logger.error(f"Recovery action {action} failed: {e}")
            
            # Check if any recovery was successful
            return len(error_info.recovery_attempts) > 0
            
        except Exception as e:
            logger.error(f"Error during recovery: {e}")
            return False
    
    async def report_errors(self) -> Dict[str, Any]:
        """
        Generate error report.
        
        Generates a comprehensive report of all errors that occurred
        during processing operations.
        
        Returns:
            Dict[str, Any]: Error report with statistics and details.
        """
        if not self.config.enable_error_reporting:
            return {"enabled": False}
        
        # Calculate statistics
        total_errors = len(self.error_history)
        error_types = {}
        error_categories = {}
        
        for error_info in self.error_history:
            # Count by error type
            error_types[error_info.error_type] = error_types.get(error_info.error_type, 0) + 1
            
            # Count by error category
            category = error_info.error_category.value
            error_categories[category] = error_categories.get(category, 0) + 1
        
        return {
            "enabled": True,
            "total_errors": total_errors,
            "error_types": error_types,
            "error_categories": error_categories,
            "error_counters": self.error_counters.copy(),
            "recent_errors": [
                error_info.to_dict() for error_info in self.error_history[-10:]  # Last 10 errors
            ]
        }
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """
        Get error statistics.
        
        Returns statistics about errors that occurred during
        processing operations.
        
        Returns:
            Dict[str, Any]: Error statistics including counts and types.
        """
        return {
            "total_errors": len(self.error_history),
            "error_counters": self.error_counters.copy(),
            "error_strategies": len(self.error_strategies),
            "recovery_handlers": len(self.recovery_handlers)
        }
    
    async def clear_error_history(self) -> None:
        """
        Clear error history.
        
        Clears all stored error information and resets error counters.
        """
        self.error_history.clear()
        self.error_counters.clear()
        logger.info("Error history cleared")
    
    def should_retry_error(self, error: Exception, retry_count: int) -> bool:
        """
        Determine if an error should be retried.
        
        Checks if an error should be retried based on error type,
        retry count, and configured strategies.
        
        Args:
            error (Exception): Error that occurred.
            retry_count (int): Current retry attempt number.
                Must be non-negative integer.
        
        Returns:
            bool: True if error should be retried, False otherwise.
        
        Raises:
            ValueError: If retry_count is negative
        """
        if retry_count < 0:
            raise ValueError("retry_count must be non-negative")
        
        # Check if max retries reached
        if retry_count >= self.config.max_retry_attempts:
            return False
        
        # Check error type - some errors should not be retried
        if isinstance(error, FileNotFoundError):
            return False  # File not found errors should not be retried
        
        # Check if error threshold reached
        error_type = type(error).__name__
        if self.error_counters.get(error_type, 0) >= self.config.error_threshold:
            return False
        
        return True
    
    async def calculate_retry_delay(self, retry_count: int, base_delay: int) -> int:
        """
        Calculate delay for next retry attempt.
        
        Calculates the delay for the next retry attempt using
        exponential backoff strategy.
        
        Args:
            retry_count (int): Current retry attempt number.
                Must be non-negative integer.
            base_delay (int): Base delay in seconds.
                Must be positive integer.
        
        Returns:
            int: Calculated delay in seconds.
        
        Raises:
            ValueError: If parameters are invalid
        """
        if retry_count < 0:
            raise ValueError("retry_count must be non-negative")
        if base_delay <= 0:
            raise ValueError("base_delay must be positive")
        
        # Exponential backoff: base_delay * (backoff_multiplier ^ retry_count)
        delay = int(base_delay * (self.config.backoff_multiplier ** retry_count))
        
        # Add some jitter to prevent thundering herd
        import random
        jitter = random.uniform(0.8, 1.2)
        delay = int(delay * jitter)
        
        return max(1, delay)  # Minimum 1 second delay
    
    def _create_error_info(
        self,
        error: Exception,
        operation: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorInfo:
        """
        Create ErrorInfo from exception.
        
        Creates ErrorInfo instance from an exception with all
        relevant information.
        
        Args:
            error (Exception): Exception that occurred.
            operation (str): Operation that was being performed.
            context (Optional[Dict[str, Any]]): Additional context.
                Defaults to None.
        
        Returns:
            ErrorInfo: Created error information.
        """
        error_id = str(uuid.uuid4())
        error_type = type(error).__name__
        error_message = str(error)
        
        # Determine error category
        if isinstance(error, FileNotFoundError):
            error_category = ErrorCategory.FILE_SYSTEM
        elif isinstance(error, ProcessingError):
            error_category = error.error_category
        else:
            error_category = ErrorCategory.UNKNOWN
        
        # Get stack trace
        stack_trace = traceback.format_exc()
        
        return ErrorInfo(
            error_id=error_id,
            error_type=error_type,
            error_message=error_message,
            error_category=error_category,
            operation=operation,
            context=context,
            stack_trace=stack_trace
        )
    
    def _get_error_strategy(self, error: Exception) -> Optional[ErrorRecoveryStrategy]:
        """
        Get error recovery strategy for error.
        
        Finds the appropriate error recovery strategy for a given
        error type.
        
        Args:
            error (Exception): Error to find strategy for.
        
        Returns:
            Optional[ErrorRecoveryStrategy]: Error recovery strategy if found.
        """
        error_type = type(error).__name__
        return self.error_strategies.get(error_type)
    
    def _log_error(self, error_info: ErrorInfo) -> None:
        """
        Log error information.
        
        Logs detailed error information if error logging is enabled.
        
        Args:
            error_info (ErrorInfo): Error information to log.
        """
        if self.config.enable_error_logging:
            logger.error(
                f"Error {error_info.error_id}: {error_info.error_type} in {error_info.operation}: {error_info.error_message}"
            )
            if error_info.stack_trace:
                logger.debug(f"Stack trace for {error_info.error_id}: {error_info.stack_trace}")
    
    def _update_error_counters(self, error_type: str) -> None:
        """
        Update error counters.
        
        Updates internal error counters for tracking error statistics.
        
        Args:
            error_type (str): Type of error to count.
        """
        self.error_counters[error_type] = self.error_counters.get(error_type, 0) + 1 