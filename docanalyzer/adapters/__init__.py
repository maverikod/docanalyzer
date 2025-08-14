"""
Adapters Package - External Service Adapters

This package contains adapters for external services including vector stores,
metadata services, and other third-party integrations.

The adapters provide a unified interface for interacting with external services
while handling connection management, error handling, and data transformation.

Author: DocAnalyzer Team
Version: 1.0.0
"""

from .vector_store_adapter import VectorStoreAdapter

__all__ = ['VectorStoreAdapter'] 