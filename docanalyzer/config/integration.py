"""
Configuration Integration - Integration with mcp_proxy_adapter Framework

This module provides integration layer between DocAnalyzer and the
mcp_proxy_adapter framework's configuration system.

It extends the framework's configuration capabilities with DocAnalyzer-specific
settings while maintaining compatibility with the existing infrastructure.

Author: DocAnalyzer Team
Version: 1.0.0
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

from mcp_proxy_adapter.core.settings import Settings, get_setting, get_custom_setting_value
from mcp_proxy_adapter.config import config as framework_config

logger = logging.getLogger(__name__)

# DocAnalyzer-specific configuration keys
DOCANALYZER_CONFIG_KEYS = {
    'file_watcher': 'file_watcher',
    'vector_store': 'vector_store', 
    'chunker': 'chunker',
    'embedding': 'embedding'
}


class DocAnalyzerConfig:
    """
    DocAnalyzer Configuration - Integration with mcp_proxy_adapter Framework
    
    Main configuration class that integrates with the mcp_proxy_adapter framework
    and provides access to DocAnalyzer-specific settings.
    
    This class extends the framework's configuration capabilities while
    maintaining full compatibility with existing infrastructure.
    
    Attributes:
        framework_config: Reference to the mcp_proxy_adapter configuration.
            Provides access to all framework settings.
        docanalyzer_settings: DocAnalyzer-specific settings dictionary.
            Contains file_watcher, vector_store, chunker, and embedding settings.
    
    Example:
        >>> docanalyzer_config = DocAnalyzerConfig()
        >>> file_watcher_settings = docanalyzer_config.get_file_watcher_settings()
        >>> vector_store_settings = docanalyzer_config.get_vector_store_settings()
    
    Raises:
        ConfigError: If DocAnalyzer configuration cannot be loaded
        ValidationError: If DocAnalyzer configuration is invalid
    """
    
    def __init__(self):
        """
        Initialize DocAnalyzer configuration integration.
        
        Loads DocAnalyzer-specific settings from the framework configuration
        and validates them for compatibility.
        
        Raises:
            ConfigError: If configuration cannot be loaded
            ValidationError: If configuration is invalid
        """
        self.framework_config = framework_config
        self.docanalyzer_settings = self._load_docanalyzer_settings()
        logger.info("DocAnalyzer configuration integration initialized")
    
    def _load_docanalyzer_settings(self) -> Dict[str, Any]:
        """
        Load DocAnalyzer-specific settings from framework configuration.
        
        Extracts DocAnalyzer settings from the framework's configuration
        and provides default values for missing settings.
        
        Returns:
            Dict[str, Any]: DocAnalyzer-specific settings dictionary.
                Contains all required configuration sections.
        
        Raises:
            ConfigError: If required settings cannot be loaded
        """
        try:
            settings = {}
            
            # Load each DocAnalyzer configuration section
            for key, config_key in DOCANALYZER_CONFIG_KEYS.items():
                section_settings = get_custom_setting_value(config_key, {})
                if section_settings:
                    settings[key] = section_settings
                    logger.debug(f"Loaded {key} settings from framework configuration")
                else:
                    logger.warning(f"No {key} settings found in framework configuration, using defaults")
                    settings[key] = self._get_default_settings(key)
            
            logger.info("DocAnalyzer settings loaded successfully")
            return settings
            
        except Exception as e:
            logger.error(f"Failed to load DocAnalyzer settings: {e}")
            raise ConfigError(f"Configuration loading failed: {e}")
    
    def _get_default_settings(self, section: str) -> Dict[str, Any]:
        """
        Get default settings for a configuration section.
        
        Args:
            section (str): Configuration section name.
                Must be one of: file_watcher, vector_store, chunker, embedding.
        
        Returns:
            Dict[str, Any]: Default settings for the section.
                Provides safe default values.
        
        Raises:
            ValueError: If section is not supported
        """
        defaults = {
            'file_watcher': {
                'directories': ["./documents", "./docs"],
                'scan_interval': 300,
                'lock_timeout': 3600,
                'max_processes': 5
            },
            'vector_store': {
                'base_url': "http://localhost",
                'port': 8007,
                'timeout': 30
            },
            'chunker': {
                'base_url': "http://localhost",
                'port': 8009,
                'timeout': 30
            },
            'embedding': {
                'base_url': "http://localhost",
                'port': 8001,
                'timeout': 30
            }
        }
        
        if section not in defaults:
            raise ValueError(f"Unsupported configuration section: {section}")
        
        return defaults[section]
    
    def get_file_watcher_settings(self) -> Dict[str, Any]:
        """
        Get file watcher configuration settings.
        
        Returns file watcher specific settings including directories to monitor,
        scan intervals, lock timeouts, and process limits.
        
        Returns:
            Dict[str, Any]: File watcher settings.
                Contains directories, scan_interval, lock_timeout, max_processes.
        
        Raises:
            ConfigError: If file watcher settings are not available
        """
        if 'file_watcher' not in self.docanalyzer_settings:
            raise ConfigError("File watcher settings not found in configuration")
        
        return self.docanalyzer_settings['file_watcher']
    
    def get_vector_store_settings(self) -> Dict[str, Any]:
        """
        Get vector store configuration settings.
        
        Returns vector store connection settings including base URL,
        port, and timeout values.
        
        Returns:
            Dict[str, Any]: Vector store settings.
                Contains base_url, port, timeout.
        
        Raises:
            ConfigError: If vector store settings are not available
        """
        if 'vector_store' not in self.docanalyzer_settings:
            raise ConfigError("Vector store settings not found in configuration")
        
        return self.docanalyzer_settings['vector_store']
    
    def get_chunker_settings(self) -> Dict[str, Any]:
        """
        Get chunker service configuration settings.
        
        Returns chunker service connection settings including base URL,
        port, and timeout values.
        
        Returns:
            Dict[str, Any]: Chunker settings.
                Contains base_url, port, timeout.
        
        Raises:
            ConfigError: If chunker settings are not available
        """
        if 'chunker' not in self.docanalyzer_settings:
            raise ConfigError("Chunker settings not found in configuration")
        
        return self.docanalyzer_settings['chunker']
    
    def get_embedding_settings(self) -> Dict[str, Any]:
        """
        Get embedding service configuration settings.
        
        Returns embedding service connection settings including base URL,
        port, and timeout values.
        
        Returns:
            Dict[str, Any]: Embedding settings.
                Contains base_url, port, timeout.
        
        Raises:
            ConfigError: If embedding settings are not available
        """
        if 'embedding' not in self.docanalyzer_settings:
            raise ConfigError("Embedding settings not found in configuration")
        
        return self.docanalyzer_settings['embedding']
    
    def get_framework_settings(self) -> Dict[str, Any]:
        """
        Get framework configuration settings.
        
        Returns all framework-level settings including server, logging,
        and commands configuration.
        
        Returns:
            Dict[str, Any]: Framework settings.
                Contains server, logging, commands sections.
        """
        return {
            'server': {
                'host': get_setting('server.host'),
                'port': get_setting('server.port'),
                'debug': get_setting('server.debug'),
                'log_level': get_setting('server.log_level')
            },
            'logging': Settings.get_logging_settings(),
            'commands': Settings.get_commands_settings()
        }
    
    def reload_configuration(self) -> None:
        """
        Reload configuration from framework.
        
        Reloads all configuration settings from the framework and
        revalidates DocAnalyzer-specific settings.
        
        Raises:
            ConfigError: If configuration reload fails
        """
        try:
            # Reload framework configuration
            self.framework_config.reload()
            
            # Reload DocAnalyzer settings
            self.docanalyzer_settings = self._load_docanalyzer_settings()
            
            logger.info("Configuration reloaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            raise ConfigError(f"Configuration reload failed: {e}")
    
    def validate_configuration(self) -> bool:
        """
        Validate current configuration.
        
        Performs comprehensive validation of both framework and
        DocAnalyzer-specific configuration settings.
        
        Returns:
            bool: True if configuration is valid, False otherwise.
        
        Raises:
            ValidationError: If configuration validation fails
        """
        try:
            # Validate framework settings
            framework_settings = self.get_framework_settings()
            
            # Validate DocAnalyzer settings
            for section in DOCANALYZER_CONFIG_KEYS.keys():
                if section not in self.docanalyzer_settings:
                    raise ValidationError(f"Missing required configuration section: {section}")
            
            logger.info("Configuration validation completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise ValidationError(f"Configuration validation failed: {e}")


class ConfigError(Exception):
    """
    Configuration Error - DocAnalyzer Configuration Exception
    
    Raised when DocAnalyzer configuration operations fail.
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
    Provides detailed error information for debugging.
    
    Attributes:
        message (str): Error message describing the validation failure.
    
    Example:
        >>> raise ValidationError("Invalid configuration")
    """
    
    def __init__(self, message: str):
        """
        Initialize validation error.
        
        Args:
            message (str): Error message describing the validation failure.
                Must be non-empty string.
        """
        super().__init__(message)
        self.message = message 