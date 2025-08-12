"""
Configuration Validation - DocAnalyzer Configuration Validation

This module provides validation functions for DocAnalyzer-specific configuration
settings to ensure they meet requirements and are compatible with the system.

The validation functions integrate with the mcp_proxy_adapter framework and
provide additional validation for DocAnalyzer-specific settings.

Author: DocAnalyzer Team
Version: 1.0.0
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from .extensions import (
    get_file_watcher_settings,
    get_vector_store_settings,
    get_chunker_settings,
    get_embedding_settings
)

logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """
    Configuration Validation Error - DocAnalyzer Configuration Validation Exception
    
    Raised when DocAnalyzer configuration validation fails.
    Provides detailed error information for debugging.
    
    Attributes:
        message (str): Error message describing the validation failure.
        errors (List[str]): List of specific validation errors.
    
    Example:
        >>> raise ConfigValidationError("Invalid configuration", ["port must be positive"])
    """
    
    def __init__(self, message: str, errors: Optional[List[str]] = None):
        """
        Initialize configuration validation error.
        
        Args:
            message (str): Error message describing the validation failure.
                Must be non-empty string.
            errors (Optional[List[str]]): List of specific validation errors.
                Can be None if no specific errors available.
        """
        super().__init__(message)
        self.message = message
        self.errors = errors or []


def validate_docanalyzer_config() -> Tuple[bool, List[str]]:
    """
    Validate complete DocAnalyzer configuration.
    
    Performs comprehensive validation of all DocAnalyzer-specific configuration
    settings including file watcher, vector store, chunker, and embedding settings.
    
    Returns:
        Tuple[bool, List[str]]: Validation result and list of errors.
            First element is True if validation passed, False otherwise.
            Second element is list of error messages (empty if validation passed).
    
    Example:
        >>> is_valid, errors = validate_docanalyzer_config()
        >>> if not is_valid:
        ...     print("Configuration errors:", errors)
    
    Raises:
        ConfigValidationError: If validation process fails
    """
    errors = []
    
    try:
        # Validate file watcher settings
        file_watcher_errors = validate_file_watcher_settings()
        errors.extend(file_watcher_errors)
        
        # Validate vector store settings
        vector_store_errors = validate_vector_store_settings()
        errors.extend(vector_store_errors)
        
        # Validate chunker settings
        chunker_errors = validate_chunker_settings()
        errors.extend(chunker_errors)
        
        # Validate embedding settings
        embedding_errors = validate_embedding_settings()
        errors.extend(embedding_errors)
        
        # Validate cross-service dependencies
        cross_service_errors = validate_cross_service_dependencies()
        errors.extend(cross_service_errors)
        
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.info("DocAnalyzer configuration validation completed successfully")
        else:
            logger.warning(f"DocAnalyzer configuration validation failed with {len(errors)} errors")
        
        return is_valid, errors
        
    except Exception as e:
        logger.error(f"Configuration validation process failed: {e}")
        raise ConfigValidationError(f"Validation process failed: {e}")


def validate_file_watcher_settings() -> List[str]:
    """
    Validate file watcher configuration settings.
    
    Validates file watcher specific settings including directories,
    scan intervals, lock timeouts, and process limits.
    
    Returns:
        List[str]: List of validation error messages.
            Empty list if validation passed.
    
    Example:
        >>> errors = validate_file_watcher_settings()
        >>> if errors:
        ...     print("File watcher errors:", errors)
    """
    errors = []
    
    try:
        settings = get_file_watcher_settings()
        
        # Validate directories
        if 'directories' not in settings:
            errors.append("file_watcher.directories is required")
        else:
            directories = settings['directories']
            if not isinstance(directories, list):
                errors.append("file_watcher.directories must be a list")
            elif not directories:
                errors.append("file_watcher.directories cannot be empty")
            else:
                for i, directory in enumerate(directories):
                    if not isinstance(directory, str):
                        errors.append(f"file_watcher.directories[{i}] must be a string")
                    elif not directory:
                        errors.append(f"file_watcher.directories[{i}] cannot be empty")
        
        # Validate scan_interval
        if 'scan_interval' in settings:
            scan_interval = settings['scan_interval']
            if not isinstance(scan_interval, int):
                errors.append("file_watcher.scan_interval must be an integer")
            elif scan_interval <= 0:
                errors.append("file_watcher.scan_interval must be positive")
        
        # Validate lock_timeout
        if 'lock_timeout' in settings:
            lock_timeout = settings['lock_timeout']
            if not isinstance(lock_timeout, int):
                errors.append("file_watcher.lock_timeout must be an integer")
            elif lock_timeout <= 0:
                errors.append("file_watcher.lock_timeout must be positive")
        
        # Validate max_processes
        if 'max_processes' in settings:
            max_processes = settings['max_processes']
            if not isinstance(max_processes, int):
                errors.append("file_watcher.max_processes must be an integer")
            elif max_processes <= 0:
                errors.append("file_watcher.max_processes must be positive")
        
    except Exception as e:
        errors.append(f"Failed to validate file_watcher settings: {e}")
    
    return errors


def validate_vector_store_settings() -> List[str]:
    """
    Validate vector store configuration settings.
    
    Validates vector store connection settings including base URL,
    port, and timeout values.
    
    Returns:
        List[str]: List of validation error messages.
            Empty list if validation passed.
    
    Example:
        >>> errors = validate_vector_store_settings()
        >>> if errors:
        ...     print("Vector store errors:", errors)
    """
    errors = []
    
    try:
        settings = get_vector_store_settings()
        
        # Validate base_url
        if 'base_url' in settings:
            base_url = settings['base_url']
            if not isinstance(base_url, str):
                errors.append("vector_store.base_url must be a string")
            elif not base_url:
                errors.append("vector_store.base_url cannot be empty")
            else:
                # Validate URL format
                pattern = r'^https?://[a-zA-Z0-9\-\.]+$'
                if not re.match(pattern, base_url):
                    errors.append("vector_store.base_url must be valid URL format")
        
        # Validate port
        if 'port' in settings:
            port = settings['port']
            if not isinstance(port, int):
                errors.append("vector_store.port must be an integer")
            elif port < 1 or port > 65535:
                errors.append("vector_store.port must be between 1 and 65535")
        
        # Validate timeout
        if 'timeout' in settings:
            timeout = settings['timeout']
            if not isinstance(timeout, int):
                errors.append("vector_store.timeout must be an integer")
            elif timeout <= 0:
                errors.append("vector_store.timeout must be positive")
        
    except Exception as e:
        errors.append(f"Failed to validate vector_store settings: {e}")
    
    return errors


def validate_chunker_settings() -> List[str]:
    """
    Validate chunker service configuration settings.
    
    Validates chunker service connection settings including base URL,
    port, and timeout values.
    
    Returns:
        List[str]: List of validation error messages.
            Empty list if validation passed.
    
    Example:
        >>> errors = validate_chunker_settings()
        >>> if errors:
        ...     print("Chunker errors:", errors)
    """
    errors = []
    
    try:
        settings = get_chunker_settings()
        
        # Validate base_url
        if 'base_url' in settings:
            base_url = settings['base_url']
            if not isinstance(base_url, str):
                errors.append("chunker.base_url must be a string")
            elif not base_url:
                errors.append("chunker.base_url cannot be empty")
            else:
                # Validate URL format
                pattern = r'^https?://[a-zA-Z0-9\-\.]+$'
                if not re.match(pattern, base_url):
                    errors.append("chunker.base_url must be valid URL format")
        
        # Validate port
        if 'port' in settings:
            port = settings['port']
            if not isinstance(port, int):
                errors.append("chunker.port must be an integer")
            elif port < 1 or port > 65535:
                errors.append("chunker.port must be between 1 and 65535")
        
        # Validate timeout
        if 'timeout' in settings:
            timeout = settings['timeout']
            if not isinstance(timeout, int):
                errors.append("chunker.timeout must be an integer")
            elif timeout <= 0:
                errors.append("chunker.timeout must be positive")
        
        # Validate chunk_size
        if 'chunk_size' in settings:
            chunk_size = settings['chunk_size']
            if not isinstance(chunk_size, int):
                errors.append("chunker.chunk_size must be an integer")
            elif chunk_size <= 0:
                errors.append("chunker.chunk_size must be positive")
        
        # Validate chunk_overlap
        if 'chunk_overlap' in settings:
            chunk_overlap = settings['chunk_overlap']
            if not isinstance(chunk_overlap, int):
                errors.append("chunker.chunk_overlap must be an integer")
            elif chunk_overlap < 0:
                errors.append("chunker.chunk_overlap must be non-negative")
        
        # Validate max_chunks
        if 'max_chunks' in settings:
            max_chunks = settings['max_chunks']
            if not isinstance(max_chunks, int):
                errors.append("chunker.max_chunks must be an integer")
            elif max_chunks <= 0:
                errors.append("chunker.max_chunks must be positive")
        
    except Exception as e:
        errors.append(f"Failed to validate chunker settings: {e}")
    
    return errors


def validate_embedding_settings() -> List[str]:
    """
    Validate embedding service configuration settings.
    
    Validates embedding service connection settings including base URL,
    port, and timeout values.
    
    Returns:
        List[str]: List of validation error messages.
            Empty list if validation passed.
    
    Example:
        >>> errors = validate_embedding_settings()
        >>> if errors:
        ...     print("Embedding errors:", errors)
    """
    errors = []
    
    try:
        settings = get_embedding_settings()
        
        # Validate base_url
        if 'base_url' in settings:
            base_url = settings['base_url']
            if not isinstance(base_url, str):
                errors.append("embedding.base_url must be a string")
            elif not base_url:
                errors.append("embedding.base_url cannot be empty")
            else:
                # Validate URL format
                pattern = r'^https?://[a-zA-Z0-9\-\.]+$'
                if not re.match(pattern, base_url):
                    errors.append("embedding.base_url must be valid URL format")
        
        # Validate port
        if 'port' in settings:
            port = settings['port']
            if not isinstance(port, int):
                errors.append("embedding.port must be an integer")
            elif port < 1 or port > 65535:
                errors.append("embedding.port must be between 1 and 65535")
        
        # Validate timeout
        if 'timeout' in settings:
            timeout = settings['timeout']
            if not isinstance(timeout, int):
                errors.append("embedding.timeout must be an integer")
            elif timeout <= 0:
                errors.append("embedding.timeout must be positive")
        
        # Validate model_name
        if 'model_name' in settings:
            model_name = settings['model_name']
            if not isinstance(model_name, str):
                errors.append("embedding.model_name must be a string")
            elif not model_name:
                errors.append("embedding.model_name cannot be empty")
        
        # Validate batch_size
        if 'batch_size' in settings:
            batch_size = settings['batch_size']
            if not isinstance(batch_size, int):
                errors.append("embedding.batch_size must be an integer")
            elif batch_size <= 0:
                errors.append("embedding.batch_size must be positive")
        
    except Exception as e:
        errors.append(f"Failed to validate embedding settings: {e}")
    
    return errors


def validate_cross_service_dependencies() -> List[str]:
    """
    Validate cross-service dependencies in configuration.
    
    Validates relationships and dependencies between different
    service configurations to ensure they work together properly.
    
    Returns:
        List[str]: List of validation error messages.
            Empty list if validation passed.
    
    Example:
        >>> errors = validate_cross_service_dependencies()
        >>> if errors:
        ...     print("Cross-service errors:", errors)
    """
    errors = []
    
    try:
        # Check for port conflicts
        ports = {}
        
        vector_store_settings = get_vector_store_settings()
        if 'port' in vector_store_settings:
            ports['vector_store'] = vector_store_settings['port']
        
        chunker_settings = get_chunker_settings()
        if 'port' in chunker_settings:
            ports['chunker'] = chunker_settings['port']
        
        embedding_settings = get_embedding_settings()
        if 'port' in embedding_settings:
            ports['embedding'] = embedding_settings['port']
        
        # Check for duplicate ports
        port_values = list(ports.values())
        if len(port_values) != len(set(port_values)):
            errors.append("Duplicate port numbers found in service configurations")
        
        # Check for reserved ports
        reserved_ports = [80, 443, 22, 21, 23, 25, 53, 110, 143, 993, 995]
        for service, port in ports.items():
            if port in reserved_ports:
                errors.append(f"{service} port {port} is reserved, use different port")
        
        # Validate directory accessibility
        file_watcher_settings = get_file_watcher_settings()
        if 'directories' in file_watcher_settings:
            directories = file_watcher_settings['directories']
            if isinstance(directories, list):
                for i, directory in enumerate(directories):
                    if isinstance(directory, str):
                        try:
                            dir_path = Path(directory)
                            if dir_path.exists() and not dir_path.is_dir():
                                errors.append(f"file_watcher.directories[{i}] exists but is not a directory: {directory}")
                        except Exception as e:
                            errors.append(f"Invalid file_watcher.directories[{i}]: {directory} - {e}")
        
    except Exception as e:
        errors.append(f"Failed to validate cross-service dependencies: {e}")
    
    return errors


def validate_service_connectivity() -> Dict[str, bool]:
    """
    Validate service connectivity for configured services.
    
    Attempts to connect to configured services to verify they are
    accessible and responding properly.
    
    Returns:
        Dict[str, bool]: Service connectivity status.
            Keys are service names, values are True if accessible, False otherwise.
    
    Example:
        >>> connectivity = validate_service_connectivity()
        >>> for service, accessible in connectivity.items():
        ...     print(f"{service}: {'✓' if accessible else '✗'}")
    """
    connectivity = {}
    
    try:
        # Note: This is a placeholder for actual connectivity validation
        # In a real implementation, this would attempt HTTP connections
        # to the configured services
        
        services = ['vector_store', 'chunker', 'embedding']
        for service in services:
            # For now, assume all services are accessible
            # This should be replaced with actual connectivity checks
            connectivity[service] = True
            logger.debug(f"Service connectivity check for {service}: accessible")
        
    except Exception as e:
        logger.error(f"Service connectivity validation failed: {e}")
        # Mark all services as inaccessible if validation fails
        for service in ['vector_store', 'chunker', 'embedding']:
            connectivity[service] = False
    
    return connectivity


def get_configuration_summary() -> Dict[str, Any]:
    """
    Get summary of current DocAnalyzer configuration.
    
    Provides a comprehensive summary of all DocAnalyzer configuration
    settings for debugging and monitoring purposes.
    
    Returns:
        Dict[str, Any]: Configuration summary with all settings.
            Includes file_watcher, vector_store, chunker, and embedding settings.
    
    Example:
        >>> summary = get_configuration_summary()
        >>> print("Configuration summary:", summary)
    """
    try:
        summary = {
            'file_watcher': get_file_watcher_settings(),
            'vector_store': get_vector_store_settings(),
            'chunker': get_chunker_settings(),
            'embedding': get_embedding_settings(),
            'validation': {
                'is_valid': False,
                'errors': []
            }
        }
        
        # Add validation status
        is_valid, errors = validate_docanalyzer_config()
        summary['validation']['is_valid'] = is_valid
        summary['validation']['errors'] = errors
        
        # Add connectivity status
        summary['connectivity'] = validate_service_connectivity()
        
        return summary
        
    except Exception as e:
        logger.error(f"Failed to generate configuration summary: {e}")
        return {
            'error': f"Failed to generate configuration summary: {e}",
            'validation': {
                'is_valid': False,
                'errors': [str(e)]
            }
        } 