"""
Configuration Integration Package - DocAnalyzer Configuration Management

This package provides integration with the mcp_proxy_adapter framework's
configuration system and extends it with DocAnalyzer-specific settings.

The package integrates with:
- mcp_proxy_adapter.core.settings for base configuration
- mcp_proxy_adapter.config for configuration management
- mcp_proxy_adapter.core.logging for logging integration

Author: DocAnalyzer Team
Version: 1.0.0
"""

from .integration import DocAnalyzerConfig
from .extensions import (
    get_file_watcher_settings,
    get_vector_store_settings,
    get_chunker_settings,
    get_embedding_settings
)
from .validation import validate_docanalyzer_config

__all__ = [
    'DocAnalyzerConfig',
    'get_file_watcher_settings',
    'get_vector_store_settings', 
    'get_chunker_settings',
    'get_embedding_settings',
    'validate_docanalyzer_config'
] 