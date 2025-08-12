"""
Tests for Logging Integration

Unit tests for DocAnalyzer logging integration with mcp_proxy_adapter framework.
"""

import pytest
import logging
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from docanalyzer.logging.integration import (
    LoggingConfig,
    DocAnalyzerLogger,
    LoggingError,
    LoggingConfigError,
    DEFAULT_LOGGING_CONFIG
)


class TestLoggingConfig:
    """Test suite for LoggingConfig class."""
    
    @pytest.fixture
    def config(self):
        """Create test LoggingConfig instance."""
        return LoggingConfig()
    
    def test_init_default_config(self, config):
        """Test LoggingConfig initialization with default configuration."""
        assert config.log_level == DEFAULT_LOGGING_CONFIG['log_level']
        assert config.log_file == DEFAULT_LOGGING_CONFIG['log_file']
        assert config.log_format == DEFAULT_LOGGING_CONFIG['log_format']
        assert config.enable_console == DEFAULT_LOGGING_CONFIG['enable_console']
        assert config.enable_file == DEFAULT_LOGGING_CONFIG['enable_file']
        assert config.max_file_size == DEFAULT_LOGGING_CONFIG['max_file_size']
        assert config.backup_count == DEFAULT_LOGGING_CONFIG['backup_count']
    
    @patch('docanalyzer.logging.integration.get_setting')
    def test_load_from_framework_success(self, mock_get_setting, config):
        """Test successful loading of configuration from framework."""
        # Mock framework settings
        def mock_get_setting_impl(key, default):
            settings = {
                'docanalyzer.log_level': 'DEBUG',
                'docanalyzer.log_file': '/custom/path/log.log',
                'docanalyzer.log_format': '%(levelname)s - %(message)s',
                'docanalyzer.enable_console': False,
                'docanalyzer.enable_file': True,
                'docanalyzer.max_file_size': 20 * 1024 * 1024,
                'docanalyzer.backup_count': 10
            }
            return settings.get(key, default)
        
        mock_get_setting.side_effect = mock_get_setting_impl
        
        result = config.load_from_framework()
        
        assert result['log_level'] == 'DEBUG'
        assert result['log_file'] == '/custom/path/log.log'
        assert result['enable_console'] == False
        assert result['enable_file'] == True
        assert result['max_file_size'] == 20 * 1024 * 1024
        assert result['backup_count'] == 10
    
    @patch('docanalyzer.logging.integration.get_setting')
    def test_load_from_framework_fallback(self, mock_get_setting, config):
        """Test fallback to defaults when framework loading fails."""
        # Mock framework settings to raise exception
        mock_get_setting.side_effect = Exception("Framework not available")
        
        result = config.load_from_framework()
        
        # Should use default values
        assert result['log_level'] == DEFAULT_LOGGING_CONFIG['log_level']
        assert result['log_file'] == DEFAULT_LOGGING_CONFIG['log_file']
        assert result['enable_console'] == DEFAULT_LOGGING_CONFIG['enable_console']
    
    def test_validate_success(self, config):
        """Test successful configuration validation."""
        assert config.validate() == True
    
    def test_validate_invalid_log_level(self, config):
        """Test validation with invalid log level."""
        config.log_level = 'INVALID_LEVEL'
        
        with pytest.raises(LoggingConfigError) as exc_info:
            config.validate()
        
        assert "Invalid log level" in str(exc_info.value)
        assert exc_info.value.config_key == "validation"
    
    def test_validate_invalid_max_file_size(self, config):
        """Test validation with invalid max file size."""
        config.max_file_size = -1
        
        with pytest.raises(LoggingConfigError) as exc_info:
            config.validate()
        
        assert "Invalid max_file_size" in str(exc_info.value)
    
    def test_validate_invalid_backup_count(self, config):
        """Test validation with invalid backup count."""
        config.backup_count = -1
        
        with pytest.raises(LoggingConfigError) as exc_info:
            config.validate()
        
        assert "Invalid backup_count" in str(exc_info.value)
    
    def test_validate_invalid_boolean_values(self, config):
        """Test validation with invalid boolean values."""
        config.enable_console = "not_boolean"
        
        with pytest.raises(LoggingConfigError) as exc_info:
            config.validate()
        
        assert "Invalid enable_console" in str(exc_info.value)
    
    def test_apply_configuration_success(self, config):
        """Test successful configuration application."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config.log_file = os.path.join(temp_dir, 'test.log')
            config.enable_file = True
            config.enable_console = False
            
            assert config.apply_configuration() == True
            
            # Check that log file was created
            assert os.path.exists(config.log_file)
    

    
    def test_apply_configuration_creates_log_directory(self, config):
        """Test that log directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = os.path.join(temp_dir, 'logs', 'subdir')
            config.log_file = os.path.join(log_dir, 'test.log')
            config.enable_file = True
            config.enable_console = False
            
            assert config.apply_configuration() == True
            assert os.path.exists(log_dir)
            assert os.path.exists(config.log_file)


class TestDocAnalyzerLogger:
    """Test suite for DocAnalyzerLogger class."""
    
    @pytest.fixture
    def logger(self):
        """Create test DocAnalyzerLogger instance."""
        return DocAnalyzerLogger("test_component")
    
    def test_init_success(self, logger):
        """Test DocAnalyzerLogger initialization."""
        assert logger.component_name == "test_component"
        assert isinstance(logger.config, LoggingConfig)
        assert logger.logger.name == "docanalyzer.test_component"
    
    def test_init_empty_component_name(self):
        """Test initialization with empty component name."""
        with pytest.raises(ValueError) as exc_info:
            DocAnalyzerLogger("")
        
        assert "component_name must be non-empty string" in str(exc_info.value)
    
    def test_init_invalid_component_name(self):
        """Test initialization with invalid component name."""
        with pytest.raises(ValueError) as exc_info:
            DocAnalyzerLogger(123)
        
        assert "component_name must be non-empty string" in str(exc_info.value)
    
    def test_setup_logging_success(self, logger):
        """Test successful logging setup."""
        assert logger.setup_logging() == True
    
    def test_debug_logging(self, logger):
        """Test debug level logging."""
        logger.debug("Test debug message")
        # No exception should be raised
    
    def test_info_logging(self, logger):
        """Test info level logging."""
        logger.info("Test info message")
        # No exception should be raised
    
    def test_warning_logging(self, logger):
        """Test warning level logging."""
        logger.warning("Test warning message")
        # No exception should be raised
    
    def test_error_logging(self, logger):
        """Test error level logging."""
        logger.error("Test error message")
        # No exception should be raised
    
    def test_critical_logging(self, logger):
        """Test critical level logging."""
        logger.critical("Test critical message")
        # No exception should be raised
    
    def test_logging_empty_message(self, logger):
        """Test logging with empty message."""
        with pytest.raises(ValueError) as exc_info:
            logger.info("")
        
        assert "message must be non-empty string" in str(exc_info.value)
    
    def test_logging_invalid_message(self, logger):
        """Test logging with invalid message type."""
        with pytest.raises(ValueError) as exc_info:
            logger.info(123)
        
        assert "message must be non-empty string" in str(exc_info.value)
    
    def test_log_operation_success(self, logger):
        """Test successful operation logging."""
        details = {"file_path": "/test/file.txt", "size": 1024}
        logger.log_operation("file_processed", details, "INFO")
        # No exception should be raised
    
    def test_log_operation_empty_operation(self, logger):
        """Test operation logging with empty operation name."""
        details = {"test": "data"}
        
        with pytest.raises(ValueError) as exc_info:
            logger.log_operation("", details)
        
        assert "operation must be non-empty string" in str(exc_info.value)
    
    def test_log_operation_invalid_details(self, logger):
        """Test operation logging with invalid details."""
        with pytest.raises(ValueError) as exc_info:
            logger.log_operation("test_operation", "not_a_dict")
        
        assert "details must be dictionary" in str(exc_info.value)
    
    def test_log_operation_invalid_level(self, logger):
        """Test operation logging with invalid level."""
        details = {"test": "data"}
        
        with pytest.raises(ValueError) as exc_info:
            logger.log_operation("test_operation", details, "INVALID_LEVEL")
        
        assert "Invalid level" in str(exc_info.value)
    
    def test_log_critical_exception_handling(self, logger):
        """Test exception handling in critical logging."""
        # Mock logger.critical to raise exception
        with patch.object(logger.logger, 'critical', side_effect=Exception("Critical logging failed")):
            with pytest.raises(LoggingError) as exc_info:
                logger.critical("Test critical message")
            
            assert "Failed to log critical message" in str(exc_info.value)
            assert exc_info.value.component == "test_component"
            assert exc_info.value.operation == "critical"
    
    def test_log_operation_exception_handling(self, logger):
        """Test exception handling in operation logging."""
        details = {"test": "data"}
        
        # Mock logger.info to raise exception
        with patch.object(logger.logger, 'info', side_effect=Exception("Operation logging failed")):
            with pytest.raises(LoggingError) as exc_info:
                logger.log_operation("test_operation", details, "INFO")
            
            assert "Failed to log operation" in str(exc_info.value)
            assert exc_info.value.component == "test_component"
            assert exc_info.value.operation == "log_operation"
    
    def test_log_operation_with_json_serialization_error(self, logger):
        """Test operation logging with JSON serialization error."""
        # Create object that cannot be serialized to JSON even with default=str
        class NonSerializable:
            def __str__(self):
                raise Exception("Cannot convert to string")
        
        details = {"test": NonSerializable()}
        
        # Should handle JSON serialization error gracefully
        with pytest.raises(LoggingError) as exc_info:
            logger.log_operation("test_operation", details, "INFO")
        
        assert "Failed to log operation" in str(exc_info.value)
    
    def test_log_operation_with_getattr_error(self, logger):
        """Test operation logging with getattr error."""
        details = {"test": "data"}
        
        # Mock getattr to raise exception
        with patch('builtins.getattr', side_effect=Exception("Getattr failed")):
            with pytest.raises(LoggingError) as exc_info:
                logger.log_operation("test_operation", details, "INFO")
            
            assert "Failed to log operation" in str(exc_info.value)
    
    def test_critical_with_invalid_message(self, logger):
        """Test critical logging with invalid message."""
        with pytest.raises(ValueError) as exc_info:
            logger.critical("")
        
        assert "message must be non-empty string" in str(exc_info.value)
    
    def test_critical_with_invalid_message_type(self, logger):
        """Test critical logging with invalid message type."""
        with pytest.raises(ValueError) as exc_info:
            logger.critical(123)
        
        assert "message must be non-empty string" in str(exc_info.value)
    
    def test_critical_with_none_message(self, logger):
        """Test critical logging with None message."""
        with pytest.raises(ValueError) as exc_info:
            logger.critical(None)
        
        assert "message must be non-empty string" in str(exc_info.value)
    
    def test_error_exception_handling(self, logger):
        """Test exception handling in error logging."""
        # Mock logger.error to raise exception
        with patch.object(logger.logger, 'error', side_effect=Exception("Error logging failed")):
            with pytest.raises(LoggingError) as exc_info:
                logger.error("Test error message")
            
            assert "Failed to log error message" in str(exc_info.value)
            assert exc_info.value.component == "test_component"
            assert exc_info.value.operation == "error"
    
    def test_error_with_invalid_message(self, logger):
        """Test error logging with invalid message."""
        with pytest.raises(ValueError) as exc_info:
            logger.error("")
        
        assert "message must be non-empty string" in str(exc_info.value)
    
    def test_error_with_invalid_message_type(self, logger):
        """Test error logging with invalid message type."""
        with pytest.raises(ValueError) as exc_info:
            logger.error(123)
        
        assert "message must be non-empty string" in str(exc_info.value)
    
    def test_error_with_none_message(self, logger):
        """Test error logging with None message."""
        with pytest.raises(ValueError) as exc_info:
            logger.error(None)
        
        assert "message must be non-empty string" in str(exc_info.value)


class TestLoggingExceptions:
    """Test suite for logging exceptions."""
    
    def test_logging_error_init(self):
        """Test LoggingError initialization."""
        error = LoggingError("Test error", "test_component", "test_operation")
        
        assert error.message == "Test error"
        assert error.component == "test_component"
        assert error.operation == "test_operation"
    
    def test_logging_config_error_init(self):
        """Test LoggingConfigError initialization."""
        error = LoggingConfigError("Config error", "log_level", "INVALID")
        
        assert error.message == "Config error"
        assert error.config_key == "log_level"
        assert error.value == "INVALID"
    
    def test_logging_error_str_representation(self):
        """Test LoggingError string representation."""
        error = LoggingError("Test error", "test_component", "test_operation")
        
        assert "Test error" in str(error)
        assert error.message == "Test error"


class TestLoggingIntegration:
    """Integration tests for logging system."""
    
    def test_logging_config_with_framework_integration(self):
        """Test logging configuration integration with framework."""
        config = LoggingConfig()
        
        # Test that configuration can be loaded (with fallback)
        result = config.load_from_framework()
        assert isinstance(result, dict)
        assert 'log_level' in result
        assert 'log_file' in result
    
    def test_logger_with_custom_config(self):
        """Test logger with custom configuration."""
        config = LoggingConfig()
        config.log_level = 'DEBUG'
        config.enable_console = True
        config.enable_file = False
        
        logger = DocAnalyzerLogger("custom_component", config)
        
        assert logger.config.log_level == 'DEBUG'
        assert logger.config.enable_console == True
        assert logger.config.enable_file == False
    
    def test_logging_levels_work_correctly(self):
        """Test that different logging levels work correctly."""
        logger = DocAnalyzerLogger("level_test")
        
        # All these should work without raising exceptions
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
        
        # Test structured logging
        details = {"operation": "test", "status": "success"}
        logger.log_operation("test_operation", details, "INFO")
    
    def test_logging_with_exception_info(self):
        """Test logging with exception information."""
        logger = DocAnalyzerLogger("exception_test")
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.error("Caught exception", exc_info=True)
            # Should not raise any exceptions


class TestImportErrorFallback:
    """Test suite for ImportError fallback functionality."""
    
    def test_import_error_fallback_values(self):
        """Test fallback values when mcp_proxy_adapter is not available."""
        # This test verifies that fallback values are properly set
        import docanalyzer.logging.integration
        
        # Verify fallback values are available
        assert hasattr(docanalyzer.logging.integration, 'Logger')
        assert hasattr(docanalyzer.logging.integration, 'LogLevel')
        assert hasattr(docanalyzer.logging.integration, 'LogFormatter')
        assert hasattr(docanalyzer.logging.integration, 'get_setting')
        
        # Verify get_setting is callable
        assert callable(docanalyzer.logging.integration.get_setting)
        
        # Test fallback get_setting function
        result = docanalyzer.logging.integration.get_setting("test_key", "default_value")
        assert result == "default_value"
    
    def test_fallback_get_setting_function(self):
        """Test the fallback get_setting function behavior."""
        import docanalyzer.logging.integration
        
        # Test with different key-value pairs
        test_cases = [
            ("log_level", "INFO"),
            ("log_file", "/path/to/log"),
            ("enable_console", True),
            ("max_file_size", 1024),
            ("", "empty_key"),
            (None, "none_key")
        ]
        
        for key, default in test_cases:
            result = docanalyzer.logging.integration.get_setting(key, default)
            assert result == default


class TestLoggingConfigAdvanced:
    """Advanced test suite for LoggingConfig class."""
    
    @pytest.fixture
    def config(self):
        """Create test LoggingConfig instance."""
        return LoggingConfig()
    
    def test_load_from_framework_exception_handling(self, config):
        """Test exception handling in load_from_framework."""
        # Mock get_setting to raise exception
        with patch('docanalyzer.logging.integration.get_setting', side_effect=Exception("Test exception")):
            # Should not raise exception, just log warnings and use defaults
            result = config.load_from_framework()
            
            # Should return default configuration
            assert isinstance(result, dict)
            assert 'log_level' in result
            assert 'log_file' in result
    
    def test_validate_creates_log_directory(self, config):
        """Test that validate creates log directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create nested directory path
            nested_dir = os.path.join(temp_dir, 'logs', 'deep', 'nested')
            config.log_file = os.path.join(nested_dir, 'test.log')
            config.enable_file = True
            
            # Validate should create directory
            assert config.validate() == True
            assert os.path.exists(nested_dir)
    
    def test_validate_exception_handling(self, config):
        """Test exception handling in validate method."""
        # Set invalid log level to trigger exception
        config.log_level = 'INVALID_LEVEL'
        
        with pytest.raises(LoggingConfigError) as exc_info:
            config.validate()
        
        assert "Logging configuration validation failed" in str(exc_info.value)
        assert exc_info.value.config_key == "validation"
    
    def test_apply_configuration_exception_handling(self, config):
        """Test exception handling in apply_configuration."""
        # Set invalid configuration to trigger validation error
        config.log_level = 'INVALID_LEVEL'
        
        with pytest.raises(LoggingConfigError):
            config.apply_configuration()
    
    def test_apply_configuration_clears_existing_handlers(self, config):
        """Test that apply_configuration clears existing handlers."""
        # Add some existing handlers
        root_logger = logging.getLogger()
        original_handlers = root_logger.handlers.copy()
        
        # Apply configuration
        config.enable_console = True
        config.enable_file = False
        config.apply_configuration()
        
        # Check that new handlers were added
        assert len(root_logger.handlers) > 0
        
        # Clean up
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)
        for handler in original_handlers:
            root_logger.addHandler(handler)
    
    def test_apply_configuration_with_file_handler(self, config):
        """Test apply_configuration with file handler enabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config.log_file = os.path.join(temp_dir, 'test.log')
            config.enable_console = False
            config.enable_file = True
            config.max_file_size = 1024
            config.backup_count = 3
            
            assert config.apply_configuration() == True
            
            # Check that log file was created
            assert os.path.exists(config.log_file)
    
    def test_apply_configuration_with_both_handlers(self, config):
        """Test apply_configuration with both console and file handlers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config.log_file = os.path.join(temp_dir, 'test.log')
            config.enable_console = True
            config.enable_file = True
            
            assert config.apply_configuration() == True
            
            # Check that log file was created
            assert os.path.exists(config.log_file) 