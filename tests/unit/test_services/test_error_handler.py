"""
Tests for Error Handler

Comprehensive test suite for error handling and recovery functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import uuid
from typing import List, Dict, Any

from docanalyzer.services.error_handler import (
    ErrorHandler,
    ErrorHandlerConfig,
    ErrorInfo,
    ErrorRecoveryStrategy
)
from docanalyzer.models.processing import ProcessingResult
from docanalyzer.models.errors import ProcessingError, ErrorCategory


class TestErrorHandlerConfig:
    """Test suite for ErrorHandlerConfig class."""
    
    def test_init_valid_config(self):
        """Test valid configuration initialization."""
        config = ErrorHandlerConfig(
            max_retry_attempts=5,
            retry_delay=10,
            backoff_multiplier=3.0,
            enable_automatic_recovery=False,
            enable_error_logging=False,
            enable_error_reporting=False,
            error_threshold=20
        )
        
        assert config.max_retry_attempts == 5
        assert config.retry_delay == 10
        assert config.backoff_multiplier == 3.0
        assert config.enable_automatic_recovery is False
        assert config.enable_error_logging is False
        assert config.enable_error_reporting is False
        assert config.error_threshold == 20
    
    def test_init_defaults(self):
        """Test configuration initialization with defaults."""
        config = ErrorHandlerConfig()
        
        assert config.max_retry_attempts == 3
        assert config.retry_delay == 5
        assert config.backoff_multiplier == 2.0
        assert config.enable_automatic_recovery is True
        assert config.enable_error_logging is True
        assert config.enable_error_reporting is True
        assert config.error_threshold == 10
    
    def test_init_invalid_max_retry_attempts(self):
        """Test initialization with invalid max_retry_attempts."""
        with pytest.raises(ValueError, match="max_retry_attempts must be non-negative"):
            ErrorHandlerConfig(max_retry_attempts=-1)
    
    def test_init_invalid_retry_delay(self):
        """Test initialization with invalid retry_delay."""
        with pytest.raises(ValueError, match="retry_delay must be positive"):
            ErrorHandlerConfig(retry_delay=0)
    
    def test_init_invalid_backoff_multiplier(self):
        """Test initialization with invalid backoff_multiplier."""
        with pytest.raises(ValueError, match="backoff_multiplier must be positive"):
            ErrorHandlerConfig(backoff_multiplier=0)
    
    def test_init_invalid_error_threshold(self):
        """Test initialization with invalid error_threshold."""
        with pytest.raises(ValueError, match="error_threshold must be positive"):
            ErrorHandlerConfig(error_threshold=0)


class TestErrorInfo:
    """Test suite for ErrorInfo class."""
    
    def test_init_valid_error_info(self):
        """Test valid error info initialization."""
        timestamp = datetime.now()
        error_info = ErrorInfo(
            error_id="test-id",
            error_type="TestError",
            error_message="Test error message",
            error_category=ErrorCategory.PROCESSING,
            operation="test_operation",
            context={"key": "value"},
            timestamp=timestamp,
            retry_count=2,
            stack_trace="test stack trace",
            recovery_attempts=["action1", "action2"]
        )
        
        assert error_info.error_id == "test-id"
        assert error_info.error_type == "TestError"
        assert error_info.error_message == "Test error message"
        assert error_info.error_category == ErrorCategory.PROCESSING
        assert error_info.operation == "test_operation"
        assert error_info.context == {"key": "value"}
        assert error_info.timestamp == timestamp
        assert error_info.retry_count == 2
        assert error_info.stack_trace == "test stack trace"
        assert error_info.recovery_attempts == ["action1", "action2"]
    
    def test_init_defaults(self):
        """Test error info initialization with defaults."""
        error_info = ErrorInfo(
            error_id="test-id",
            error_type="TestError",
            error_message="Test error message",
            error_category=ErrorCategory.PROCESSING,
            operation="test_operation"
        )
        
        assert error_info.context == {}
        assert error_info.retry_count == 0
        assert error_info.stack_trace is None
        assert error_info.recovery_attempts == []
        assert isinstance(error_info.timestamp, datetime)
    
    def test_to_dict(self):
        """Test error info to dictionary conversion."""
        error_info = ErrorInfo(
            error_id="test-id",
            error_type="TestError",
            error_message="Test error message",
            error_category=ErrorCategory.PROCESSING,
            operation="test_operation",
            context={"key": "value"},
            retry_count=2,
            stack_trace="test stack trace",
            recovery_attempts=["action1"]
        )
        
        data = error_info.to_dict()
        
        assert data["error_id"] == "test-id"
        assert data["error_type"] == "TestError"
        assert data["error_message"] == "Test error message"
        assert data["error_category"] == "processing"
        assert data["operation"] == "test_operation"
        assert data["context"] == {"key": "value"}
        assert data["retry_count"] == 2
        assert data["stack_trace"] == "test stack trace"
        assert data["recovery_attempts"] == ["action1"]
        assert "timestamp" in data
    
    def test_from_dict_valid(self):
        """Test creating error info from valid dictionary."""
        timestamp = datetime.now()
        data = {
            "error_id": "test-id",
            "error_type": "TestError",
            "error_message": "Test error message",
            "error_category": "processing",
            "operation": "test_operation",
            "context": {"key": "value"},
            "timestamp": timestamp.isoformat(),
            "retry_count": 2,
            "stack_trace": "test stack trace",
            "recovery_attempts": ["action1"]
        }
        
        error_info = ErrorInfo.from_dict(data)
        
        assert error_info.error_id == "test-id"
        assert error_info.error_type == "TestError"
        assert error_info.error_message == "Test error message"
        assert error_info.error_category == ErrorCategory.PROCESSING
        assert error_info.operation == "test_operation"
        assert error_info.context == {"key": "value"}
        assert error_info.retry_count == 2
        assert error_info.stack_trace == "test stack trace"
        assert error_info.recovery_attempts == ["action1"]
    
    def test_from_dict_missing_field(self):
        """Test creating error info from dictionary with missing field."""
        data = {
            "error_id": "test-id",
            # Missing error_type
            "error_message": "Test error message",
            "error_category": "processing",
            "operation": "test_operation"
        }
        
        with pytest.raises(ValueError, match="Required field 'error_type' missing"):
            ErrorInfo.from_dict(data)
    
    def test_from_dict_invalid_type(self):
        """Test creating error info from invalid data type."""
        with pytest.raises(ValueError, match="data must be dictionary"):
            ErrorInfo.from_dict("invalid")


class TestErrorRecoveryStrategy:
    """Test suite for ErrorRecoveryStrategy class."""
    
    def test_init_valid_strategy(self):
        """Test valid strategy initialization."""
        strategy = ErrorRecoveryStrategy(
            error_type="TestError",
            error_category=ErrorCategory.PROCESSING,
            max_retries=5,
            retry_delay=10,
            recovery_actions=["action1", "action2"],
            should_abort=False,
            custom_handler=lambda x: x
        )
        
        assert strategy.error_type == "TestError"
        assert strategy.error_category == ErrorCategory.PROCESSING
        assert strategy.max_retries == 5
        assert strategy.retry_delay == 10
        assert strategy.recovery_actions == ["action1", "action2"]
        assert strategy.should_abort is False
        assert strategy.custom_handler is not None
    
    def test_init_defaults(self):
        """Test strategy initialization with defaults."""
        strategy = ErrorRecoveryStrategy(
            error_type="TestError",
            error_category=ErrorCategory.PROCESSING
        )
        
        assert strategy.max_retries == 3
        assert strategy.retry_delay == 5
        assert strategy.recovery_actions == []
        assert strategy.should_abort is True
        assert strategy.custom_handler is None


class TestErrorHandler:
    """Test suite for ErrorHandler class."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return ErrorHandlerConfig(
            max_retry_attempts=3,
            retry_delay=5,
            backoff_multiplier=2.0,
            enable_automatic_recovery=True,
            enable_error_logging=True,
            enable_error_reporting=True,
            error_threshold=10
        )
    
    @pytest.fixture
    def handler(self, config):
        """Create test error handler instance."""
        return ErrorHandler(config)
    
    def test_init_valid_handler(self, config):
        """Test valid handler initialization."""
        handler = ErrorHandler(config)
        
        assert handler.config == config
        assert len(handler.error_strategies) == 0
        assert len(handler.error_history) == 0
        assert len(handler.error_counters) == 0
        assert len(handler.recovery_handlers) == 0
    
    def test_init_invalid_config(self):
        """Test handler initialization with invalid config."""
        with pytest.raises(ValueError, match="config must be ErrorHandlerConfig instance"):
            ErrorHandler("invalid")
    
    @pytest.mark.asyncio
    async def test_handle_error_success(self, handler):
        """Test successful error handling."""
        error = ValueError("Test error")
        
        result = await handler.handle_error(error, "test_operation")
        
        assert isinstance(result, ProcessingResult)
        assert result.success is False
        assert "Test error" in result.message
        assert len(handler.error_history) == 1
        assert "ValueError" in handler.error_counters
    
    @pytest.mark.asyncio
    async def test_handle_error_with_context(self, handler):
        """Test error handling with context."""
        error = ValueError("Test error")
        context = {"file_path": "/test/file.txt", "line": 10}
        
        result = await handler.handle_error(error, "test_operation", context)
        
        assert isinstance(result, ProcessingResult)
        assert len(handler.error_history) == 1
        error_info = handler.error_history[0]
        assert error_info.context == context
    
    @pytest.mark.asyncio
    async def test_handle_error_with_retry_count(self, handler):
        """Test error handling with retry count."""
        error = ValueError("Test error")
        
        result = await handler.handle_error(error, "test_operation", retry_count=2)
        
        assert isinstance(result, ProcessingResult)
        assert len(handler.error_history) == 1
        error_info = handler.error_history[0]
        assert error_info.retry_count == 2
    
    @pytest.mark.asyncio
    async def test_handle_error_file_not_found(self, handler):
        """Test handling FileNotFoundError."""
        error = FileNotFoundError("File not found")
        
        result = await handler.handle_error(error, "test_operation")
        
        assert isinstance(result, ProcessingResult)
        assert len(handler.error_history) == 1
        error_info = handler.error_history[0]
        assert error_info.error_category == ErrorCategory.FILE_SYSTEM
    
    @pytest.mark.asyncio
    async def test_handle_error_processing_error(self, handler):
        """Test handling ProcessingError."""
        error = ProcessingError("TestError", "Test message", ErrorCategory.DATABASE)
        
        result = await handler.handle_error(error, "test_operation")
        
        assert isinstance(result, ProcessingResult)
        assert len(handler.error_history) == 1
        error_info = handler.error_history[0]
        assert error_info.error_category == ErrorCategory.DATABASE
    
    @pytest.mark.asyncio
    async def test_retry_operation_success(self, handler):
        """Test successful operation retry."""
        async def test_operation():
            return "success"
        
        result = await handler.retry_operation(test_operation)
        
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_retry_operation_sync_function(self, handler):
        """Test retry with synchronous function."""
        def test_operation():
            return "success"
        
        result = await handler.retry_operation(test_operation)
        
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_retry_operation_failure(self, handler):
        """Test operation retry with failure."""
        async def test_operation():
            raise ValueError("Test error")
        
        with pytest.raises(ProcessingError, match="Operation failed after 3 retries"):
            await handler.retry_operation(test_operation)
    
    @pytest.mark.asyncio
    async def test_retry_operation_custom_retries(self, handler):
        """Test operation retry with custom retry settings."""
        async def test_operation():
            raise ValueError("Test error")
        
        with pytest.raises(ProcessingError, match="Operation failed after 1 retries"):
            await handler.retry_operation(test_operation, max_retries=1)
    
    def test_add_error_strategy(self, handler):
        """Test adding error strategy."""
        strategy = ErrorRecoveryStrategy(
            error_type="TestError",
            error_category=ErrorCategory.PROCESSING
        )
        
        handler.add_error_strategy(strategy)
        
        assert "TestError" in handler.error_strategies
        assert handler.error_strategies["TestError"] == strategy
    
    def test_add_error_strategy_invalid(self, handler):
        """Test adding invalid error strategy."""
        with pytest.raises(ValueError, match="strategy must be ErrorRecoveryStrategy instance"):
            handler.add_error_strategy("invalid")
    
    def test_remove_error_strategy_success(self, handler):
        """Test successful strategy removal."""
        strategy = ErrorRecoveryStrategy(
            error_type="TestError",
            error_category=ErrorCategory.PROCESSING
        )
        handler.error_strategies["TestError"] = strategy
        
        result = handler.remove_error_strategy("TestError")
        
        assert result is True
        assert "TestError" not in handler.error_strategies
    
    def test_remove_error_strategy_not_found(self, handler):
        """Test strategy removal when not found."""
        result = handler.remove_error_strategy("NonexistentError")
        
        assert result is False
    
    def test_remove_error_strategy_invalid_type(self, handler):
        """Test strategy removal with invalid type."""
        with pytest.raises(ValueError, match="error_type must be string"):
            handler.remove_error_strategy(123)
    
    @pytest.mark.asyncio
    async def test_recover_from_error_success(self, handler):
        """Test successful error recovery."""
        strategy = ErrorRecoveryStrategy(
            error_type="TestError",
            error_category=ErrorCategory.PROCESSING,
            recovery_actions=["action1", "action2"]
        )
        handler.error_strategies["TestError"] = strategy
        
        error_info = ErrorInfo(
            error_id="test-id",
            error_type="TestError",
            error_message="Test error",
            error_category=ErrorCategory.PROCESSING,
            operation="test_operation"
        )
        
        result = await handler.recover_from_error(error_info)
        
        assert result is True
        assert len(error_info.recovery_attempts) == 2
    
    @pytest.mark.asyncio
    async def test_recover_from_error_no_strategy(self, handler):
        """Test error recovery without strategy."""
        error_info = ErrorInfo(
            error_id="test-id",
            error_type="TestError",
            error_message="Test error",
            error_category=ErrorCategory.PROCESSING,
            operation="test_operation"
        )
        
        result = await handler.recover_from_error(error_info)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_recover_from_error_invalid_info(self, handler):
        """Test error recovery with invalid error info."""
        with pytest.raises(ValueError, match="error_info must be ErrorInfo instance"):
            await handler.recover_from_error("invalid")
    
    @pytest.mark.asyncio
    async def test_report_errors_enabled(self, handler):
        """Test error reporting when enabled."""
        # Add some errors
        error = ValueError("Test error")
        await handler.handle_error(error, "test_operation")
        
        report = await handler.report_errors()
        
        assert report["enabled"] is True
        assert report["total_errors"] == 1
        assert "ValueError" in report["error_types"]
        assert "unknown" in report["error_categories"]
        assert len(report["recent_errors"]) == 1
    
    @pytest.mark.asyncio
    async def test_report_errors_disabled(self, handler):
        """Test error reporting when disabled."""
        handler.config.enable_error_reporting = False
        
        report = await handler.report_errors()
        
        assert report["enabled"] is False
    
    def test_get_error_statistics(self, handler):
        """Test getting error statistics."""
        # Add some strategies
        strategy = ErrorRecoveryStrategy(
            error_type="TestError",
            error_category=ErrorCategory.PROCESSING
        )
        handler.error_strategies["TestError"] = strategy
        
        stats = handler.get_error_statistics()
        
        assert stats["total_errors"] == 0
        assert stats["error_strategies"] == 1
        assert stats["recovery_handlers"] == 0
        assert "error_counters" in stats
    
    @pytest.mark.asyncio
    async def test_clear_error_history(self, handler):
        """Test clearing error history."""
        # Add some errors
        error = ValueError("Test error")
        await handler.handle_error(error, "test_operation")
        
        assert len(handler.error_history) == 1
        assert len(handler.error_counters) > 0
        
        await handler.clear_error_history()
        
        assert len(handler.error_history) == 0
        assert len(handler.error_counters) == 0
    
    def test_should_retry_error_retryable(self, handler):
        """Test should retry for retryable error."""
        error = ValueError("Test error")
        
        result = handler.should_retry_error(error, 0)
        
        assert result is True
    
    def test_should_retry_error_max_retries_reached(self, handler):
        """Test should retry when max retries reached."""
        error = ValueError("Test error")
        
        result = handler.should_retry_error(error, 3)  # Max retries is 3
        
        assert result is False
    
    def test_should_retry_error_file_not_found(self, handler):
        """Test should retry for FileNotFoundError."""
        error = FileNotFoundError("File not found")
        
        result = handler.should_retry_error(error, 0)
        
        assert result is False
    
    def test_should_retry_error_threshold_reached(self, handler):
        """Test should retry when error threshold reached."""
        error = ValueError("Test error")
        
        # Add errors to reach threshold
        for _ in range(10):  # Threshold is 10
            handler.error_counters["ValueError"] = handler.error_counters.get("ValueError", 0) + 1
        
        result = handler.should_retry_error(error, 0)
        
        assert result is False
    
    def test_should_retry_error_invalid_retry_count(self, handler):
        """Test should retry with invalid retry count."""
        error = ValueError("Test error")
        
        with pytest.raises(ValueError, match="retry_count must be non-negative"):
            handler.should_retry_error(error, -1)
    
    @pytest.mark.asyncio
    async def test_calculate_retry_delay(self, handler):
        """Test retry delay calculation."""
        delay = await handler.calculate_retry_delay(2, 5)
        
        # With backoff_multiplier=2.0: 5 * (2^2) = 20, plus jitter
        assert delay >= 16  # 20 * 0.8 = 16
        assert delay <= 24  # 20 * 1.2 = 24
    
    @pytest.mark.asyncio
    async def test_calculate_retry_delay_minimum(self, handler):
        """Test retry delay minimum value."""
        delay = await handler.calculate_retry_delay(0, 1)
        
        assert delay >= 1  # Minimum 1 second
    
    @pytest.mark.asyncio
    async def test_calculate_retry_delay_invalid_retry_count(self, handler):
        """Test retry delay calculation with invalid retry count."""
        with pytest.raises(ValueError, match="retry_count must be non-negative"):
            await handler.calculate_retry_delay(-1, 5)
    
    @pytest.mark.asyncio
    async def test_calculate_retry_delay_invalid_base_delay(self, handler):
        """Test retry delay calculation with invalid base delay."""
        with pytest.raises(ValueError, match="base_delay must be positive"):
            await handler.calculate_retry_delay(1, 0)
    
    def test_create_error_info(self, handler):
        """Test creating error info from exception."""
        error = ValueError("Test error")
        
        error_info = handler._create_error_info(error, "test_operation")
        
        assert error_info.error_type == "ValueError"
        assert error_info.error_message == "Test error"
        assert error_info.error_category == ErrorCategory.UNKNOWN
        assert error_info.operation == "test_operation"
        assert error_info.context == {}
        assert error_info.stack_trace is not None
        assert isinstance(error_info.error_id, str)
    
    def test_create_error_info_with_context(self, handler):
        """Test creating error info with context."""
        error = ValueError("Test error")
        context = {"key": "value"}
        
        error_info = handler._create_error_info(error, "test_operation", context)
        
        assert error_info.context == context
    
    def test_create_error_info_file_not_found(self, handler):
        """Test creating error info for FileNotFoundError."""
        error = FileNotFoundError("File not found")
        
        error_info = handler._create_error_info(error, "test_operation")
        
        assert error_info.error_category == ErrorCategory.FILE_SYSTEM
    
    def test_create_error_info_processing_error(self, handler):
        """Test creating error info for ProcessingError."""
        error = ProcessingError("TestError", "Test message", ErrorCategory.DATABASE)
        
        error_info = handler._create_error_info(error, "test_operation")
        
        assert error_info.error_category == ErrorCategory.DATABASE
    
    def test_get_error_strategy_found(self, handler):
        """Test getting error strategy when found."""
        strategy = ErrorRecoveryStrategy(
            error_type="ValueError",
            error_category=ErrorCategory.PROCESSING
        )
        handler.error_strategies["ValueError"] = strategy
        
        error = ValueError("Test error")
        result = handler._get_error_strategy(error)
        
        assert result == strategy
    
    def test_get_error_strategy_not_found(self, handler):
        """Test getting error strategy when not found."""
        error = ValueError("Test error")
        result = handler._get_error_strategy(error)
        
        assert result is None
    
    def test_log_error_enabled(self, handler):
        """Test error logging when enabled."""
        error_info = ErrorInfo(
            error_id="test-id",
            error_type="TestError",
            error_message="Test error",
            error_category=ErrorCategory.PROCESSING,
            operation="test_operation"
        )
        
        with patch('docanalyzer.services.error_handler.logger') as mock_logger:
            handler._log_error(error_info)
            
            mock_logger.error.assert_called_once()
    
    def test_log_error_disabled(self, handler):
        """Test error logging when disabled."""
        handler.config.enable_error_logging = False
        
        error_info = ErrorInfo(
            error_id="test-id",
            error_type="TestError",
            error_message="Test error",
            error_category=ErrorCategory.PROCESSING,
            operation="test_operation"
        )
        
        with patch('docanalyzer.services.error_handler.logger') as mock_logger:
            handler._log_error(error_info)
            
            mock_logger.error.assert_not_called()
    
    def test_update_error_counters(self, handler):
        """Test updating error counters."""
        handler._update_error_counters("TestError")
        
        assert handler.error_counters["TestError"] == 1
        
        handler._update_error_counters("TestError")
        
        assert handler.error_counters["TestError"] == 2 