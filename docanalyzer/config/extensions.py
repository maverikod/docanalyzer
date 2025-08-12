"""
Configuration Extensions - DocAnalyzer Configuration Extensions

This module provides extension functions for accessing DocAnalyzer-specific
configuration settings through the mcp_proxy_adapter framework.

These functions provide convenient access to DocAnalyzer settings while
maintaining integration with the existing framework infrastructure.

Author: DocAnalyzer Team
Version: 1.0.0
"""

import logging
from typing import Dict, Any, List, Optional

from mcp_proxy_adapter.core.settings import get_custom_setting_value

logger = logging.getLogger(__name__)


def get_file_watcher_settings() -> Dict[str, Any]:
    """
    Get file watcher configuration settings.
    
    Retrieves file watcher specific settings from the framework configuration
    including directories to monitor, scan intervals, lock timeouts, and process limits.
    
    Returns:
        Dict[str, Any]: File watcher settings with the following structure:
            - directories (List[str]): List of directories to monitor
            - scan_interval (int): Interval between scans in seconds
            - lock_timeout (int): Lock timeout in seconds
            - max_processes (int): Maximum number of concurrent processes
    
    Example:
        >>> settings = get_file_watcher_settings()
        >>> print(settings['directories'])  # ["./documents", "./docs"]
        >>> print(settings['scan_interval'])  # 300
    
    Raises:
        KeyError: If file_watcher settings are not found in configuration
    """
    settings = get_custom_setting_value('file_watcher', {})
    
    if not settings:
        logger.warning("No file_watcher settings found, using defaults")
        settings = {
            'directories': ["./documents", "./docs"],
            'scan_interval': 300,
            'lock_timeout': 3600,
            'max_processes': 5
        }
    
    logger.debug(f"Retrieved file_watcher settings: {settings}")
    return settings


def get_vector_store_settings() -> Dict[str, Any]:
    """
    Get vector store configuration settings.
    
    Retrieves vector store connection settings from the framework configuration
    including base URL, port, and timeout values.
    
    Returns:
        Dict[str, Any]: Vector store settings with the following structure:
            - base_url (str): Base URL for vector store service
            - port (int): Port number for vector store service
            - timeout (int): Request timeout in seconds
    
    Example:
        >>> settings = get_vector_store_settings()
        >>> print(settings['base_url'])  # "http://localhost"
        >>> print(settings['port'])  # 8007
    
    Raises:
        KeyError: If vector_store settings are not found in configuration
    """
    settings = get_custom_setting_value('vector_store', {})
    
    if not settings:
        logger.warning("No vector_store settings found, using defaults")
        settings = {
            'base_url': "http://localhost",
            'port': 8007,
            'timeout': 30
        }
    
    logger.debug(f"Retrieved vector_store settings: {settings}")
    return settings


def get_chunker_settings() -> Dict[str, Any]:
    """
    Get chunker service configuration settings.
    
    Retrieves chunker service connection settings from the framework configuration
    including base URL, port, and timeout values.
    
    Returns:
        Dict[str, Any]: Chunker settings with the following structure:
            - base_url (str): Base URL for chunker service
            - port (int): Port number for chunker service
            - timeout (int): Request timeout in seconds
    
    Example:
        >>> settings = get_chunker_settings()
        >>> print(settings['base_url'])  # "http://localhost"
        >>> print(settings['port'])  # 8009
    
    Raises:
        KeyError: If chunker settings are not found in configuration
    """
    settings = get_custom_setting_value('chunker', {})
    
    if not settings:
        logger.warning("No chunker settings found, using defaults")
        settings = {
            'base_url': "http://localhost",
            'port': 8009,
            'timeout': 30
        }
    
    logger.debug(f"Retrieved chunker settings: {settings}")
    return settings


def get_embedding_settings() -> Dict[str, Any]:
    """
    Get embedding service configuration settings.
    
    Retrieves embedding service connection settings from the framework configuration
    including base URL, port, and timeout values.
    
    Returns:
        Dict[str, Any]: Embedding settings with the following structure:
            - base_url (str): Base URL for embedding service
            - port (int): Port number for embedding service
            - timeout (int): Request timeout in seconds
    
    Example:
        >>> settings = get_embedding_settings()
        >>> print(settings['base_url'])  # "http://localhost"
        >>> print(settings['port'])  # 8001
    
    Raises:
        KeyError: If embedding settings are not found in configuration
    """
    settings = get_custom_setting_value('embedding', {})
    
    if not settings:
        logger.warning("No embedding settings found, using defaults")
        settings = {
            'base_url': "http://localhost",
            'port': 8001,
            'timeout': 30
        }
    
    logger.debug(f"Retrieved embedding settings: {settings}")
    return settings


def get_file_watcher_directories() -> List[str]:
    """
    Get list of directories to monitor from file watcher settings.
    
    Convenience function to extract just the directories list from
    file watcher configuration.
    
    Returns:
        List[str]: List of directory paths to monitor.
            Defaults to ["./documents", "./docs"] if not configured.
    
    Example:
        >>> directories = get_file_watcher_directories()
        >>> print(directories)  # ["./documents", "./docs"]
    """
    settings = get_file_watcher_settings()
    return settings.get('directories', ["./documents", "./docs"])


def get_file_watcher_scan_interval() -> int:
    """
    Get scan interval from file watcher settings.
    
    Convenience function to extract just the scan interval from
    file watcher configuration.
    
    Returns:
        int: Scan interval in seconds.
            Defaults to 300 (5 minutes) if not configured.
    
    Example:
        >>> interval = get_file_watcher_scan_interval()
        >>> print(interval)  # 300
    """
    settings = get_file_watcher_settings()
    return settings.get('scan_interval', 300)


def get_file_watcher_lock_timeout() -> int:
    """
    Get lock timeout from file watcher settings.
    
    Convenience function to extract just the lock timeout from
    file watcher configuration.
    
    Returns:
        int: Lock timeout in seconds.
            Defaults to 3600 (1 hour) if not configured.
    
    Example:
        >>> timeout = get_file_watcher_lock_timeout()
        >>> print(timeout)  # 3600
    """
    settings = get_file_watcher_settings()
    return settings.get('lock_timeout', 3600)


def get_file_watcher_max_processes() -> int:
    """
    Get maximum processes from file watcher settings.
    
    Convenience function to extract just the maximum processes from
    file watcher configuration.
    
    Returns:
        int: Maximum number of concurrent processes.
            Defaults to 5 if not configured.
    
    Example:
        >>> max_procs = get_file_watcher_max_processes()
        >>> print(max_procs)  # 5
    """
    settings = get_file_watcher_settings()
    return settings.get('max_processes', 5)


def get_vector_store_url() -> str:
    """
    Get vector store service URL.
    
    Convenience function to construct the full vector store service URL
    from base_url and port settings.
    
    Returns:
        str: Complete vector store service URL.
            Format: {base_url}:{port}
    
    Example:
        >>> url = get_vector_store_url()
        >>> print(url)  # "http://localhost:8007"
    """
    settings = get_vector_store_settings()
    base_url = settings.get('base_url', 'http://localhost')
    port = settings.get('port', 8007)
    return f"{base_url}:{port}"


def get_chunker_url() -> str:
    """
    Get chunker service URL.
    
    Convenience function to construct the full chunker service URL
    from base_url and port settings.
    
    Returns:
        str: Complete chunker service URL.
            Format: {base_url}:{port}
    
    Example:
        >>> url = get_chunker_url()
        >>> print(url)  # "http://localhost:8009"
    """
    settings = get_chunker_settings()
    base_url = settings.get('base_url', 'http://localhost')
    port = settings.get('port', 8009)
    return f"{base_url}:{port}"


def get_embedding_url() -> str:
    """
    Get embedding service URL.
    
    Convenience function to construct the full embedding service URL
    from base_url and port settings.
    
    Returns:
        str: Complete embedding service URL.
            Format: {base_url}:{port}
    
    Example:
        >>> url = get_embedding_url()
        >>> print(url)  # "http://localhost:8001"
    """
    settings = get_embedding_settings()
    base_url = settings.get('base_url', 'http://localhost')
    port = settings.get('port', 8001)
    return f"{base_url}:{port}"


def get_service_timeout(service_name: str) -> int:
    """
    Get timeout setting for a specific service.
    
    Generic function to get timeout setting for any DocAnalyzer service.
    
    Args:
        service_name (str): Name of the service.
            Must be one of: 'vector_store', 'chunker', 'embedding'.
    
    Returns:
        int: Timeout value in seconds.
            Defaults to 30 if not configured.
    
    Raises:
        ValueError: If service_name is not supported
    
    Example:
        >>> timeout = get_service_timeout('vector_store')
        >>> print(timeout)  # 30
    """
    supported_services = ['vector_store', 'chunker', 'embedding']
    
    if service_name not in supported_services:
        raise ValueError(f"Unsupported service: {service_name}. Must be one of {supported_services}")
    
    if service_name == 'vector_store':
        settings = get_vector_store_settings()
    elif service_name == 'chunker':
        settings = get_chunker_settings()
    elif service_name == 'embedding':
        settings = get_embedding_settings()
    
    return settings.get('timeout', 30) 