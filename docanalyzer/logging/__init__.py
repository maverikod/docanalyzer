"""
Logging Module - Integration with mcp_proxy_adapter Framework

This module provides integration layer between DocAnalyzer and the
mcp_proxy_adapter framework's logging system.

It extends the framework's logging capabilities with DocAnalyzer-specific
logging configurations while maintaining compatibility with existing infrastructure.

Author: DocAnalyzer Team
Version: 1.0.0
"""

from .integration import DocAnalyzerLogger, LoggingConfig

__all__ = [
    'DocAnalyzerLogger',
    'LoggingConfig'
] 