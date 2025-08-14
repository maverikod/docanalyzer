"""
Unified Configuration Package - DocAnalyzer Unified Configuration Management

This package provides a unified configuration system that combines
DocAnalyzer-specific settings with the mcp_proxy_adapter framework
configuration into a single, coherent interface.

The package integrates with:
- mcp_proxy_adapter.core.settings for base configuration
- mcp_proxy_adapter.config for configuration management
- mcp_proxy_adapter.core.logging for logging integration

Author: DocAnalyzer Team
Version: 1.0.0
"""

# Legacy imports for backward compatibility
from .integration import DocAnalyzerConfig
from .extensions import (
    get_file_watcher_settings,
    get_vector_store_settings,
    get_chunker_settings,
    get_embedding_settings
)
from .validation import validate_docanalyzer_config

# New unified configuration
from .unified_config import (
    UnifiedConfig,
    ServerConfig,
    LoggingConfig,
    CommandsConfig,
    FileWatcherConfig,
    VectorStoreConfig,
    ChunkerConfig,
    EmbeddingConfig,
    ConfigError,
    ValidationError,
    get_unified_config,
    reload_unified_config
)

__all__ = [
    # Legacy exports for backward compatibility
    'DocAnalyzerConfig',
    'get_file_watcher_settings',
    'get_vector_store_settings', 
    'get_chunker_settings',
    'get_embedding_settings',
    'validate_docanalyzer_config',
    
    # New unified configuration exports
    'UnifiedConfig',
    'ServerConfig',
    'LoggingConfig',
    'CommandsConfig',
    'FileWatcherConfig',
    'VectorStoreConfig',
    'ChunkerConfig',
    'EmbeddingConfig',
    'ConfigError',
    'ValidationError',
    'get_unified_config',
    'reload_unified_config'
] 