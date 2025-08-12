"""
Tests for Error Models

Comprehensive test suite for error models including ProcessingError
and ErrorHandler classes.

Author: DocAnalyzer Team
Version: 1.0.0
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from docanalyzer.models.errors import (
    ErrorSeverity, ErrorCategory, ProcessingError, ErrorHandler
)


class TestErrorSeverity:
    """Test suite for ErrorSeverity enum."""
    
    def test_error_severity_values(self):
        """Test that ErrorSeverity has expected values."""
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.CRITICAL.value == "critical"


class TestErrorCategory:
    """Test suite for ErrorCategory enum."""
    
    def test_error_category_values(self):
        """Test that ErrorCategory has expected values."""
        assert ErrorCategory.FILE_SYSTEM.value == "file_system"
        assert ErrorCategory.PROCESSING.value == "processing"
        assert ErrorCategory.DATABASE.value == "database"
        assert ErrorCategory.NETWORK.value == "network"
        assert ErrorCategory.CONFIGURATION.value == "configuration"
        assert ErrorCategory.VALIDATION.value == "validation"
        assert ErrorCategory.PERMISSION.value == "permission"
        assert ErrorCategory.UNKNOWN.value == "unknown"


class TestProcessingError:
    """Test suite for ProcessingError class."""
    
    @pytest.fixture
    def processing_error(self):
        """Create ProcessingError instance for testing."""
        return ProcessingError(
            error_type="FileNotFoundError",
            error_message="File not found",
            error_category=ErrorCategory.FILE_SYSTEM
        )
    
    def test_processing_error_creation_success(self):
        """Test successful ProcessingError creation."""
        # Act
        error = ProcessingError(
            error_type="FileNotFoundError",
            error_message="File not found",
            error_category=ErrorCategory.FILE_SYSTEM
        )
        
        # Assert
        assert error.error_type == "FileNotFoundError"
        assert error.error_message == "File not found"
        assert error.error_category == ErrorCategory.FILE_SYSTEM
        assert error.error_severity == ErrorSeverity.MEDIUM
        assert error.file_path is None
        assert error.operation is None
        assert error.stack_trace is None
        assert error.context_data == {}
        assert error.retry_count == 0
        assert error.max_retries == 3
        assert error.is_recoverable is True
        assert error.recovery_action is None
    
    def test_processing_error_creation_with_optional_params(self):
        """Test ProcessingError creation with optional parameters."""
        # Arrange
        timestamp = datetime.now()
        context_data = {"file_size": 1024, "user_id": "user123"}
        
        # Act
        error = ProcessingError(
            error_type="PermissionError",
            error_message="Permission denied",
            error_category=ErrorCategory.PERMISSION,
            error_severity=ErrorSeverity.HIGH,
            file_path="/path/to/file.txt",
            operation="file_read",
            stack_trace="Traceback...",
            context_data=context_data,
            timestamp=timestamp,
            retry_count=2,
            max_retries=5,
            is_recoverable=False,
            recovery_action="Check file permissions"
        )
        
        # Assert
        assert error.error_severity == ErrorSeverity.HIGH
        assert error.file_path == "/path/to/file.txt"
        assert error.operation == "file_read"
        assert error.stack_trace == "Traceback..."
        assert error.context_data == context_data
        assert error.timestamp == timestamp
        assert error.retry_count == 2
        assert error.max_retries == 5
        assert error.is_recoverable is False
        assert error.recovery_action == "Check file permissions"
    
    def test_processing_error_creation_empty_type(self):
        """Test ProcessingError creation with empty error type."""
        # Act & Assert
        with pytest.raises(ValueError, match="error_type must be non-empty string"):
            ProcessingError("", "File not found", ErrorCategory.FILE_SYSTEM)
    
    def test_processing_error_creation_empty_message(self):
        """Test ProcessingError creation with empty error message."""
        # Act & Assert
        with pytest.raises(ValueError, match="error_message must be non-empty string"):
            ProcessingError("FileNotFoundError", "", ErrorCategory.FILE_SYSTEM)
    
    def test_processing_error_creation_invalid_category(self):
        """Test ProcessingError creation with invalid error category."""
        # Act & Assert
        with pytest.raises(TypeError, match="error_category must be ErrorCategory enum value"):
            ProcessingError("FileNotFoundError", "File not found", "invalid_category")
    
    def test_processing_error_creation_invalid_severity(self):
        """Test ProcessingError creation with invalid error severity."""
        # Act & Assert
        with pytest.raises(TypeError, match="error_severity must be ErrorSeverity enum value"):
            ProcessingError(
                "FileNotFoundError",
                "File not found",
                ErrorCategory.FILE_SYSTEM,
                error_severity="invalid_severity"
            )
    
    def test_processing_error_creation_negative_retry_count(self):
        """Test ProcessingError creation with negative retry count."""
        # Act & Assert
        with pytest.raises(ValueError, match="retry_count must be non-negative integer"):
            ProcessingError(
                "FileNotFoundError",
                "File not found",
                ErrorCategory.FILE_SYSTEM,
                retry_count=-1
            )
    
    def test_processing_error_creation_invalid_max_retries(self):
        """Test ProcessingError creation with invalid max retries."""
        # Act & Assert
        with pytest.raises(ValueError, match="max_retries must be positive integer"):
            ProcessingError(
                "FileNotFoundError",
                "File not found",
                ErrorCategory.FILE_SYSTEM,
                max_retries=0
            )
    
    def test_increment_retry_count(self, processing_error):
        """Test increment_retry_count method."""
        # Act
        processing_error.increment_retry_count()
        
        # Assert
        assert processing_error.retry_count == 1
    
    def test_increment_retry_count_multiple(self, processing_error):
        """Test increment_retry_count method multiple times."""
        # Act
        processing_error.increment_retry_count()
        processing_error.increment_retry_count()
        processing_error.increment_retry_count()
        
        # Assert
        assert processing_error.retry_count == 3
    
    def test_increment_retry_count_max_reached(self, processing_error):
        """Test increment_retry_count when max retries reached."""
        # Arrange
        processing_error.retry_count = 3  # Max retries
        
        # Act
        processing_error.increment_retry_count()
        
        # Assert
        assert processing_error.retry_count == 3  # Should not exceed max
    
    def test_can_retry_true(self, processing_error):
        """Test can_retry when retry is possible."""
        # Act
        can_retry = processing_error.can_retry()
        
        # Assert
        assert can_retry is True
    
    def test_can_retry_max_reached(self, processing_error):
        """Test can_retry when max retries reached."""
        # Arrange
        processing_error.retry_count = 3  # Max retries
        
        # Act
        can_retry = processing_error.can_retry()
        
        # Assert
        assert can_retry is False
    
    def test_can_retry_not_recoverable(self, processing_error):
        """Test can_retry when error is not recoverable."""
        # Arrange
        processing_error.is_recoverable = False
        
        # Act
        can_retry = processing_error.can_retry()
        
        # Assert
        assert can_retry is False
    
    def test_add_context_data(self, processing_error):
        """Test add_context_data method."""
        # Act
        processing_error.add_context_data("file_size", 1024)
        processing_error.add_context_data("user_id", "user123")
        
        # Assert
        assert processing_error.context_data["file_size"] == 1024
        assert processing_error.context_data["user_id"] == "user123"
    
    def test_add_context_data_empty_key(self, processing_error):
        """Test add_context_data with empty key."""
        # Act & Assert
        with pytest.raises(ValueError, match="key must be non-empty string"):
            processing_error.add_context_data("", "value")
    
    def test_add_context_data_invalid_key_type(self, processing_error):
        """Test add_context_data with invalid key type."""
        # Act & Assert
        with pytest.raises(TypeError, match="key must be string"):
            processing_error.add_context_data(123, "value")
    
    def test_get_context_data(self, processing_error):
        """Test get_context_data method."""
        # Arrange
        processing_error.add_context_data("file_size", 1024)
        
        # Act
        file_size = processing_error.get_context_data("file_size")
        user_id = processing_error.get_context_data("user_id", "default")
        
        # Assert
        assert file_size == 1024
        assert user_id == "default"
    
    def test_get_context_data_empty_key(self, processing_error):
        """Test get_context_data with empty key."""
        # Act & Assert
        with pytest.raises(ValueError, match="key must be non-empty string"):
            processing_error.get_context_data("")
    
    def test_get_context_data_invalid_key_type(self, processing_error):
        """Test get_context_data with invalid key type."""
        # Act & Assert
        with pytest.raises(TypeError, match="key must be string"):
            processing_error.get_context_data(123)
    
    def test_to_dict(self, processing_error):
        """Test to_dict method."""
        # Act
        data = processing_error.to_dict()
        
        # Assert
        assert data["error_type"] == "FileNotFoundError"
        assert data["error_message"] == "File not found"
        assert data["error_category"] == "file_system"
        assert data["error_severity"] == "medium"
        assert data["file_path"] is None
        assert data["operation"] is None
        assert data["stack_trace"] is None
        assert data["context_data"] == {}
        assert data["retry_count"] == 0
        assert data["max_retries"] == 3
        assert data["is_recoverable"] is True
        assert data["recovery_action"] is None
        assert "timestamp" in data
    
    def test_from_dict(self, processing_error):
        """Test from_dict method."""
        # Arrange
        data = processing_error.to_dict()
        
        # Act
        new_error = ProcessingError.from_dict(data)
        
        # Assert
        assert new_error.error_type == processing_error.error_type
        assert new_error.error_message == processing_error.error_message
        assert new_error.error_category == processing_error.error_category
    
    def test_from_dict_missing_required_fields(self):
        """Test from_dict method with missing required fields."""
        # Arrange
        data = {"error_type": "FileNotFoundError"}  # Missing other required fields
        
        # Act & Assert
        with pytest.raises(ValueError, match="Required field 'error_message' missing in data"):
            ProcessingError.from_dict(data)
    
    def test_from_exception(self):
        """Test from_exception method."""
        # Arrange
        exception = FileNotFoundError("File not found")
        
        # Act
        error = ProcessingError.from_exception(
            exception=exception,
            error_category=ErrorCategory.FILE_SYSTEM,
            file_path="/path/to/file.txt",
            operation="file_read"
        )
        
        # Assert
        assert error.error_type == "FileNotFoundError"
        assert error.error_message == "File not found"
        assert error.error_category == ErrorCategory.FILE_SYSTEM
        assert error.file_path == "/path/to/file.txt"
        assert error.operation == "file_read"
        assert error.stack_trace is not None
    
    def test_from_exception_invalid_exception(self):
        """Test from_exception with invalid exception."""
        # Act & Assert
        with pytest.raises(TypeError, match="exception must be Exception instance"):
            ProcessingError.from_exception(
                exception="not an exception",
                error_category=ErrorCategory.FILE_SYSTEM
            )
    
    def test_from_exception_invalid_category(self):
        """Test from_exception with invalid error category."""
        # Arrange
        exception = FileNotFoundError("File not found")
        
        # Act & Assert
        with pytest.raises(ValueError, match="error_category must be valid ErrorCategory enum value"):
            ProcessingError.from_exception(
                exception=exception,
                error_category="invalid_category"
            )
    
    def test_equality(self, processing_error):
        """Test equality comparison."""
        # Arrange
        same_error = ProcessingError(
            error_type=processing_error.error_type,
            error_message=processing_error.error_message,
            error_category=processing_error.error_category
        )
        
        # Act & Assert
        assert processing_error == same_error
    
    def test_inequality(self, processing_error):
        """Test inequality comparison."""
        # Arrange
        different_error = ProcessingError(
            error_type="PermissionError",
            error_message=processing_error.error_message,
            error_category=processing_error.error_category
        )
        
        # Act & Assert
        assert processing_error != different_error
    
    def test_equality_different_type(self, processing_error):
        """Test equality with different type."""
        # Act & Assert
        assert processing_error != "not a ProcessingError"
    
    def test_repr(self, processing_error):
        """Test string representation."""
        # Act
        repr_str = repr(processing_error)
        
        # Assert
        assert "ProcessingError" in repr_str
        assert processing_error.error_type in repr_str
        assert processing_error.error_category.value in repr_str
        assert processing_error.error_severity.value in repr_str


class TestErrorHandler:
    """Test suite for ErrorHandler class."""
    
    @pytest.fixture
    def error_handler(self):
        """Create ErrorHandler instance for testing."""
        return ErrorHandler()
    
    @pytest.fixture
    def mock_handler(self):
        """Create mock handler function."""
        return Mock()
    
    @pytest.fixture
    def processing_error(self):
        """Create ProcessingError instance for testing."""
        return ProcessingError(
            error_type="FileNotFoundError",
            error_message="File not found",
            error_category=ErrorCategory.FILE_SYSTEM
        )
    
    def test_error_handler_creation_success(self):
        """Test successful ErrorHandler creation."""
        # Act
        handler = ErrorHandler()
        
        # Assert
        assert handler.error_handlers == {}
        assert handler.default_handler is None
        assert handler.error_log == []
        assert handler.max_error_log_size == 1000
        assert handler.error_counters == {}
    
    def test_error_handler_creation_with_optional_params(self):
        """Test ErrorHandler creation with optional parameters."""
        # Arrange
        mock_handler = Mock()
        handlers = {ErrorCategory.FILE_SYSTEM: mock_handler}
        
        # Act
        handler = ErrorHandler(
            error_handlers=handlers,
            default_handler=mock_handler,
            max_error_log_size=500
        )
        
        # Assert
        assert handler.error_handlers == handlers
        assert handler.default_handler == mock_handler
        assert handler.max_error_log_size == 500
    
    def test_error_handler_creation_invalid_max_size(self):
        """Test ErrorHandler creation with invalid max error log size."""
        # Act & Assert
        with pytest.raises(ValueError, match="max_error_log_size must be positive integer"):
            ErrorHandler(max_error_log_size=0)
    
    def test_error_handler_creation_invalid_handlers(self):
        """Test ErrorHandler creation with invalid handlers."""
        # Arrange
        invalid_handlers = {ErrorCategory.FILE_SYSTEM: "not callable"}
        
        # Act & Assert
        with pytest.raises(TypeError, match="Handler for category ErrorCategory.FILE_SYSTEM must be callable"):
            ErrorHandler(error_handlers=invalid_handlers)
    
    def test_register_handler(self, error_handler, mock_handler):
        """Test register_handler method."""
        # Act
        error_handler.register_handler(ErrorCategory.FILE_SYSTEM, mock_handler)
        
        # Assert
        assert error_handler.error_handlers[ErrorCategory.FILE_SYSTEM] == mock_handler
    
    def test_register_handler_invalid_category(self, error_handler, mock_handler):
        """Test register_handler with invalid category."""
        # Act & Assert
        with pytest.raises(ValueError, match="category must be valid ErrorCategory enum value"):
            error_handler.register_handler("invalid_category", mock_handler)
    
    def test_register_handler_invalid_handler(self, error_handler):
        """Test register_handler with invalid handler."""
        # Act & Assert
        with pytest.raises(TypeError, match="handler must be callable"):
            error_handler.register_handler(ErrorCategory.FILE_SYSTEM, "not callable")
    
    def test_handle_error_with_category_handler(self, error_handler, mock_handler, processing_error):
        """Test handle_error with category-specific handler."""
        # Arrange
        error_handler.register_handler(ErrorCategory.FILE_SYSTEM, mock_handler)
        
        # Act
        result = error_handler.handle_error(processing_error)
        
        # Assert
        assert result is True
        mock_handler.assert_called_once_with(processing_error)
        assert len(error_handler.error_log) == 1
        assert error_handler.error_log[0] == processing_error
        assert error_handler.error_counters["FileNotFoundError"] == 1
    
    def test_handle_error_with_default_handler(self, error_handler, mock_handler, processing_error):
        """Test handle_error with default handler."""
        # Arrange
        error_handler.default_handler = mock_handler
        
        # Act
        result = error_handler.handle_error(processing_error)
        
        # Assert
        assert result is True
        mock_handler.assert_called_once_with(processing_error)
        assert len(error_handler.error_log) == 1
        assert error_handler.error_log[0] == processing_error
    
    def test_handle_error_no_handler(self, error_handler, processing_error):
        """Test handle_error with no handler available."""
        # Act
        result = error_handler.handle_error(processing_error)
        
        # Assert
        assert result is False
        assert len(error_handler.error_log) == 1
        assert error_handler.error_log[0] == processing_error
    
    def test_handle_error_none(self, error_handler):
        """Test handle_error with None error."""
        # Act & Assert
        with pytest.raises(ValueError, match="error cannot be None"):
            error_handler.handle_error(None)
    
    def test_handle_error_invalid_type(self, error_handler):
        """Test handle_error with invalid error type."""
        # Act & Assert
        with pytest.raises(TypeError, match="error must be ProcessingError instance"):
            error_handler.handle_error("not a ProcessingError")
    
    def test_handle_error_log_size_limit(self, error_handler, processing_error):
        """Test handle_error respects log size limit."""
        # Arrange
        error_handler.max_error_log_size = 2
        
        # Act
        error_handler.handle_error(processing_error)
        error_handler.handle_error(processing_error)
        error_handler.handle_error(processing_error)
        
        # Assert
        assert len(error_handler.error_log) == 2  # Should not exceed max size
    
    def test_get_error_count(self, error_handler, processing_error):
        """Test get_error_count method."""
        # Arrange
        error_handler.handle_error(processing_error)
        error_handler.handle_error(processing_error)
        
        # Act
        count = error_handler.get_error_count("FileNotFoundError")
        
        # Assert
        assert count == 2
    
    def test_get_error_count_empty_type(self, error_handler):
        """Test get_error_count with empty error type."""
        # Act & Assert
        with pytest.raises(ValueError, match="error_type must be non-empty string"):
            error_handler.get_error_count("")
    
    def test_get_error_count_invalid_type(self, error_handler):
        """Test get_error_count with invalid error type."""
        # Act & Assert
        with pytest.raises(TypeError, match="error_type must be string"):
            error_handler.get_error_count(123)
    
    def test_get_error_count_not_found(self, error_handler):
        """Test get_error_count for non-existent error type."""
        # Act
        count = error_handler.get_error_count("NonExistentError")
        
        # Assert
        assert count == 0
    
    def test_get_errors_by_category(self, error_handler, processing_error):
        """Test get_errors_by_category method."""
        # Arrange
        error_handler.handle_error(processing_error)
        
        # Act
        errors = error_handler.get_errors_by_category(ErrorCategory.FILE_SYSTEM)
        
        # Assert
        assert len(errors) == 1
        assert errors[0] == processing_error
    
    def test_get_errors_by_category_invalid_category(self, error_handler):
        """Test get_errors_by_category with invalid category."""
        # Act & Assert
        with pytest.raises(ValueError, match="category must be valid ErrorCategory enum value"):
            error_handler.get_errors_by_category("invalid_category")
    
    def test_get_errors_by_category_empty(self, error_handler):
        """Test get_errors_by_category for empty category."""
        # Act
        errors = error_handler.get_errors_by_category(ErrorCategory.DATABASE)
        
        # Assert
        assert errors == []
    
    def test_clear_error_log(self, error_handler, processing_error):
        """Test clear_error_log method."""
        # Arrange
        error_handler.handle_error(processing_error)
        assert len(error_handler.error_log) == 1
        assert len(error_handler.error_counters) == 1
        
        # Act
        error_handler.clear_error_log()
        
        # Assert
        assert len(error_handler.error_log) == 0
        assert len(error_handler.error_counters) == 0
    
    def test_get_error_statistics(self, error_handler, processing_error):
        """Test get_error_statistics method."""
        # Arrange
        error_handler.handle_error(processing_error)
        error_handler.handle_error(processing_error)
        
        # Act
        stats = error_handler.get_error_statistics()
        
        # Assert
        assert stats["total_errors"] == 2
        assert stats["errors_by_type"]["FileNotFoundError"] == 2
        assert stats["errors_by_category"]["file_system"] == 2
        assert stats["errors_by_severity"]["medium"] == 2
        assert len(stats["recent_errors"]) == 2
    
    def test_get_error_statistics_empty(self, error_handler):
        """Test get_error_statistics with no errors."""
        # Act
        stats = error_handler.get_error_statistics()
        
        # Assert
        assert stats["total_errors"] == 0
        assert stats["errors_by_type"] == {}
        assert stats["errors_by_category"] == {}
        assert stats["errors_by_severity"] == {}
        assert stats["recent_errors"] == []
    
    def test_to_dict(self, error_handler):
        """Test to_dict method."""
        # Act
        data = error_handler.to_dict()
        
        # Assert
        assert data["handler_id"] == error_handler.handler_id
        assert data["max_error_log_size"] == error_handler.max_error_log_size
        assert "registered_categories" in data  # Handlers are not serialized
        assert data["has_default_handler"] is False  # Default handler is not serialized
    
    def test_from_dict(self):
        """Test from_dict method."""
        # Arrange
        data = {
            "handler_id": "test_id",
            "max_error_log_size": 500,
            "error_handlers": {},
            "default_handler": None
        }
        
        # Act
        handler = ErrorHandler.from_dict(data)
        
        # Assert
        assert handler.handler_id == "test_id"
        assert handler.max_error_log_size == 500
        assert handler.error_handlers == {}  # Must be re-registered
        assert handler.default_handler is None  # Must be re-registered
    
    def test_from_dict_missing_required_fields(self):
        """Test from_dict method with missing required fields."""
        # Arrange
        data = {"max_error_log_size": 500}  # Missing handler_id
        
        # Act & Assert
        with pytest.raises(ValueError, match="Required field 'handler_id' missing in data"):
            ErrorHandler.from_dict(data)
    
    def test_equality(self, error_handler):
        """Test equality comparison."""
        # Arrange
        same_handler = ErrorHandler()
        same_handler.handler_id = error_handler.handler_id
        
        # Act & Assert
        assert error_handler == same_handler
    
    def test_inequality(self, error_handler):
        """Test inequality comparison."""
        # Arrange
        different_handler = ErrorHandler()
        
        # Act & Assert
        assert error_handler != different_handler
    
    def test_equality_different_type(self, error_handler):
        """Test equality with different type."""
        # Act & Assert
        assert error_handler != "not an ErrorHandler"
    
    def test_repr(self, error_handler):
        """Test string representation."""
        # Act
        repr_str = repr(error_handler)
        
        # Assert
        assert "ErrorHandler" in repr_str
        assert error_handler.handler_id in repr_str
        assert "handlers=0" in repr_str
        assert "errors=0" in repr_str 