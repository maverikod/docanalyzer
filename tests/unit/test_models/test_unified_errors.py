"""
Tests for Unified Errors Module

Comprehensive test suite for the unified error handling system.
Tests all error types, contexts, and error handling functionality.
"""

import pytest
from datetime import datetime
from typing import Dict, Any

from docanalyzer.models.unified_errors import (
    ErrorCategory,
    ErrorSeverity,
    ErrorContext,
    UnifiedError,
    UnifiedErrorHandler
)


class TestErrorCategory:
    """Test suite for ErrorCategory enum."""
    
    def test_error_category_values(self):
        """Test that all error categories have correct values."""
        assert ErrorCategory.CONFIGURATION.value == "configuration"
        assert ErrorCategory.CONNECTION.value == "connection"
        assert ErrorCategory.PROCESSING.value == "processing"
        assert ErrorCategory.VALIDATION.value == "validation"
        assert ErrorCategory.SYSTEM.value == "system"
        assert ErrorCategory.PERMISSION.value == "permission"
        assert ErrorCategory.RESOURCE.value == "resource"
        assert ErrorCategory.TIMEOUT.value == "timeout"
        assert ErrorCategory.UNKNOWN.value == "unknown"
    
    def test_error_category_from_string(self):
        """Test creating ErrorCategory from string."""
        assert ErrorCategory("configuration") == ErrorCategory.CONFIGURATION
        assert ErrorCategory("processing") == ErrorCategory.PROCESSING
        assert ErrorCategory("unknown") == ErrorCategory.UNKNOWN


class TestErrorSeverity:
    """Test suite for ErrorSeverity enum."""
    
    def test_error_severity_values(self):
        """Test that all error severities have correct values."""
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.CRITICAL.value == "critical"
    
    def test_error_severity_from_string(self):
        """Test creating ErrorSeverity from string."""
        assert ErrorSeverity("low") == ErrorSeverity.LOW
        assert ErrorSeverity("high") == ErrorSeverity.HIGH
        assert ErrorSeverity("critical") == ErrorSeverity.CRITICAL


class TestErrorContext:
    """Test suite for ErrorContext dataclass."""
    
    def test_error_context_creation(self):
        """Test creating ErrorContext with required fields."""
        context = ErrorContext(
            component="test_component",
            operation="test_operation"
        )
        
        assert context.component == "test_component"
        assert context.operation == "test_operation"
        assert isinstance(context.timestamp, datetime)
        assert context.metadata == {}
        assert context.user_id is None
        assert context.session_id is None
    
    def test_error_context_with_optional_fields(self):
        """Test creating ErrorContext with optional fields."""
        metadata = {"file_path": "/test/file.txt"}
        context = ErrorContext(
            component="file_processor",
            operation="process_file",
            metadata=metadata,
            user_id="user123",
            session_id="session456"
        )
        
        assert context.component == "file_processor"
        assert context.operation == "process_file"
        assert context.metadata == metadata
        assert context.user_id == "user123"
        assert context.session_id == "session456"
    
    def test_error_context_to_dict(self):
        """Test converting ErrorContext to dictionary."""
        context = ErrorContext(
            component="test_component",
            operation="test_operation",
            metadata={"key": "value"},
            user_id="user123"
        )
        
        result = context.to_dict()
        
        assert result["component"] == "test_component"
        assert result["operation"] == "test_operation"
        assert result["metadata"] == {"key": "value"}
        assert result["user_id"] == "user123"
        assert result["session_id"] is None
        assert "timestamp" in result


class TestUnifiedError:
    """Test suite for UnifiedError class."""
    
    def test_unified_error_creation(self):
        """Test creating UnifiedError with required fields."""
        context = ErrorContext("test_component", "test_operation")
        error = UnifiedError(
            error_id="test_error_001",
            message="Test error message",
            category=ErrorCategory.PROCESSING,
            severity=ErrorSeverity.MEDIUM,
            context=context
        )
        
        assert error.error_id == "test_error_001"
        assert error.message == "Test error message"
        assert error.category == ErrorCategory.PROCESSING
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.context == context
        assert error.original_error is None
        assert error.stack_trace is None
        assert error.retryable is False
        assert error.max_retries == 0
    
    def test_unified_error_with_optional_fields(self):
        """Test creating UnifiedError with optional fields."""
        context = ErrorContext("test_component", "test_operation")
        cause = Exception("Original error")
        
        error = UnifiedError(
            error_id="validation_error_001",
            message="Invalid input",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.HIGH,
            context=context,
            original_error=cause,
            stack_trace="Traceback...",
            retryable=True,
            max_retries=3
        )
        
        assert error.error_id == "validation_error_001"
        assert error.message == "Invalid input"
        assert error.category == ErrorCategory.VALIDATION
        assert error.severity == ErrorSeverity.HIGH
        assert error.context == context
        assert error.original_error == cause
        assert error.stack_trace == "Traceback..."
        assert error.retryable is True
        assert error.max_retries == 3
    
    def test_unified_error_to_dict(self):
        """Test converting UnifiedError to dictionary."""
        context = ErrorContext("test_component", "test_operation")
        error = UnifiedError(
            error_id="test_error_001",
            message="Test message",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.LOW,
            context=context,
            retryable=True,
            max_retries=2
        )
        
        result = error.to_dict()
        
        assert result["error_id"] == "test_error_001"
        assert result["message"] == "Test message"
        assert result["category"] == "system"
        assert result["severity"] == "low"
        assert result["context"]["component"] == "test_component"
        assert result["retryable"] is True
        assert result["max_retries"] == 2
    
    def test_unified_error_str_representation(self):
        """Test string representation of UnifiedError."""
        context = ErrorContext("test_component", "test_operation")
        error = UnifiedError(
            error_id="test_error_001",
            message="Test message",
            category=ErrorCategory.PROCESSING,
            severity=ErrorSeverity.MEDIUM,
            context=context
        )
        
        error_str = str(error)
        assert "PROCESSING" in error_str
        assert "Test message" in error_str
        assert "test_error_001" in error_str
    
    def test_unified_error_repr_representation(self):
        """Test repr representation of UnifiedError."""
        context = ErrorContext("test_component", "test_operation")
        error = UnifiedError(
            error_id="test_error_001",
            message="Test message",
            category=ErrorCategory.PROCESSING,
            severity=ErrorSeverity.MEDIUM,
            context=context
        )
        
        error_repr = repr(error)
        assert "UnifiedError" in error_repr
        assert "test_error_001" in error_repr


class TestUnifiedErrorHandler:
    """Test suite for UnifiedErrorHandler class."""
    
    def test_unified_error_handler_creation(self):
        """Test creating UnifiedErrorHandler instance."""
        handler = UnifiedErrorHandler()
        
        assert handler.logger is not None
        assert handler.error_registry == {}
        assert handler.error_counters == {}
    
    def test_create_error(self):
        """Test creating an error through handler."""
        handler = UnifiedErrorHandler()
        
        error = handler.create_error(
            error_id="test_error_001",
            message="Test error",
            category=ErrorCategory.PROCESSING,
            severity=ErrorSeverity.MEDIUM,
            component="test_component",
            operation="test_operation"
        )
        
        assert error.error_id == "test_error_001"
        assert error.message == "Test error"
        assert error.category == ErrorCategory.PROCESSING
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.context.component == "test_component"
        assert error.context.operation == "test_operation"
    
    def test_log_error(self):
        """Test logging an error."""
        handler = UnifiedErrorHandler()
        
        context = ErrorContext("test_component", "test_operation")
        error = UnifiedError(
            error_id="test_error_001",
            message="Test error",
            category=ErrorCategory.PROCESSING,
            severity=ErrorSeverity.MEDIUM,
            context=context
        )
        
        # Should not raise any exception
        handler.log_error(error)
    
    def test_get_error_summary(self):
        """Test getting error summary."""
        handler = UnifiedErrorHandler()
        
        # Create some errors
        for i in range(3):
            error = handler.create_error(
                error_id=f"error_{i}",
                message=f"Error {i}",
                category=ErrorCategory.PROCESSING,
                severity=ErrorSeverity.MEDIUM,
                component="test_component",
                operation="test_operation"
            )
            handler.log_error(error)
        
        statistics = handler.get_error_statistics()
        
        assert "total_errors" in statistics
        assert "category_distribution" in statistics
        assert "severity_distribution" in statistics
        assert statistics["category_distribution"]["processing"] == 3
        assert statistics["severity_distribution"]["medium"] == 3
    
    def test_clear_errors(self):
        """Test clearing all errors."""
        handler = UnifiedErrorHandler()
        
        # Create and log an error
        error = handler.create_error(
            error_id="test_error_001",
            message="Test error",
            category=ErrorCategory.PROCESSING,
            severity=ErrorSeverity.MEDIUM,
            component="test_component",
            operation="test_operation"
        )
        handler.log_error(error)
        
        # Clear errors
        handler.clear_error_registry()
        
        statistics = handler.get_error_statistics()
        assert statistics["total_errors"] == 0 