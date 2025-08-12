"""
Tests for Error Models

Comprehensive test suite for error handling models including ProcessingError
and ErrorHandler classes.

Author: DocAnalyzer Team
Version: 1.0.0
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from docanalyzer.models.errors import (
    ProcessingError, ErrorHandler, ErrorCategory, ErrorSeverity
)


class TestProcessingError:
    """Test suite for ProcessingError class."""
    
    @pytest.fixture
    def basic_error(self):
        """Create basic ProcessingError instance."""
        return ProcessingError(
            error_type="FileNotFoundError",
            error_message="File not found",
            error_category=ErrorCategory.FILE_SYSTEM
        )
    
    def test_init_basic(self, basic_error):
        """Test basic initialization."""
        assert basic_error.error_type == "FileNotFoundError"
        assert basic_error.error_message == "File not found"
        assert basic_error.error_category == ErrorCategory.FILE_SYSTEM
        assert basic_error.error_severity == ErrorSeverity.MEDIUM
        assert basic_error.retry_count == 0
        assert basic_error.max_retries == 3
        assert basic_error.is_recoverable is True
        assert isinstance(basic_error.error_id, str)
        assert isinstance(basic_error.timestamp, datetime)
    
    def test_init_with_all_parameters(self):
        """Test initialization with all parameters."""
        timestamp = datetime.now()
        error = ProcessingError(
            error_type="PermissionError",
            error_message="Access denied",
            error_category=ErrorCategory.PERMISSION,
            error_id="test-id-123",
            error_severity=ErrorSeverity.HIGH,
            file_path="/path/to/file.txt",
            operation="read_file",
            stack_trace="Traceback...",
            context_data={"user": "test_user"},
            timestamp=timestamp,
            retry_count=2,
            max_retries=5,
            is_recoverable=False,
            recovery_action="Check permissions"
        )
        
        assert error.error_id == "test-id-123"
        assert error.error_severity == ErrorSeverity.HIGH
        assert error.file_path == "/path/to/file.txt"
        assert error.operation == "read_file"
        assert error.stack_trace == "Traceback..."
        assert error.context_data == {"user": "test_user"}
        assert error.timestamp == timestamp
        assert error.retry_count == 2
        assert error.max_retries == 5
        assert error.is_recoverable is False
        assert error.recovery_action == "Check permissions"
    
    def test_init_validation_errors(self):
        """Test initialization validation errors."""
        # Empty error_type
        with pytest.raises(ValueError, match="error_type must be non-empty string"):
            ProcessingError("", "message", ErrorCategory.FILE_SYSTEM)
        
        # Empty error_message
        with pytest.raises(ValueError, match="error_message must be non-empty string"):
            ProcessingError("Type", "", ErrorCategory.FILE_SYSTEM)
        
        # Invalid error_category
        with pytest.raises(TypeError, match="error_category must be ErrorCategory enum value"):
            ProcessingError("Type", "message", "invalid_category")
        
        # Invalid error_severity
        with pytest.raises(TypeError, match="error_severity must be ErrorSeverity enum value"):
            ProcessingError("Type", "message", ErrorCategory.FILE_SYSTEM, error_severity="invalid")
        
        # Negative retry_count
        with pytest.raises(ValueError, match="retry_count must be non-negative integer"):
            ProcessingError("Type", "message", ErrorCategory.FILE_SYSTEM, retry_count=-1)
        
        # Invalid max_retries
        with pytest.raises(ValueError, match="max_retries must be positive integer"):
            ProcessingError("Type", "message", ErrorCategory.FILE_SYSTEM, max_retries=0)
    
    def test_increment_retry_count(self, basic_error):
        """Test retry count increment."""
        assert basic_error.retry_count == 0
        basic_error.increment_retry_count()
        assert basic_error.retry_count == 1
        basic_error.increment_retry_count()
        assert basic_error.retry_count == 2
    
    def test_increment_retry_count_max_limit(self):
        """Test retry count doesn't exceed max_retries."""
        error = ProcessingError("Type", "message", ErrorCategory.FILE_SYSTEM, max_retries=2)
        error.increment_retry_count()
        error.increment_retry_count()
        error.increment_retry_count()  # Should not increment beyond max
        assert error.retry_count == 2
    
    def test_can_retry(self, basic_error):
        """Test can_retry method."""
        assert basic_error.can_retry() is True
        
        # After max retries
        error = ProcessingError("Type", "message", ErrorCategory.FILE_SYSTEM, max_retries=1)
        error.increment_retry_count()
        assert error.can_retry() is False
        
        # Non-recoverable error
        error = ProcessingError("Type", "message", ErrorCategory.FILE_SYSTEM, is_recoverable=False)
        assert error.can_retry() is False
    
    def test_add_context_data(self, basic_error):
        """Test adding context data."""
        basic_error.add_context_data("file_size", 1024)
        basic_error.add_context_data("user_id", "user123")
        
        assert basic_error.get_context_data("file_size") == 1024
        assert basic_error.get_context_data("user_id") == "user123"
        assert basic_error.get_context_data("nonexistent", "default") == "default"
    
    def test_add_context_data_validation(self, basic_error):
        """Test context data validation."""
        with pytest.raises(TypeError, match="key must be string"):
            basic_error.add_context_data(123, "value")
        
        with pytest.raises(ValueError, match="key must be non-empty string"):
            basic_error.add_context_data("", "value")
    
    def test_get_context_data_validation(self, basic_error):
        """Test context data retrieval validation."""
        with pytest.raises(TypeError, match="key must be string"):
            basic_error.get_context_data(123)
        
        with pytest.raises(ValueError, match="key must be non-empty string"):
            basic_error.get_context_data("")
    
    def test_to_dict(self, basic_error):
        """Test dictionary conversion."""
        data = basic_error.to_dict()
        
        assert data["error_type"] == "FileNotFoundError"
        assert data["error_message"] == "File not found"
        assert data["error_category"] == "file_system"
        assert data["error_severity"] == "medium"
        assert data["retry_count"] == 0
        assert data["max_retries"] == 3
        assert data["is_recoverable"] is True
        assert isinstance(data["timestamp"], str)
        assert isinstance(data["error_id"], str)
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "error_type": "FileNotFoundError",
            "error_message": "File not found",
            "error_category": "file_system",
            "error_severity": "high",
            "file_path": "/path/file.txt",
            "timestamp": "2023-01-01T12:00:00",
            "retry_count": 2,
            "max_retries": 5,
            "is_recoverable": False
        }
        
        error = ProcessingError.from_dict(data)
        
        assert error.error_type == "FileNotFoundError"
        assert error.error_message == "File not found"
        assert error.error_category == ErrorCategory.FILE_SYSTEM
        assert error.error_severity == ErrorSeverity.HIGH
        assert error.file_path == "/path/file.txt"
        assert error.retry_count == 2
        assert error.max_retries == 5
        assert error.is_recoverable is False
    
    def test_from_dict_validation(self):
        """Test from_dict validation."""
        # Missing required field
        with pytest.raises(ValueError, match="Required field 'error_type' missing"):
            ProcessingError.from_dict({"error_message": "msg", "error_category": "file_system"})
        
        # Invalid data type
        with pytest.raises(TypeError, match="data must be dictionary"):
            ProcessingError.from_dict("not a dict")
        
        # Invalid enum values
        with pytest.raises(ValueError, match="Invalid error_category"):
            ProcessingError.from_dict({
                "error_type": "Type",
                "error_message": "Message",
                "error_category": "invalid_category"
            })
    
    def test_from_exception(self):
        """Test creation from exception."""
        try:
            raise FileNotFoundError("File not found")
        except FileNotFoundError as e:
            error = ProcessingError.from_exception(
                e, ErrorCategory.FILE_SYSTEM, "/path/file.txt", "read_file"
            )
        
        assert error.error_type == "FileNotFoundError"
        assert error.error_message == "File not found"
        assert error.error_category == ErrorCategory.FILE_SYSTEM
        assert error.file_path == "/path/file.txt"
        assert error.operation == "read_file"
        assert "Traceback" in error.stack_trace
    
    def test_from_exception_validation(self):
        """Test from_exception validation."""
        with pytest.raises(TypeError, match="exception must be Exception instance"):
            ProcessingError.from_exception("not an exception", ErrorCategory.FILE_SYSTEM)
        
        with pytest.raises(ValueError, match="error_category must be valid ErrorCategory enum value"):
            ProcessingError.from_exception(Exception("test"), "invalid_category")
    
    def test_equality(self):
        """Test equality comparison."""
        error1 = ProcessingError("Type", "Message", ErrorCategory.FILE_SYSTEM)
        error2 = ProcessingError("Type", "Message", ErrorCategory.FILE_SYSTEM)
        error3 = ProcessingError("Different", "Message", ErrorCategory.FILE_SYSTEM)
        
        assert error1 == error2
        assert error1 != error3
        assert error1 != "not an error"
    
    def test_repr(self, basic_error):
        """Test string representation."""
        repr_str = repr(basic_error)
        assert "ProcessingError" in repr_str
        assert "FileNotFoundError" in repr_str
        assert "file_system" in repr_str
        assert "medium" in repr_str
        assert "0/3" in repr_str  # retries


class TestErrorHandler:
    """Test suite for ErrorHandler class."""
    
    @pytest.fixture
    def handler(self):
        """Create basic ErrorHandler instance."""
        return ErrorHandler()
    
    @pytest.fixture
    def mock_handler_func(self):
        """Create mock handler function."""
        return Mock()
    
    def test_init_basic(self, handler):
        """Test basic initialization."""
        assert isinstance(handler.handler_id, str)
        assert handler.max_error_log_size == 1000
        assert handler.error_log == []
        assert handler.error_counters == {}
        assert handler.error_handlers == {}
        assert handler.default_handler is None
    
    def test_init_with_parameters(self):
        """Test initialization with parameters."""
        mock_handler = Mock()
        handler = ErrorHandler(
            handler_id="test-id",
            error_handlers={ErrorCategory.FILE_SYSTEM: mock_handler},
            default_handler=mock_handler,
            max_error_log_size=500
        )
        
        assert handler.handler_id == "test-id"
        assert handler.max_error_log_size == 500
        assert ErrorCategory.FILE_SYSTEM in handler.error_handlers
        assert handler.default_handler == mock_handler
    
    def test_init_validation(self):
        """Test initialization validation."""
        with pytest.raises(ValueError, match="max_error_log_size must be positive integer"):
            ErrorHandler(max_error_log_size=0)
        
        with pytest.raises(TypeError, match="Handler for category"):
            ErrorHandler(error_handlers={ErrorCategory.FILE_SYSTEM: "not callable"})
        
        with pytest.raises(TypeError, match="default_handler must be callable"):
            ErrorHandler(default_handler="not callable")
    
    def test_register_handler(self, handler, mock_handler_func):
        """Test handler registration."""
        handler.register_handler(ErrorCategory.FILE_SYSTEM, mock_handler_func)
        
        assert ErrorCategory.FILE_SYSTEM in handler.error_handlers
        assert handler.error_handlers[ErrorCategory.FILE_SYSTEM] == mock_handler_func
    
    def test_register_handler_validation(self, handler, mock_handler_func):
        """Test handler registration validation."""
        with pytest.raises(ValueError, match="category must be valid ErrorCategory enum value"):
            handler.register_handler("invalid_category", mock_handler_func)
        
        with pytest.raises(TypeError, match="handler must be callable"):
            handler.register_handler(ErrorCategory.FILE_SYSTEM, "not callable")
    
    def test_handle_error_success(self, handler, mock_handler_func):
        """Test successful error handling."""
        handler.register_handler(ErrorCategory.FILE_SYSTEM, mock_handler_func)
        
        error = ProcessingError("FileNotFoundError", "File not found", ErrorCategory.FILE_SYSTEM)
        result = handler.handle_error(error)
        
        assert result is True
        assert len(handler.error_log) == 1
        assert handler.error_log[0] == error
        assert handler.error_counters["FileNotFoundError"] == 1
        mock_handler_func.assert_called_once_with(error)
    
    def test_handle_error_no_handler(self, handler):
        """Test error handling without registered handler."""
        error = ProcessingError("FileNotFoundError", "File not found", ErrorCategory.FILE_SYSTEM)
        result = handler.handle_error(error)
        
        assert result is False
        assert len(handler.error_log) == 1
        assert handler.error_counters["FileNotFoundError"] == 1
    
    def test_handle_error_with_default_handler(self, handler, mock_handler_func):
        """Test error handling with default handler."""
        handler.default_handler = mock_handler_func
        
        error = ProcessingError("FileNotFoundError", "File not found", ErrorCategory.FILE_SYSTEM)
        result = handler.handle_error(error)
        
        assert result is True
        mock_handler_func.assert_called_once_with(error)
    
    def test_handle_error_validation(self, handler):
        """Test error handling validation."""
        with pytest.raises(ValueError, match="error cannot be None"):
            handler.handle_error(None)
        
        with pytest.raises(TypeError, match="error must be ProcessingError instance"):
            handler.handle_error("not an error")
    
    def test_handle_error_log_size_limit(self):
        """Test error log size limit."""
        handler = ErrorHandler(max_error_log_size=2)
        
        error1 = ProcessingError("Error1", "Message1", ErrorCategory.FILE_SYSTEM)
        error2 = ProcessingError("Error2", "Message2", ErrorCategory.FILE_SYSTEM)
        error3 = ProcessingError("Error3", "Message3", ErrorCategory.FILE_SYSTEM)
        
        handler.handle_error(error1)
        handler.handle_error(error2)
        handler.handle_error(error3)
        
        assert len(handler.error_log) == 2
        assert handler.error_log[0] == error2  # Oldest removed
        assert handler.error_log[1] == error3
    
    def test_get_error_count(self, handler):
        """Test error count retrieval."""
        error1 = ProcessingError("FileNotFoundError", "File not found", ErrorCategory.FILE_SYSTEM)
        error2 = ProcessingError("FileNotFoundError", "Another file not found", ErrorCategory.FILE_SYSTEM)
        error3 = ProcessingError("PermissionError", "Access denied", ErrorCategory.PERMISSION)
        
        handler.handle_error(error1)
        handler.handle_error(error2)
        handler.handle_error(error3)
        
        assert handler.get_error_count("FileNotFoundError") == 2
        assert handler.get_error_count("PermissionError") == 1
        assert handler.get_error_count("NonexistentError") == 0
    
    def test_get_error_count_validation(self, handler):
        """Test error count validation."""
        with pytest.raises(TypeError, match="error_type must be string"):
            handler.get_error_count(123)
        
        with pytest.raises(ValueError, match="error_type must be non-empty string"):
            handler.get_error_count("")
    
    def test_get_errors_by_category(self, handler):
        """Test error filtering by category."""
        file_error = ProcessingError("FileNotFoundError", "File not found", ErrorCategory.FILE_SYSTEM)
        perm_error = ProcessingError("PermissionError", "Access denied", ErrorCategory.PERMISSION)
        db_error = ProcessingError("DatabaseError", "DB error", ErrorCategory.DATABASE)
        
        handler.handle_error(file_error)
        handler.handle_error(perm_error)
        handler.handle_error(db_error)
        
        file_errors = handler.get_errors_by_category(ErrorCategory.FILE_SYSTEM)
        assert len(file_errors) == 1
        assert file_errors[0] == file_error
        
        perm_errors = handler.get_errors_by_category(ErrorCategory.PERMISSION)
        assert len(perm_errors) == 1
        assert perm_errors[0] == perm_error
    
    def test_get_errors_by_category_validation(self, handler):
        """Test error category filtering validation."""
        with pytest.raises(ValueError, match="category must be valid ErrorCategory enum value"):
            handler.get_errors_by_category("invalid_category")
    
    def test_clear_error_log(self, handler):
        """Test error log clearing."""
        error1 = ProcessingError("Error1", "Message1", ErrorCategory.FILE_SYSTEM)
        error2 = ProcessingError("Error2", "Message2", ErrorCategory.FILE_SYSTEM)
        
        handler.handle_error(error1)
        handler.handle_error(error2)
        
        assert len(handler.error_log) == 2
        assert len(handler.error_counters) == 2
        
        handler.clear_error_log()
        
        assert len(handler.error_log) == 0
        assert len(handler.error_counters) == 0
    
    def test_get_error_statistics(self, handler):
        """Test error statistics generation."""
        error1 = ProcessingError("FileNotFoundError", "File not found", ErrorCategory.FILE_SYSTEM, error_severity=ErrorSeverity.MEDIUM)
        error2 = ProcessingError("PermissionError", "Access denied", ErrorCategory.PERMISSION, error_severity=ErrorSeverity.HIGH)
        error3 = ProcessingError("FileNotFoundError", "Another file not found", ErrorCategory.FILE_SYSTEM, error_severity=ErrorSeverity.LOW)
        
        handler.handle_error(error1)
        handler.handle_error(error2)
        handler.handle_error(error3)
        
        stats = handler.get_error_statistics()
        
        assert stats["total_errors"] == 3
        assert stats["errors_by_category"]["file_system"] == 2
        assert stats["errors_by_category"]["permission"] == 1
        assert stats["errors_by_type"]["FileNotFoundError"] == 2
        assert stats["errors_by_type"]["PermissionError"] == 1
        assert stats["errors_by_severity"]["medium"] == 1
        assert stats["errors_by_severity"]["high"] == 1
        assert stats["errors_by_severity"]["low"] == 1
        assert len(stats["recent_errors"]) == 3
    
    def test_to_dict(self, handler):
        """Test dictionary conversion."""
        handler.register_handler(ErrorCategory.FILE_SYSTEM, Mock())
        handler.default_handler = Mock()
        
        data = handler.to_dict()
        
        assert data["handler_id"] == handler.handler_id
        assert data["max_error_log_size"] == 1000
        assert data["error_log_size"] == 0
        assert data["error_counters"] == {}
        assert "file_system" in data["registered_categories"]
        assert data["has_default_handler"] is True
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "handler_id": "test-id",
            "max_error_log_size": 500
        }
        
        handler = ErrorHandler.from_dict(data)
        
        assert handler.handler_id == "test-id"
        assert handler.max_error_log_size == 500
    
    def test_from_dict_validation(self):
        """Test from_dict validation."""
        with pytest.raises(TypeError, match="data must be dictionary"):
            ErrorHandler.from_dict("not a dict")
        
        with pytest.raises(ValueError, match="Required field 'handler_id' missing"):
            ErrorHandler.from_dict({"max_error_log_size": 500})
    
    def test_equality(self):
        """Test equality comparison."""
        handler1 = ErrorHandler(handler_id="test-id")
        handler2 = ErrorHandler(handler_id="test-id")
        handler3 = ErrorHandler(handler_id="different-id")
        
        assert handler1 == handler2
        assert handler1 != handler3
        assert handler1 != "not a handler"
    
    def test_repr(self, handler):
        """Test string representation."""
        repr_str = repr(handler)
        assert "ErrorHandler" in repr_str
        assert handler.handler_id in repr_str
        assert "handlers=0" in repr_str
        assert "errors=0" in repr_str 