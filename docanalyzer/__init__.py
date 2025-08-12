"""
Document Analyzer Service Package.

A service for indexing documents by monitoring directories from configuration
and adding new documents to the database.
"""

__version__ = "1.0.0"
__author__ = "Document Analyzer Team"
__description__ = "Document indexing service with directory monitoring"

from docanalyzer.main import main

__all__ = ["main", "__version__"] 