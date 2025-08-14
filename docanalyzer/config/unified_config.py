"""
Unified Configuration - DocAnalyzer Unified Configuration System

This module provides a unified configuration system that combines
DocAnalyzer-specific settings with the mcp_proxy_adapter framework
configuration into a single, coherent interface.

The unified configuration eliminates duplication and provides
a single source of truth for all configuration settings.

Author: DocAnalyzer Team
Version: 1.0.0
"""

import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field

from mcp_proxy_adapter.core.settings import Settings, get_setting, get_custom_setting_value
from mcp_proxy_adapter.config import config as framework_config

logger = logging.getLogger(__name__)


@dataclass
class ServerConfig:
    """
    Server Configuration - Unified Server Settings
    
    Contains all server-related configuration settings including
    host, port, debug mode, and other server-specific options.
    
    Attributes:
        host (str): Server host address. Defaults to "0.0.0.0".
        port (int): Server port number. Must be between 1 and 65535.
            Defaults to 8015.
        debug (bool): Enable debug mode. Defaults to False.
        log_level (str): Logging level. Must be one of: DEBUG, INFO, WARNING, ERROR.
            Defaults to "INFO".
    """
    host: str = "0.0.0.0"
    port: int = 8015
    debug: bool = False
    log_level: str = "INFO"


@dataclass
class LoggingConfig:
    """
    Logging Configuration - Unified Logging Settings
    
    Contains all logging-related configuration settings including
    log levels, file paths, and formatting options.
    
    Attributes:
        level (str): Logging level. Must be one of: DEBUG, INFO, WARNING, ERROR.
            Defaults to "INFO".
        log_dir (str): Directory for log files. Defaults to "./logs/docanalyzer".
        log_file (str): Main log file name. Defaults to "docanalyzer.log".
        error_log_file (str): Error log file name. Defaults to "docanalyzer_error.log".
        access_log_file (str): Access log file name. Defaults to "docanalyzer_access.log".
        file_processing_log (str): File processing log file name. Defaults to "file_processing.log".
        max_file_size (str): Maximum log file size. Defaults to "10MB".
        backup_count (int): Number of backup log files. Must be positive.
            Defaults to 5.
        format (str): Log message format. Defaults to standard format.
        date_format (str): Date format for log messages. Defaults to standard format.
        console_output (bool): Enable console output. Defaults to True.
        file_output (bool): Enable file output. Defaults to True.
    """
    level: str = "INFO"
    log_dir: str = "./logs/docanalyzer"
    log_file: str = "docanalyzer.log"
    error_log_file: str = "docanalyzer_error.log"
    access_log_file: str = "docanalyzer_access.log"
    file_processing_log: str = "file_processing.log"
    max_file_size: str = "10MB"
    backup_count: int = 5
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    console_output: bool = True
    file_output: bool = True


@dataclass
class CommandsConfig:
    """
    Commands Configuration - Unified Commands Settings
    
    Contains all command-related configuration settings including
    auto-discovery and custom command paths.
    
    Attributes:
        auto_discovery (bool): Enable automatic command discovery.
            Defaults to True.
        discovery_path (str): Path for command discovery.
            Defaults to "docanalyzer.commands".
        custom_commands_path (Optional[str]): Path for custom commands.
            Can be None if no custom commands. Defaults to None.
    """
    auto_discovery: bool = True
    discovery_path: str = "docanalyzer.commands"
    custom_commands_path: Optional[str] = None


@dataclass
class FileWatcherConfig:
    """
    File Watcher Configuration - Unified File Watcher Settings
    
    Contains all file watcher related configuration settings including
    directories to monitor, scan intervals, and process limits.
    
    Attributes:
        directories (List[str]): List of directories to monitor.
            Defaults to ["./documents", "./docs"].
        scan_interval (int): Interval between scans in seconds.
            Must be positive integer. Defaults to 300.
        lock_timeout (int): Lock timeout in seconds.
            Must be positive integer. Defaults to 3600.
        max_processes (int): Maximum number of concurrent processes.
            Must be positive integer. Defaults to 5.
    """
    directories: list[str] = field(default_factory=lambda: ["./documents", "./docs"])
    scan_interval: int = 300
    lock_timeout: int = 3600
    max_processes: int = 5


@dataclass
class VectorStoreConfig:
    """
    Vector Store Configuration - Unified Vector Store Settings
    
    Contains all vector store related configuration settings including
    connection details and timeouts.
    
    Attributes:
        base_url (str): Vector store base URL. Defaults to "http://localhost".
        port (int): Vector store port number. Must be between 1 and 65535.
            Defaults to 8007.
        timeout (int): Request timeout in seconds. Must be positive integer.
            Defaults to 30.
    """
    base_url: str = "http://localhost"
    port: int = 8007
    timeout: int = 30


@dataclass
class ChunkerConfig:
    """
    Chunker Configuration - Unified Chunker Settings
    
    Contains all chunker related configuration settings including
    connection details and timeouts.
    
    Attributes:
        base_url (str): Chunker base URL. Defaults to "http://localhost".
        port (int): Chunker port number. Must be between 1 and 65535.
            Defaults to 8009.
        timeout (int): Request timeout in seconds. Must be positive integer.
            Defaults to 30.
    """
    base_url: str = "http://localhost"
    port: int = 8009
    timeout: int = 30


@dataclass
class EmbeddingConfig:
    """
    Embedding Configuration - Unified Embedding Settings
    
    Contains all embedding related configuration settings including
    connection details and timeouts.
    
    Attributes:
        base_url (str): Embedding service base URL. Defaults to "http://localhost".
        port (int): Embedding service port number. Must be between 1 and 65535.
            Defaults to 8001.
        timeout (int): Request timeout in seconds. Must be positive integer.
            Defaults to 30.
    """
    base_url: str = "http://localhost"
    port: int = 8001
    timeout: int = 30


class UnifiedConfig:
    """
    Unified Configuration - Single Source of Truth for All Settings
    
    Main configuration class that unifies DocAnalyzer-specific settings
    with the mcp_proxy_adapter framework configuration.
    
    This class provides a single interface for accessing all configuration
    settings while maintaining compatibility with existing infrastructure.
    
    Attributes:
        server (ServerConfig): Server configuration settings.
        logging (LoggingConfig): Logging configuration settings.
        commands (CommandsConfig): Commands configuration settings.
        file_watcher (FileWatcherConfig): File watcher configuration settings.
        vector_store (VectorStoreConfig): Vector store configuration settings.
        chunker (ChunkerConfig): Chunker configuration settings.
        embedding (EmbeddingConfig): Embedding configuration settings.
        framework_config: Reference to the mcp_proxy_adapter configuration.
            Provides access to all framework settings.
    
    Example:
        >>> config = UnifiedConfig()
        >>> server_host = config.server.host
        >>> vector_store_url = f"{config.vector_store.base_url}:{config.vector_store.port}"
        >>> file_watcher_dirs = config.file_watcher.directories
    
    Raises:
        ConfigError: If configuration cannot be loaded
        ValidationError: If configuration is invalid
    """
    
    def __init__(self):
        """
        Initialize unified configuration.
        
        Loads all configuration settings from the framework configuration
        and creates unified configuration objects.
        
        Raises:
            ConfigError: If configuration cannot be loaded
            ValidationError: If configuration is invalid
        """
        self.framework_config = framework_config
        self._load_all_configurations()
        logger.info("Unified configuration initialized successfully")
    
    def _load_all_configurations(self) -> None:
        """
        Load all configuration sections.
        
        Loads server, logging, commands, and DocAnalyzer-specific
        configuration settings from the framework configuration.
        
        Raises:
            ConfigError: If configuration cannot be loaded
        """
        try:
            # Load framework configuration sections
            self.server = self._load_server_config()
            self.logging = self._load_logging_config()
            self.commands = self._load_commands_config()
            
            # Load DocAnalyzer-specific configuration sections
            self.file_watcher = self._load_file_watcher_config()
            self.vector_store = self._load_vector_store_config()
            self.chunker = self._load_chunker_config()
            self.embedding = self._load_embedding_config()
            
            logger.info("All configuration sections loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise ConfigError(f"Configuration loading failed: {e}")
    
    def _load_server_config(self) -> ServerConfig:
        """
        Load server configuration from framework settings.
        
        Returns:
            ServerConfig: Server configuration object.
        """
        server_settings = Settings.get_server_settings()
        return ServerConfig(
            host=server_settings.get('host', '0.0.0.0'),
            port=server_settings.get('port', 8015),
            debug=server_settings.get('debug', False),
            log_level=server_settings.get('log_level', 'INFO')
        )
    
    def _load_logging_config(self) -> LoggingConfig:
        """
        Load logging configuration from framework settings.
        
        Returns:
            LoggingConfig: Logging configuration object.
        """
        logging_settings = Settings.get_logging_settings()
        return LoggingConfig(
            level=logging_settings.get('level', 'INFO'),
            log_dir=logging_settings.get('log_dir', './logs/docanalyzer'),
            log_file=logging_settings.get('log_file', 'docanalyzer.log'),
            error_log_file=logging_settings.get('error_log_file', 'docanalyzer_error.log'),
            access_log_file=logging_settings.get('access_log_file', 'docanalyzer_access.log'),
            file_processing_log=logging_settings.get('file_processing_log', 'file_processing.log'),
            max_file_size=logging_settings.get('max_file_size', '10MB'),
            backup_count=logging_settings.get('backup_count', 5),
            format=logging_settings.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            date_format=logging_settings.get('date_format', '%Y-%m-%d %H:%M:%S'),
            console_output=logging_settings.get('console_output', True),
            file_output=logging_settings.get('file_output', True)
        )
    
    def _load_commands_config(self) -> CommandsConfig:
        """
        Load commands configuration from framework settings.
        
        Returns:
            CommandsConfig: Commands configuration object.
        """
        commands_settings = Settings.get_commands_settings()
        return CommandsConfig(
            auto_discovery=commands_settings.get('auto_discovery', True),
            discovery_path=commands_settings.get('discovery_path', 'docanalyzer.commands'),
            custom_commands_path=commands_settings.get('custom_commands_path')
        )
    
    def _load_file_watcher_config(self) -> FileWatcherConfig:
        """
        Load file watcher configuration from framework settings.
        
        Returns:
            FileWatcherConfig: File watcher configuration object.
        """
        file_watcher_settings = get_custom_setting_value('file_watcher', {})
        return FileWatcherConfig(
            directories=file_watcher_settings.get('directories', ["./documents", "./docs"]),
            scan_interval=file_watcher_settings.get('scan_interval', 300),
            lock_timeout=file_watcher_settings.get('lock_timeout', 3600),
            max_processes=file_watcher_settings.get('max_processes', 5)
        )
    
    def _load_vector_store_config(self) -> VectorStoreConfig:
        """
        Load vector store configuration from framework settings.
        
        Returns:
            VectorStoreConfig: Vector store configuration object.
        """
        vector_store_settings = get_custom_setting_value('vector_store', {})
        return VectorStoreConfig(
            base_url=vector_store_settings.get('base_url', 'http://localhost'),
            port=vector_store_settings.get('port', 8007),
            timeout=vector_store_settings.get('timeout', 30)
        )
    
    def _load_chunker_config(self) -> ChunkerConfig:
        """
        Load chunker configuration from framework settings.
        
        Returns:
            ChunkerConfig: Chunker configuration object.
        """
        chunker_settings = get_custom_setting_value('chunker', {})
        return ChunkerConfig(
            base_url=chunker_settings.get('base_url', 'http://localhost'),
            port=chunker_settings.get('port', 8009),
            timeout=chunker_settings.get('timeout', 30)
        )
    
    def _load_embedding_config(self) -> EmbeddingConfig:
        """
        Load embedding configuration from framework settings.
        
        Returns:
            EmbeddingConfig: Embedding configuration object.
        """
        embedding_settings = get_custom_setting_value('embedding', {})
        return EmbeddingConfig(
            base_url=embedding_settings.get('base_url', 'http://localhost'),
            port=embedding_settings.get('port', 8001),
            timeout=embedding_settings.get('timeout', 30)
        )
    
    def reload_configuration(self) -> None:
        """
        Reload all configuration settings.
        
        Reloads all configuration sections from the framework configuration
        and updates the unified configuration objects.
        
        Raises:
            ConfigError: If configuration reload fails
        """
        try:
            logger.info("Reloading unified configuration...")
            self._load_all_configurations()
            logger.info("Configuration reloaded successfully")
        except Exception as e:
            logger.error(f"Configuration reload failed: {e}")
            raise ConfigError(f"Configuration reload failed: {e}")
    
    def validate_configuration(self) -> bool:
        """
        Validate current configuration.
        
        Performs comprehensive validation of all configuration settings
        to ensure they meet requirements and are compatible.
        
        Returns:
            bool: True if configuration is valid, False otherwise.
        
        Raises:
            ValidationError: If configuration validation fails
        """
        errors = []
        
        # Validate server configuration
        if not (1 <= self.server.port <= 65535):
            errors.append(f"Server port must be between 1 and 65535, got {self.server.port}")
        
        if self.server.log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
            errors.append(f"Invalid log level: {self.server.log_level}")
        
        # Validate logging configuration
        if self.logging.level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
            errors.append(f"Invalid logging level: {self.logging.level}")
        
        if self.logging.backup_count <= 0:
            errors.append("Backup count must be positive")
        
        # Validate file watcher configuration
        if self.file_watcher.scan_interval <= 0:
            errors.append("Scan interval must be positive")
        
        if self.file_watcher.lock_timeout <= 0:
            errors.append("Lock timeout must be positive")
        
        if self.file_watcher.max_processes <= 0:
            errors.append("Max processes must be positive")
        
        # Validate service configurations
        for service_name, service_config in [
            ('vector_store', self.vector_store),
            ('chunker', self.chunker),
            ('embedding', self.embedding)
        ]:
            if not (1 <= service_config.port <= 65535):
                errors.append(f"{service_name} port must be between 1 and 65535, got {service_config.port}")
            
            if service_config.timeout <= 0:
                errors.append(f"{service_name} timeout must be positive")
        
        if errors:
            logger.warning(f"Configuration validation failed with {len(errors)} errors")
            raise ValidationError("Configuration validation failed", errors)
        
        logger.info("Configuration validation completed successfully")
        return True
    
    def get_service_url(self, service_name: str) -> str:
        """
        Get service URL for specified service.
        
        Constructs the full URL for a service based on its configuration.
        
        Args:
            service_name (str): Name of the service (vector_store, chunker, embedding).
                Must be one of the supported service names.
        
        Returns:
            str: Full service URL including protocol, host, and port.
        
        Raises:
            ValueError: If service name is not supported
        """
        service_configs = {
            'vector_store': self.vector_store,
            'chunker': self.chunker,
            'embedding': self.embedding
        }
        
        if service_name not in service_configs:
            raise ValueError(f"Unsupported service: {service_name}")
        
        config = service_configs[service_name]
        return f"{config.base_url}:{config.port}"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Converts all configuration sections to a dictionary format
        for serialization or debugging purposes.
        
        Returns:
            Dict[str, Any]: Configuration as dictionary.
        """
        return {
            'server': {
                'host': self.server.host,
                'port': self.server.port,
                'debug': self.server.debug,
                'log_level': self.server.log_level
            },
            'logging': {
                'level': self.logging.level,
                'log_dir': self.logging.log_dir,
                'log_file': self.logging.log_file,
                'error_log_file': self.logging.error_log_file,
                'access_log_file': self.logging.access_log_file,
                'file_processing_log': self.logging.file_processing_log,
                'max_file_size': self.logging.max_file_size,
                'backup_count': self.logging.backup_count,
                'format': self.logging.format,
                'date_format': self.logging.date_format,
                'console_output': self.logging.console_output,
                'file_output': self.logging.file_output
            },
            'commands': {
                'auto_discovery': self.commands.auto_discovery,
                'discovery_path': self.commands.discovery_path,
                'custom_commands_path': self.commands.custom_commands_path
            },
            'file_watcher': {
                'directories': self.file_watcher.directories,
                'scan_interval': self.file_watcher.scan_interval,
                'lock_timeout': self.file_watcher.lock_timeout,
                'max_processes': self.file_watcher.max_processes
            },
            'vector_store': {
                'base_url': self.vector_store.base_url,
                'port': self.vector_store.port,
                'timeout': self.vector_store.timeout
            },
            'chunker': {
                'base_url': self.chunker.base_url,
                'port': self.chunker.port,
                'timeout': self.chunker.timeout
            },
            'embedding': {
                'base_url': self.embedding.base_url,
                'port': self.embedding.port,
                'timeout': self.embedding.timeout
            }
        }


class ConfigError(Exception):
    """
    Configuration Error - Unified Configuration Exception
    
    Raised when unified configuration operations fail.
    Provides detailed error information for debugging.
    
    Attributes:
        message (str): Error message describing the failure.
    
    Example:
        >>> raise ConfigError("Configuration loading failed")
    """
    
    def __init__(self, message: str):
        """
        Initialize configuration error.
        
        Args:
            message (str): Error message describing the failure.
                Must be non-empty string.
        """
        super().__init__(message)
        self.message = message


class ValidationError(Exception):
    """
    Validation Error - Configuration Validation Exception
    
    Raised when configuration validation fails.
    Provides detailed error information and list of validation errors.
    
    Attributes:
        message (str): Error message describing the validation failure.
        errors (List[str]): List of specific validation errors.
    
    Example:
        >>> raise ValidationError("Configuration validation failed", ["port must be positive"])
    """
    
    def __init__(self, message: str, errors: Optional[list[str]] = None):
        """
        Initialize validation error.
        
        Args:
            message (str): Error message describing the validation failure.
                Must be non-empty string.
            errors (Optional[List[str]]): List of specific validation errors.
                Can be None if no specific errors available.
        """
        super().__init__(message)
        self.message = message
        self.errors = errors or []


# Global configuration instance
_unified_config: Optional[UnifiedConfig] = None


def get_unified_config() -> UnifiedConfig:
    """
    Get global unified configuration instance.
    
    Returns a singleton instance of the unified configuration.
    Creates the instance if it doesn't exist.
    
    Returns:
        UnifiedConfig: Global unified configuration instance.
    
    Raises:
        ConfigError: If configuration cannot be created
    """
    global _unified_config
    
    if _unified_config is None:
        _unified_config = UnifiedConfig()
    
    return _unified_config


def reload_unified_config() -> None:
    """
    Reload global unified configuration.
    
    Reloads the global unified configuration instance.
    Useful for updating configuration during runtime.
    
    Raises:
        ConfigError: If configuration reload fails
    """
    global _unified_config
    
    if _unified_config is not None:
        _unified_config.reload_configuration()
    else:
        _unified_config = UnifiedConfig() 