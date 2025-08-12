"""
Logging Integration - Integration with mcp_proxy_adapter Framework

This module provides integration layer between DocAnalyzer and the
mcp_proxy_adapter framework's logging system.

It extends the framework's logging capabilities with DocAnalyzer-specific
logging configurations while maintaining compatibility with existing infrastructure.

Author: DocAnalyzer Team
Version: 1.0.0
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import json
from datetime import datetime

# Import framework logging components
try:
    from mcp_proxy_adapter.core.logging import Logger, LogLevel, LogFormatter
    from mcp_proxy_adapter.core.settings import get_setting
except ImportError:
    # Fallback for development/testing
    Logger = logging.Logger
    LogLevel = int
    LogFormatter = logging.Formatter
    
    def get_setting(key: str, default: Any) -> Any:
        """Fallback get_setting function for development/testing."""
        return default

logger = logging.getLogger(__name__)

# DocAnalyzer-specific logging configuration keys
DOCANALYZER_LOGGING_KEYS = {
    'log_level': 'docanalyzer.log_level',
    'log_file': 'docanalyzer.log_file',
    'log_format': 'docanalyzer.log_format',
    'enable_console': 'docanalyzer.enable_console',
    'enable_file': 'docanalyzer.enable_file',
    'max_file_size': 'docanalyzer.max_file_size',
    'backup_count': 'docanalyzer.backup_count'
}

# Default logging configuration
DEFAULT_LOGGING_CONFIG = {
    'log_level': 'INFO',
    'log_file': 'logs/docanalyzer.log',
    'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'enable_console': True,
    'enable_file': True,
    'max_file_size': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5
}


class LoggingConfig:
    """
    Logging Configuration - DocAnalyzer Logging Settings
    
    Manages DocAnalyzer-specific logging configuration and provides
    integration with the mcp_proxy_adapter framework's logging system.
    
    This class handles loading, validation, and application of logging
    settings while maintaining compatibility with the framework.
    
    Attributes:
        log_level (str): Logging level for DocAnalyzer components.
            Values: DEBUG, INFO, WARNING, ERROR, CRITICAL.
        log_file (str): Path to the log file for DocAnalyzer.
            Must be writable path.
        log_format (str): Format string for log messages.
            Uses standard Python logging format.
        enable_console (bool): Whether to enable console logging.
            Defaults to True.
        enable_file (bool): Whether to enable file logging.
            Defaults to True.
        max_file_size (int): Maximum size of log file in bytes.
            Defaults to 10MB.
        backup_count (int): Number of backup log files to keep.
            Defaults to 5.
    
    Example:
        >>> config = LoggingConfig()
        >>> config.load_from_framework()
        >>> config.validate()
    
    Raises:
        LoggingConfigError: If configuration is invalid
        ValidationError: If settings cannot be validated
    """
    
    def __init__(self):
        """
        Initialize LoggingConfig instance.
        
        Sets up default configuration and prepares for integration
        with the framework's logging system.
        """
        self.config = DEFAULT_LOGGING_CONFIG.copy()
        self.log_level = self.config['log_level']
        self.log_file = self.config['log_file']
        self.log_format = self.config['log_format']
        self.enable_console = self.config['enable_console']
        self.enable_file = self.config['enable_file']
        self.max_file_size = self.config['max_file_size']
        self.backup_count = self.config['backup_count']
        logger.debug("LoggingConfig initialized with default configuration")
    
    def load_from_framework(self) -> Dict[str, Any]:
        """
        Load logging configuration from framework settings.
        
        Attempts to load DocAnalyzer-specific logging settings from
        the mcp_proxy_adapter framework configuration.
        
        Returns:
            Dict[str, Any]: Loaded logging configuration.
                Contains all logging settings with fallback to defaults.
        
        Raises:
            LoggingConfigError: If configuration cannot be loaded
        """
        try:
            loaded_config = {}
            
            # Try to load each setting from framework
            for key, config_key in DOCANALYZER_LOGGING_KEYS.items():
                try:
                    value = get_setting(config_key, self.config[key])
                    loaded_config[key] = value
                    logger.debug(f"Loaded {key} from framework: {value}")
                except Exception as e:
                    logger.warning(f"Failed to load {key} from framework, using default: {e}")
                    loaded_config[key] = self.config[key]
            
            # Update instance attributes
            self.config.update(loaded_config)
            self.log_level = self.config['log_level']
            self.log_file = self.config['log_file']
            self.log_format = self.config['log_format']
            self.enable_console = self.config['enable_console']
            self.enable_file = self.config['enable_file']
            self.max_file_size = self.config['max_file_size']
            self.backup_count = self.config['backup_count']
            
            logger.info("Logging configuration loaded from framework successfully")
            return loaded_config
            
        except Exception as e:
            error_msg = f"Failed to load logging configuration from framework: {e}"
            logger.error(error_msg)
            raise LoggingConfigError(error_msg, "framework_loading", str(e))
    
    def validate(self) -> bool:
        """
        Validate logging configuration.
        
        Checks that all logging settings are valid and compatible
        with the framework's requirements.
        
        Returns:
            bool: True if configuration is valid, False otherwise.
        
        Raises:
            ValidationError: If configuration validation fails
        """
        try:
            # Validate log level
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if self.log_level not in valid_levels:
                raise ValueError(f"Invalid log level: {self.log_level}. Must be one of {valid_levels}")
            
            # Validate log file path
            if self.enable_file:
                log_path = Path(self.log_file)
                if not log_path.parent.exists():
                    log_path.parent.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created log directory: {log_path.parent}")
            
            # Validate numeric values
            if self.max_file_size <= 0:
                raise ValueError(f"Invalid max_file_size: {self.max_file_size}. Must be positive")
            
            if self.backup_count < 0:
                raise ValueError(f"Invalid backup_count: {self.backup_count}. Must be non-negative")
            
            # Validate boolean values
            if not isinstance(self.enable_console, bool):
                raise ValueError(f"Invalid enable_console: {self.enable_console}. Must be boolean")
            
            if not isinstance(self.enable_file, bool):
                raise ValueError(f"Invalid enable_file: {self.enable_file}. Must be boolean")
            
            logger.info("Logging configuration validation passed")
            return True
            
        except Exception as e:
            error_msg = f"Logging configuration validation failed: {e}"
            logger.error(error_msg)
            raise LoggingConfigError(error_msg, "validation", str(e))
    
    def apply_configuration(self) -> bool:
        """
        Apply logging configuration to the system.
        
        Configures the logging system with current settings
        and integrates with the framework's logging infrastructure.
        
        Returns:
            bool: True if configuration was applied successfully.
        
        Raises:
            LoggingConfigError: If configuration cannot be applied
        """
        try:
            # Validate configuration first
            self.validate()
            
            # Configure root logger
            root_logger = logging.getLogger()
            root_logger.setLevel(getattr(logging, self.log_level))
            
            # Clear existing handlers
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)
            
            # Create formatter
            formatter = logging.Formatter(self.log_format)
            
            # Add console handler if enabled
            if self.enable_console:
                console_handler = logging.StreamHandler()
                console_handler.setFormatter(formatter)
                root_logger.addHandler(console_handler)
                logger.debug("Console logging enabled")
            
            # Add file handler if enabled
            if self.enable_file:
                from logging.handlers import RotatingFileHandler
                file_handler = RotatingFileHandler(
                    self.log_file,
                    maxBytes=self.max_file_size,
                    backupCount=self.backup_count
                )
                file_handler.setFormatter(formatter)
                root_logger.addHandler(file_handler)
                logger.debug(f"File logging enabled: {self.log_file}")
            
            logger.info("Logging configuration applied successfully")
            return True
            
        except Exception as e:
            error_msg = f"Failed to apply logging configuration: {e}"
            logger.error(error_msg)
            raise LoggingConfigError(error_msg, "configuration_application", str(e))


class DocAnalyzerLogger:
    """
    DocAnalyzer Logger - Integration with Framework Logging
    
    Main logging class that integrates DocAnalyzer with the
    mcp_proxy_adapter framework's logging system.
    
    This class provides unified logging interface for all DocAnalyzer
    components while maintaining compatibility with the framework.
    
    Attributes:
        config (LoggingConfig): Logging configuration instance.
            Manages all logging settings and framework integration.
        logger (Logger): Framework logger instance.
            Provides actual logging functionality.
        component_name (str): Name of the logging component.
            Used for log message identification.
    
    Example:
        >>> docanalyzer_logger = DocAnalyzerLogger("file_processor")
        >>> docanalyzer_logger.info("Processing file: example.txt")
        >>> docanalyzer_logger.error("Failed to process file", exc_info=True)
    
    Raises:
        LoggingError: When logging operations fail
        ConfigurationError: When logging configuration is invalid
    """
    
    def __init__(self, component_name: str, config: Optional[LoggingConfig] = None):
        """
        Initialize DocAnalyzerLogger instance.
        
        Args:
            component_name (str): Name of the logging component.
                Must be non-empty string. Used for log identification.
            config (Optional[LoggingConfig], optional): Logging configuration.
                Defaults to None. If None, creates default configuration.
        
        Raises:
            ValueError: If component_name is empty
            ConfigurationError: If configuration is invalid
        """
        if not component_name or not isinstance(component_name, str):
            raise ValueError("component_name must be non-empty string")
        
        self.component_name = component_name
        self.config = config if config else LoggingConfig()
        self.logger = logging.getLogger(f"docanalyzer.{component_name}")
        
        # Setup logging for this component
        self.setup_logging()
        logger.debug(f"DocAnalyzerLogger initialized for component: {component_name}")
    
    def setup_logging(self) -> bool:
        """
        Setup logging for the component.
        
        Configures logging handlers, formatters, and levels
        according to the current configuration.
        
        Returns:
            bool: True if logging was setup successfully.
        
        Raises:
            LoggingError: If logging setup fails
        """
        try:
            # Apply configuration if not already applied
            if not self.logger.handlers:
                self.config.apply_configuration()
            
            # Set component-specific logger level
            self.logger.setLevel(getattr(logging, self.config.log_level))
            
            logger.debug(f"Logging setup completed for component: {self.component_name}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to setup logging for component {self.component_name}: {e}"
            logger.error(error_msg)
            raise LoggingError(error_msg, self.component_name, "setup_logging")
    
    def debug(self, message: str, **kwargs) -> None:
        """
        Log debug message.
        
        Args:
            message (str): Debug message to log.
                Must be non-empty string.
            **kwargs: Additional logging parameters.
                Can include exc_info, extra, etc.
        
        Raises:
            LoggingError: If logging fails
        """
        if not message or not isinstance(message, str):
            raise ValueError("message must be non-empty string")
        
        try:
            self.logger.debug(message, **kwargs)
        except Exception as e:
            error_msg = f"Failed to log debug message: {e}"
            raise LoggingError(error_msg, self.component_name, "debug")
    
    def info(self, message: str, **kwargs) -> None:
        """
        Log info message.
        
        Args:
            message (str): Info message to log.
                Must be non-empty string.
            **kwargs: Additional logging parameters.
                Can include exc_info, extra, etc.
        
        Raises:
            LoggingError: If logging fails
        """
        if not message or not isinstance(message, str):
            raise ValueError("message must be non-empty string")
        
        try:
            self.logger.info(message, **kwargs)
        except Exception as e:
            error_msg = f"Failed to log info message: {e}"
            raise LoggingError(error_msg, self.component_name, "info")
    
    def warning(self, message: str, **kwargs) -> None:
        """
        Log warning message.
        
        Args:
            message (str): Warning message to log.
                Must be non-empty string.
            **kwargs: Additional logging parameters.
                Can include exc_info, extra, etc.
        
        Raises:
            LoggingError: If logging fails
        """
        if not message or not isinstance(message, str):
            raise ValueError("message must be non-empty string")
        
        try:
            self.logger.warning(message, **kwargs)
        except Exception as e:
            error_msg = f"Failed to log warning message: {e}"
            raise LoggingError(error_msg, self.component_name, "warning")
    
    def error(self, message: str, **kwargs) -> None:
        """
        Log error message.
        
        Args:
            message (str): Error message to log.
                Must be non-empty string.
            **kwargs: Additional logging parameters.
                Can include exc_info, extra, etc.
        
        Raises:
            LoggingError: If logging fails
        """
        if not message or not isinstance(message, str):
            raise ValueError("message must be non-empty string")
        
        try:
            self.logger.error(message, **kwargs)
        except Exception as e:
            error_msg = f"Failed to log error message: {e}"
            raise LoggingError(error_msg, self.component_name, "error")
    
    def critical(self, message: str, **kwargs) -> None:
        """
        Log critical message.
        
        Args:
            message (str): Critical message to log.
                Must be non-empty string.
            **kwargs: Additional logging parameters.
                Can include exc_info, extra, etc.
        
        Raises:
            LoggingError: If logging fails
        """
        if not message or not isinstance(message, str):
            raise ValueError("message must be non-empty string")
        
        try:
            self.logger.critical(message, **kwargs)
        except Exception as e:
            error_msg = f"Failed to log critical message: {e}"
            raise LoggingError(error_msg, self.component_name, "critical")
    
    def log_operation(self, operation: str, details: Dict[str, Any], level: str = "INFO") -> None:
        """
        Log operation with structured details.
        
        Args:
            operation (str): Name of the operation being logged.
                Must be non-empty string.
            details (Dict[str, Any]): Operation details to log.
                Can contain any structured data.
            level (str, optional): Logging level for the operation.
                Defaults to "INFO". Valid values: DEBUG, INFO, WARNING, ERROR, CRITICAL.
        
        Raises:
            LoggingError: If logging fails
            ValueError: If level is invalid
        """
        if not operation or not isinstance(operation, str):
            raise ValueError("operation must be non-empty string")
        
        if not isinstance(details, dict):
            raise ValueError("details must be dictionary")
        
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if level not in valid_levels:
            raise ValueError(f"Invalid level: {level}. Must be one of {valid_levels}")
        
        try:
            # Create structured log message
            log_message = f"Operation: {operation} | Details: {json.dumps(details, default=str)}"
            
            # Log with appropriate level
            log_method = getattr(self.logger, level.lower())
            log_method(log_message)
            
        except Exception as e:
            error_msg = f"Failed to log operation: {e}"
            raise LoggingError(error_msg, self.component_name, "log_operation")


class LoggingError(Exception):
    """
    Logging Error - Exception for logging operations.
    
    Raised when logging operations fail, such as when trying to
    write to a log file that cannot be accessed or when logging
    configuration is invalid.
    
    Attributes:
        message (str): Error message describing the logging failure
        component (Optional[str]): Component where the error occurred
        operation (Optional[str]): Operation that failed
    """
    
    def __init__(self, message: str, component: Optional[str] = None, operation: Optional[str] = None):
        """
        Initialize LoggingError instance.
        
        Args:
            message (str): Error message describing the logging failure
            component (Optional[str]): Component where the error occurred
            operation (Optional[str]): Operation that failed
        """
        super().__init__(message)
        self.message = message
        self.component = component
        self.operation = operation


class LoggingConfigError(Exception):
    """
    Logging Configuration Error - Exception for logging configuration.
    
    Raised when logging configuration operations fail, such as when
    trying to load invalid configuration or when required settings
    are missing.
    
    Attributes:
        message (str): Error message describing the configuration failure
        config_key (Optional[str]): Configuration key that caused the error
        value (Optional[Any]): Invalid value that caused the error
    """
    
    def __init__(self, message: str, config_key: Optional[str] = None, value: Optional[Any] = None):
        """
        Initialize LoggingConfigError instance.
        
        Args:
            message (str): Error message describing the configuration failure
            config_key (Optional[str]): Configuration key that caused the error
            value (Optional[Any]): Invalid value that caused the error
        """
        super().__init__(message)
        self.message = message
        self.config_key = config_key
        self.value = value 