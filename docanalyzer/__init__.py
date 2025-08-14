"""
Document Analyzer Service Package.

A service for indexing documents by monitoring directories from configuration
and adding new documents to the database.
"""

from docanalyzer._version import __version__, __version_tuple__, version, version_tuple

__author__ = "Document Analyzer Team"
__description__ = "Document indexing service with directory monitoring"

# Import _version module for testing purposes
import docanalyzer._version as _version

# Import submodules for testing purposes
import docanalyzer.logging
import docanalyzer.monitoring
import docanalyzer.adapters

__all__ = ["__version__", "__version_tuple__", "version", "version_tuple", "__author__", "__description__", "_version", "logging", "monitoring", "adapters"]

# Import main only when explicitly requested to avoid uvicorn dependency
def get_main():
    """Get the main function without importing it at module level."""
    from docanalyzer.main import main
    return main 